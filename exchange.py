import requests
import datetime
from dopplerconfig import config
from bs4 import BeautifulSoup


def check_weekend(today):
    if today.strftime("%A") in ["Saturday", "Sunday"]:
        return True
    else:
        return False


# get data from website regarding the requested year's public holidays and append them to a list
def api_data(yr):
    public_holiday = list()
    # make an API request with the year="yr" parameter and save the json to data variable
    response = requests.get("https://zilelibere.webventure.ro/api/" + yr)
    data = response.json()
    # iterate over the data and filter out public holidays that are not on weekends
    for iterated_data in data:
        for iter_date in iterated_data['date']:
            # change the format of the date
            new_date_format = datetime.datetime.strptime(iter_date["date"], "%Y/%m/%d").strftime("%d %m %Y")
            # add the dictionary to the list of public holidays
            public_holiday.append(new_date_format)
    return public_holiday


def scraping():
    url = "https://www.cursbnr.ro/"
    response = requests.get(url)
    # save the response in Unicode format
    soup = BeautifulSoup(response.text, "html.parser")
    # save the first 3 elements of div tags with class="currency value"
    currency_values = soup.find_all("div", class_="currency-value")[:3]
    # join the list of currency values into one string
    values_text = ''.join([value.text for value in currency_values])
    return values_text.strip()


def send_notification():
    print("SEND NOTIFICATION FUNCTION  exchange ")
    day = datetime.date.today()
    new_day_format = day.strftime("%d %m %Y")
    if new_day_format in api_data(str(datetime.datetime.now().year)):
        # send notification that it is a public holiday and the exchange rate is the same as last time
        text = f"Astăzi este sărbătoare națională, iar cursul valutar va rămâne la fel ca in ultima zi lucratoare. \n {scraping()}"
        requests.post(config.exchange, data=text.encode(encoding='utf-8'),
                      headers={"Actions": "view, Deschide siteul, https://www.cursbnr.ro/curs-bnr-azi"})
    elif check_weekend(day):
        # send notification that it is weekend and the exchange rate is the same as the last working day
        text = f"Astăzi este weekend, iar cursul valutar va rămâne la fel ca in ultima zi lucratoare. \n {scraping()}"
        requests.post(config.exchange, data=text.encode(encoding='utf-8'),
                      headers={"Actions": "view, Deschide siteul, https://www.cursbnr.ro/curs-bnr-azi"})
    else:
        # send notification with the exchange rate
        text = f"Cursul valutar pentru {new_day_format} este \n {scraping()}"
        requests.post(config.exchange, data=text.encode(encoding='utf-8'),
                      headers={"Actions": "view, Deschide siteul, https://www.cursbnr.ro/curs-bnr-azi"})
