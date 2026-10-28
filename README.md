# AWS Buddy: talk to your AWS account

An AI agent you chat with in plain English. Ask "which of my buckets are risky?" and it decides
which tools to call, checks your real AWS account, and answers. If something needs fixing, it
asks you before changing anything.

From the masterclass "Building AI Agents" at AIVISKAR 2026, CGC University, Mohali.

## The one idea

```
You ask a question
   -> the AI decides which tool to call
   -> the tool checks your real AWS account
   -> the AI reads the result, maybe calls another tool
   -> the AI answers
```

**An agent = an AI model + tools + a loop. Its permissions decide what it can break.**

## The 4 stages

| Stage | Tools it has | What you'll see |
| --- | --- | --- |
| 1 | none | It can only guess. An AI alone can't see your systems. |
| 2 | `list_buckets`, `bucket_details` | It checks your real account and finds the risky bucket. |
| 3 | + `turn_on_block_public_access` | It can fix the problem, but asks "Approve? (y/n)" first. |
| 4 | + `call_any_aws_api` | Too much power. Ask it to delete a bucket: IAM blocks it. |

## The demo world (created by `setup.sh`)

| Bucket | Story |
| --- | --- |
| `<prefix>-website` | Healthy: locked down, 4 small files |
| `<prefix>-student-photos` | **Risky:** Block Public Access is OFF |
| `<prefix>-backups` | Biggest: 5 backup files, versioning on |
| `<prefix>-old-project` | Forgotten: empty |

## Files

| Path | What it is |
| --- | --- |
| `config.env` | Your settings: admin profile, region, bucket prefix |
| `setup/setup.sh` | Creates the 4 buckets and the agent's limited IAM role |
| `setup/verify.sh` | Checks the agent can look but can't delete |
| `setup/reset.sh` | Makes student-photos risky again, to repeat the demo |
| `setup/teardown.sh` | Deletes everything |
| `agent/buddy.py` | The chat. `python buddy.py <stage>` |
| `agent/tools.py` | The 4 tools. Read the docstrings: that's what the AI reads |
| `agent/model.py` | Which AI model to use (Gemini, Claude API or Bedrock) |
| `iam/agent-policy.json` | What the agent is allowed to do. The real guardrail. |
| `DEMO.md` | Questions to ask, stage by stage |

## Setup

**You need:** an AWS account you can experiment in, AWS CLI v2, Python 3.10+.

**1. Install**
```bash
cd aws-buddy
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
chmod +x setup/*.sh
```

**2. Pick a model.** Gemini has a free tier: get a key at [aistudio.google.com](https://aistudio.google.com).
Put these in a file, e.g. `~/buddy.env`, and run `source ~/buddy.env` in every new terminal:
```bash
export AWS_REGION=ap-south-1           # same as config.env
export MODEL_PROVIDER=gemini
export GEMINI_API_KEY=<your key>
export MODEL_ID=gemini-3.5-flash
export MODEL_FALLBACKS=gemini-3.8-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite
```
Free tiers get busy ("503 high demand"). If the main model is busy, Buddy switches to the next
backup automatically and prints one line saying so.

**3. Configure.** Edit `config.env`: set `PREFIX` to something unique, like `aiviskar-<yourname>`.

**4. Create the demo world**
```bash
./setup/setup.sh
```
Paste the `[profile buddy]` block it prints into `~/.aws/config`, then:
```bash
./setup/verify.sh        # every line should say OK
```

**5. Chat**
```bash
cd agent
source ../config.env     # so the agent knows your PREFIX
python buddy.py 2
```

## Clean up
```bash
./setup/teardown.sh
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `The config profile (buddy) could not be found` | Paste the block from `setup.sh` into `~/.aws/config` |
| `AccessDenied` on everything | Your terminal's `AWS_REGION` differs from `config.env`. The first line of `buddy.py` prints the region it's using. |
| Blank answer | Try another model, e.g. `MODEL_ID=gemini-2.5-flash` |
| `429` / `RESOURCE_EXHAUSTED` | Free-tier limit hit. Wait a minute. |
| `BucketAlreadyExists` in setup | Someone else owns that name. Change `PREFIX` in `config.env`. |

## Build your own next

Swap in different tools and you have a different agent:
- **Cost finder:** tools that list idle EC2 instances, unattached disks, old snapshots
- **Security checker:** tools for open security groups, users without MFA, old access keys
- **Log explainer:** a tool that reads CloudWatch errors and summarises them

Keep the same rules: read-only tools by default, one narrow tool per change, a human approval before
any change, and IAM permissions that match.
# aws-buddy
