import requests
from requests.auth import HTTPBasicAuth
import base64
import json
import datetime
import platform
import traceback
import httpx

from utils import normalize_and_validate_phone_number_ke
from core.errors import InvalidPhoneNumberException


from core import config


SETTINGS = config.GlobalSettings()


class MpesaAPI:
    def __init__(
        self, consumer_key, consumer_secret, business_shortcode, online_passkey
    ):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.business_shortcode = business_shortcode
        self.online_passkey = online_passkey

    async def get_mpesa_token(self):
        api_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                api_url, auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret)
            )

        if response.status_code == 200:
            return {
                "success": True,
                "detail": response.json(),
                "status_code": response.status_code,
                "token": response.json()["access_token"],
            }
        else:
            print("response::", response.text, response)
            return {
                "success": False,
                "detail": response.text
                or "Access token not granted. This is an error on our side, if it happens please report as soon as possible.",
                "status_code": response.status_code,
                "token": None,
            }

    def generate_password(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        data_to_encode = (
            f"{self.business_shortcode}{self.online_passkey}{timestamp}".encode("utf-8")
        )
        password = base64.b64encode(data_to_encode).decode("utf-8")
        return password, timestamp

    async def make_stk_push(self, phone, amount, callback_url):
        try:
            access_token = await self.get_mpesa_token()
            if access_token["success"]:
                try:
                    phone = normalize_and_validate_phone_number_ke(phone)
                except InvalidPhoneNumberException as e:
                    return {
                        "success": False,
                        "detail": str(e),
                        "status_code": 400,
                    }

                password, timestamp = self.generate_password()

                headers = {
                    "Authorization": f"Bearer {access_token['token']}",
                    "Content-Type": "application/json",
                }

                request_body = {
                    "BusinessShortCode": self.business_shortcode,
                    "Password": password,
                    "Timestamp": timestamp,
                    "TransactionType": "CustomerBuyGoodsOnline",
                    "Amount": amount,
                    "PartyA": phone,
                    "PartyB": 4858770,
                    "PhoneNumber": phone,
                    "CallBackURL": callback_url,
                    "AccountReference": "UNIQUE_REFERENCE",
                    "TransactionDesc": "Payment for shit",
                }

                api_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        api_url, json=request_body, headers=headers
                    )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "detail": json.loads(response.text),
                        "status_code": response.status_code,
                    }
                else:
                    return {
                        "success": False,
                        "detail": json.loads(response.text),
                        "status_code": response.status_code,
                    }
            else:
                return access_token

        except Exception as e:
            return {
                "success": False,
                "detail": {"errorMessage": str(e)},
                "trace": traceback.format_exc(),
                "status_code": 500,
            }


async def initiate_stk_push(phone, amount, callback_url):
    consumer_key = SETTINGS.C2B_CONSUMER_KEY
    consumer_secret = SETTINGS.C2B_CONSUMER_SECRET
    business_shortcode = SETTINGS.C2B_SHORTCODE
    online_passkey = SETTINGS.C2B_ONLINE_PASSKEY

    if platform.system() == "Windows":
        callback_url = "https://mucra.pythonanywhere.com/api/mchwapez/callback"

    mpesa_api = MpesaAPI(
        consumer_key, consumer_secret, business_shortcode, online_passkey
    )

    response = await mpesa_api.make_stk_push(phone, amount, callback_url)
    return response


if __name__ == "__main__":
    phone_number = "254114068425"
    amount_to_pay = "50"
    response = initiate_stk_push(
        phone_number, amount_to_pay, "htps://mucra.pythonanywhere.com"
    )
    print(response)
