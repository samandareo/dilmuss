from flask import Flask, render_template, request, redirect, url_for , session, flash
import requests
import json
from datetime import datetime, timedelta
import pysqlite3 as sqlite3
import psycopg2

app = Flask(__name__)
app.secret_key = ''

URL = '' # your checkout(kassa) programm api-url
AUTH_ENDPOINT = '/auth/login'
ACCEPT_HEADER = 'application/json'
CONTENT_TYPE_HEADER = 'application/json'
TOKEN_PREFIX = 'Bearer '
global access_token, status
status = "404"
access_token = ""
SECRET_TOKEN = "" #serve as refresh token
from credentials import users

# CONNECTION TO DATABASE
global conn, cursor
conn = psycopg2.connect(
    host="host",
    database="dbname",
    user="user",
    password="password",
    port="5432"
)
cursor = conn.cursor()

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
        global status , conn, cursor
        status = response.status_code
        new_token = response.json().get('data', {}).get('access_token')

        if new_token:
            cursor.execute(f"UPDATE credentials SET value = '{new_token}' WHERE name = 'token'")
            conn.commit()

        
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


def get_information(shop_id):
        today_date = datetime.now().date()
        yesterday_date = today_date - timedelta(days=1)
        current_time = datetime.now()
    
        if 9 <= current_time.hour < 23:  # Time between 9 AM and 11 PM
            interval_hour = (current_time.hour - 9) // 2 * 2 + 9  # Calculate closest interval hour within 9AM-11PM
        else:
            interval_hour = 23  # Default to 9 AM if outside the interval time range
        
        # Set the minutes and seconds to zero
        global interval_time, cursor
        interval_time = current_time.replace(hour=interval_hour, minute=0, second=0, microsecond=0)

        cursor.execute("SELECT value FROM credentials WHERE name = 'token'")
        access_token = cursor.fetchone()[0]

        if access_token is None:
            print("No token found in the database.")
            return None

        method = '/seller-general-table/'
        params = {
            'start_date': str(today_date),
            'end_date': str(today_date),
            'page': 1,
            'limit': 10000,
            'shop_ids': f"{shop_id}",
            'currency': 'UZS',
            'detalization': 'hour'
        }
        headers = {
            'accept': ACCEPT_HEADER,
            'Content-Type': CONTENT_TYPE_HEADER,
            'Authorization': TOKEN_PREFIX + access_token
        }
        data = {
            "seller_stats_by_date": []
        }

        while True:
            request = make_api_request(method,headers, params)
            if request['seller_stats_by_date'] == []:
                break
            for item in request['seller_stats_by_date']:
                data['seller_stats_by_date'].append(item)
            params['page'] += 1
            print(params['page'])
        return data


@app.route('/')
def index():
    return render_template('index.html')


