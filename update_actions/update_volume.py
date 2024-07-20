import pandas as pd
import yfinance as yf
import psycopg2
import numpy as np
import os
import pytz
from datetime import datetime

jkt_day = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%A")

conn_str = os.getenv('NEON_CONN_STR')
conn = psycopg2.connect(conn_str)
cur = conn.cursor()

composites = ["^JKSE", "^JKLQ45"]

def update_volume(cursor, code) :
    
    two_days_data = yf.Ticker(code).history("2d", "1d")
    two_days_data.index = two_days_data.index.strftime("%Y-%m-%d")
    
    if jkt_day == "Saturday" :
        yesterday_date = two_days_data.index.values[1]
        yesterday_volume = two_days_data["Volume"].values[1]
    else :
        yesterday_date = two_days_data.index.values[0]
        yesterday_volume = two_days_data["Volume"].values[0]
    
    cur.execute("""UPDATE {} SET "Volume" = {} WHERE "Date" = '{}';""".format(code, yesterday_volume, yesterday_date))

for code in composites :
    update_volume(cur, code)

conn.commit()

cur.close()
conn.close()