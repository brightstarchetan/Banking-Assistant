import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import random

load_dotenv()
API_KEY = os.getenv('NESSIE_API_KEY')
if not API_KEY:
    print("Error: NESSIE_API_KEY not found in .env file or environment.")
    exit()

BASE_URL = 'http://api.nessieisreal.com'
HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json'}
PARAMS = {'key': API_KEY}

CUSTOMER_NAMES = ["Alice", "Tom", "Sam"]
CUSTOMER_DATA_FILE = "customer_data.py"

customer_id_map = {}
customer_account_id_map = {}
customer_security_map = {}
merchant_id_map = {}

SECURITY_ANSWERS = {
    "Alice": {
        "What is your mother's maiden name?": "Johnson",
        "What was the name of your first pet?": "Bobby",
        "In what city were you born?": "Austin"
    },
    "Tom": {
        "What is your mother's maiden name?": "Brown",
        "What was the name of your first pet?": "Max",
        "In what city were you born?": "San Francisco"
    },
    "Sam": {
        "What is your mother's maiden name?": "Smith",
        "What was the name of your first pet?": "Whiskers",
        "In what city were you born?": "New York"
    }
}

# Predefined merchants (we’ll create them via the API)
MERCHANTS = [
    {
        "name": "Starbucks",
        "category": "Coffee Shop",
        "address": {"street_number": "1", "street_name": "Main St", "city": "New York", "state": "NY", "zip": "10001"},
        "geocode": {"lat": 40.7128, "lng": -74.0060}
    },
    {
        "name": "Amazon",
        "category": "Retail",
        "address": {"street_number": "410", "street_name": "Terry Ave", "city": "Seattle", "state": "WA", "zip": "98109"},
        "geocode": {"lat": 47.6221, "lng": -122.3365}
    },
    {
        "name": "Walmart",
        "category": "Retail",
        "address": {"street_number": "702", "street_name": "S Main St", "city": "Bentonville", "state": "AR", "zip": "72712"},
        "geocode": {"lat": 36.3729, "lng": -94.2088}
    },
    {
        "name": "Apple Store",
        "category": "Electronics",
        "address": {"street_number": "767", "street_name": "5th Ave", "city": "New York", "state": "NY", "zip": "10153"},
        "geocode": {"lat": 40.7638, "lng": -73.9720}
    },
    {
        "name": "McDonald's",
        "category": "Restaurant",
        "address": {"street_number": "1100", "street_name": "Market St", "city": "San Francisco", "state": "CA", "zip": "94102"},
        "geocode": {"lat": 37.7793, "lng": -122.4192}
    },
    {
        "name": "Target",
        "category": "Retail",
        "address": {"street_number": "1000", "street_name": "N Broadway", "city": "Chicago", "state": "IL", "zip": "60610"},
        "geocode": {"lat": 41.9025, "lng": -87.6311}
    },
    {
        "name": "Best Buy",
        "category": "Electronics",
        "address": {"street_number": "7601", "street_name": "Metro Blvd", "city": "Bloomington", "state": "MN", "zip": "55439"},
        "geocode": {"lat": 44.8547, "lng": -93.2427}
    },
    {
        "name": "Whole Foods",
        "category": "Grocery",
        "address": {"street_number": "270", "street_name": "E 4th St", "city": "Austin", "state": "TX", "zip": "78701"},
        "geocode": {"lat": 30.2680, "lng": -97.7417}
    },
    {
        "name": "Uber",
        "category": "Transportation",
        "address": {"street_number": "1455", "street_name": "Market St", "city": "San Francisco", "state": "CA", "zip": "94103"},
        "geocode": {"lat": 37.7766, "lng": -122.4177}
    },
    {
        "name": "Lyft",
        "category": "Transportation",
        "address": {"street_number": "185", "street_name": "Berry St", "city": "San Francisco", "state": "CA", "zip": "94107"},
        "geocode": {"lat": 37.7765, "lng": -122.3910}
    },
    {
        "name": "Barnes & Noble",
        "category": "Bookstore",
        "address": {"street_number": "33", "street_name": "E 17th St", "city": "New York", "state": "NY", "zip": "10003"},
        "geocode": {"lat": 40.7333, "lng": -73.9897}
    },
    {
        "name": "Chipotle",
        "category": "Restaurant",
        "address": {"street_number": "201", "street_name": "E 13th St", "city": "New York", "state": "NY", "zip": "10003"},
        "geocode": {"lat": 40.7336, "lng": -73.9872}
    }
]

