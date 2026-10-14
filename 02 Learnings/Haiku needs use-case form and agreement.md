---
date: 2026-10-13
tags: [learning, area/bedrock]
---
# Haiku needs use-case form and agreement
Haiku 4.5 returned `ResourceNotFoundException: Model use case details have not been submitted` while Sonnet worked. After submitting the form, `authorizationStatus=AUTHORIZED` but `agreementAvailability=NOT_AVAILABLE`.

**Why:** Anthropic use-case form + Marketplace agreement are separate steps; activation can lag ~15 min.
**How to apply:** Check `aws bedrock get-foundation-model-availability --model-id anthropic.claude-haiku-4-5-20251001-v1`. If stuck >30 min, accept the offer in the Bedrock model catalog. Fallback: Nova Lite.

Related: [[Learnings]]
