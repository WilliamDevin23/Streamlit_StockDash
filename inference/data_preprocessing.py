import numpy as np
import pandas as pd

def ma_for_predict(data) :
    data = data.copy()
    data["5MA"] = data["Close"].rolling(window=5).mean()
    data["10MA"] = data["Close"].rolling(window=10).mean()
    return data
    
def stochastic(data, period=None, k=None, d=None, for_predict=True) :
    stock_history = data.copy()
    if for_predict :
        stock_history["FastK-Stochastic"] = 100*(stock_history["Close"] - stock_history["Low"].rolling(window=20).min())\
                                            /(stock_history["High"].rolling(window=20).max() - stock_history["Low"].rolling(window=20).min())
        stock_history["K-Stochastic"] = stock_history["FastK-Stochastic"].rolling(window=5).mean()
        stock_history["D-Stochastic"] = stock_history["K-Stochastic"].rolling(window=5).mean()
        stock_history.drop(columns=["FastK-Stochastic"], axis=1, inplace=True)
    else :
        stock_history["FastK-Stochastic"] = 100*(stock_history["Close"] - stock_history["Low"].rolling(window=period).min())\
                                            /(stock_history["High"].rolling(window=period).max() - stock_history["Low"].rolling(window=period).min())
        stock_history["K-Stochastic"] = stock_history["FastK-Stochastic"].rolling(window=k).mean()
        stock_history["D-Stochastic"] = stock_history["K-Stochastic"].rolling(window=d).mean()
        stock_history.drop(columns=["FastK-Stochastic"], axis=1, inplace=True)
    return stock_history

def clean_data(data) :
    data = data.copy()
    data.dropna(inplace=True)
    data = data.loc[(data != 0).all(axis=1)]
    return data
    
def normalize_data(data, max, min) :
    new_data = data.copy()
    new_data -= min
    new_data /= (max - min)
    return new_data
    
def reverse_transform(data, max, min) :
    new_data = data.copy()
    new_data *= (max - min)
    new_data += min
    return new_data

def prepare_data(stock_data) :
    stock_data = stock_data[["Close", "High", "Low", "Volume"]]
    stock_data = ma_for_predict(stock_data)
    stock_data = stochastic(stock_data)
    stock_data = clean_data(stock_data)
    stock_data = stock_data[["Close", "Volume", "5MA", "10MA", "K-Stochastic", "D-Stochastic"]]
    data_arr = np.array(stock_data.values)
    return data_arr
    
def resample(data, period, interval) :

    # Cut the data
    last_day = data.index[-1]
    if period[1:] == "mo" :
        first_day = last_day - pd.DateOffset(days=30)
        monday_before = first_day - pd.DateOffset(days=first_day.weekday())
        data = data.loc[monday_before:]
    elif period[1:] == "y" :
        n_period = int(period.replace("y", ""))
        first_day = last_day - pd.DateOffset(days=n_period*365)
        first_day = first_day.replace(day=1)
        data = data.loc[first_day:]
    
    # Resample :
    if interval[1:] == "wk" :
        data = data.resample("W-FRI").agg({"Open":"first", "High":"max",
                                           "Low":"min", "Close":"last",
                                           "Volume":"sum"})
    elif interval[1:] == "mo" :
        data = data.resample("M").agg({"Open":"first", "High":"max",
                                       "Low":"min", "Close":"last",
                                       "Volume":"sum"})
    
    return data