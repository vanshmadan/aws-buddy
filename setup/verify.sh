#!/usr/bin/env bash
# Checks the agent's role: it can look, it can apply the one fix, it can NOT delete.
cd "$(dirname "$0")"
source ../config.env
A="--profile $AGENT_PROFILE --region $AWS_REGION"
ok=0
check() { echo -n "$1 "; if eval "$2" >/dev/null 2>&1; then echo OK; else echo FAIL; ok=1; fi; }
check_denied() { echo -n "$1 "; if eval "$2" >/dev/null 2>&1; then echo "FAIL (it was allowed!)"; ok=1; else echo "OK (AccessDenied)"; fi; }

check        "agent can list buckets ............" "aws s3api list-buckets $A"
check        "agent can look inside a bucket ...." "aws s3api list-objects-v2 --bucket $PREFIX-website --max-keys 1 $A"
check        "agent can read security settings .." "aws s3api get-bucket-versioning --bucket $PREFIX-backups $A"
check_denied "agent CANNOT delete a bucket ......" "aws s3api delete-bucket --bucket $PREFIX-old-project $A"
check_denied "agent CANNOT read file contents ..." "aws s3api get-object --bucket $PREFIX-website --key index.html /dev/null $A"

[ $ok -eq 0 ] && echo "All good." || echo "Fix the FAIL lines before going on."
exit $ok
