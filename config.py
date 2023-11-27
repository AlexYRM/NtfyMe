import os
import json
import dotenv
import requests
dotenv.load_dotenv()


class Config:
    def __init__(self):
        self.doppler_token = os.getenv("DOPPLER_TOKEN")
        self.url = "https://api.doppler.com/v3/configs/config/secrets/download?format=json"
        self.exchange = ""
        self.fuelprice = ""
        self.squash_url = ""
        self.squash_cookies = ""
        self.squash_payload = ""
        self.parsing_data()

    # Function to download secrets from doppler server by sending a get request
    def download_secrets(self, token):
        payload = {}
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.request("GET", self.url, headers=headers, data=payload)
        return response.text

    # Function to download and parse data from the Doppler and store them in the class attributes
    def parsing_data(self):
        # Download secrets using the provided token
        json_data = self.download_secrets(self.doppler_token)
        # Parse the downloaded JSON data
        data = json.loads(json_data)
        # Extract specific values from the parsed JSON data and store them in class attributes
        self.exchange = data.get("SERVER_EXCHANGE")
        self.fuelprice = data.get("SERVER_FUELPRICE")
        self.squash_url = data.get("SERVER_SQUASH_URL")
        self.squash_cookies = data.get("SQUASH_COOKIE")
        self.squash_payload = data.get("SQUASH_PAYLOAD")


config = Config()
