import json
import requests

with open("CheckoutRequestID.json", "r") as f:
    data_file = json.load(f)

checkout_request_id = data_file["CheckoutRequestID"]
amount = data_file["amount"]

payload = {
    "Body": {
        "stkCallback": {
            "MerchantRequestID": "1b9c-4f44-9990-c96a0f32b46416940412",
            "CheckoutRequestID": checkout_request_id,  # Loaded dynamically
            "ResultCode": 0,
            "ResultDesc": "The service request is processed successfully.",
            "CallbackMetadata": {
                "Item": [
                    {"Name": "Amount", "Value": amount},
                    {"Name": "MpesaReceiptNumber", "Value": "TCN6S9WZDY"},
                    {"Name": "TransactionDate", "Value": 20250323134822},
                    {"Name": "PhoneNumber", "Value": 254114068425},
                ]
            },
        }
    }
}

# payload = {
#     "Body": {
#         "stkCallback": {
#             "MerchantRequestID": "1b9c-4f44-9990-c96a0f32b46416940412",
#             "CheckoutRequestID": checkout_request_id,  # Loaded dynamically
#             "ResultCode": 1,
#             "ResultDesc": "Request flabbergasted by user. Fuck, Fuck, Fuck",
#             "CallbackMetadata": {
#                 "Item": [
#                     {"Name": "Amount", "Value": 30},
#                     {"Name": "MpesaReceiptNumber", "Value": "TCN6S9WZDY"},
#                     {"Name": "TransactionDate", "Value": 20250323134822},
#                     {"Name": "PhoneNumber", "Value": 254114068425},
#                 ]
#             },
#         }
#     }
# }

url = "http://localhost:5000/api/m-pesa-callbacks/c2b-callback"
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)

print("Status:", response.status_code)
print("Response:", response.text)
