import requests
import datetime
from config import config
from bs4 import BeautifulSoup

public_holiday = list()


# check if current day is in the list of public holidays
def check_public_holiday(data_dict, date):
    for elem in data_dict:
        if date in elem.values():
            return True
    else:
        return False


# get data from website regarding the requested year's public holidays and append them to a list
def api_data(yr):
    # make an API request with the year="yr" parameter and save the json to data variable
    response = requests.get("https://zilelibere.webventure.ro/api/" + yr)
    data = response.json()
    # iterate over the data and filter out public holidays that are not on weekends
    for iterated_data in data:
        if iterated_data["date"][0]["weekday"] not in ["Sun", "Sat"]:
            # change the format of the date
            new_date_format = datetime.datetime.strptime(iterated_data["date"][0]["date"], "%Y/%m/%d").strftime(
                "%Y-%m-%d")
            # create a public holiday dictionary with name and date
            public_holiday_dict = {"name": iterated_data["name"], "date": new_date_format}
            # add the dictionary to the list of public holidays
            public_holiday.append(public_holiday_dict)


def scraping():
    url = "https://www.cursbnr.ro/"
    response = requests.get(url)
    # save the response in Unicode format
    soup = BeautifulSoup(response.text, "html.parser")
    # save the first 3 elements of div tags with class="currency value"
    currency_values = soup.find_all("div", class_="currency-value")[:3]
    # join the list of currency values into one string
    values_text = ''.join([value.text for value in currency_values])
    print(values_text.strip())
    return values_text.strip()


def send_notification():
    print("SEND NOTIFICATION FUNCTION  exchange=> ")
    print(config.exchange)
    day = datetime.date.today()
    new_day_format = day.strftime("%d %B %Y")
    api_data(str(datetime.datetime.now().year))
    if check_public_holiday(public_holiday, day):
        # send notification that it is a public holiday and the exchange rate is the same as last time
        text = f"Astăzi este sărbătoare națională, iar cursul valutar va rămâne la fel. \n {scraping()}"
        requests.post(config.exchange, data=text.encode(encoding='utf-8'),
                      headers={"Actions": "view, Deschide siteul, https://www.cursbnr.ro/curs-bnr-azi"})
    else:
        # send notification with the exchange rate
        text = f"Cursul valutar pentru {new_day_format} este \n {scraping()}"
        requests.post(config.exchange, data=text.encode(encoding='utf-8'),
                      headers={"Actions": "view, Deschide siteul, https://www.cursbnr.ro/curs-bnr-azi"})


