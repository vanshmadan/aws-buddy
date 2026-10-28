#!/usr/bin/env bash
# Puts student-photos back into its "risky" state so you can run the fix demo again.
cd "$(dirname "$0")"
source ../config.env
aws s3api put-public-access-block --profile "$ADMIN_PROFILE" --region "$AWS_REGION" \
  --bucket "$PREFIX-student-photos" \
  --public-access-block-configuration BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false \
  && echo "student-photos is risky again (Block Public Access OFF). Ready for the next run."
