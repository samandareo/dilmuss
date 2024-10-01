import psycopg2

conn = psycopg2.connect(
    host="host",
    database="dbname",
    user="user",
    password="password",
    port="5432"
)

cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS oazis (id TEXT PRIMARY KEY, plan INTEGER, name TEXT, position TEXT, shift INTEGER, phone TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS xavas (id TEXT PRIMARY KEY, plan INTEGER, name TEXT, position TEXT, shift INTEGER, phone TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS magnit (id TEXT PRIMARY KEY, plan INTEGER, name TEXT, position TEXT, shift INTEGER, phone TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS beruniy (id TEXT PRIMARY KEY, plan INTEGER, name TEXT, position TEXT, shift INTEGER, phone TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS nazira (id TEXT PRIMARY KEY, plan INTEGER, name TEXT, position TEXT, shift INTEGER, phone TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS dressa (id TEXT PRIMARY KEY, plan INTEGER, name TEXT, position TEXT, shift INTEGER, phone TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS muddi (id TEXT PRIMARY KEY, plan INTEGER, name TEXT, position TEXT, shift INTEGER, phone TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS lady_house (id TEXT PRIMARY KEY, plan INTEGER, name TEXT, position TEXT, shift INTEGER, phone TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS paris_nds (id TEXT PRIMARY KEY, plan INTEGER, name TEXT, position TEXT, shift INTEGER, phone TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS instyle (id TEXT PRIMARY KEY, plan INTEGER, name TEXT, position TEXT, shift INTEGER, phone TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS credentials (id SERIAL PRIMARY KEY, name TEXT, value TEXT)")

conn.commit()
cur.close()
conn.close()
