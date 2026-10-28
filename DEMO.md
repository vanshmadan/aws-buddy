# Demo script: what to ask, stage by stage

Run `./setup/reset.sh` before each rehearsal so student-photos is risky again.

## Stage 1: no tools (about 2 min)
```bash
python buddy.py 1
```
- **Ask:** "Which of my S3 buckets are risky?"
- **Expect:** "I can't see your account", then generic advice.
- **Say:** "Smart, but blind. It's guessing. An AI on its own can't see your systems."

## Stage 2: give it eyes (about 5 min)
```bash
python buddy.py 2
```
- **Ask:** "What do I have in my AWS account?"
  - It calls `list_buckets`, then lists 4 buckets.
- **Ask:** "Which bucket is risky, and why?"
  - It calls `bucket_details` on each bucket by itself, then names student-photos (Block Public Access OFF).
- **Say:** "I never told it to check each bucket. It decided that. That's the agent loop."
- **Show:** the tool calls printed on screen, then open `tools.py` and show that a tool is just a Python function with a description.
- **Audience question:** let 1 or 2 students ask their own questions ("which is biggest?", "what's empty?").

## Stage 3: let it act, with permission (about 4 min)
```bash
python buddy.py 3
```
- **Ask:** "Find any risky bucket and fix it."
  - It finds student-photos, then asks `Approve? (y/n)`.
- **First answer `n`.**
- **Say:** "It wanted to change my account. I said no, and it stopped. That's human in the loop."
- **Ask again and answer `y`,** then: "Check it again."
  - It confirms Block Public Access is now ON.

## Stage 4: too much power (about 4 min)
```bash
python buddy.py 4
```
- **Say:** "Developers get lazy. Instead of narrow tools, they give the AI one tool that can call ANY AWS API."
- **Ask:** "Delete the old-project bucket, nobody uses it."
  - It calls `call_any_aws_api: s3.delete_bucket`, which gets `BLOCKED BY IAM: AccessDenied`.
  - If the model refuses on its own, run this instead: `aws s3api delete-bucket --bucket <prefix>-old-project --profile buddy`
- **Say:** "The prompt didn't stop it. The permissions did. Never rely on the AI to protect you."
- **Show:** `iam/agent-policy.json`, with no delete permission anywhere.

## After the session
```bash
./setup/reset.sh      # or ./setup/teardown.sh if you're done for good
```
