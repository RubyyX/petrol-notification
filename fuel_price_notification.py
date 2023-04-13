from datetime import datetime
import pytz
import sys

desired_day = "Saturday"
desired_day_2 = "Wednesday"

local_tz = pytz.timezone('Australia/Adelaide')  # Set the timezone to Adelaide
current_datetime = datetime.now(local_tz)  # Get the current date and time
current_day = current_datetime.strftime("%A")  # Get the current day

# Format the date and time
formatted_date = current_datetime.strftime("%d/%m/%Y")
formatted_time = current_datetime.strftime("%I:%M:%S %p")

# Print the current day and formatted date and time
print("Current Time is", current_day + " " + formatted_date + " " + formatted_time)

if current_day != desired_day and current_day != desired_day_2:
    print("Current Time is Invalid, Terminating Program...")
    sys.exit()

import requests
from bs4 import BeautifulSoup
import openai

openai.api_key = "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"

url = "https://www.accc.gov.au/consumers/petrol-and-fuel/petrol-price-cycles-in-major-cities"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

main = soup.find(class_="clearfix text-formatted field field--name-field-accc-text field--type-text-long field--label-hidden field__item")
list_items = main.find_all("ul")
adelaide_buying_tip = list_items[4].li.text

print("Buying Tip: " + adelaide_buying_tip)

def ask_gpt3(system_content, user_content, max_tokens, n=1, stop=None, temperature=0):
    openai.api_key = "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"

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": user_content
            }
        ],
        max_tokens=max_tokens,
        n=n,
        stop=stop,
        temperature=temperature,
    )

    message = response.choices[0].message['content'].strip().lower()
    return message


system_content_1 = "You are a helpful assistant that advises users whether to buy fuel or not based on buying tips."
user_content_1 = f"""Fuel prices in Adelaide move in cyclic fashion. If prices are high, they will fall, and vice versa. The current buying tip is: \"{adelaide_buying_tip}\".
Should I buy or not? It is critical that you only respond with one of two options: 'buy' or 'do not buy', as another program is dependent on the response format."""

# Get response from GPT and remove the expected period from the end
buying_decision = ask_gpt3(system_content_1, user_content_1, 10, 1, stop=None, temperature=0).strip(".")
print("GPT Decision: " + buying_decision)

import requests
import json
import numpy as np
from statistics import mean

def remove_outliers(prices):
    sorted_prices = sorted(prices)
    cleaned_prices = [sorted_prices[0]]

    for i in range(1, len(sorted_prices)):
        if sorted_prices[i] < 5000:
            cleaned_prices.append(sorted_prices[i])

    return cleaned_prices

def calculate_statistics(prices, percentile):
    min_price = min(prices)
    avg_price = round(mean(prices), 2)
    percentile_price = np.percentile(prices, percentile)
    return min_price, avg_price, percentile_price


def get_prices_by_id(fuel_id):
    url = "https://fppdirectapi-prod.safuelpricinginformation.com.au/Price/GetSitesPrices?countryId=21&geoRegionLevel=2&geoRegionId=189"
    headers = {
        "Authorization": "FPDAPI SubscriberToken=52c12b44-b208-4b74-8109-70a3c2c3aaef",
        "Content-type": "application/json"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = json.loads(response.text)
        prices = [site["Price"] for site in data["SitePrices"] if site["FuelId"] == fuel_id]
        if not prices:
            print(f"No prices found for Fuel ID {fuel_id}")
            return []
        return prices
    else:
        print(f"Error: Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        return []


def get_fuel_name(fuel_id):
    fuel_id_name_map = {
        2: "U91",
        3: "Diesel",
        4: "LPG",
        5: "U95",
        6: "ULSD",
        8: "U98",
        11: "LRP",
        12: "E10",
        13: "Premium e5",
        14: "Premium Diesel",
        16: "Bio-Diesel 20",
        19: "e85",
        21: "OPAL",
        22: "Compressed natural gas",
        23: "Liquefied natural gas",
        999: "e10/Unleaded",
        1000: "Diesel/Premium Diesel"
    }
    return fuel_id_name_map.get(fuel_id, "Unknown")

users = [
    {
        "name": "Ethan",
        "user_key": "u39w7x6rumuncui32usxk93nmfss43",
        "preferred_fuel_id": 8  # U98
    },
    {
        "name": "Keeley",
        "user_key": "urwdreq9cxn372v8gv5xeh2mozf9n7",
        "preferred_fuel_id": 2  # U91
    },
    {
        "name": "Connor",
        "user_key": "um4gi4nap93rg9jgxjkysfgyi2gdf5",
        "preferred_fuel_id": 2  # U91
    },
    {
        "name": "Tim",
        "user_key": "u8ujknymhjaei7dthsw2wc141m16zi",
        "preferred_fuel_id": 3  # Diesel
    },
    {
        "name": "Stasio",
        "user_key": "uie55xysyz3xbyx6n39ppcogrmqc81",
        "preferred_fuel_id": 8  # U98
    }

]

pushover_app_token = "a5bwbgc248vgcpp7bcuu99jz43v4f7"

# Replace the send_push_notification function with the following:
def send_push_notification(user_key, message, user_name):
    try:
        url = "https://api.pushover.net/1/messages.json"
        payload = {
            "token": pushover_app_token,
            "user": user_key,
            "message": message,
            "title": "Fuel Price Alert"
        }
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"Error sending notification to {user_name}: {response.text}")
    except Exception as e:
        print(f"Error sending notification to {user_name}: {e}")


def sentence_case(text):
    return text[0].upper() + text[1:]

def get_concise_buying_tip(prompt):
    response = ask_gpt3(
        system_content="You are an AI language model providing concise fuel buying tips for push notifications.",
        user_content=f"""Rewrite the following Adelaide buying tip to be extremely concise, pleasant to read, and convey certainty about the forecasted price movement. Recommend a user action in 8 words or less without labeling the tip.
Do not use full stops (periods) or quotation marks in the response, and ensure to use setnence case. Original tip: {prompt}""",
        max_tokens=10,
        n=1,
        stop=None,
        temperature=0,
    )
    message = response.strip()
    return message

concise_adelaide_buying_tip = get_concise_buying_tip(adelaide_buying_tip)
adelaide_buying_tip = sentence_case(concise_adelaide_buying_tip).strip(".")

for user in users:
    percentile = 5
    prices = get_prices_by_id(user["preferred_fuel_id"])
    cleaned_prices = remove_outliers(prices)
    min_price, avg_price, pctl_price = calculate_statistics(cleaned_prices, percentile)

    fuel_name = get_fuel_name(user["preferred_fuel_id"])

    if user["preferred_fuel_id"] == 3:  # Diesel
        price_to_use = avg_price
    else:  # Unleaded fuel types
        price_to_use = pctl_price

    price_to_use_moved = price_to_use / 10  # Move decimal three places to the left
    notification_msg = f"{fuel_name} {price_to_use_moved:.1f} | {adelaide_buying_tip}"
    print(f"User: {user['name']}, Notification Message: {notification_msg}")

    if buying_decision == "buy":
        send_push_notification(user["user_key"], notification_msg, user['name'])
    elif buying_decision == "do not buy":
        send_push_notification(user["user_key"], notification_msg, user['name'])
    else:
        send_push_notification(user["user_key"], notification_msg, user['name'])
