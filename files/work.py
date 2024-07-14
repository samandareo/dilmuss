import pandas as pd
import sqlite3

data = pd.read_json('response.json')
data = pd.DataFrame(data)

#