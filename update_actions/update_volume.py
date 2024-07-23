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
    
    data = yf.Ticker(code).history("1d", "1d")
    data.index = data.index.strftime("%Y-%m-%d")
    
    yesterday_date = data.index.values[0]
    yesterday_volume = data["Volume"].values[0]
    
    cur.execute("""UPDATE {} SET "Volume" = {} WHERE "Date" = '{}';""".format(db_name, yesterday_volume, yesterday_date))

for code in composites :
    update_volume(cur, code)

conn.commit()

cur.close()
conn.close()