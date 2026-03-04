# simulate_mpesa_b2c_result.py
import json
import requests
from uuid import uuid4
from datetime import datetime

with open("ConversationID.json", "r") as f:
    data_file = json.load(f)

ConversationID = data_file.get("ConversationID")
OriginatorConversationID = data_file.get("OriginatorConversationID")
amount = data_file.get("amount")

print("ConversationID:", ConversationID)
print("OriginatorConversationID:", OriginatorConversationID)
print("amount:", amount)


payload = {
    "Result": {
        "ResultType": 0,
        "ResultCode": 0,
        "ResultDesc": "The service request is processed successfully.",
        "OriginatorConversationID": OriginatorConversationID,
        "ConversationID": ConversationID,
        "TransactionID": str(uuid4()),
        "ResultParameters": {
            "ResultParameter": [
                {"Key": "TransactionAmount", "Value": amount},
                {"Key": "TransactionReceipt", "Value": "ABC123DEF"},
                {
                    "Key": "B2CRecipientIsRegisteredCustomer",
                    "Value": "Y",
                },
                {"Key": "TransactionCompletedDateTime", "Value": "mpesa_datetime_now"},
                {"Key": "ReceiverPartyPublicName", "Value": "254712345678 - JOHN DOE"},
                {
                    "Key": "B2CChargesPaidAccountAvailableFunds",
                    "Value": "1450.00",
                },
                {"Key": "B2CUtilityAccountAvailableFunds", "Value": "1000000.00"},
                {"Key": "B2CWorkingAccountAvailableFunds", "Value": "500000.00"},
                {"Key": "Occasion", "Value": "Salary"},
                {"Key": "AccountReference", "Value": "REF-INV-001"},
            ]
        },
    }
}

# payload = {
#     "Result": {
#         "ResultType": 0,
#         "ResultCode": 1,
#         "ResultDesc": "Request rejected by the M-Pesa system (reason: Recipient unavailable).",
#         "OriginatorConversationID": OriginatorConversationID,
#         "ConversationID": ConversationID,
#         "TransactionID": None,
#         "ResultParameters": {
#             "ResultParameter": [
#                 {"Key": "FailedReason", "Value": "Recipient MSISDN not registered"},
#                 {"Key": "AttemptedAmount", "Value": "1500.00"},
#                 {"Key": "AttemptedDateTime", "Value": "mpesa_datetime_now()"},
#                 {"Key": "AccountReference", "Value": "REF-INV-001"},
#             ]
#         },
#     }
# }

url = "http://localhost:5000/api/m-pesa-callbacks/result/ResultURL/x"

headers = {"Content-Type": "application/json"}


def post_payload(url, payload):
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        print("Status:", resp.status_code)
        print("Response body:", resp.text)
    except requests.exceptions.RequestException as e:
        print("Request failed:", str(e))


if __name__ == "__main__":
    post_payload(url, payload)
