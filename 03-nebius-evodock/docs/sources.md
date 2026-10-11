# Official documentation checked on 2026-10-11

1. https://docs.tokenfactory.nebius.com/quickstart — OpenAI-compatible endpoint, server-side NEBIUS_API_KEY and chat/completions request form.
2. https://api.tokenfactory.nebius.com/docs — official API reference. The page is JavaScript-rendered; direct OpenAPI JSON retrieval was not available in this research pass. Runtime model discovery is implemented as GET /v1/models and is verified by offline contract tests only, not a live account call.
3. https://github.com/nebius/token-factory-cookbook/blob/main/models/nemotron/nemotron3-super-120B.md — official NVIDIA model cookbook; regional US-central1 endpoint and exact Super model example. Example is not a hardcoded runtime selection.
4. https://docs.tokenfactory.nebius.com/ai-models-inference/json — JSON/JSON-schema options depend on model support; check the JSON mode tag on the actual model card. Local validation remains mandatory.
5. https://github.com/nebius/token-factory-cookbook/tree/main/models/nemotron — current official NVIDIA cookbook catalog; availability must still be discovered for the account.
6. https://nebiusglobalaihackathon.devpost.com/rules and https://nebiusglobalaihackathon.devpost.com/details/faqs — contest/service-access references supplied by the parent acceptance review. This code package does not assert final legal or eligibility verification and no submission occurred.
7. https://github.com/2929496964-wq/evovid-pocket — public MIT upstream; fixed base commit in PROVENANCE.md.

Only official provider documentation informs the integration design. All fixture content is synthetic. No service credentials or private user source material were used in research.
