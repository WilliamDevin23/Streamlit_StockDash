import pandas as pd
import yfinance as yf
import psycopg2
import numpy as np
import os

conn_str = os.getenv('NEON_CONN_STR')
conn = psycopg2.connect(conn_str)
cur = conn.cursor()

composites = ["^JKSE", "^JKLQ45"]

def update_volume(cursor, code) :
    if code == "^JKSE" :
        db_name = "ihsg"
    else :
        db_name = "lq45"
    
    data = yf.Ticker(code).history("1wk", "1d")
    data.reset_index(inplace=True)
    data["Date"] = data["Date"].apply(lambda x: x.strftime("%Y-%m-%d"))
    
    cur.execute("""SELECT MAX("Date") FROM {};""".format(db_name))
    latest_date_from_db = cur.fetchall()[-1][0]
    latest_date_from_db = latest_date_from_db.strftime("%Y-%m-%d")
    data = data[data["Date"] == latest_date_from_db]
    
    cur.execute("""UPDATE {} SET "Volume" = {} WHERE "Date" = '{}';""".format(db_name, data["Volume"].values[0], latest_date_from_db))

for code in composites :
    update_volume(cur, code)

conn.commit()

cur.close()
conn.close()