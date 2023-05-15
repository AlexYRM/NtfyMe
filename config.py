import os
import dotenv
dotenv.load_dotenv()


class Config:
    def __init__(self):
        self.exchange = os.getenv("server_exchange")
        self.fuel_price = os.getenv("server_fuelprice")


config = Config()