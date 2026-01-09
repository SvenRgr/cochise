#!/usr/bin/env python3
"""Simple AWS connectivity check:
Tries to use boto3 to call STS GetCallerIdentity; if boto3 missing,
falls back to `aws sts get-caller-identity` CLI.
Prints concise status and exits with non-zero codes on error.
"""
import os
from dotenv import load_dotenv
import json
import subprocess
import sys

load_dotenv()

def check_with_boto3():
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, EndpointConnectionError, ClientError
    except Exception:
        return (False, "boto3-not-available")

    try:
        sts = boto3.client("sts")
        resp = sts.get_caller_identity()
        return (True, resp)
    except NoCredentialsError:
        return (False, "no-credentials")
    except EndpointConnectionError as e:
        return (False, f"endpoint-error: {e}")
    except ClientError as e:
        return (False, f"client-error: {e}")
    except Exception as e:
        return (False, f"unknown-error: {e}")


def check_with_awscli():
    try:
        proc = subprocess.run(["aws", "sts", "get-caller-identity", "--output", "json"], capture_output=True, text=True)
    except FileNotFoundError:
        return (False, "aws-cli-not-found")

    if proc.returncode != 0:
        return (False, f"aws-cli-error: {proc.stderr.strip()}")

    try:
        return (True, json.loads(proc.stdout))
    except Exception as e:
        return (False, f"parse-error: {e}")


def main():
    # load environment variables from .env if python-dotenv is available
    if load_dotenv:
        try:
            load_dotenv()
        except Exception:
            pass
    ok, data = check_with_boto3()
    if ok:
        print("AWS reachable via boto3:")
        print(json.dumps(data, indent=2))
        sys.exit(0)

    # boto3 not available or failed
    if data == "boto3-not-available":
        ok2, data2 = check_with_awscli()
        if ok2:
            print("AWS reachable via aws-cli:")
            print(json.dumps(data2, indent=2))
            sys.exit(0)
        else:
            print(f"AWS check failed (aws-cli): {data2}")
            sys.exit(3)

    # boto3 was available but returned an error
    if data == "no-credentials":
        print("AWS check failed: no credentials available for boto3")
        sys.exit(2)

    print(f"AWS check failed (boto3): {data}")
    sys.exit(4)

if __name__ == "__main__":
    main()
