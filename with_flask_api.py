from flask import Flask, render_template
import requests
import json
from datetime import datetime

app = Flask(__name__)

URL = 'https://api-admin.billz.ai/v1'
AUTH_ENDPOINT = '/auth/login'
ACCEPT_HEADER = 'application/json'
CONTENT_TYPE_HEADER = 'application/json'
TOKEN_PREFIX = 'Bearer '
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfcGxhdGZvcm1faWQiOiI3ZDRhNGMzOC1kZDg0LTQ5MDItYjc0NC0wNDg4YjgwYTRjMDEiLCJjb21wYW55X2lkIjoiYTIwZmNlMmQtN2FlYS00NzgyLWEyMGYtNGRlMzkwYjgxNzIzIiwiZGF0YSI6IiIsImV4cCI6MTcxODAzNjA1OSwiaWF0IjoxNzE2NzQwMDU5LCJpZCI6IjYzYmJhMTNmLTM1ZTYtNGUzZi1iY2Y4LWM0ZDEzNmU5NDQ2ZiIsInVzZXJfaWQiOiIzMzFlOTQxYS1hYWU5LTQ2NDEtYjc2Mi0yZTM1MzE0OTEzMzUifQ.6D87afmJ5uMjhyAUlWjAPCoCSfRc0_Rxqra532usZR0"
SECRET_TOKEN = "ecdd4e117df3f684ba2bfc55234bfdcc8847b1e914a4904f2e348857db1d694b629fef32b909e4f3a972c37bcf6fab0c41a53bd720a5cc01e4196fd01db9c17fa664c73948d5c730703bf4c0f4c17dd45e8876f91d794da74147f4752b36125d7423bd074c7ff79d8d2c73e7e4aefb9425c118a59dbd37c7"


sales_plan = 15000000


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
        new_token = response.json().get('data', {}).get('access_token')
        if new_token:
            return new_token
        else:
            print('Token retrieval failed: No access token in response.')
            return None
    except requests.exceptions.RequestException as e:
        print(f'Token retrieval failed: {str(e)}')
        return None

def make_api_request(method,headers, params):
    response = requests.get(URL + method, headers=headers, params=params)
    if response.status_code != 200:
        print('Token eskirgan. Yangilanmoqda...')
        new_token = get_new_token(SECRET_TOKEN)
        headers['Authorization'] = 'Bearer ' + str(new_token)
        response = requests.get(URL + method, headers=headers, params=params)
    return response.json()
 
@app.route('/')
def index():
    today_date = datetime.now().date()
    current_time = datetime.now()

    if 9 <= current_time.hour < 23:  # Time between 9 AM and 11 PM
        interval_hour = (current_time.hour - 9) // 2 * 2 + 9  # Calculate closest interval hour within 9AM-11PM
    else:
        interval_hour = 23  # Default to 9 AM if outside the interval time range
    
    # Set the minutes and seconds to zero
    interval_time = current_time.replace(hour=interval_hour, minute=0, second=0, microsecond=0)



    method = '/seller-general-table/'
    params = {
        'start_date': str(today_date),
        'end_date': str(today_date),
        'page': 1,
        'limit': 10000000,
        'shop_ids': "a93a6aac-748b-4ee9-a4f3-7498cd1606f6,5a31a945-7567-437a-8d66-fd355260b6e8",
        'currency': 'UZS',
        'detalization': 'hour'
    }
    headers = {
        'accept': ACCEPT_HEADER,
        'Content-Type': CONTENT_TYPE_HEADER,
        'Authorization': TOKEN_PREFIX + ACCESS_TOKEN
    }
    data = make_api_request(method,headers, params)
    

    xavas_sellers = [
        '56c15498-18f0-4f24-b68f-f68cf790c086',
        '613320af-4659-4e36-91ec-644350b39a81',
        '10585d36-3f14-4a11-956c-846c9b386c97',
        '1b46d22f-41c1-43c4-87cc-0174989949f1',
        'd0f947af-1fae-4820-892a-d44d9c819a6d',
        '8827e64b-af5a-4ae6-8ae4-8164b2e6e523',
        '0a2b39c7-9774-4fe8-a226-f54012aa96f0'
    ]

    dilmuss_xavas = [entry for entry in data['seller_stats_by_date'] if entry['seller_id'] in xavas_sellers]


    xavas_team_plan = {
        "56c15498-18f0-4f24-b68f-f68cf790c086": 20000,
        "613320af-4659-4e36-91ec-644350b39a81": 20000,
        "10585d36-3f14-4a11-956c-846c9b386c97": 20000,
        "1b46d22f-41c1-43c4-87cc-0174989949f1": 20000,
        "d0f947af-1fae-4820-892a-d44d9c819a6d": 20000,
        "8827e64b-af5a-4ae6-8ae4-8164b2e6e523": 20000,
        "0a2b39c7-9774-4fe8-a226-f54012aa96f0": 20000
    }

    xavas_sales = {}


    for entry in dilmuss_xavas:
        seller_name = entry['seller_name']
        seller_id = entry['seller_id']
        net_gross_sales = entry['net_gross_sales']
        print(f'{seller_name} => {net_gross_sales}')

        if seller_id in xavas_sellers:
            if seller_name not in xavas_sales:
                xavas_sales[seller_name] = {'total_sales': net_gross_sales, 'plan': xavas_team_plan[seller_id], 'percentage': 0}
            else:
                xavas_sales[seller_name]['total_sales'] += net_gross_sales/1000
                print(f'${seller_name} => ${net_gross_sales}')
            xavas_sales[seller_name]['percentage'] = (xavas_sales[seller_name]['total_sales'] / xavas_team_plan[seller_id]) * 100


  
    xavas_sales = dict(sorted(xavas_sales.items(), key=lambda item: item[1]['total_sales'], reverse=True))

    return render_template('index.html', oazis_sales=xavas_sales, current_time=interval_time)


def format_currency(value):
    return "{:,.0f}".format(value)

app.jinja_env.filters['currency'] = format_currency

if __name__ == "__main__":
    app.run(debug=True)
