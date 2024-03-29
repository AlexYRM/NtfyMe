import os
import json
import dotenv
import requests
dotenv.load_dotenv()


class DopplerConfig:
    def __init__(self):
        self.doppler_token = os.getenv("doppler_token")
        self.url = "https://api.doppler.com/v3/configs/config/secrets/download?format=json"
        self.exchange = ""
        self.fuelprice = ""
        self.squash_url = ""
        self.squash_cookies = ""
        self.squash_payload = ""
        self.parsing_data()

    def download_secrets(self, token):
        payload = {}
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.request("GET", self.url, headers=headers, data=payload)
        return response.text

    def create_ntfy_topic_name(self, station_id: str):
        topic_name = f"https://ntfy.sh/{self.fuelprice}{station_id.replace('.', '_')}"
        return topic_name

    def parsing_data(self):
        json_data = self.download_secrets(self.doppler_token)
        data = json.loads(json_data)
        self.exchange = data.get("SERVER_EXCHANGE")
        self.fuelprice = data.get("SERVER_FUELPRICE")
        self.squash_url = data.get("SERVER_SQUASH_URL")
        self.squash_cookies = data.get("SQUASH_COOKIE")
        self.squash_payload = data.get("SQUASH_PAYLOAD")
        print(self.exchange)
        print(self.fuelprice)
        print(self.squash_url)
        print(self.squash_cookies)
        print(self.squash_payload)


config = DopplerConfig()
