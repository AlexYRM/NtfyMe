import os
import dotenv
dotenv.load_dotenv()


class Config:
    def __init__(self):
        self.exchange = os.getenv("server_exchange")
        self.fuelprice = os.getenv("server_fuelprice")
        self.squash_url = os.getenv("server_squash_url")
        self.squash_cookies = os.getenv("squash_cookies")
        self.squash_payload = os.getenv("squash_payload")

    def create_ntfy_topic_name(self, station_id: str):
        topic_name = f"https://ntfy.sh/{self.fuelprice}{station_id.replace('.', '_')}"
        return topic_name


config = Config()
