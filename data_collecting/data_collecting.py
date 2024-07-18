import streamlit as st
from requests_ratelimiter import LimiterSession
import yfinance as yf
import pandas as pd
from inference.data_preprocessing import prepare_data, resample
from inference.prediction import get_forecast_date

session = LimiterSession(per_minute=12)
conn = st.connection("neon", type="sql")
    
def get_codes():
    df = conn.query("SELECT * FROM lq45_codes;", ttl=0)
    df["Long Name"] = df["code"] + " " + "(" + df["name"] + ")"
    choice = list(df["Long Name"].values)
    return ["IHSG (Indeks Harga Saham Gabungan)", "LQ45 (Liquid 45)"] + sorted(choice)

def get_news(code) :
    news_df = conn.query("""SELECT * FROM news WHERE "Code" = '{}';""".format(code), ttl=0)
    return news_df.values

def get_stock(ticker=None, period="10y", interval="1d"):
    
    if ticker == "ihsg" :
        stock_tick = yf.Ticker("^JKSE", session=session)
    elif ticker == "lq45" :
        stock_tick = yf.Ticker("^JKLQ45", session=session)
    else :
        stock_tick = yf.Ticker(ticker.upper()+".JK", session=session)
    
    predicted_days = get_forecast_date()
    
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
        stock_data = conn.query("""SELECT * FROM {};""".format(ticker[:4]))
        stock_data.set_index("Date", inplace=True)
        
        today_data = stock_tick.history(period="1d", interval="1d", prepost=True)
        today_data.index = today_data.index.strftime("%Y-%m-%d")
        stock_data = pd.concat([stock_data, today_data], axis=0)
        stock_data.index = pd.to_datetime(stock_data.index)
        
        if interval[1:] == "d":
            dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                   end=predicted_days[-1], freq="D")
            dt_all_str = [d.strftime("%Y-%m-%d") for d in dt_all.tolist()]
        
        else :
            stock_data = resample(stock_data, period, interval)
            if interval[1:] == "wk":
                dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                       end=stock_data.index.tolist()[-1], freq="7D")
                dt_all_str = [d.strftime("%Y-%m-%d") for d in dt_all.tolist()]
                
            else :
                dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                       end=stock_data.index.tolist()[-1], freq="ME")
                dt_all_str = [d.strftime("%Y-%m") for d in dt_all.tolist()]
        
    dt_breaks = [d for d in dt_all_str if not d in stock_data.index.tolist() and not d in predicted_days]
    stock_data = stock_data.loc[stock_data["Close"] != 0]
    return stock_data, dt_breaks