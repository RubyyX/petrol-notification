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
        model="gpt-3.5-turbo",
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

from pushover import init, Client
import requests
import json
from statistics import mean

def get_min_avg_fuel_price_by_id(fuel_id):
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
            return None, None
        min_price = min(prices)
        avg_price = round(mean(prices), 2)
        return min_price, avg_price
    else:
        print(f"Error: Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        return None, None

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
        "preferred_fuel_id": 8  # Unleaded fuel
    },
    {
        "name": "Keeley",
        "user_key": "urwdreq9cxn372v8gv5xeh2mozf9n7",
        "preferred_fuel_id": 2  # Unleaded fuel
    },
    {
        "name": "Connor",
        "user_key": "um4gi4nap93rg9jgxjkysfgyi2gdf5",
        "preferred_fuel_id": 2  # Unleaded fuel
    },
    {
        "name": "Tim",
        "user_key": "usuiknymhiaei7dthsw2wc141m16zi",
        "preferred_fuel_id": 3  # Unleaded fuel
    }
    
]

pushover_app_token = "a5bwbgc248vgcpp7bcuu99jz43v4f7"

def send_push_notification(user_key, message, user_name):
    try:
        init(pushover_app_token)
        client = Client(user_key)
        client.send_message(message, title="Fuel Price Alert")
    except Exception as e:
        print(f"Error sending notification to {user_name}: {e}")
    
def sentence_case(text):
    return text[0].upper() + text[1:]

def get_concise_buying_tip(prompt):
    response = ask_gpt3(
        system_content="You are a helpful assistant that rephrases sentences to make men extremely concise and suitable for short push notifications.",
        user_content=f"""Please make this Adelaide buying tip extremely concise. Ensure it also sounds pleasant to read for a short push notification. Furthermore, ensure
you use language that makes the notification sound certain about the forecasted price movement, and doesn't use speculative language. Do not label the notification e.g.:
'Adelaide buying tip: ...', just keep it concise. Keep to 6 words or less. Buying tip: {prompt}""",
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.5,
    )
    message = response.strip()
    return message

concise_adelaide_buying_tip = get_concise_buying_tip(adelaide_buying_tip)
adelaide_buying_tip = sentence_case(concise_adelaide_buying_tip).strip(".")

for user in users:
    min_fuel_price, average_fuel_price = get_min_avg_fuel_price_by_id(user["preferred_fuel_id"])
    min_fuel_price_moved = min_fuel_price / 10  # Move decimal three places to the left
    fuel_name = get_fuel_name(user["preferred_fuel_id"])
    
    notification_msg = f"{fuel_name} {min_fuel_price_moved:.1f} | {adelaide_buying_tip}"
    print(f"User: {user['name']}, Notification Message: {notification_msg}")
    
    if buying_decision == "buy":
        send_push_notification(user["user_key"], notification_msg, user['name'])
    elif buying_decision == "do not buy":
        send_push_notification(user["user_key"], notification_msg, user['name'])
    else:
        send_push_notification(user["user_key"], notification_msg, user['name'])