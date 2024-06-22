import pysqlite3 as sqlite3

# def create_database_and_table():
#     conn = sqlite3.connect('users.db')
#     cursor = conn.cursor()

#     cursor.execute('''
#     CREATE TABLE IF NOT EXISTS responded_users (
#         user_id INTEGER PRIMARY KEY
#     )
#     ''')

#     conn.commit()
#     conn.close()


conn = sqlite3.connect('database/plan.db')
cursor = conn.cursor()


cursor.execute("SELECT * FROM information")
db_information = cursor.fetchall()

for row in db_information:
    print(row)