💻 Examples
Common Response Format
Most Common Success Case
Every successful API call will return a response in the following format:
{
    "response": <obj-response>,
    "async": false
}
Where <obj-response> is a JSON map { ... } containing the response information, if any. The content of this object depends on each API; please refer to the documentation API Endpoints.
In Case of an Error
{
    "response": {
        "errorMessage" : <string-err>
    },
    "async": false
}
Where <string-err> is an error message in the form of a human-readable sentence.
In Case of Server Busy (async mode)
If the server is very busy, your request will automatically enter asynchronous mode. In this case, you must retry with the same nonce until you receive a response synchronously.
{
    "async": true,
    "expiration": <string-date-iso8601>
    "urlResponse": <string-url>
}
Where <string-date-iso8601> is a date in the format ISO 8601 like "2024-12-20T09:33:14.768Z" e.g., and <string-url> is a that points to the response in the future.
The expiration date means that the server will give up processing the message after a certain point. If you receive an asynchronous response, you have two options:
1.
simply retry the same call with the same nonce until it returns synchronously or up to the maximum expiration date limit.
2.
OR actively fetch the response from the URL returned in "urlResponse".
If you choose the second approach, remember that the format returned at the response URL is a JSON containing the content of <obj-response> directly.
Examples
 Note: The following codes are just a draft and was generated with the help of generative AI. If you find any errors, please report them to our team so we can make the necessary corrections.

 import requests
import secrets
import time
from datetime import datetime, timezone
from dateutil import parser

nonce = secrets.token_hex(16)
url = "https://depix.eulen.app/api/deposit"
headers = {
    "X-Nonce": nonce,
    "Authorization": "Bearer <token>",  # Replace with your token
    "Content-Type": "application/json",
}
body = {
    "amountInCents": 100
}

max_attempts = 10
attempts = 0
async_expiration = None

while True:
    response = requests.post(url, json=body, headers=headers, timeout=10)

    if response.status_code not in [200, 201, 202]:
        print(f"Request failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        break

    data = response.json()

    if data.get('async') is False:
        print(f"Response received: {data}")
        break
    elif data.get('async') is True:
        if not async_expiration:
            async_expiration = parser.isoparse(data.get('expiration'))
        if datetime.now(timezone.utc) >= async_expiration:
            print("Expiration reached. No response received in time.")
            break
        time.sleep(1)
    else:
        print("Unexpected response format.")
        print(f"Response: {data}")
        break

    attempts += 1
    if attempts >= max_attempts:
        print("Maximum number of attempts reached due to timeout.")
        break