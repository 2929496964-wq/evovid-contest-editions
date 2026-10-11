# Existing Sandbox configuration and real acceptance run

This is guidance for the owner to configure an existing suitable developer setup. It does **not** create an account, application, OAuth grant or persistent credential, accept an agreement, or authorize real spending. If those steps are needed, the owner must handle them under the service's current terms. Do not put credentials in chat or a public deliverable.

## Configure on your own computer

1. Use an existing PayPal developer application in the **Sandbox** environment and its associated Sandbox business merchant. Obtain its **Sandbox client ID**, **Sandbox secret** and **merchant ID** through the owner's approved account access. An API client ID and merchant ID are distinct.
2. Copy `.env.example` to private `.env`. Set `PAYMENT_MODE=sandbox`, `PAYPAL_SANDBOX_CLIENT_ID`, `PAYPAL_SANDBOX_SECRET`, and `PAYPAL_SANDBOX_MERCHANT_ID`. The variables must all be present. Never use live credentials.
3. Start with `start.bat` / `start.sh`. Open the exact configured loopback address, normally `http://127.0.0.1:8715`. Set `PORT` to another unused local port if necessary. If you explicitly set `APP_ORIGIN`, its port must match `PORT`; only localhost/127.0.0.1 HTTP origins are accepted.
4. Confirm the persistent UI banner says **PAYPAL SANDBOX · TEST MONEY ONLY**. The fixture controls must not exist in this mode. A previous fixture purchase must show as locked in Sandbox.
5. Choose a fictional brief. For the real AI acceptance item, separately configure an already-running local model and select **My local AI model**. Save edits and render the actual preview.
6. Continue to PayPal Sandbox. The one-time price shown by this edition is **USD 4.99 in test money** for one revision's downloadable MP4, with no shipping/subscription. This prototype has no refund workflow. Use an appropriate existing **Sandbox buyer**, separate from the merchant. Never use a real buyer payment method or real funds.
7. Approve in the Sandbox checkout and return. The local server queries the order, validates details, captures, then queries again before rights are granted. Do not treat the return page as completion. If a browser blocks a return or the connection is interrupted, reopen the same studio and choose **Verify existing order**. If the server reports `APPROVED`, the explicit **Capture approved Sandbox order** control performs the next step. `PENDING` stays locked.
8. Download and play the MP4. Refresh and restart; confirm the same browser/session retains the purchased revision. Do not switch between `localhost` and `127.0.0.1` mid-flow.

## Verify before calling it an actual integration pass

Record only nonsecret evidence: application revision, model ID, brief/output hashes, project ID/revision, Sandbox order ID/capture ID, status, expected amount/currency/merchant, exported video hash, and the real screen flow. Do not record passwords, `.env`, client secret, bearer token, billing details or cookies. Show the persistent Sandbox banner.

A real model response must change the storyboard, preview and export. A real Sandbox buyer approval must lead to a verified capture. Check actual cancel/denial, refresh after capture, wrong project attempts and download. The unit tests/mock adapter are useful but **do not replace these tests**. After an actual successful run, update a separate acceptance record with its evidence; do not simply relabel the provided fixture files.

If the provider omits required order evidence or refuses configuration/checkout, the app intentionally stays locked and shows a recoverable/verification error. Inspect the existing order in the authorized Sandbox dashboard rather than repeatedly making new projects to pay again. Never weaken amount/merchant validation to make a demo pass.

## Official references consulted 2026-10-11

- [REST API authentication](https://developer.paypal.com/api/get-started/)
- [Orders v2 overview and GET](https://developer.paypal.com/api/orders/v2/)
- [Create order](https://developer.paypal.com/api/orders/v2/orders-create)
- [Capture order](https://developer.paypal.com/api/orders/v2/orders-capture)
- [Idempotency behavior](https://developer.paypal.com/api/rest/reference/idempotency/)
- [Hackathon requirements](https://paypalaihackathon.devpost.com/)
- [Official contest rules](https://paypalaihackathon.devpost.com/rules)

The adapter uses server REST Orders v2 plus redirect approval, not a hybrid of incompatible JS SDK versions. Webhooks, refunds and MCP are intentionally outside this minimum story.

## 中文安全提示

凭据只在用户自己的本地 `.env` 填写。缺少合规开发账户/应用时，由用户本人决定并完成开户、协议和凭据创建；本代码不代办。必须使用 Sandbox 商户和 Sandbox 测试买家，不使用真实资金。真实模型+Sandbox 端到端未实测前，不得将模拟样片或测试日志当成比赛实际支付证明。付款状态不确定时核实原订单，勿新建另一项目重复付款。
