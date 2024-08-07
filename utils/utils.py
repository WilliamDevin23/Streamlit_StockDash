import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import streamlit as st
import time
from inference.data_processing import stochastic

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
    if data[0] > data[-1]:
        return "red"
    else:
        return "green"

def volume_hover_coloring(data):
    for i in range(1, len(data)) :
        if data["Close"].iloc[i] > data["Open"].iloc[i] :
            data.iloc[i, -1] = "green"
        elif data["Close"].iloc[i] == data["Open"].iloc[i] :
            if data["Close"].iloc[i] > data["Close"].iloc[i-1] :
                data.iloc[i, -1] = "green"
            elif data["Close"].iloc[i] < data["Close"].iloc[i-1] :
                data.iloc[i, -1] = "red"
            else :
                data.iloc[i, -1] = data.iloc[i-1, -1]
        else :
            data.iloc[i, -1] = "red"
    return data
    
def make_graph(data, datebreaks, interval, chart_type, ma_arr, colors, stochastic_param, size=3):
    if interval[1:] == "d":
        dval = int(interval[0])*60*24
    elif interval[1:] == "wk":
        dval = int(interval[0])*60*24*7
    else :
        dval = int(interval[0])*60*24*30

    new_data = data.copy()
    new_data.insert(len(new_data.columns), "Color", "gray")
    new_data.iloc[0, -1] = "green" if new_data["Open"].values[0] <= new_data["Close"].values[0] else "red"
    new_data = volume_hover_coloring(new_data)
    new_data = add_ma(new_data, ma_arr)
    
    volume_candle_hover_color = new_data["Color"].values
    
    if len(stochastic_param) > 0 :
        period=stochastic_param[0]
        k=stochastic_param[1]
        d=stochastic_param[2]
        
        new_data = stochastic(new_data, period=period, k=k, d=d, for_predict=False)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                            subplot_titles=('', f'Stochastic ({period}, {k}, {d})'), row_width=[0.3, 0.8])
        
        fig.add_trace(go.Scatter(x=new_data.index, y=new_data["K-Stochastic"], name="%K", 
                                 marker={'color':colors["stoch_color"][0], 'size':size},
                                 mode='lines', showlegend=True), row=2, col=1)
        fig.add_trace(go.Scatter(x=new_data.index, y=new_data["D-Stochastic"], name="%D", 
                                 marker={'color':colors["stoch_color"][1], 'size':size},
                                 mode='lines', showlegend=True), row=2, col=1)
        fig.update_traces(hoverlabel=dict(bgcolor='black'), selector=dict(type='scatter'))
    
    else :
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                            subplot_titles=('', 'Volume'), row_width=[0.3, 0.8])
        fig.add_trace(go.Bar(x=data.index, y=data["Volume"], showlegend=False,
                      marker_color=volume_candle_hover_color, name="Volume"), row=2, col=1)
        fig.update_traces(hoverlabel=dict(bgcolor=volume_candle_hover_color),
                          selector=dict(type='bar'))
        
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(x=new_data.index,
                    open=new_data["Open"], close=new_data["Close"],
                    high=new_data["High"], low=new_data["Low"], showlegend=False, name="Price",
                    increasing_line_color='green', decreasing_line_color='red'), row=1, col=1)
        
        fig.update_traces(hoverlabel=dict(bgcolor=volume_candle_hover_color),
                          selector=dict(type="candlestick"))
    
    else :
        data_arr = new_data["Open"].tolist()[:1] + new_data["Close"].tolist()[1:]
        color = line_coloring(data_arr)
        fig.add_trace(go.Scatter(x=new_data.index, y=data_arr, line=dict(color=color, width=3),
                      showlegend=False, name="Price"), row=1, col=1)
    
    fig.update_layout(margin={"b":8, "t":8, "l":8, "r":8},
                      autosize=True, template='plotly_dark',
                      xaxis_rangeslider_visible=False,
                      modebar_add = ['drawline', 'drawrect', 'eraseshape'],
                      modebar_remove = ['lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d'],
                      legend=dict(yanchor='top', xanchor='left', x=0.01, y=0.98),
                      newshape=dict(line_color='cyan',
                                    fillcolor='cyan',
                                    opacity=0.28),
                                    hoverlabel_font=dict(color="white"))
    fig.update_xaxes(rangebreaks=[{"values":datebreaks, "dvalue": dval*60*1000}])
    
    if len(ma_arr) > 0 and len(colors) > 0 :
        for ma, color in zip(ma_arr, colors["ma_color"]) :
            fig.add_trace(go.Scatter(x=new_data.index, y=new_data["MA "+str(ma)], name="MA "+str(ma), 
                                     marker={'color':color, 'size':size}, hoverinfo='skip'))
    
    return fig

def add_ma(data, window_size) :
    if window_size is not None :
        for w in window_size :
            data["MA "+str(w)] = data["Close"].rolling(window=w).mean()
    return data