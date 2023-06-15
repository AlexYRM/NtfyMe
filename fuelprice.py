import json
import time
import base64
import datetime
import requests
import pytesseract
import pandas as pd
from PIL import Image
from io import BytesIO
from config import config
from db_connection import DBConnection


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
DB = DBConnection()
# DB.create_tables()


# Retrieve the data from the website and process it to return it as a string
def scraping(payload: str):
    # Send the POST request to the specified URL with payload and headers
    response = requests.post(url=DB.url, data=payload, headers=DB.headers)
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


# Change name and URL depending on what station is monitored
def website(st_name):
    if "PETROM" in st_name:
        return ["Petrom", "https://www.petrom.ro/ro-ro/persoane-fizice/localizator-statii"]
    else:
        return ["OMV", "https://www.omv.ro/ro-ro/statii-de-distributie-carburant/localizare-statii-omv"]


def extra_sorting(dict_data):
    # Define a dictionary mapping the original values to the desired values
    new_dict = {'OMV MaxxMotion Diesel': 'Motorina Premium', 'OMV MaxxMotion 95': 'Benzina Standard',
                'OMV MaxxMotion 100plus': 'Benzina Premium', 'OMV Diesel': 'Motorina Standard', 'GPL Auto': 'GPL',
                'Benzina Standard 95': 'Benzina Standard', 'Motorina Standard': 'Motorina Standard',
                'Benzina Extra 99': 'Benzina Premium', 'Motorina Extra': 'Motorina Premium'}
    # Retrieve the value associated with the key `dict_data` from the dictionary
    # If the key is not found, return the original `dict_data` value
    return new_dict.get(dict_data, dict_data)


# Sort the data into a dictionary for further use
def sort_data(info_text):
    sorted_data = dict()            # will store sorted data
    info_text_list = list()         # will store info_text split by newline
    fuel_type = list()              # variable which will store the fuel types
    fuel_price = list()             # variable which will store the fuel prices
    # Iterate through each row of the text extracted from the image and append to list
    for i in info_text.split("\n"):
        if i != "":
            info_text_list.append(i)
    # If there are more than 4 item in the list we will use this part of code to parse through this type of data
    if len(info_text_list) > 4:
        for i in info_text_list:
            # Save the Date in sorted_data
            if "Data" in i:
                sorted_data["Date"] = i.split(" ")[1]
            # Save the fuel prices
            elif "RON" in i:
                fuel_price.append(i.replace("RON", "").strip())
            # Save the fuel types
            elif i.strip():
                # Do not append "AdBlue" to fuel_type
                if "AdBlue" not in i:
                    fuel_type.append(extra_sorting(i))
    # Else we will parte the data with this code
    else:
        for i in info_text_list:
            # Save the Date in sorted_data
            if "Data" in i:
                sorted_data["Date"] = i[10:20]
            # Append the data to each list
            else:
                # Sort the string to no have "RON" termination, then split from last whitespace and append each side
                fuel_price.append(i.replace("RON", "").strip().rsplit(" ", 1)[1])
                fuel_type.append(extra_sorting(i.replace("RON", "").strip().rsplit(" ", 1)[0]))
    # In sorted_data create key "Stocare" with keys from the fuel_type list and values from the fuel_price list
    # This will be used to store the fuel prices for future expansion of the project to displaying price fluctuations
    sorted_data["Archiving"] = dict(zip(fuel_type, fuel_price))
    # Create a list of strings where each string contains an item from fuel_type and its corresponding item from fuel_price
    # This will be displayed to the user
    sorted_data["ForUser"] = [f"{item_1} = {item_2} RON" for item_1, item_2 in zip(fuel_type, fuel_price)]
    return sorted_data


def to_database(st_name, new_data):
    st_id = DB.get_or_create_station(st_name=st_name, omv_petrom_station_id=DB.station_ids[0])
    # Rearrange the data
    archiving_data = {"Date": new_data["Date"], "Station_ID": st_id}
    archiving_data.update(new_data['Archiving'])
    # Create a DataFrame from the data
    df = pd.DataFrame.from_records([archiving_data])
    if not DB.check_if_station_has_data_for_date(date=new_data["Date"], st_id=st_id):
        # Save the DataFrame to SQLite
        df.to_sql("fuel_data", DB.conn, if_exists='append', index=False)


# Create the text which will be sent, adjusted for the number of fuel types sold by the station
def correct_text(data, station_name):
    # Create the initial text with the date and station name
    txt = f"Pe data de {datetime.datetime.strptime(data['Date'], '%Y-%m-%d').strftime('%d %m %Y')} la statia " \
          f"{station_name} \npreturile la combustibili sunt urmatoarele:\n"
    # Iterate through the fuel price data
    for no in range(len(data['ForUser'])):
        # Create the text for each fuel type
        txt2 = f"\n{data['ForUser'][no]}"
        # Append the text to the main text
        txt += txt2
    return txt


# Send notification to the user with t
def send_notification():
    # Retrieve the station sequence list from the DB object.
    DB.station_sequence_list()
    # Iterate over the station IDs in the sequence list.
    for num in range(len(DB.station_ids)):
        # Scrape data by calling the scraping function with the payload created by DB.create_payload().
        srted_data = sort_data(scraping(DB.create_payload()))
        # Retrieve the station name using the current station ID from the DB object.
        station_name = DB.retrieve_station_name(DB.station_ids[0])
        # Adjust the text by calling the correct_text function with the scraped data and station name.
        user_displayed_text = correct_text(data=srted_data, station_name=station_name)
        # Saves the data to the database by calling the to_database function with the station name and scraped data.
        to_database(st_name=station_name, new_data=srted_data)
        # Send a notification using the requests.post method with the appropriate parameters.
        requests.post(
            config.create_ntfy_topic_name(station_id=DB.station_ids[0]),
            data=user_displayed_text.encode(encoding='utf-8'),
            headers={"Actions": f"view, Deschide siteul {website(station_name)[0]}, {website(station_name)[1]}; "
                                "view, Istoric preturi, https://ntfyme.safe.tere.ro/"}
        )
        # Removes the first station ID from the DB.station_ids list.
        DB.station_ids.pop(0)
        # Pause the execution for 15 seconds
        time.sleep(15)

