import streamlit as st
from requests_ratelimiter import LimiterSession
import yfinance as yf
import pandas as pd
import pytz
import re
from datetime import datetime
from inference.data_preprocessing import prepare_data, resample
from inference.prediction import get_forecast_date

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

def get_news(code) :
    news_df = conn.query("""SELECT * FROM news WHERE "Code" = '{}';""".format(code), ttl=0)
    return news_df.values

@st.cache_data
def get_stock(ticker=None, period="10y", interval="1d"):
    
    if ticker == "ihsg" :
        stock_tick = yf.Ticker("^JKSE", session=session)
    elif ticker == "lq45" :
        stock_tick = yf.Ticker("^JKLQ45", session=session)
    else :
        stock_tick = yf.Ticker(ticker.upper()+".JK", session=session)
    
    predicted_days = get_forecast_date()
    
    # Minute and hour timeframes data aren't saved in database.
    if interval[1:] == "m" or interval[1:] == "h" :
        stock_data = stock_tick.history(period=period, interval=interval, prepost=True)
        stock_data.index = stock_data.index.strftime("%Y-%m-%d %H:%M:%S")
        
        if interval[1:] == "m":
            dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                   end=stock_data.index.tolist()[-1], freq="5min")
        else :
            dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                   end=stock_data.index.tolist()[-1], freq="h")
        
        dt_all_str = [d.strftime("%Y-%m-%d %H:%M:%S") for d in dt_all.tolist()]
    
    
    else :
        updated_status = is_updated(ticker)
        first_date = get_first_date(ticker, period, interval)
        stock_data = conn.query("""SELECT * FROM {} WHERE "Date" >= '{}';""".format(ticker[:4], first_date))
        
        if not updated_status :
            today_data = stock_tick.history(period="1d", interval="1d", prepost=True)
            today_data.reset_index(inplace=True)
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

@st.cache_data
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

@st.cache_data
def get_maximum_date(code) :
    max_date = conn.query("""SELECT MAX("Date") FROM {};""".format(code))["max"].values.tolist()[0]
    max_date = max_date.strftime("%Y-%m-%d")
    max_date = datetime.strptime(max_date, "%Y-%m-%d")
    return max_date

@st.cache_data
def is_updated(code) :
    today_date, today_day, _, _ = get_today()
    updated_date = get_maximum_date(code)
    if today_date == updated_date or today_day == "Saturday" or today_day == "Sunday" :
        return True
    else :
        return False