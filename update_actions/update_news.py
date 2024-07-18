import concurrent.futures
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os
import psycopg2
from .news_helper import *

conn_str = os.getenv('NEON_CONN_STR')
conn = psycopg2.connect(conn_str)
cur = conn.cursor()
cur.execute("SELECT code FROM lq45;")
codes = cur.fetchall()
codes = sorted([c[0] for c in codes] + ["IHSG", "LQ45"])
cur.close()
conn.close()

with concurrent.futures.ThreadPoolExecutor() as executor :
    futures = []
    data = []
    for code in codes :
        futures.append(executor.submit(get_articles, code=code))
    for future in concurrent.futures.as_completed(futures) :
        data.append(future.result())

data = np.reshape(data, (-1, 6))
df = to_dataframe(data)
df = change_date_format(df)
df["Publisher"] = df.apply(fill_publisher, axis=1)

engine = create_engine(conn_str)
df.to_sql('news', engine, if_exists='replace', index=False)