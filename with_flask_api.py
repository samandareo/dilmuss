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
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfcGxhdGZvcm1faWQiOiI3ZDRhNGMzOC1kZDg0LTQ5MDItYjc0NC0wNDg4YjgwYTRjMDEiLCJjb21wYW55X2lkIjoiYTIwZmNlMmQtN2FlYS00NzgyLWEyMGYtNGRlMzkwYjgxNzIzIiwiZGF0YSI6IiIsImV4cCI6MTcxNTMzNjExOCwiaWF0IjoxNzE0MDQwMTE4LCJpZCI6ImViYmZiOTVkLTVlOGQtNDlkMS1iZTY2LWEzZDY2Njc4Y2VhZCIsInVzZXJfaWQiOiIzMzFlOTQxYS1hYWU5LTQ2NDEtYjc2Mi0yZTM1MzE0OTEzMzUifQ.T7Pt6ci_6qWtDajNYFmG3s1zUtSweaV4vXGgSJi7qRo"
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
    response = requests.post(URL + AUTH_ENDPOINT, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        SECRET_TOKEN = response.json()['data']['access_token']
        return response.json()['data']['access_token']
    else:
        print('Token retrieval failed: ', response.status_code)
        return None

def make_api_request(method,headers, params):
    response = requests.get(URL + method, headers=headers, params=params)
    if response.status_code != 200:
        print('Token eskirgan. Yangilanmoqda...')
        headers['Authorization'] = 'Bearer ' + get_new_token(URL)
        response = requests.get(URL + method, headers=headers, params=params)
        print('API request failed: ', response.status_code)
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

    oazis_sellers = [
        '9d3b2c6f-d58f-4018-8a91-6d5fbd1a9251',
        'ca610bd2-710b-4119-b4fb-943a2c2e1d5a',
        '1cedf98b-3712-43c7-92f4-267d26d0f900',
        '356f9378-f923-4838-aca8-0fe5eff99d06',
        'e894b09a-7124-455a-b576-e7d1faa4e36c',
        '1cf400f7-24ca-422d-9c0c-2785fc6d446d',
        '6bcd38ae-076d-4031-98ed-0b93bcf7b863'
    ]

    dilmuss_xavas = [entry for entry in data['seller_stats_by_date'] if entry['seller_id'] in xavas_sellers]
    dilmuss_oazis = [entry for entry in data['seller_stats_by_date'] if entry['seller_id'] in oazis_sellers]

    current_hour = datetime.now().hour
    dilmuss_xavas_time = [entry for entry in dilmuss_xavas if datetime.strptime(entry['date'], '%Y-%m-%d %H:%M:%S').hour <= current_hour]
    dilmuss_oazis_time = [entry for entry in dilmuss_oazis if datetime.strptime(entry['date'], '%Y-%m-%d %H:%M:%S').hour <= current_hour]


    xavas_team_plan = {
        "XAVAS 1-KAMANDA .": 20000,
        "XAVAS 2- KAMANDA .": 20000,
        "XAVAS 3- KAMANDA .": 20000
    }
    default_plan = 20000  

    xavas_sales = {}
    oazis_sales = {}


    for entry in data['seller_stats_by_date']:
        seller_name = entry['seller_name']
        net_gross_sales = entry['net_gross_sales']
        if seller_name.startswith("XAVAS"):
            plan = xavas_team_plan.get(seller_name, default_plan)
            if seller_name in xavas_sales:
                xavas_sales[seller_name]['total_sales'] += net_gross_sales/1000
            else:
                xavas_sales[seller_name] = {'total_sales': net_gross_sales, 'plan': plan, 'percentage': 0}
            xavas_sales[seller_name]['percentage'] = (xavas_sales[seller_name]['total_sales'] / plan) * 100
        else:
            plan = default_plan
            if seller_name in oazis_sales:
                oazis_sales[seller_name]['total_sales'] += net_gross_sales/1000
            else:
                oazis_sales[seller_name] = {'total_sales': net_gross_sales, 'plan': plan, 'percentage': 0}
            oazis_sales[seller_name]['percentage'] = (oazis_sales[seller_name]['total_sales'] / plan) * 100

  
    xavas_sales = dict(sorted(xavas_sales.items(), key=lambda item: item[1]['total_sales'], reverse=True))
    oazis_sales = dict(sorted(oazis_sales.items(), key=lambda item: item[1]['total_sales'], reverse=True))

    return render_template('index.html', oazis_sales=oazis_sales, xavas_sales=xavas_sales, current_time=interval_time)


def format_currency(value):
    return "{:,.0f}".format(value)

app.jinja_env.filters['currency'] = format_currency

if __name__ == "__main__":
    app.run(debug=True)
