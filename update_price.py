import pandas as pd
import yfinance as yf
import psycopg2
import numpy as np
import os

lq45 = pd.read_csv("LQ45_CODEName.csv")
codes = lq45["Code"].values.tolist() + ["ihsg", "lq45"]
codes = [c.lower() for c in codes]

conn_str = os.getenv('NEON_CONN_STR')
conn = psycopg2.connect(conn_str)
cur = conn.cursor()

def update_price(cursor, code) :
    if code == "ihsg":
        code_cap = "^JKSE"
    elif code == "lq45":
        code_cap = "^JKLQ45"
    else :
        code_cap = code.upper() + ".JK"
    
    today_price = yf.Ticker(code_cap).history("1d", "1d")
    today_price.index = today_price.index.strftime("%Y-%m-%d")
    today_price.reset_index(inplace=True)
    
    today_price = np.squeeze(today_price.values)
    
    cur.execute("INSERT INTO {} VALUES ('{}', {}, {}, {}, {}, {}, {}, {});".format(code, *today_price))

for code in codes :
    update_price(cur, code)

conn.commit()

cur.close()
conn.close()