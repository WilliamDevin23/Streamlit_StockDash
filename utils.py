import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from requests_ratelimiter import LimiterSession

session = LimiterSession(per_minute=12)

def get_idx():
    url = "https://id.wikipedia.org/wiki/Daftar_perusahaan_yang_tercatat_di_Bursa_Efek_Indonesia"
    source = requests.get(url)
    soup = BeautifulSoup(source.text, 'html.parser')

    # Stock Codes and Names
    cell = soup.find_all('td')
    companies = []
    i = 0
    while i < len(cell) :
        code = cell[i].get_text()[5:]
        i += 1
        name = " (" + cell[i].get_text().strip() + ")"
        i += 2
        companies.append(code + name)
    return ['IHSG (Indeks Harga Saham Gabungan)'] + sorted(companies)

def get_stock(ticker, period, interval):
    stock = yf.Ticker(ticker, session=session)
    stock_data = stock.history(period=period, interval=interval, prepost=False)
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
                                end=stock_data.index.tolist()[-1], freq="D")
        if interval[1:] == "wk":
            dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                                end=stock_data.index.tolist()[-1], freq="7D")
        
        dt_all_str = [d.strftime("%Y-%m-%d") for d in dt_all.tolist()]

    else:
        stock_data.index = stock_data.index.strftime("%Y-%m")
        dt_all = pd.date_range(start=stock_data.index.tolist()[0],
                            end=stock_data.index.tolist()[-1], freq="ME")
        
        dt_all_str = [d.strftime("%Y-%m") for d in dt_all.tolist()]

    dt_breaks = [d for d in dt_all_str if not d in stock_data.index.tolist()]
    return stock_data, dt_breaks

def get_metric(data):
    stat = {}
    open_price = data["Open"].values[0]
    close_price = round(data["Close"].values[-1], 2)
    diff = round(close_price - open_price, 2)
    diff_percentage = round(diff*100/open_price, 2)
    stat["Close"] = close_price
    stat["Diff"] = diff
    stat["Percent"] = diff_percentage
    return stat

def line_coloring(data):
    if data["Close"].values[0] > data["Close"].values[-1]:
        return "red"
    else:
        return "green"

def make_graph(data, datebreaks, interval, chart_type):
    if interval[1:] == "m":
        dval = int(interval[0])
    elif interval[1:] == "h":
        dval = int(interval[0])*60
    elif interval[1:] == "d":
        dval = int(interval[0])*60*24
    elif interval[1:] == "wk":
        dval = int(interval[0])*60*24*7
    else :
        dval = int(interval[0])*60*24*30
    
    if chart_type == "Candlestick":
        fig = go.Figure(data=[go.Candlestick(x=data.index,
                        open=data["Open"], close=data["Close"],
                        high=data["High"], low=data["Low"])])
    else :
        color = line_coloring(data)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data["Close"], line=dict(color=color, width=3)))
    fig.update_layout(margin={"b":8, "t":8, "l":8, "r":8},
                    autosize=True, template='plotly_dark',
                    xaxis_rangeslider_visible=False)
    fig.update_xaxes(rangebreaks=[{"values":datebreaks, "dvalue": dval*60*1000}])
    return fig