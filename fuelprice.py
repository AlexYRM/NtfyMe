import json
import base64
import datetime
import requests
import pytesseract
from PIL import Image
from io import BytesIO
from config import config

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Information for the POST request
url = "https://app.wigeogis.com/kunden/omv/data/details.php"
payload = "LNG=RO&CTRISO=ROU&VEHICLE=CAR&MODE=NEXTDOOR&BRAND=PETROM&ID=RO.1761.8&DISTANCE=0&HASH=4b04c7dad0af1b323512a2" \
          "fe682824c8dd687f98&TS=1684138447"
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "origin": "https://www.petrom.ro",
    "Accept": "application/json"
}

station_name = "statia Petrom din Constanta de pe strada Soveja(lac Tabacarie)"


# Retrieve the data from the website and process it to return it as a string
def scraping():
    # Send the POST request to the specified URL with payload and headers
    response = requests.post(url, data=payload, headers=headers)
    # Parse the response text as JSON and store it a variable
    raw_data_dict = json.loads(response.text)
    # Extract the encoded image data from the 'priceUrl' field of the dictionary
    encoded_image = raw_data_dict["priceUrl"].split(",")[1]
    # Decode the base64-encoded image data into bytes
    image_bytes = base64.b64decode(encoded_image)
    # Create a buffer containing the image data
    image_buffer = BytesIO(image_bytes)
    # Open the image from the buffer
    image = Image.open(image_buffer)
    # Use Tesseract OCR to extract text from the image
    text = pytesseract.image_to_string(image)
    return text


# Sort the data into a dictionary for further use
def sort_data(info_text):
    sorted_data = dict()            # will store sorted data
    fuel_type = list()              # variable which will store the fuel types
    fuel_price = list()             # variable which will store the fuel prices
    # iterate through each row of the text extracted from the image
    for i in info_text.split("\n"):
        # Save the Date in sorted_data
        if "Data" in i:
            sorted_data["Date"] = i.split(" ")[1]
        # Save the fuel types
        elif "Motorina" in i or "Benzina" in i or "GPL" in i:
            fuel_type.append(i)
        # Save the fuel prices
        elif "RON" in i:
            fuel_price.append(i.split()[0])

    # In sorted_data create key "Stocare" with keys from the fuel_type list and values from the fuel_price list
    # This will be used to store the fuel prices for future expansion of the project to displaying price fluctuations
    sorted_data["Archiving"] = dict(zip(fuel_type, fuel_price))
    # Create a list of strings where each string contains an item from fuel_type and its corresponding item from fuel_price
    # This will be displayed to the user
    sorted_data["ForUser"] = [f"{item_1} = {item_2} RON" for item_1, item_2 in zip(fuel_type, fuel_price)]
    return sorted_data


# Create the text which will be sent, adjusted for the number of fuel types sold by the station
def correct_text(data):
    txt = f"Pe data de {datetime.datetime.strptime(data['Date'], '%Y-%m-%d').strftime('%d %m %Y')} la {station_name} \n" \
          f"preturile la combustibili sunt urmatoarele:\n"
    for no in range(len(data['ForUser'])):
        txt2 = f"\n{data['ForUser'][no]}"
        txt += txt2
    return txt


# Send notification to the user with t
def send_notification():
    # user_displayed_text = correct_text(sort_data(scraping()))
    user_displayed_text = "Incercare FUELPRICE.py"
    requests.post(
        config.fuel_price,
        data=user_displayed_text.encode(encoding='utf-8'),
        headers={"Actions": "view, Deschide siteul, https://www.petrom.ro/ro-ro/persoane-fizice/localizator-statii"}
    )
