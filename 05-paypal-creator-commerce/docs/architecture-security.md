# Architecture and security boundaries

## Components and data flow

```text
Browser (session cookie + CSRF, no PayPal secret)
  → FastAPI on 127.0.0.1
      → SQLite: sessions / projects / immutable revisions
      → local AI /v1/chat/completions, or explicitly labeled fixture
      → Pillow frames → FFmpeg H.264 preview (watermarked)
      → immutable internal order + server price + stable idempotency keys
      → PayPal Sandbox OAuth client-credentials token, Orders v2 create
  → approved Sandbox checkout URL → PayPal buyer approval → local return
  → server GET order → validate project association, amount, currency, payee
      → capture ONLY if APPROVED with no existing capture
      → GET complete authoritative order
      → verify COMPLETED capture, final_capture, exact amount and payee
      → transaction: unique capture + unique revision entitlement
  → authenticated export → actual 720×1280 H.264 file
```

`commerce/config.py` is the only environment-configuration entry point. `planner.py` validates bounded model output; `paypal.py` encapsulates official REST calls and evidence verification. `app.py` owns authenticated project/payment/export routes. `store.py` defines the durable ledger. `render.py` renders original artwork. `static/` contains dependency-free client HTML, CSS and JS.

## Identity, project and file boundaries

- A cryptographically random session cookie is hashed before storage and marked HttpOnly/SameSite=Lax. A separate session CSRF token must accompany every mutating request.
- State-changing API requests require an exact allowed loopback `Origin`, JSON content type and a 32 KiB body limit. Models use bounded lengths/counts/durations and reject extra fields. Host allowlisting reduces DNS-rebinding exposure. There is no CORS allowance.
- Every project, source JSON, preview, evidence, order and export request verifies the browser session. An order identifier supplied by another browser returns 404.
- File names come only from server-generated UUIDs and validated revision integers. Only `static/` is public; runtime databases, configuration, render caches and source code have no static route.
- CSP blocks external script/fonts/assets and framing. No front-end PayPal secret, bearer token or complete provider response is returned or logged. The client never receives payer billing details.
- Project revisions are immutable snapshots with hashes. A checkout is tied to a session, project, revision, SKU, price, currency and merchant. Edits while payment is uncertain are blocked. Optimistic revision numbers reject stale-tab writes.
- JSON imports strictly contain storyboard content, never rights, sessions or payment records.

## Payment invariants

The server's one SKU is `portrait-hd-export`: USD 4.99 test money. A client-supplied `amount`, `currency`, `paid`, or arbitrary PayPal order ID is rejected by schema. Checkout redirects and JavaScript events cannot directly grant a right.

PayPal API base is the constant `https://api-m.sandbox.paypal.com`. Redirects are not followed by the API client. Approval URLs must be HTTPS on `www.sandbox.paypal.com`, with no embedded credentials or nonstandard port. Custom/live payment hosts and modes are rejected. The HTTP client has connection and total-operation timeouts and ignores ambient proxy variables.

Before capture, the trusted remote order is checked against the stored PayPal ID, internal `reference_id`, `custom_id`, payee merchant ID, and exact currency/Decimal amount. Existing captures, including `PENDING`, are reconciled without another capture request. After capture, the server reads the full order and requires exactly one purchase unit and one final `COMPLETED` capture whose amount, currency and merchant match. Unexpected/partial/mismatched evidence fails closed.

Each order stores different UUID request IDs for create and capture. Retries reuse the same IDs. The order record commits before calling PayPal. Uncertain creation reuses its key only in a conservative five-minute window; older unknown creates are stopped for manual inspection, rather than inventing a fresh order. This is a safety bound, not a claim about PayPal's full retention period.

A transaction creates the capture and entitlement. Unique constraints cover provider order IDs, capture IDs, per-order rights and `(project, revision, mode)` rights. A process-wide lock serializes local checkout transitions. This is deliberately a single-process local service; a multi-worker/public deployment would need a durable distributed state-machine/locking design.

## Interrupted and rejected flows

- `CREATED`/`APPROVED` is not payment completion.
- Browser cancel marks local checkout `CANCELED` and leaves exports locked. It does not claim to void/refund a provider transaction; reopening uses the same known order.
- `PENDING` and `VERIFYING` retain the order. Cancel/edit cannot discard an uncertain payment. Refresh can query the same order. No automatic second checkout is created.
- Completed capture with a lost response is recovered by server GET of that same order. Capture retries first query provider state.
- Amount, currency, merchant, order or reference mismatch marks `REJECTED`; it grants nothing. This intentionally requires investigation rather than automatically collecting another payment.
- A later revision cannot borrow the previous revision's entitlement. Previously rendered purchased revisions remain downloadable through their original authenticated URL.
- Encoding failure does not remove the entitlement. Rerendering costs no extra test payment.
- Fixture endpoints are inaccessible in Sandbox mode. Fixture capture IDs and rights cannot satisfy Sandbox authorization.

## Explicit limits

There is no production payment capability, webhook, refund/dispute workflow, subscription, payout, remote LLM, arbitrary media upload, credential creation, cloud deployment, or public user-account system. No payment/compliance/eligibility assurances are implied. Do not expose this server publicly. Computer administrators can access its local files. Browser cookie deletion intentionally does not have an insecure recovery bypass.

Rendering is bounded to 24 seconds / 5 scenes and guarded by a process timeout. The app uses installed FFmpeg or the pinned package's encoder; it does not download model weights. A user-supplied system font path is configuration, never model-selected or browser-selected.