def create_customer(first_name):
    url = f'{BASE_URL}/customers'
    payload = {
        "first_name": first_name,
        "last_name": "Smith",
        "address": {
            "street_number": "123",
            "street_name": "Main St",
            "city": "Anytown",
            "state": "VA",
            "zip": "12345"
        }
    }
    try:
        response = requests.post(url, headers=HEADERS, params=PARAMS, data=json.dumps(payload))
        response.raise_for_status()
        return response.json().get('objectCreated', {}).get('_id')
    except requests.exceptions.RequestException as e:
        print(f"Error creating customer {first_name}: {e}")
        return None

def create_account(customer_id, nickname):
    url = f'{BASE_URL}/customers/{customer_id}/accounts'
    payload = {
        "type": "Checking",
        "nickname": f"{nickname}'s Checking",
        "rewards": 1000,
        "balance": 5000
    }
    try:
        response = requests.post(url, headers=HEADERS, params=PARAMS, data=json.dumps(payload))
        response.raise_for_status()
        return response.json().get('objectCreated', {}).get('_id')
    except requests.exceptions.RequestException as e:
        print(f"Error creating account for customer {customer_id}: {e}")
        return None

def create_merchant(merchant):
    url = f'{BASE_URL}/merchants'
    try:
        response = requests.post(url, headers=HEADERS, params=PARAMS, data=json.dumps(merchant))
        response.raise_for_status()
        merchant_id = response.json().get('objectCreated', {}).get('_id')
        if merchant_id:
            merchant_id_map[merchant['name']] = merchant_id
            print(f"Created merchant '{merchant['name']}' with ID {merchant_id}")
            return merchant_id
    except requests.exceptions.RequestException as e:
        print(f"Error creating merchant {merchant['name']}: {e}")
    return None

def create_purchases(account_id, num_purchases=10):
    url = f'{BASE_URL}/accounts/{account_id}/purchases'
    for i in range(num_purchases):
        purchase_date = (datetime.now() - timedelta(days=num_purchases - i)).strftime('%Y-%m-%d')
        merchant_name, merchant_id = random.choice(list(merchant_id_map.items()))
        payload = {
            "merchant_id": merchant_id,
            "medium": "balance",
            "purchase_date": purchase_date,
            "status": "completed",
            "amount": round(random.uniform(5.0, 150.0), 2),
            "description": f"{merchant_name} purchase"
        }
        try:
            response = requests.post(url, headers=HEADERS, params=PARAMS, data=json.dumps(payload))
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error creating purchase {i+1} for account {account_id}: {e}")
            break

def main():
    # Step 1: create merchants
    for merchant in MERCHANTS:
        create_merchant(merchant)

    # Step 2: create customers, accounts, and purchases
    for name in CUSTOMER_NAMES:
        customer_id = create_customer(name)
        if not customer_id:
            continue

        account_id = create_account(customer_id, name)
        if not account_id:
            continue

        customer_id_map[name] = customer_id
        customer_account_id_map[name] = account_id
        customer_security_map[name] = SECURITY_ANSWERS.get(name)

        create_purchases(account_id)
        print(f"Created customer, account, and purchases for {name}")
        print("-" * 20)

    # Step 3: write data to file
    try:
        with open(CUSTOMER_DATA_FILE, 'w') as f:
            f.write("# Auto-generated customer data\n\n")
            f.write(f"customer_id_map = {json.dumps(customer_id_map, indent=4)}\n\n")
            f.write(f"customer_account_id_map = {json.dumps(customer_account_id_map, indent=4)}\n\n")
            f.write(f"customer_security_map = {json.dumps(customer_security_map, indent=4)}\n\n")
            f.write(f"merchant_id_map = {json.dumps(merchant_id_map, indent=4)}\n")
        print(f"Customer data written to {CUSTOMER_DATA_FILE}")
    except IOError as e:
        print(f"Error writing file: {e}")

if __name__ == "__main__":
    main()
