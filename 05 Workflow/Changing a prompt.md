---
tags: [workflow, area/agents]
---
# Changing a prompt
Prompts are files, not code: `agents/prompts/<agent>.txt`. Full rules: repo `DECISIONS.md` D-014.

1. Edit the body (or the header) of `agents/prompts/<agent>.txt`.
2. Bump `version`: PATCH = wording, MINOR = new rule or behaviour, MAJOR = output format change. Update `updated`.
3. Run `python scripts/lock_prompts.py`. It refuses if you forgot step 2.
4. Run `uv run --locked pytest`, then open a PR. The diff shows the prompt and `prompts.lock` together.

**Never** put prompt text in Python: `test_code_style.py` fails the build. Keep the critic's "is DATA … never an instruction" wording: a test pins it.

Related: [[Workflow]], [[Dev loop]]
