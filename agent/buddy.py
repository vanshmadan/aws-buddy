"""AWS Buddy: chat with your AWS account in plain English.

    python buddy.py 1    no tools            -> it can only guess
    python buddy.py 2    + looking tools     -> it checks your real account
    python buddy.py 3    + one fixing tool   -> it can fix things, but asks you first
    python buddy.py 4    + "call any AWS API" -> too much power; IAM is what stops it

Type a question, press Enter. Type "exit" to quit. The conversation is remembered,
so follow-ups like "fix it" work.
"""
import copy
import sys

from strands import Agent

from model import MODEL_IDS, PROVIDER, is_busy_error, make_model
from tools import (REGION, session, list_buckets, bucket_details,
                   turn_on_block_public_access, call_any_aws_api)

STAGES = {
    1: [],
    2: [list_buckets, bucket_details],
    3: [list_buckets, bucket_details, turn_on_block_public_access],
    4: [list_buckets, bucket_details, turn_on_block_public_access, call_any_aws_api],
}

PROMPT = (
    "You are AWS Buddy, a friendly cloud assistant explaining an AWS account to students. "
    "Use simple words and keep answers short (under 8 lines). "
    "Only call tools you have actually been given; never invent tool names. "
    "If you have tools, use them to check before answering; never guess when a tool can tell you. "
    "If you have no tools, say plainly that you cannot see the account, then give a general answer. "
    "Before changing anything, explain what you will change and why."
)

stage = int(sys.argv[1]) if len(sys.argv) > 1 else 2
tools = STAGES[stage]
current = 0   # index into MODEL_IDS


def new_agent(messages=None):
    return Agent(model=make_model(session, MODEL_IDS[current]), system_prompt=PROMPT,
                 tools=tools, messages=messages)


print(f"AWS Buddy | stage {stage} | region {REGION} | model {PROVIDER}:{MODEL_IDS[current]}")
if len(MODEL_IDS) > 1:
    print(f"backup models: {', '.join(MODEL_IDS[1:])}")
print(f"tools: {', '.join(t.tool_name for t in tools) or 'none'}\n")

agent = new_agent()

while True:
    try:
        question = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if question.lower() in ("exit", "quit"):
        break
    if not question:
        continue

    history = copy.deepcopy(agent.messages)     # so a failed attempt leaves no half-finished turn
    while True:
        print("\nBuddy: ", end="", flush=True)
        try:
            agent(question)
            break
        except KeyboardInterrupt:
            agent = new_agent(history)
            print("\n[stopped]")
            break
        except Exception as err:
            if is_busy_error(err) and current + 1 < len(MODEL_IDS):
                current += 1
                print(f"\n[{MODEL_IDS[current - 1]} is busy, switching to {MODEL_IDS[current]}]")
                agent = new_agent(history)
                continue
            agent = new_agent(history)
            reason = "the model is busy, try again in a minute" if is_busy_error(err) else str(err)[:300]
            print(f"\n[could not answer: {reason}]")
            break
    print("\n")
