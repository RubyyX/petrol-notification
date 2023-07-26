from datetime import datetime
import pytz
import sys
import requests
from bs4 import BeautifulSoup
import openai
import boto3

desired_day = "Saturday"
desired_day_2 = "Wednesday"

# set adelaide timezone and date/ time variables
local_tz = pytz.timezone('Australia/Adelaide')
current_datetime = datetime.now(local_tz)
current_day = current_datetime.strftime("%A")

# Format the date and time
formatted_date = current_datetime.strftime("%d/%m/%Y")
formatted_time = current_datetime.strftime("%I:%M:%S %p")

# print the current day and formatted date and time
print("Current Time is", current_day + " " + formatted_date + " " + formatted_time)

if current_day != desired_day and current_day != desired_day_2:
    print("Current Time is Invalid, Terminating Program...")
    sys.exit()

openai.api_key = "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"

# scraping accc website for buying tip ------

url = "https://www.accc.gov.au/consumers/petrol-and-fuel/petrol-price-cycles-in-major-cities"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# Find the appropriate div containing buying tips
main = soup.find_all(class_="clearfix text-formatted field field--name-field-accc-text field--type-text-long field--label-hidden field__item")[0]
list_items = main.find_all("ul")

# If there aren't at least 5 <ul> elements, print an error message and stop
if len(list_items) < 5:
    print(f"Error: Expected at least 5 <ul> elements in 'main', but found only {len(list_items)}")
    sys.exit()

# Get the text of the <p> element within the first <li> element within the fifth <ul>
adelaide_buying_tip = list_items[4].li.p.text

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


# defining core functions ------

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

# Gets 5th percentile price for a fuel type
def get_price(fuel_id):
    prices = get_prices_by_id(fuel_id)
    cleaned_prices = remove_outliers(prices)
    _, _, pctl_price = calculate_statistics(cleaned_prices, 5)
    return pctl_price

# Gets next ID for the DynamoDB table
def get_next_id(table):
    response = table.scan()
    items = response['Items']
    ids = [int(item['id']) for item in items]
    next_id = max(ids) + 1 if ids else 0
    return str(next_id)

# create user dictionary to store friends' details and fuel pref
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
        system_content="You are an AI language model who provides concise fuel buying tips suitable for push notifications.",
        user_content=f"""Rewrite the following Adelaide city buying tip to be extremely concise, pleasant to read, and convey certainty about the forecasted price movement. Recommend a user action in 8 words or less without labeling the tip.
Do not use full stops (periods) or quotation marks in the response, and ensure to use setnence case. Buying tip: {prompt}""",
        max_tokens=10,
        n=1,
        stop=None,
        temperature=1,
    )
    message = response.strip()
    return message

concise_adelaide_buying_tip = get_concise_buying_tip(adelaide_buying_tip)
adelaide_buying_tip = sentence_case(concise_adelaide_buying_tip).strip(".")

# insert price into the database ------

# function to return last record in database
def get_record(index=0):
    # Initialize a DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2', 
                            aws_access_key_id='AKIAXFDHSRD2URBMV25P',
                            aws_secret_access_key='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')

    # Get the DynamoDB table
    table = dynamodb.Table('pricedata')

    response = table.scan()

    items = sorted(response['Items'], key=lambda x: int(x['id']), reverse=True)

    if len(items) < 2: # return None if < 2 rows
        return None
    elif index == 1:
        return items[1] # return second most recent entry
    else:
        return items[0] # return most recent entry
    

# function to insert today's prices into the database
def insert_data():
    # Set up DynamoDB resource
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2', 
                            aws_access_key_id='AKIAXFDHSRD2URBMV25P', 
                            aws_secret_access_key='Qv/qUwtJNYqdw5xWx+zILhl2YmLvguCKK6FFxWfH')

    # Get your table
    table = dynamodb.Table('pricedata')

    # Get next ID
    next_id = get_next_id(table)

    # Get current date
    current_date = datetime.now().strftime("%d/%m/%Y")

    # Calculate 5th percentile prices
    u91_price = get_price(2) 
    u95_price = get_price(5) 
    u98_price = get_price(8)
    diesel_price = get_price(3) 

    # Create item to insert
    item = {
        'id': next_id,
        'date': current_date,
        'u91': str(u91_price),
        'u95': str(u95_price),
        'u98': str(u98_price),
        'diesel': str(diesel_price)
    }

    # Insert item
    table.put_item(Item=item)
    print("Today's fuel prices successfully uploaded DynamoDB ...")
    
    

# calculate percentage change ------

# insert today's prices into table
# insert_data()

# Retrieve the 2 most recent records
last_record = get_record()
second_last_record = get_record(1)

# pct change between new prices and last prices repsectively
def calc_pct_chng(rec0, rec1):
    
    # create a dictionary to store percentage changes
    pct_changes = {}

    if rec0 is None:
        
        print("ERROR: Database contains < 2 rows")
        
    else:
        
        # calculate and store percentage changes for each fuel type
        for fuel_type in ["u91", "u95", "u98", "diesel"]:
            try:
                old_price = float(rec1[fuel_type])
                new_price = float(rec0[fuel_type])
                percent_change = ((new_price/old_price) - 1) * 100
                pct_changes[fuel_type] = percent_change
            except KeyError:
                print(f"WARNING: data for {fuel_type} not found in DB in pct-change calculation")
    
    return pct_changes

# sending notifications loop ------

pct_changes = calc_pct_chng(last_record, second_last_record)
print("Percentage Changes: ")
print(pct_changes)

for user in users:
    percentile = 5
    prices = get_prices_by_id(user["preferred_fuel_id"])
    cleaned_prices = remove_outliers(prices)
    min_price, avg_price, pctl_price = calculate_statistics(cleaned_prices, percentile)

    fuel_name = get_fuel_name(user["preferred_fuel_id"])
    print(f"Fuel name for user {user['name']}: {fuel_name}")  # Debugging print statement

    if user["preferred_fuel_id"] == 3:  # Diesel
        price_to_use = avg_price
    else:  # Unleaded fuel types
        price_to_use = pctl_price

    price_to_use_moved = price_to_use / 10  # Move decimal three places to the left
    pct_chng = round(pct_changes.get(fuel_name.lower(), 'N/A'), 2)
    
    if pct_chng > 0:
        pct_chng = str("+" + str(pct_chng))
    else:
        pct_chng = str(pct_chng)
    
    notification_msg = f"{fuel_name} @{price_to_use_moved:.1f} ({pct_chng}%) {adelaide_buying_tip}"
    print(f"User: {user['name']}, Notification Message: {notification_msg}")
    
    # sending notification
    send_push_notification(user["user_key"], notification_msg, user['name'])