# --------------------- XAVAS --------------------- #
@app.route('/xavas')
def xavas():
    try:
        global conn, cursor
        data = get_information("5a31a945-7567-437a-8d66-fd355260b6e8")
        
        cursor.execute("SELECT id FROM xavas")
        db_information = cursor.fetchall()
        sellers = []

        for row in db_information:
            sellers.append(row[0])

        dilmuss = [entry for entry in data['seller_stats_by_date'] if entry['seller_id'] in sellers]
    
        team_plan = {}

        cursor.execute("SELECT * FROM xavas")
        db_information = cursor.fetchall()

        for row in db_information:
            team_plan[row[0]] = row[1]

    
        sales = {}
        sales_pr = {}
    

        for entry in dilmuss:
            seller_id = entry['seller_id']
            for row in db_information:
                if seller_id == row[0]:
                    seller_name = row[2]
                    seller_position = row[3]
                    seller_shift = row[4]
                    break
            net_gross_sales = entry['net_gross_sales']
            
            if interval_time.hour >= 17 and seller_shift == 2:
                if seller_position == 'sotuvchi':
                    if seller_id in sellers:
                        if seller_name not in sales:
                            sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                        else:
                            sales[seller_name]['total_sales'] += net_gross_sales/1000
                        sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
                elif seller_position == 'romol':
                    if seller_id in sellers:
                        if seller_name not in sales_pr:
                            sales_pr[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                        else:
                            sales_pr[seller_name]['total_sales'] += net_gross_sales/1000
                        sales_pr[seller_name]['percentage'] = (sales_pr[seller_name]['total_sales'] / team_plan[seller_id]) * 100
            elif interval_time.hour < 17 and (seller_shift == 1 or seller_shift == 0):
                if seller_position == 'sotuvchi':
                    if seller_id in sellers:
                        if seller_name not in sales:
                            sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                        else:
                            sales[seller_name]['total_sales'] += net_gross_sales/1000
                        sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
                elif seller_position == 'romol':
                    if seller_id in sellers:
                        if seller_name not in sales_pr:
                            sales_pr[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                        else:
                            sales_pr[seller_name]['total_sales'] += net_gross_sales/1000
                        sales_pr[seller_name]['percentage'] = (sales_pr[seller_name]['total_sales'] / team_plan[seller_id]) * 100
    
        
      
        sales = dict(sorted(sales.items(), key=lambda item: item[1]['total_sales'], reverse=True))
        sales_pr = dict(sorted(sales_pr.items(), key=lambda item: item[1]['total_sales'], reverse=True))
        return render_template('xavas.html', oazis_sales=sales, oazis_sales_2=sales_pr,current_time=interval_time)
    except Exception as e:
        app.logger.error(e)
        global status
        return render_template('error.html', error_message=status, branch='xavas')


# --------------------- OAZIS --------------------- #
@app.route('/oazis')
def oazis():
    try:
        global conn, cursor
        data = get_information("a93a6aac-748b-4ee9-a4f3-7498cd1606f6")
        
        cursor.execute("SELECT id FROM oazis")
        db_information = cursor.fetchall()
        sellers = []

        for row in db_information:
            sellers.append(row[0])

        dilmuss = [entry for entry in data['seller_stats_by_date'] if entry['seller_id'] in sellers]
    
        team_plan = {}

        cursor.execute("SELECT * FROM oazis")
        db_information = cursor.fetchall()

        for row in db_information:
            team_plan[row[0]] = row[1]

    
        sales = {}
        sales_pr = {}
    

        for entry in dilmuss:
            seller_id = entry['seller_id']
            for row in db_information:
                if seller_id == row[0]:
                    seller_name = row[2]
                    seller_position = row[3]
                    seller_shift = row[4]
                    break
            net_gross_sales = entry['net_gross_sales']
            
            if interval_time.hour >= 17 and seller_shift == 2:
                if seller_position == 'sotuvchi':
                    if seller_id in sellers:
                        if seller_name not in sales:
                            sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                        else:
                            sales[seller_name]['total_sales'] += net_gross_sales/1000
                        sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
                elif seller_position == 'romol':
                    if seller_id in sellers:
                        if seller_name not in sales_pr:
                            sales_pr[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                        else:
                            sales_pr[seller_name]['total_sales'] += net_gross_sales/1000
                        sales_pr[seller_name]['percentage'] = (sales_pr[seller_name]['total_sales'] / team_plan[seller_id]) * 100
            elif interval_time.hour < 17 and (seller_shift == 1 or seller_shift == 0):
                if seller_position == 'sotuvchi':
                    if seller_id in sellers:
                        if seller_name not in sales:
                            sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                        else:
                            sales[seller_name]['total_sales'] += net_gross_sales/1000
                        sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
                elif seller_position == 'romol':
                    if seller_id in sellers:
                        if seller_name not in sales_pr:
                            sales_pr[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                        else:
                            sales_pr[seller_name]['total_sales'] += net_gross_sales/1000
                        sales_pr[seller_name]['percentage'] = (sales_pr[seller_name]['total_sales'] / team_plan[seller_id]) * 100
    
        
      
        sales = dict(sorted(sales.items(), key=lambda item: item[1]['total_sales'], reverse=True))
        sales_pr = dict(sorted(sales_pr.items(), key=lambda item: item[1]['total_sales'], reverse=True))
        return render_template('oazis.html', oazis_sales=sales, oazis_sales_2=sales_pr,current_time=interval_time)
    except Exception as e:
        app.logger.error(e)
        global status
        return render_template('error.html', error_message=status, branch='oazis')
    
# --------------------- PARIS --------------------- #
@app.route('/paris')
def paris():
    try:
        global conn, cursor
        data = get_information("b36214b2-ccc9-44ee-a5ab-550e8ce75212")
        
        cursor.execute("SELECT id FROM paris")
        db_information = cursor.fetchall()
        sellers = []

        for row in db_information:
            sellers.append(row[0])

        dilmuss = [entry for entry in data['seller_stats_by_date'] if entry['seller_id'] in sellers]
    
        team_plan = {}

        cursor.execute("SELECT * FROM paris")
        db_information = cursor.fetchall()

        for row in db_information:
            team_plan[row[0]] = row[1]

    
        sales = {}
    

        for entry in dilmuss:
            seller_id = entry['seller_id']
            for row in db_information:
                if seller_id == row[0]:
                    seller_name = row[2]
                    seller_position = row[3]
                    seller_shift = row[4]
                    break
            net_gross_sales = entry['net_gross_sales']
            
            if interval_time.hour >= 17 and seller_shift == 2:
                if seller_id in sellers:
                    if seller_name not in sales:
                        sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                    else:
                        sales[seller_name]['total_sales'] += net_gross_sales/1000
                    sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
            elif interval_time.hour < 17 and (seller_shift == 1 or seller_shift == 0):
                if seller_id in sellers:
                    if seller_name not in sales:
                        sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                    else:
                        sales[seller_name]['total_sales'] += net_gross_sales/1000
                    sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
                    
      
        sales = dict(sorted(sales.items(), key=lambda item: item[1]['total_sales'], reverse=True))

        return render_template('paris.html', sales=sales,current_time=interval_time)
    except Exception as e:
        app.logger.error(e)
        global status
        return render_template('error.html', error_message=status, branch='paris')

# --------------------- DRESSA --------------------- #
@app.route('/dressa')
def dressa():
    try:
        global conn, cursor
        data = get_information("198dbb62-12b6-45b2-8bba-fdf829994b50")
        
        cursor.execute("SELECT id FROM dressa")
        db_information = cursor.fetchall()
        sellers = []

        for row in db_information:
            sellers.append(row[0])

        dilmuss = [entry for entry in data['seller_stats_by_date'] if entry['seller_id'] in sellers]
    
        team_plan = {}

        cursor.execute("SELECT * FROM dressa")
        db_information = cursor.fetchall()

        for row in db_information:
            team_plan[row[0]] = row[1]

    
        sales = {}
    

        for entry in dilmuss:
            seller_id = entry['seller_id']
            for row in db_information:
                if seller_id == row[0]:
                    seller_name = row[2]
                    seller_position = row[3]
                    seller_shift = row[4]
                    break
            net_gross_sales = entry['net_gross_sales']
            
            if interval_time.hour >= 17 and seller_shift == 2:
                if seller_id in sellers:
                    if seller_name not in sales:
                        sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                    else:
                        sales[seller_name]['total_sales'] += net_gross_sales/1000
                    sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
            elif interval_time.hour < 17 and (seller_shift == 1 or seller_shift == 0):
                if seller_id in sellers:
                    if seller_name not in sales:
                        sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                    else:
                        sales[seller_name]['total_sales'] += net_gross_sales/1000
                    sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
                    
      
        sales = dict(sorted(sales.items(), key=lambda item: item[1]['total_sales'], reverse=True))

        return render_template('dressa.html', sales=sales,current_time=interval_time)
    except Exception as e:
        app.logger.error(e)
        global status
        return render_template('error.html', error_message=status, branch='dressa')
    

# --------------------- Lady House --------------------- #
@app.route('/lady')
def lady():
    try:
        global conn, cursor
        data = get_information("faf6343c-aeb4-4b44-9943-bcfade326b03")
        
        cursor.execute("SELECT id FROM lady")
        db_information = cursor.fetchall()
        sellers = []

        for row in db_information:
            sellers.append(row[0])

        dilmuss = [entry for entry in data['seller_stats_by_date'] if entry['seller_id'] in sellers]
    
        team_plan = {}

        cursor.execute("SELECT * FROM lady")
        db_information = cursor.fetchall()

        for row in db_information:
            team_plan[row[0]] = row[1]

    
        sales = {}
    

        for entry in dilmuss:
            seller_id = entry['seller_id']
            for row in db_information:
                if seller_id == row[0]:
                    seller_name = row[2]
                    seller_position = row[3]
                    seller_shift = row[4]
                    break
            net_gross_sales = entry['net_gross_sales']
            
            if interval_time.hour >= 17 and seller_shift == 2:
                if seller_id in sellers:
                    if seller_name not in sales:
                        sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                    else:
                        sales[seller_name]['total_sales'] += net_gross_sales/1000
                    sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
            elif interval_time.hour < 17 and (seller_shift == 1 or seller_shift == 0):
                if seller_id in sellers:
                    if seller_name not in sales:
                        sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                    else:
                        sales[seller_name]['total_sales'] += net_gross_sales/1000
                    sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
                    
      
        sales = dict(sorted(sales.items(), key=lambda item: item[1]['total_sales'], reverse=True))

        return render_template('lady.html', sales=sales,current_time=interval_time)
    except Exception as e:
        app.logger.error(e)
        global status
        return render_template('error.html', error_message=status, branch='lady')


# --------------------- NAZIRA --------------------- #
@app.route('/nazira')
def nazira():
    try:
        global conn, cursor
        data = get_information("611622c0-210b-4a64-88a6-b855be3d842d")
        
        cursor.execute("SELECT id FROM nazira")
        db_information = cursor.fetchall()
        sellers = []

        for row in db_information:
            sellers.append(row[0])

        dilmuss = [entry for entry in data['seller_stats_by_date'] if entry['seller_id'] in sellers]
    
        team_plan = {}

        cursor.execute("SELECT * FROM nazira")
        db_information = cursor.fetchall()

        for row in db_information:
            team_plan[row[0]] = row[1]

    
        sales = {}
    

        for entry in dilmuss:
            seller_id = entry['seller_id']
            for row in db_information:
                if seller_id == row[0]:
                    seller_name = row[2]
                    seller_position = row[3]
                    seller_shift = row[4]
                    break
            net_gross_sales = entry['net_gross_sales']
            
            if interval_time.hour >= 17 and seller_shift == 2:
                if seller_id in sellers:
                    if seller_name not in sales:
                        sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                    else:
                        sales[seller_name]['total_sales'] += net_gross_sales/1000
                    sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
            elif interval_time.hour < 17 and (seller_shift == 1 or seller_shift == 0):
                if seller_id in sellers:
                    if seller_name not in sales:
                        sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                    else:
                        sales[seller_name]['total_sales'] += net_gross_sales/1000
                    sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
                    
      
        sales = dict(sorted(sales.items(), key=lambda item: item[1]['total_sales'], reverse=True))

        return render_template('nazira.html', sales=sales,current_time=interval_time)
    except Exception as e:
        app.logger.error(e)
        global status
        return render_template('error.html', error_message=status, branch='nazira')

# --------------------- Instyle --------------------- #
@app.route('/instyle')
def instyle():
    try:
        global conn, cursor
        data = get_information("e927b1b4-f9b3-4fdd-8470-8e6a2f3c1365")
        
        cursor.execute("SELECT id FROM instyle")
        db_information = cursor.fetchall()
        sellers = []

        for row in db_information:
            sellers.append(row[0])

        dilmuss = [entry for entry in data['seller_stats_by_date'] if entry['seller_id'] in sellers]
    
        team_plan = {}

        cursor.execute("SELECT * FROM instyle")
        db_information = cursor.fetchall()

        for row in db_information:
            team_plan[row[0]] = row[1]

    
        sales = {}
    

        for entry in dilmuss:
            seller_id = entry['seller_id']
            for row in db_information:
                if seller_id == row[0]:
                    seller_name = row[2]
                    seller_position = row[3]
                    seller_shift = row[4]
                    break
            net_gross_sales = entry['net_gross_sales']
            
            if interval_time.hour >= 17 and seller_shift == 2:
                if seller_id in sellers:
                    if seller_name not in sales:
                        sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                    else:
                        sales[seller_name]['total_sales'] += net_gross_sales/1000
                    sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
            elif interval_time.hour < 17 and (seller_shift == 1 or seller_shift == 0):
                if seller_id in sellers:
                    if seller_name not in sales:
                        sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                    else:
                        sales[seller_name]['total_sales'] += net_gross_sales/1000
                    sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
                    
      
        sales = dict(sorted(sales.items(), key=lambda item: item[1]['total_sales'], reverse=True))

        return render_template('instyle.html', sales=sales,current_time=interval_time)
    except Exception as e:
        app.logger.error(e)
        global status
        return render_template('error.html', error_message=status, branch='instyle')
    

# --------------------- Muddi --------------------- #
@app.route('/muddi')
def muddi():
    try:
        global conn, cursor
        data = get_information("0e0ec5e4-3ba0-4a73-82ae-7877f4789cf1")
        
        cursor.execute("SELECT id FROM muddi")
        db_information = cursor.fetchall()
        sellers = []

        for row in db_information:
            sellers.append(row[0])

        dilmuss = [entry for entry in data['seller_stats_by_date'] if entry['seller_id'] in sellers]
    
        team_plan = {}

        cursor.execute("SELECT * FROM muddi")
        db_information = cursor.fetchall()

        for row in db_information:
            team_plan[row[0]] = row[1]

    
        sales = {}
    

        for entry in dilmuss:
            seller_id = entry['seller_id']
            for row in db_information:
                if seller_id == row[0]:
                    seller_name = row[2]
                    seller_position = row[3]
                    seller_shift = row[4]
                    break
            net_gross_sales = entry['net_gross_sales']
            
            if interval_time.hour >= 17 and seller_shift == 2:
                if seller_id in sellers:
                    if seller_name not in sales:
                        sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                    else:
                        sales[seller_name]['total_sales'] += net_gross_sales/1000
                    sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
            elif interval_time.hour < 17 and (seller_shift == 1 or seller_shift == 0):
                if seller_id in sellers:
                    if seller_name not in sales:
                        sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                    else:
                        sales[seller_name]['total_sales'] += net_gross_sales/1000
                    sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
                    
      
        sales = dict(sorted(sales.items(), key=lambda item: item[1]['total_sales'], reverse=True))

        return render_template('muddi.html', sales=sales,current_time=interval_time)
    except Exception as e:
        app.logger.error(e)
        global status
        return render_template('error.html', error_message=status, branch='muddi')

# --------------------- Beruniy --------------------- #
@app.route('/beruniy')
def beruniy():
    try:
        global conn, cursor
        data = get_information("5d9949c0-eb71-49e1-888d-8784f106f8dd")
        
        cursor.execute("SELECT id FROM beruniy")
        db_information = cursor.fetchall()
        sellers = []

        for row in db_information:
            sellers.append(row[0])

        dilmuss = [entry for entry in data['seller_stats_by_date'] if entry['seller_id'] in sellers]
    
        team_plan = {}

        cursor.execute("SELECT * FROM beruniy")
        db_information = cursor.fetchall()

        for row in db_information:
            team_plan[row[0]] = row[1]

    
        sales = {}
        sales_pr = {}
    

        for entry in dilmuss:
            seller_id = entry['seller_id']
            for row in db_information:
                if seller_id == row[0]:
                    seller_name = row[2]
                    seller_position = row[3]
                    seller_shift = row[4]
                    break
            net_gross_sales = entry['net_gross_sales']
            
            if interval_time.hour >= 17 and seller_shift == 2:
                if seller_position == 'sotuvchi':
                    if seller_id in sellers:
                        if seller_name not in sales:
                            sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                        else:
                            sales[seller_name]['total_sales'] += net_gross_sales/1000
                        sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
                elif seller_position == 'romol':
                    if seller_id in sellers:
                        if seller_name not in sales_pr:
                            sales_pr[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                        else:
                            sales_pr[seller_name]['total_sales'] += net_gross_sales/1000
                        sales_pr[seller_name]['percentage'] = (sales_pr[seller_name]['total_sales'] / team_plan[seller_id]) * 100
            elif interval_time.hour < 17 and (seller_shift == 1 or seller_shift == 0):
                if seller_position == 'sotuvchi':
                    if seller_id in sellers:
                        if seller_name not in sales:
                            sales[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                        else:
                            sales[seller_name]['total_sales'] += net_gross_sales/1000
                        sales[seller_name]['percentage'] = (sales[seller_name]['total_sales'] / team_plan[seller_id]) * 100
                elif seller_position == 'romol':
                    if seller_id in sellers:
                        if seller_name not in sales_pr:
                            sales_pr[seller_name] = {'total_sales': net_gross_sales, 'plan': team_plan[seller_id], 'percentage': 0}
                        else:
                            sales_pr[seller_name]['total_sales'] += net_gross_sales/1000
                        sales_pr[seller_name]['percentage'] = (sales_pr[seller_name]['total_sales'] / team_plan[seller_id]) * 100
    
        
      
        sales = dict(sorted(sales.items(), key=lambda item: item[1]['total_sales'], reverse=True))
        sales_pr = dict(sorted(sales_pr.items(), key=lambda item: item[1]['total_sales'], reverse=True))
        return render_template('beruniy.html', sales=sales, sales_2=sales_pr,current_time=interval_time)
    except Exception as e:
        app.logger.error(e)
        global status
        return render_template('error.html', error_message=status, branch='beruniy')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['logged_in'] = True
            session['username'] = username
            session['from_login'] = True
            return redirect(url_for(f'show_plan'))
        else:
            error = 'Username yoki parol xato! Iltimos qayta urinib ko\'ring!'
            return render_template('login.html', error=error, username=username)
    return render_template('login.html', error=None)


@app.route('/plan')
def show_plan():
    if 'logged_in' in session and session['logged_in'] and session.get('from_login'):
        session['from_login'] = False
        tbname = session['username']
        global conn, cursor
        
        cursor.execute(f"SELECT id, name, plan FROM {tbname}")
        db_information = cursor.fetchall()

        return render_template('plan.html', products=[{'id': id,'name': name, 'plan': plan} for id, name, plan in db_information])
    else:
        return redirect(url_for('login'))

@app.route('/update_plan', methods=['POST'])
def update_plan():
    if 'username' in session:
        tbname = session['username']
        product_id = request.form['update']
        new_plan = request.form['new_plan']

        global conn, cursor
        print(product_id, new_plan)
        cursor.execute(f"UPDATE {tbname} SET plan = {new_plan} WHERE id = '{product_id}'")
        conn.commit()
        session['from_login'] = True
        return redirect(url_for('show_plan'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('from_login', None)
    return redirect(url_for('login'))

def format_currency(value):
    return "{:,.0f}".format(value)

app.jinja_env.filters['currency'] = format_currency

if __name__ == "__main__":
    app.run(port=5000, debug=True)

