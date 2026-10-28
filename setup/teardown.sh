#!/usr/bin/env bash
# Deletes everything setup.sh created. Run after the session (inside the venv, it uses boto3).
cd "$(dirname "$0")"
source ../config.env
P="--profile $ADMIN_PROFILE --region $AWS_REGION"
for b in website student-photos backups old-project; do
  # removes every object and every old version, then the bucket
  python3 -c "import boto3,sys; b=boto3.Session(profile_name='$ADMIN_PROFILE',region_name='$AWS_REGION').resource('s3').Bucket('$PREFIX-$b'); b.object_versions.delete(); b.delete()" \
    && echo "deleted $PREFIX-$b"
done
aws iam delete-role-policy $P --role-name "$AGENT_ROLE" --policy-name buddy
aws iam delete-role $P --role-name "$AGENT_ROLE" && echo "deleted agent role"
echo "Done. Remove the [profile $AGENT_PROFILE] block from ~/.aws/config."
