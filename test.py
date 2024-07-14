import requests
import json
import sqlite3
from datetime import datetime
import time
import pandas as pd

URL = 'https://api-admin.billz.ai/v1'
AUTH_ENDPOINT = '/auth/login'
ACCEPT_HEADER = 'application/json'
CONTENT_TYPE_HEADER = 'application/json'
TOKEN_PREFIX = 'Bearer '
global access_token, status
status = "404"

SECRET_TOKEN = "ecdd4e117df3f684ba2bfc55234bfdcc8847b1e914a4904f2e348857db1d694b629fef32b909e4f3a972c37bcf6fab0c41a53bd720a5cc01e4196fd01db9c17fa664c73948d5c730703bf4c0f4c17dd45e8876f91d794da74147f4752b36125d7423bd074c7ff79d8d2c73e7e4aefb9425c118a59dbd37c7"

def get_new_token(SECRET_TOKEN):
    headers = {
        'accept': ACCEPT_HEADER,
        'Content-Type': CONTENT_TYPE_HEADER
    }
    data = {
        "secret_token": SECRET_TOKEN
    }
    try:
        response = requests.post(URL + AUTH_ENDPOINT, headers=headers, data=json.dumps(data))
        global status
        status = response.status_code
        new_token = response.json().get('data', {}).get('access_token')

        if new_token:
            # UPDATE TOKEN FROM DATABASE
            conn = sqlite3.connect('database/credentials.db')
            cursor = conn.cursor()

            cursor.execute("UPDATE credential SET value = ? WHERE name = 'token'", (new_token,))
            conn.commit()
            conn.close()
            # ----------------------------
        
            return new_token
        else:
            print('Token retrieval failed: No access token in response.')
            return None
    except requests.exceptions.RequestException as e:
        print(f'Token retrieval failed: {str(e)}')
        return None
    
def make_api_request(method,headers, params):
    response = requests.get(URL + method, headers=headers, params=params)
    if response.status_code == 401:
        print('Token eskirgan. Yangilanmoqda...')
        new_token = get_new_token(SECRET_TOKEN)
        if not new_token:
            print('Token yangilashda xatolik yuz berdi')
            return None
        print("Token yangilandi. So'rovni qayta jo'natamiz...")
        headers['Authorization'] = 'Bearer ' + str(new_token)
        response = requests.get(URL + method, headers=headers, params=params)
    elif response.status_code == 500:
        global status
        status = response.status_code
        print('Serverda xatolik yuz berdi')
        return None
    return response.json()


# def get_information():
#         today_date = datetime.now().date()
#         current_time = datetime.now()
    
#         if 9 <= current_time.hour < 23:  # Time between 9 AM and 11 PM
#             interval_hour = (current_time.hour - 9) // 2 * 2 + 9  # Calculate closest interval hour within 9AM-11PM
#         else:
#             interval_hour = 23  # Default to 9 AM if outside the interval time range
        
#         # Set the minutes and seconds to zero
#         global interval_time
#         interval_time = current_time.replace(hour=interval_hour, minute=0, second=0, microsecond=0)

#         conn = sqlite3.connect('database/credentials.db')
#         cursor = conn.cursor()

#         access_token = cursor.execute("SELECT value FROM credential WHERE name = 'token'").fetchone()[0]
#         conn.close()

#         method = '/seller-general-table/'
#         params = {
#             'start_date': str(today_date),
#             'end_date': str(today_date),
#             'page': 1,
#             'limit': 10000000,
#             'shop_ids': "a93a6aac-748b-4ee9-a4f3-7498cd1606f6,5a31a945-7567-437a-8d66-fd355260b6e8,92a24d88-be00-48bf-8935-bca2a10ca9bb,5d9949c0-eb71-49e1-888d-8784f106f8dd,611622c0-210b-4a64-88a6-b855be3d842d,198dbb62-12b6-45b2-8bba-fdf829994b50,0e0ec5e4-3ba0-4a73-82ae-7877f4789cf1,faf6343c-aeb4-4b44-9943-bcfade326b03,b36214b2-ccc9-44ee-a5ab-550e8ce75212,e927b1b4-f9b3-4fdd-8470-8e6a2f3c1365",
#             'currency': 'UZS',
#             'detalization': 'hour'
#         }
#         headers = {
#             'accept': ACCEPT_HEADER,
#             'Content-Type': CONTENT_TYPE_HEADER,
#             'Authorization': TOKEN_PREFIX + access_token
#         }
#         data = {
#             "seller_stats_by_date": []
#         }

#         while True:
#             request = make_api_request(method,headers, params)
#             if request['seller_stats_by_date'] == []:
#                 break
#             for item in request['seller_stats_by_date']:
#                 data['seller_stats_by_date'].append(item)
#             params['page'] += 1
#         return 

# import pandas as pd

# pd = pd.DataFrame(get_information())
# print(pd)
