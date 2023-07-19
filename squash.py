import re
import json
import requests
import datetime
from config import config
from bs4 import BeautifulSoup


class SquashConnection:
    def __init__(self):
        self.session = requests.session()
        self.login_url = "https://www.activ-squash.booking-sports.ro/"
        self.payload = config.squash_payload
        self.cookies = config.squash_cookies

    def daily_info(self, url, date):
        availability_dict = dict()
        message_list = list()
        response = self.session.get(url, cookies=json.loads(self.cookies))
        soup = BeautifulSoup(response.content, "html.parser")
        # Find the <a> tag with alt="Fa o rezervare"
        a_tag = soup.find_all('a', alt='Fa o rezervare', )
        if not a_tag:
            message_list = [f"Pe {date.day} {self.month_mapping(date=date.month)} nu este nici un teren liber. Reincearca mai tarziu, poate ai noroc!"]
        else:
            for elem in a_tag:
                if int(re.search(r"ora_start=(\d+)", elem["href"]).group(1)) >= 19:
                    day, month, year, start_time, field_no = self.reservation_info(elem["href"])
                    # If the hour is already writen append to the list, if not create a list and add the field number
                    if start_time in availability_dict:
                        availability_dict[start_time].append(field_no)
                    else:
                        availability_dict[start_time] = [field_no]
            if len(availability_dict) == 0:
                message_list = [f"Pe {date.day} {self.month_mapping(date=date.month)} nu este nici un teren liber "
                                f"intre 19 si 22. Reincearca mai tarziu, poate ai noroc!"]
            else:
                for hours, fields in availability_dict.items():
                    if fields:
                        x = f" Ora {hours} ({', '.join(str(f) for f in fields)})"
                        print(x)
                        message_list.append(x)
                date_msg = f"{date.day} ({self.date_mapping(date=date)}) {self.month_mapping(date=date.month)}"
                message_list.insert(0, date_msg)
        return message_list

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

    def reservation_info(self, raw_data):
        day = re.search(r"zi=(\d+)", raw_data).group(1)
        month = re.search(r"month=(\d+)", raw_data).group(1)
        month = self.month_mapping(month)
        year = re.search(r"year=(\d+)", raw_data).group(1)
        start_time = re.search(r"ora_start=(\d+)", raw_data).group(1)
        field_no = re.search(r"teren=(\d+)", raw_data).group(1)
        return day, month, year, start_time, field_no


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
        return month_dict.get(date)

    def date_mapping(self, date):
        day_dict = {
            "Monday": "Luni",
            "Tuesday": "Marti",
            "Wednesday": "Miercuri",
            "Thursday": "Joi",
            "Friday": "Vineri"
        }
        return day_dict.get(date.strftime('%A'))

    def format_message(self, msg):
        formatted_msg_list = []
        for sublist in msg:
            if len(sublist) > 1:
                formatted_msg_list.append(sublist[0])
                ora_items = sorted(sublist[1:], key=lambda x: int(re.search(r'\d+', x).group()))
                formatted_msg_list.append(", ".join(ora_items))
            else:
                formatted_msg_list.append(sublist[0])

        return "\n".join(formatted_msg_list)

    def notification_message(self):
        message = []
        with self.session as session:
            session.post(url=self.login_url, data=json.loads(self.payload)) # transform payload in a dict
            days_urls, n3xt_days = self.date_selection()
            for url, day in zip(days_urls, n3xt_days):
                message.append(self.daily_info(url=url, date=day))
        return self.format_message(message)

    def send_notification(self):
        print("incepe send_notification")
        msg = self.notification_message()
        print(config.squash_url)
        print(type(config.squash_url))
        requests.post(
            url=config.squash_url,
            data=msg,
            headers={
                "Actions": "http, Verifica din nou disponibilitatea, https://ntfyme.alexirimia.online/, method=POST body={\"check_squash_avbl\"}; "
                           "view, Fa o rezervare, https://www.activ-squash.booking-sports.ro/"}
        )


sq = SquashConnection()

# sq.send_notification()
