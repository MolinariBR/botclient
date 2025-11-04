🪝 Webhook
Webhook Documentation
WARNING: The webhook is still in the beta phase. Breaking changes may occur.
Overview
A webhook is a way for our system to send real-time events to your server via HTTP requests, without your server needing to ask for the event. You can register an URL that will receive events right after they happen.
For example, you can use a webhook to be notified whenever a deposit's status is changed to depix_sent, refunded or other states. See also: https://docs.eulen.app/deposit-status-string-1443187m0
Registering a webhook
On your Telegram channel with Eulen, you can register a webhok with:
/registerwebhook <type> <url> <secret>
Type: What kind of event data will be sent. Currently, the only supported webhook type is deposit.
URL: The URL that events will be sent to.
Secret: You should create a secret of at least 16 characters. For maximum security, you can generate 32 random bytes as hex to use as a secret. You can do this by running this command on your terminal: openssl rand -hex 32.
Example Telegram command:
/registerwebhook deposit https://example.com/webhooks/deposit b4b8de163b9582b8281efa0be7360caba585b1c5240504a24c6dae43f504f922
If you want to follow the HTTP Basic Authorization standard (This is useful for compatibility with tools such as curl), you should do a Base64 of username:password
For example, partner:b4b8de163b9582b8281efa0be7360caba585b1c5240504a24c6dae43f504f922 would become cGFydG5lcjpiNGI4ZGUxNjNiOTU4MmI4MjgxZWZhMGJlNzM2MGNhYmE1ODViMWM1MjQwNTA0YTI0YzZkYWU0M2Y1MDRmOTIy
To encode the credentials in Base64, you can use this command on your terminal: echo -n 'username:password' | base64
Request Format (Deposit)
The deposit webhook sends a POST request with the following JSON body:
DepositWebhookBody
bankTxId
string 
required
blockchainTxID
string 
optional
customerMessage
string 
optional
A message passed by the customer when paying
payerName
string 
required
payerTaxNumber
string 
required
pixKey
string 
required
qrId
string 
optional
status
enum<string> 
(DepositStatus)
DepositStatus
required
Allowed values:
pending
depix_sent
under_review
canceled
error
refunded
expired
valueInCents
integer 
required
expiration
string 
optional
payerEUID
string 
required
Example:
{
  "bankTxId": "fitbank_E1320335420250228200542878498597",
  "blockchainTxID": "4c7dff78eddb910b912f633d83472981fa5b8447859a7c66e49957f2a88167af",
  "customerMessage": "Message from payer here",
  "payerName": "John Doe",
  "payerEUID": "EU123456789012345",
  "payerTaxNumber": "12345678901",
  "expiration":"2025-03-05T14:33:56-03:00",
  "pixKey": "68fa2517-5c6d-412d-b991-f0762eeec2e3",
  "qrId": "01954e29d3337e388d5d1cb846b0d053",
  "status": "depix_sent",
  "valueInCents": 12345
}
Authorization Header
This replicates the secret that was previously given when registering the webhook on Telegram. Example:
Authorization: Basic b4b8de163b9582b8281efa0be7360caba585b1c5240504a24c6dae43f504f922
Handling the webhook on your server
Please remember to:
⚠️ Verify the Authorization header to ensure the request is coming from the correct source.
Return a 200 OK response on successful processing.
Return a response within 15 seconds to avoid timeouts.
Use the deposits API for fallback in case the webhook fails.