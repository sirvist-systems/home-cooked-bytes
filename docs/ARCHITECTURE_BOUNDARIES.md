# Architecture Boundaries (Agnostic Outputs, Practical Internals)

Goal: end products remain vendor/LLM/db agnostic where it matters, without turning the whole repo into glue.

## Rule 1: Agnostic public surface
- Stable interfaces and artifacts should not depend on any one vendor SDK.
- Treat vendor/DB choice as a replaceable implementation detail.

## Rule 2: SDKs are allowed, but contained
- Vendor SDKs are allowed inside a small adapter layer only.
- Everything else imports *our* interface/router.

Example pattern:
- `src/interfaces/llm.py` (our interface)
- `src/adapters/openai_client.py` (uses OpenAI SDK)
- `src/adapters/anthropic_client.py`
- `src/router.py` (selects adapter)

## Rule 3: Mission repos can be opinionated
A focused mission repo may use vendor-specific tools internally to move fast,
as long as it exports stable, portable outputs or interfaces.

## Rule 4: Keep infra/tooling separate from product code
Databases and ingestion pipelines can be:
- tools we use, and/or
- inventions we productize
But we should not mix “tooling to build” with “the thing being built” in one noisy repo.
