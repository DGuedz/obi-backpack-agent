
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('CMC_API_KEY')
url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
headers = {
    'X-CMC_PRO_API_KEY': api_key,
    'Accept': 'application/json'
}
params = {
    'start': '1',
    'limit': '5',
    'convert': 'USD'
}

print(f"Testing Key: {api_key[:5]}...")
try:
    response = requests.get(url, headers=headers, params=params)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Data received.")
        data = response.json()
        print(f"Top 1: {data['data'][0]['name']}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
