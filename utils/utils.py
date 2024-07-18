import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import streamlit as st
from datetime import datetime
import time
from inference.data_preprocessing import stochastic

def get_metric(data, forecast):
    stat = {}
    open_price = data["Open"].values[0]
    close_price = round(data["Close"].values[-1], 2)

    diff = round(close_price - open_price, 2)
    diff_percentage = round(diff*100/open_price, 2)
    
    for f in forecast :
        diff_forecast = round(f - open_price)
        diff_percentage_forecast = round(diff_forecast*100/open_price, 2)
        if "Diff Forecast" not in stat :
            stat["Diff Forecast"] = []
            stat["Diff Forecast"].append(diff_forecast)
        else :
            stat["Diff Forecast"].append(diff_forecast)
        
        if "Percent Forecast" not in stat :
            stat["Percent Forecast"] = []
            stat["Percent Forecast"].append(diff_percentage_forecast)
        else :
            stat["Percent Forecast"].append(diff_percentage_forecast)

    stat["Close"] = close_price
    stat["Diff"] = diff
    stat["Percent"] = diff_percentage

    return stat

def line_coloring(data):
    if data[0] > data[-1]:
        return "red"
    else:
        return "green"

def make_graph(data, datebreaks, interval, chart_type, ma_arr, colors, stochastic_param, size=3):
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

    new_data = data.copy()
    volume_color = np.where(new_data["Close"] >= new_data["Open"], "green", "red")
    volume_color[0] = "green" if new_data["Open"].values[0] <= new_data["Close"].values[0] else "red"
    new_data = add_ma(new_data, ma_arr)
    if len(stochastic_param) > 0 :
        period=stochastic_param[0]
        k=stochastic_param[1]
        d=stochastic_param[2]
        
        new_data = stochastic(new_data, period=period, k=k, d=d, for_predict=False)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                            subplot_titles=('', f'Stochastic ({period}, {k}, {d})'), row_width=[0.3, 0.8])
        
        fig.add_trace(go.Scatter(x=new_data.index, y=new_data["K-Stochastic"], name="%K", 
                                 marker={'color':'yellow', 'size':size}, mode='lines', showlegend=True), row=2, col=1)
        fig.add_trace(go.Scatter(x=new_data.index, y=new_data["D-Stochastic"], name="%D", 
                                 marker={'color':'blue', 'size':size}, mode='lines', showlegend=True), row=2, col=1)
    
    else :
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, subplot_titles=('', 'Volume'), row_width=[0.3, 0.8])
        fig.add_trace(go.Bar(x=data.index, y=data["Volume"], showlegend=False, marker_color=volume_color, name="Volume"), row=2, col=1)
        
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(x=new_data.index,
                    open=new_data["Open"], close=new_data["Close"],
                    high=new_data["High"], low=new_data["Low"], showlegend=False, name="Price",
                    increasing_line_color='green', decreasing_line_color='red'), row=1, col=1)
    else :
        data_arr = new_data["Open"].tolist()[:1] + new_data["Close"].tolist()[1:]
        color = line_coloring(data_arr)
        fig.add_trace(go.Scatter(x=new_data.index, y=data_arr, line=dict(color=color, width=3)), row=1, col=1)
    
    fig.update_layout(margin={"b":8, "t":8, "l":8, "r":8},
                      autosize=True, template='plotly_dark',
                      xaxis_rangeslider_visible=False,
                      modebar_add = ['drawline', 'drawrect', 'eraseshape'],
                      modebar_remove = ['lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d'],
                      legend=dict(yanchor='top', xanchor='left', x=0.01, y=0.99),
                      hovermode='x')
    fig.update_xaxes(rangebreaks=[{"values":datebreaks, "dvalue": dval*60*1000}])
    
    if len(ma_arr) > 0 and len(colors) > 0 :
        for ma, color in zip(ma_arr, colors) :
            fig.add_trace(go.Scatter(x=new_data.index, y=new_data["MA "+str(ma)], name="MA "+str(ma), 
                                     marker={'color':color, 'size':size}, hoverinfo='skip'))
    return fig

def add_ma(data, window_size) :
    if window_size is not None :
        for w in window_size :
            data["MA "+str(w)] = data["Close"].rolling(window=w).mean()
    return data

def getcolor():
    color=['aliceblue', 'blue', 'cyan', 'gray', 'gold', 'hotpink', 'lavender', 'lightgreen', 'magenta', 'orange']

    return color

def timer(placeholder) :
    jkt_tz = pytz.timezone('Asia/Jakarta')
    with placeholder :
        jkt_now = datetime.now(jkt_tz)
        open_time = datetime(jkt_now.year, jkt_now.month, jkt_now.day, 9, 15, 0)
        jkt_now = jkt_now.replace(tzinfo=None)
        diff = open_time - jkt_now
        minutes_diff = divmod(diff.seconds, 60)
        st.header("Market will be opened in 00:{:02d}:{:02d}".format(minutes_diff[0], minutes_diff[1]))
        time.sleep(1)