from pydantic_settings import BaseSettings, SettingsConfigDict


class GlobalSettings(BaseSettings):
    DATABASE_URL: str

    C2B_CONSUMER_KEY: str
    C2B_CONSUMER_SECRET: str
    C2B_SHORTCODE: str
    C2B_ONLINE_PASSKEY: str

    B2C_CONSUMER_KEY: str
    B2C_CONSUMER_SECRET: str
    B2C_SHORTCODE: str
    B2C_INITIATOR_NAME: str
    B2C_SECURITY_CREDENTIAL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
