import streamlit as st
from requests_ratelimiter import LimiterSession
import yfinance as yf
import pandas as pd
import pytz
import re
from datetime import datetime, timedelta
from inference.data_processing import resample

session = LimiterSession(per_minute=12)

@st.cache_resource
def get_conn():
    conn = st.connection("neon", type="sql")
    return conn
    
conn = get_conn()

@st.cache_data
def get_codes():
    df = conn.query("SELECT * FROM lq45_codes;", ttl=0)
    df["Long Name"] = df["code"] + " " + "(" + df["name"] + ")"
    choice = list(df["Long Name"].values)
    return ["IHSG (Indeks Harga Saham Gabungan)", "LQ45 (Liquid 45)"] + sorted(choice)

@st.cache_data
def get_news(code) :
    news_df = conn.query("""SELECT * FROM news WHERE "Code" = '{}' ORDER BY "Date" DESC;""".format(code), ttl=0)
    news_df["Date"] = news_df["Date"].apply(lambda x: x.strftime("%Y-%m-%d"))
    return news_df.values

@st.cache_data(ttl=3600)
def get_stock_from_db(code, first_date):
    stock_data = conn.query("""SELECT * FROM {} WHERE "Date" >= '{}';""".format(code[:4], first_date))
    return stock_data    

def get_stock(code=None, period="10y", interval="1d"):
    
    if code == "ihsg" :
        stock_tick = yf.Ticker("^JKSE", session=session)
    elif code == "lq45" :
        stock_tick = yf.Ticker("^JKLQ45", session=session)
    else :
        stock_tick = yf.Ticker(code.upper()+".JK", session=session)
    
    predicted_days = get_forecast_date(code)
    
    updated_status, today_data = is_updated(code)
    first_date = get_first_date(code, period, interval)
    stock_data = get_stock_from_db(code, first_date)
    
    if not updated_status :
        stock_data = pd.concat([stock_data, today_data], axis=0)
    
    stock_data["Date"] = stock_data["Date"].apply(lambda x: x.strftime("%Y-%m-%d"))
    stock_data.set_index("Date", inplace=True)
    
    if interval[1:] == "d":
        dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                               end=predicted_days[-1], freq="D")
        dt_all_str = [d.strftime("%Y-%m-%d") for d in dt_all.tolist()]
    else :
        stock_data = resample(stock_data, interval)
        if interval[1:] == "wk":
            dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                   end=stock_data.index.tolist()[-1], freq="7D")
            dt_all_str = [d.strftime("%Y-%m-%d") for d in dt_all.tolist()]
            
        else :
            dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                   end=stock_data.index.tolist()[-1], freq="ME")
            dt_all_str = [d.strftime("%Y-%m") for d in dt_all.tolist()]
        
    dt_breaks = [d for d in dt_all_str if not d in stock_data.index.tolist() and not d in predicted_days]
    return stock_data, dt_breaks

def get_first_date(code, period, interval) :
    amount, period = re.findall(r'\d+|\D+', period)
    amount = int(amount)
    
    last_date = get_maximum_date(code)
    
    if period == "mo" :
        first_date = last_date - pd.DateOffset(days=amount*30)
        
    elif period == "y" :
        first_date = last_date - pd.DateOffset(days=amount*365)
    
    
    if interval[1:] == "wk" :
        first_date = first_date - pd.DateOffset(days=first_date.weekday())
        
    elif interval[1:] == "mo" :
        first_date = first_date.replace(day=1)
    
    first_date = first_date.strftime("%Y-%m-%d")
    return first_date

def get_today() :
    jkt_tz = pytz.timezone('Asia/Jakarta')
    jkt_date = datetime.now(jkt_tz)
    jkt_hour = int(jkt_date.strftime("%H"))
    jkt_minute = int(jkt_date.strftime("%M"))
    jkt_day = jkt_date.strftime("%A")
    
    jkt_date = jkt_date.strftime("%Y-%m-%d")
    jkt_date = datetime.strptime(jkt_date, "%Y-%m-%d")
    
    return jkt_date, jkt_day, jkt_hour, jkt_minute

@st.cache_data(ttl=3600)
def get_maximum_date(code) :
    max_date = conn.query("""SELECT MAX("Date") FROM {};""".format(code))["max"].values.tolist()[0]
    max_date = max_date.strftime("%Y-%m-%d")
    max_date = datetime.strptime(max_date, "%Y-%m-%d")
    return max_date

def is_updated(code) :
    if code == "ihsg" :
        tick = "^JKSE"
    elif code == "lq45" :
        tick = "^JKLQ45"
    else :
        tick = code.upper() + ".JK"
    today_data = yf.Ticker(tick).history("1d", "1d", prepost=True).reset_index()
    today_data["Date"] = today_data["Date"].apply(lambda x: x.strftime("%Y-%m-%d"))
    latest_date_from_yf = today_data["Date"].values[-1]
    latest_date_from_db = get_maximum_date(code).strftime("%Y-%m-%d")
    if latest_date_from_db == latest_date_from_yf :
        return True, None
    else :
        return False, today_data
        
def get_forecast_date(code) :
    latest_date_from_db = get_maximum_date(code)
    dates = []
    i = 0
    while len(dates) < 10 :
        if (latest_date_from_db + timedelta(days=1*i)).strftime("%A") not in ['Sunday', 'Saturday'] :
            dates.append((latest_date_from_db + timedelta(days=1*i)).strftime("%Y-%m-%d"))
            i += 1
        else :
            latest_date_from_db = latest_date_from_db + timedelta(days=1)
    return dates