#!/usr/bin/env bash
# Creates the demo world: 4 S3 buckets with different "stories", plus the agent's limited IAM role.
#   <prefix>-website        healthy: locked down, a few small files
#   <prefix>-student-photos RISKY: Block Public Access turned OFF
#   <prefix>-backups        biggest: versioning on, ~25 MB of files
#   <prefix>-old-project    forgotten: empty
set -euo pipefail
cd "$(dirname "$0")"
source ../config.env
P="--profile $ADMIN_PROFILE --region $AWS_REGION"

ACCOUNT=$(aws sts get-caller-identity $P --query Account --output text)
echo "Account $ACCOUNT, region $AWS_REGION, prefix $PREFIX"
TMP=$(mktemp -d)

echo "== 1/5 Buckets"
for b in website student-photos backups old-project; do
  aws s3 mb "s3://$PREFIX-$b" $P >/dev/null && echo "   created $PREFIX-$b"
done

echo "== 2/5 Files"
for f in index.html about.html style.css logo.png; do head -c 4000 /dev/urandom > "$TMP/$f"; done
aws s3 cp "$TMP/" "s3://$PREFIX-website/" --recursive $P >/dev/null
for i in $(seq 1 12); do head -c 300000 /dev/urandom > "$TMP/photo_$i.jpg"; done
aws s3 cp "$TMP/" "s3://$PREFIX-student-photos/" --recursive --exclude "*" --include "photo_*" $P >/dev/null
for d in mon tue wed thu fri; do head -c 5000000 /dev/urandom > "$TMP/db-backup-$d.sql.gz"; done
aws s3 cp "$TMP/" "s3://$PREFIX-backups/" --recursive --exclude "*" --include "db-backup-*" $P >/dev/null
echo "   uploaded demo files"

echo "== 3/5 Bucket settings"
aws s3api put-bucket-versioning $P --bucket "$PREFIX-backups" --versioning-configuration Status=Enabled
# The risky one: switch OFF Block Public Access (no public policy is added; the risk is the open door)
if aws s3api put-public-access-block $P --bucket "$PREFIX-student-photos" \
     --public-access-block-configuration BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false; then
  echo "   student-photos: Block Public Access OFF (this is the risk the agent should find)"
else
  echo "   WARNING: could not turn off Block Public Access on student-photos (account policy?). Demo still works, it just won't find a risky bucket."
fi

echo "== 4/5 Agent role (read-only + one fix, no delete)"
sed -e "s/PREFIX/$PREFIX/g" ../iam/agent-policy.json > "$TMP/policy.json"
aws iam create-role $P --role-name "$AGENT_ROLE" \
  --assume-role-policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::$ACCOUNT:root\"},\"Action\":\"sts:AssumeRole\"}]}" >/dev/null
aws iam put-role-policy $P --role-name "$AGENT_ROLE" --policy-name buddy --policy-document "file://$TMP/policy.json"
rm -rf "$TMP"

echo "== 5/5 Done. Add this to ~/.aws/config (once):"
cat <<EOF

[profile $AGENT_PROFILE]
role_arn = arn:aws:iam::$ACCOUNT:role/$AGENT_ROLE
source_profile = $ADMIN_PROFILE
region = $AWS_REGION

Then run:  ./setup/verify.sh
EOF
