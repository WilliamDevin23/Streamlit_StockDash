import streamlit as st
from requests_ratelimiter import LimiterSession
import yfinance as yf
import pandas as pd
from inference.data_preprocessing import prepare_data
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

def get_stock(ticker, period, interval, for_predict=False):
    stock = yf.Ticker(ticker, session=session)
    stock_data = stock.history(period=period, interval=interval, prepost=True)
    predicted_days = get_forecast_date()
    
    if not for_predict:
        if interval[1:] == "m" or interval[1:] == "h":
            stock_data.index = stock_data.index.strftime("%Y-%m-%d %H:%M:%S")

            if interval[1:] == "m":
                dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                    end=stock_data.index.tolist()[-1], freq="5min")
            else :
                dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                    end=stock_data.index.tolist()[-1], freq="h")
            dt_all_str = [d.strftime("%Y-%m-%d %H:%M:%S") for d in dt_all.tolist()]
        
        elif interval[1:] == "d" or interval[1:] == "wk" :
            stock_data.index = stock_data.index.strftime("%Y-%m-%d")

            if interval[1:] == "d":
                dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                    end=predicted_days[-1], freq="D")
            if interval[1:] == "wk":
                dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                    end=stock_data.index.tolist()[-1], freq="7D")
            
            dt_all_str = [d.strftime("%Y-%m-%d") for d in dt_all.tolist()]

        else:
            stock_data.index = stock_data.index.strftime("%Y-%m")
            dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                end=stock_data.index.tolist()[-1], freq="ME")
            
            dt_all_str = [d.strftime("%Y-%m") for d in dt_all.tolist()]
        
        
        dt_breaks = [d for d in dt_all_str if not d in stock_data.index.tolist() and not d in predicted_days]
        stock_data = stock_data.loc[stock_data["Close"] != 0]
        return stock_data, dt_breaks

    else :
        stock_data = prepare_data(stock_data)
        return stock_data