"""
Ingest the supplied Walmart CSV batch from local storage to Amazon S3.

Why this script exists:
- The source files were supplied locally as one controlled project batch.
- Instead of manually uploading each file, this utility validates the complete
  batch, uploads it to S3, verifies the uploaded objects, and writes a manifest.
- The script simulates the responsibilities of an upstream producer in a small
  portfolio/project setting.

This is intentionally not a fully generic ingestion framework. It is specific
 to the Walmart project delivery and checks exactly the files/columns expected
for this assignment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
import pandas as pd
from botocore.exceptions import ClientError


# Resolve important local folders from the script location instead of assuming
# the user runs the script from a specific directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_DIR = PROJECT_ROOT / "manifests"


# This dictionary is the batch contract for the project.
#
# It says:
# - exactly which files are expected
# - exactly which columns each file should contain
#
# For this controlled project, being strict is useful. If a file is missing,
# renamed, or has unexpected columns, the script should stop before uploading.
#
# A more generic version of this utility could move this contract into a YAML
# config file instead of hardcoding it here.
EXPECTED_FILES: dict[str, list[str]] = {
    "stores.csv": ["Store", "Type", "Size"],
    "department.csv": ["Store", "Dept", "Date", "Weekly_Sales", "IsHoliday"],
    "fact.csv": [
        "Store",
        "Date",
        "Temperature",
        "Fuel_Price",
        "MarkDown1",
        "MarkDown2",
        "MarkDown3",
        "MarkDown4",
        "MarkDown5",
        "CPI",
        "Unemployment",
        "IsHoliday",
    ],
}


def parse_args() -> argparse.Namespace:
    """Define command-line options for the script.

    argparse lets the script be reused without editing the code every time.

    The `default=` value is used when the option is not provided.
    The `help=` text appears when running the script with `-h` or `--help`.
    """
    parser = argparse.ArgumentParser(
        description="Validate and upload the Walmart local CSV batch to S3."
    )
    parser.add_argument("--aws-profile", default="retail-poc", help="Local AWS CLI profile to use.")
    parser.add_argument("--bucket", default="walmart-sales-landing-jenny", help="Destination S3 bucket name.")
    parser.add_argument("--prefix", default="landing/walmart/batch_01", help="Destination S3 prefix for this batch.")
    parser.add_argument("--batch-label", default="original_source", help="Human-readable label for this batch.")
    parser.add_argument("--allow-overwrite", action="store_true", help="Allow overwriting existing S3 objects.")
    return parser.parse_args()


def calculate_md5(path: Path) -> str:
    """Calculate an MD5 checksum for a local file.

    A checksum is a file fingerprint. If the file content changes, the checksum
    changes too.

    MD5 is not used here for security. It is used as a simple integrity check
    for a controlled project batch. In stricter production, SHA-256 or cloud
    object checksums may be preferred.
    """
    md5 = hashlib.md5()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            md5.update(chunk)
    return md5.hexdigest()


def validate_local_file(filename: str, expected_columns: list[str]) -> dict[str, Any]:
    """Validate one local CSV file and collect metadata about it.

    This function answers:
    - Does the expected file exist?
    - Does it contain the expected columns in the expected order?
    - How many rows does it contain?
    - How large is the file?
    - What is its checksum?
    """
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing required source file: {path}")

    df = pd.read_csv(path)
    actual_columns = list(df.columns)
    if actual_columns != expected_columns:
        raise ValueError(
            f"Unexpected columns for {filename}\n"
            f"Expected: {expected_columns}\n"
            f"Actual:   {actual_columns}"
        )

    return {
        "filename": filename,
        "source_path": str(path.relative_to(PROJECT_ROOT)),
        "row_count": int(len(df)),
        "column_count": int(len(actual_columns)),
        "columns": actual_columns,
        "size_bytes": int(path.stat().st_size),
        "md5": calculate_md5(path),
    }


def s3_object_exists(s3_client: Any, bucket: str, key: str) -> bool:
    """Return True when the destination S3 object already exists.

    This protects the original batch from being overwritten by accident.
    """
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code")
        if error_code in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def upload_file(s3_client: Any, bucket: str, key: str, local_path: Path, md5: str) -> None:
    """Upload one local file to S3.

    The checksum is stored as object metadata so the later verification step can
    confirm that the expected file was uploaded to the expected object.
    """
    s3_client.upload_file(
        Filename=str(local_path),
        Bucket=bucket,
        Key=key,
        ExtraArgs={"Metadata": {"source-md5": md5}},
    )


def verify_uploaded_file(s3_client: Any, bucket: str, key: str, expected_size: int, expected_md5: str) -> dict[str, Any]:
    """Verify the uploaded S3 object using metadata.

    This does not re-download the whole file. It checks:
    - S3 ContentLength matches the local file size.
    - The stored source-md5 metadata matches the local checksum.
    """
    response = s3_client.head_object(Bucket=bucket, Key=key)
    actual_size = int(response["ContentLength"])
    metadata = response.get("Metadata", {})
    actual_md5 = metadata.get("source-md5")

    if actual_size != expected_size or actual_md5 != expected_md5:
        raise ValueError(
            f"S3 verification failed for s3://{bucket}/{key}\n"
            f"Expected size: {expected_size}, actual size: {actual_size}\n"
            f"Expected md5:  {expected_md5}, actual md5:  {actual_md5}"
        )

    return {
        "s3_key": key,
        "s3_uri": f"s3://{bucket}/{key}",
        "verified_size_bytes": actual_size,
        "verified_source_md5": actual_md5,
        "verification_status": "passed",
    }


def main() -> None:
    """Run the complete local-to-S3 batch ingestion workflow."""
    args = parse_args()
    prefix = args.prefix.strip("/")

    # Optional safety check: if EXPECTED_AWS_ACCOUNT_ID is set in the shell,
    # stop when the AWS profile points to a different account.
    # This is useful when multiple AWS accounts are in use and the user wants
    # to avoid accidentally uploading to the wrong account 
    expected_account_id = os.getenv("EXPECTED_AWS_ACCOUNT_ID")

    session = boto3.Session(profile_name=args.aws_profile)
    sts_client = session.client("sts")
    s3_client = session.client("s3")

    identity = sts_client.get_caller_identity()
    account_id = identity.get("Account")
    if expected_account_id and account_id != expected_account_id:
        raise PermissionError(f"AWS account mismatch. Expected {expected_account_id}, actual {account_id}")

    ingestion_timestamp = datetime.now(timezone.utc)
    ingestion_timestamp_text = ingestion_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

    print("Walmart local batch ingestion")
    print("-----------------------------")
    print(f"AWS profile:     {args.aws_profile}")
    print(f"AWS account:     {account_id}")
    print(f"S3 bucket:       {args.bucket}")
    print(f"S3 prefix:       {prefix}")
    print(f"Batch label:     {args.batch_label}")
    print(f"Ingestion time:  {ingestion_timestamp_text}")
    print()

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "project": "walmart-sales-analytics-engineering",
        "batch_label": args.batch_label,
        "ingestion_timestamp_utc": ingestion_timestamp_text,
        "aws_profile": args.aws_profile,
        "aws_account_id": account_id,
        "s3_bucket": args.bucket,
        "s3_prefix": prefix,
        "files": [],
    }

    print("1. Validating local source files")
    validated_files = []
    for filename, expected_columns in EXPECTED_FILES.items():
        file_metadata = validate_local_file(filename, expected_columns)
        validated_files.append(file_metadata)
        print(f"   OK {filename}: {file_metadata['row_count']:,} rows, {file_metadata['size_bytes']:,} bytes")

    print()
    print("2. Checking destination objects")
    for file_metadata in validated_files:
        filename = file_metadata["filename"]
        s3_key = f"{prefix}/{filename}"
        exists = s3_object_exists(s3_client, args.bucket, s3_key)
        if exists and not args.allow_overwrite:
            raise FileExistsError(
                f"Destination already exists: s3://{args.bucket}/{s3_key}\n"
                "Use --allow-overwrite only if you intentionally want to replace it."
            )
        status = "exists; overwrite allowed" if exists else "available"
        print(f"   OK s3://{args.bucket}/{s3_key} -> {status}")

    print()
    print("3. Uploading files to S3")
    for file_metadata in validated_files:
        filename = file_metadata["filename"]
        local_path = DATA_DIR / filename
        s3_key = f"{prefix}/{filename}"

        upload_file(s3_client=s3_client, bucket=args.bucket, key=s3_key, local_path=local_path, md5=file_metadata["md5"])
        verification = verify_uploaded_file(
            s3_client=s3_client,
            bucket=args.bucket,
            key=s3_key,
            expected_size=file_metadata["size_bytes"],
            expected_md5=file_metadata["md5"],
        )

        file_manifest = {**file_metadata, **verification}
        manifest["files"].append(file_manifest)
        print(f"   UPLOADED {verification['s3_uri']}")

    manifest_filename = f"{args.batch_label}_{ingestion_timestamp.strftime('%Y%m%dT%H%M%SZ')}_manifest.json"
    local_manifest_path = MANIFEST_DIR / manifest_filename
    local_manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    manifest_s3_key = f"{prefix}/_manifest/{manifest_filename}"
    s3_client.put_object(
        Bucket=args.bucket,
        Key=manifest_s3_key,
        Body=local_manifest_path.read_bytes(),
        ContentType="application/json",
        Metadata={"batch-label": args.batch_label},
    )

    print()
    print("4. Manifest written")
    print(f"   Local: {local_manifest_path}")
    print(f"   S3:    s3://{args.bucket}/{manifest_s3_key}")
    print()
    print("INGESTION COMPLETE")
    print("------------------")
    print(f"Uploaded file count: {len(manifest['files'])}")
    print(f"Landing prefix: s3://{args.bucket}/{prefix}/")



if __name__ == "__main__":
    main()
