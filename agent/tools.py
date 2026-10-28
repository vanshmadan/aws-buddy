"""The agent's tools. Each one is a normal Python function with a docstring.

The docstring is what the AI reads to decide WHEN to use the tool.
Everything runs as the limited `buddy` AWS role (see iam/agent-policy.json).
"""
import os

import boto3
from strands import tool

REGION = os.environ.get("AWS_REGION", "ap-south-1")
PREFIX = os.environ.get("PREFIX", "aiviskar-vansh")
session = boto3.Session(profile_name=os.environ.get("AGENT_PROFILE", "buddy"), region_name=REGION)
s3 = session.client("s3")

PRICE_PER_GB_MONTH = 0.025   # approximate S3 Standard price, USD; for estimates only


# ---------- Looking tools (read-only) ----------

@tool
def list_buckets() -> str:
    """List all S3 buckets (storage folders) in this AWS account, with their creation date."""
    rows = [f"{b['Name']}  (created {b['CreationDate']:%Y-%m-%d})" for b in s3.list_buckets()["Buckets"]]
    return "\n".join(rows) or "No buckets."


@tool
def bucket_details(bucket: str) -> str:
    """Show what's inside one bucket and how it is secured: number of files, total size,
    estimated monthly cost, whether Block Public Access is ON, encryption and versioning.

    Args:
        bucket: The exact bucket name.
    """
    count, size = 0, 0
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            count += 1
            size += obj["Size"]

    try:
        cfg = s3.get_public_access_block(Bucket=bucket)["PublicAccessBlockConfiguration"]
        public_block = "ON (safe)" if all(cfg.values()) else "OFF (risky: files could be made public)"
    except s3.exceptions.ClientError:
        public_block = "NOT SET (risky)"

    try:
        rules = s3.get_bucket_encryption(Bucket=bucket)["ServerSideEncryptionConfiguration"]["Rules"]
        encryption = rules[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
    except s3.exceptions.ClientError:
        encryption = "none"

    versioning = s3.get_bucket_versioning(Bucket=bucket).get("Status", "Off")
    mb = size / 1_000_000
    cost = size / 1_000_000_000 * PRICE_PER_GB_MONTH
    return (f"bucket: {bucket}\nfiles: {count}\nsize: {mb:.1f} MB\n"
            f"estimated cost: ${cost:.4f} per month\n"
            f"block public access: {public_block}\nencryption: {encryption}\nversioning: {versioning}")


# ---------- Acting tool (changes something, so a human must approve) ----------

@tool
def turn_on_block_public_access(bucket: str, reason: str) -> str:
    """Turn ON Block Public Access for a bucket so nothing in it can be made public.
    This changes the account, so a human must approve it first.

    Args:
        bucket: The exact bucket name.
        reason: One line explaining why.
    """
    print(f"\n>>> The agent wants to turn ON Block Public Access for: {bucket}")
    print(f">>> Reason: {reason}")
    if input(">>> Approve? (y/n) ").strip().lower() != "y":
        return "The human said no. Do not retry."
    s3.put_public_access_block(Bucket=bucket, PublicAccessBlockConfiguration={
        "BlockPublicAcls": True, "IgnorePublicAcls": True,
        "BlockPublicPolicy": True, "RestrictPublicBuckets": True})
    return f"Done: Block Public Access is now ON for {bucket}."


# ---------- The dangerous idea (stage 4 only) ----------

@tool
def call_any_aws_api(service: str, operation: str, parameters: dict) -> str:
    """Call ANY AWS API. Example: service="s3", operation="delete_bucket", parameters={"Bucket": "x"}.

    Args:
        service: AWS service name, e.g. "s3".
        operation: Operation name in snake_case, e.g. "delete_bucket".
        parameters: Arguments for the call.
    """
    print(f"\n>>> call_any_aws_api: {service}.{operation}({parameters})")
    try:
        result = getattr(session.client(service), operation)(**parameters)
        result.pop("ResponseMetadata", None)
        return f"Success: {str(result)[:1500]}"
    except Exception as e:
        print(f">>> BLOCKED BY IAM: {e}")
        return f"Error: {e}"
