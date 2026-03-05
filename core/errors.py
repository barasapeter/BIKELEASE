INVALID_PHONE_MESSAGE = "The phone number provided is invalid. Please confirm you have provided a valid phone number."
SHOP_NOT_FOUND_MESSAGE = "Shop requested not found."


class InvalidPhoneNumberException(Exception):
    def __init__(self, message: str = INVALID_PHONE_MESSAGE, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class ShopNotFoundError(Exception):
    def __init__(self, message: str = SHOP_NOT_FOUND_MESSAGE, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message
