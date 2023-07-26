import re
import json
import requests
import datetime
from bs4 import BeautifulSoup
from dopplerconfig import config


class SquashConnection:
    def __init__(self):
        self.session = requests.session()
        self.login_url = "https://www.activ-squash.booking-sports.ro/"
        self.payload = config.squash_payload
        self.cookies = config.squash_cookies

    #  Retrieves daily information about squash court availability
    def daily_info(self, url, date):
        # Dictionary to store available hours and their corresponding field numbers
        availability_dict = dict()
        # List to store the messages for each day's availability
        message_list = list()
        # Send a GET request to the URL. Use json.loads to convert JSON formatted string to dictionary
        response = self.session.get(url, cookies=json.loads(self.cookies))
        # Parse the response content with BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        # Find the <a> tag with alt="Fa o rezervare"
        a_tag = soup.find_all('a', alt='Fa o rezervare', )
        # If no available slots are found, create a message indicating that there are no available fields that day
        if not a_tag:
            message_list = [f"Pe {date.day} {self.month_mapping(date=date.month)} nu este nici un teren liber. "
                            f"Reincearca mai tarziu, poate ai noroc!"]
        # If available slots are found, process each <a> tag
        else:
            for elem in a_tag:
                # Check if the start time for the reservation is greater than or equal to 19 (7 PM)
                if int(re.search(r"ora_start=(\d+)", elem["href"]).group(1)) >= 19:
                    # Extract day, month, year, start_time, and field_no information from the <a> tag's href attribute
                    day, month, year, start_time, field_no = self.reservation_info(elem["href"])
                    # If the hour is already written, append the field number to the list, else create a new list
                    if start_time in availability_dict:
                        availability_dict[start_time].append(field_no)
                    else:
                        availability_dict[start_time] = [field_no]
            # If there are no available slots between 19 and 22, create a message indicating the same
            if len(availability_dict) == 0:
                message_list = [f"Pe {date.day} {self.month_mapping(date=date.month)} nu este nici un teren liber "
                                f"intre 19 si 22. Reincearca mai tarziu, poate ai noroc!"]
            # If there are available slots between 19 and 22, create messages for each available slot
            else:
                for hours, fields in availability_dict.items():
                    if fields:
                        # Create a message for each hour and its corresponding available fields
                        x = f" Ora {hours} ({', '.join(str(f) for f in fields)})"
                        message_list.append(x)
                # Insert the date message at the beginning of the message list
                date_msg = f"{date.day} ({self.date_mapping(date=date)}) {self.month_mapping(date=date.month)}"
                message_list.insert(0, date_msg)
        return message_list

    # This function selects the next 5 days (excluding weekends) to check squash court availability
    def date_selection(self):
        days_urls = list()
        n3xt_days = list()
        current_date = datetime.date.today()
        five_days = [current_date + datetime.timedelta(days=i) for i in range(7)]
        for date in five_days:
            if date.weekday() not in [5, 6]:  # Exclude Saturdays and Sundays (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
                url = f"https://www.activ-squash.booking-sports.ro/index.php?ozi={date.day}&month={date.month}&year=" \
                      f"{date.year}&lang=ro&sport_id=1"
                days_urls.append(url)
                n3xt_days.append(date)
        return days_urls, n3xt_days

    # This function extracts reservation information from the raw_data provided
    def reservation_info(self, raw_data):
        day = re.search(r"zi=(\d+)", raw_data).group(1)
        month = re.search(r"month=(\d+)", raw_data).group(1)
        month = self.month_mapping(month)
        year = re.search(r"year=(\d+)", raw_data).group(1)
        start_time = re.search(r"ora_start=(\d+)", raw_data).group(1)
        field_no = re.search(r"teren=(\d+)", raw_data).group(1)
        return day, month, year, start_time, field_no

    # Define a dictionary that maps month numbers to month names in Romanian
    def month_mapping(self, date):
        month_dict = {
            1: "Ianuarie",
            2: "Februarie",
            3: "Martie",
            4: "Aprilie",
            5: "Mai",
            6: "Iunie",
            7: "Iulie",
            8: "August",
            9: "Septembrie",
            10: "Octombrie",
            11: "Noiembrie",
            12: "Decembrie"
        }
        # Use the date argument to get the month number, then use the month_dict to get the corresponding month name
        return month_dict.get(date)

    # Define a dictionary that maps English day names to day names in Romanian
    def date_mapping(self, date):
        day_dict = {
            "Monday": "Luni",
            "Tuesday": "Marti",
            "Wednesday": "Miercuri",
            "Thursday": "Joi",
            "Friday": "Vineri"
        }
        # Use the date argument to get the English day name, then use the day_dict to get the corresponding Romanian day name
        return day_dict.get(date.strftime('%A'))

    # Format a message from a list to a string
    def format_message(self, msg):
        formatted_msg_list = []
        for sublist in msg:
            # If there is more than one item in the sublist, extract the first item and add it to the formatted_msg_list
            if len(sublist) > 1:
                # Add the first item to the formatted_msg_list
                formatted_msg_list.append(sublist[0])
                # Sort the remaining items in the sublist by their numeric value (assuming they have a number in them)
                ora_items = sorted(sublist[1:], key=lambda x: int(re.search(r'\d+', x).group()))
                # Join the sorted items with a comma and add them to the formatted_msg_list
                formatted_msg_list.append(", ".join(ora_items))
            else:
                # If there is only one item in the sublist, add it to the formatted_msg_list as is
                formatted_msg_list.append(sublist[0])
        # Join the formatted_msg_list items with newline characters to create the final formatted message
        return "\n".join(formatted_msg_list)

    # Scrape for information on specific dates and create a formatted message to be used later on
    def notification_message(self):
        # Initialize an empty list to store messages
        message = []
        with self.session as session:
            # Perform a POST request to log in using the specified payload
            # Use json.loads to convert the payload from JSON formatted string to dictionary
            session.post(url=self.login_url, data=json.loads(self.payload))
            # Get a list of URLs and corresponding dates using the date_selection method
            days_urls, n3xt_days = self.date_selection()
            # Iterate through the URLs and dates using zip
            for url, day in zip(days_urls, n3xt_days):
                # Call the daily_info method to get availability information for each day
                message.append(self.daily_info(url=url, date=day))
        # Format the collected messages and return the final formatted message
        return self.format_message(message)

    # Send notification to ntfy app
    def send_notification(self):
        print("Start SquashNotification")
        # Call the notification_message method to get the formatted message
        msg = self.notification_message()
        # Perform a POST request to the squash URL with the formatted message as data and additional headers
        print(f"MESAJUL ESTE =>{msg}")
        print(config.squash_payload)
        print(config.squash_cookies)
        print(config.squash_url)
        requests.post(
            url=config.squash_url,
            data=msg,
            headers={
                "Actions": "http, Verifica din nou disponibilitatea, https://ntfyme.alexirimia.online/check_squash_avbl, "
                           "method=POST, headers.accept=application/json; "
                           "view, Fa o rezervare, https://www.activ-squash.booking-sports.ro/"}
        )


sq = SquashConnection()
