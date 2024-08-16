import numpy as np
import pandas as pd
import streamlit as st
import tensorflow as tf

def windowed_dataset(data, n_past, n_future, batch_size, for_forecast=False):
    dataset = tf.data.Dataset.from_tensor_slices(data)
    
    if not for_forecast :
        dataset = dataset.window(n_past+n_future, shift=1, drop_remainder=True)
        dataset = dataset.flat_map(lambda window: window.batch(n_past+n_future))
        dataset = dataset.map(lambda window: (window[:n_past], window[n_past:, :1]))
    else :
        dataset = dataset.window(n_past, shift=1, drop_remainder=True)
        dataset = dataset.flat_map(lambda window: window.batch(n_past))
    dataset = dataset.batch(batch_size).prefetch(1)
    return dataset
    
def ma_for_predict(data) :
    data = data.copy()
    data["5MA"] = data["Close"].rolling(window=5).mean()
    data["10MA"] = data["Close"].rolling(window=10).mean()
    return data

def stochastic(data, period=None, k=None, d=None, for_predict=True) :
    stock_history = data.copy()
    if for_predict :
        stock_history["FastK-Stochastic"] = (stock_history["Close"] - stock_history["Low"].rolling(window=14).min())\
                                            /(stock_history["High"].rolling(window=14).max() - stock_history["Low"].rolling(window=14).min())
        stock_history["K-Stochastic"] = stock_history["FastK-Stochastic"].rolling(window=3).mean()
        stock_history["D-Stochastic"] = stock_history["K-Stochastic"].rolling(window=3).mean()
        stock_history.drop(columns=["FastK-Stochastic"], inplace=True)
    else :
        stock_history["FastK-Stochastic"] = (stock_history["Close"] - stock_history["Low"].rolling(window=period).min())\
                                            /(stock_history["High"].rolling(window=period).max() - stock_history["Low"].rolling(window=period).min())
        stock_history["K-Stochastic"] = stock_history["FastK-Stochastic"].rolling(window=k).mean()
        stock_history["D-Stochastic"] = stock_history["K-Stochastic"].rolling(window=d).mean()
        stock_history.drop(columns=["FastK-Stochastic"], inplace=True)
    return stock_history

def clean_data(data) :
    new_data = data.copy()
    new_data.dropna(inplace=True)
    return new_data

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
    stock_data = clean_data(stock_data)
    stock_data = ma_for_predict(stock_data)
    stock_data = stochastic(stock_data)
    stock_data = clean_data(stock_data)
    stock_data = stock_data[["Close", "Volume", "5MA", "10MA", "K-Stochastic", "D-Stochastic"]]
    data_arr = np.array(stock_data.values)
    return data_arr
    
def resample(data, interval) :
    data.index = pd.to_datetime(data.index, format="%Y-%m-%d")
    if interval[1:] == "wk" :
        data = data.resample("W-FRI").agg({"Open":"first", "High":"max",
                                           "Low":"min", "Close":"last",
                                           "Volume":"sum"})
        data.index = data.index.strftime("%Y-%m-%d")
    elif interval[1:] == "mo" :
        data = data.resample("ME").agg({"Open":"first", "High":"max",
                                        "Low":"min", "Close":"last",
                                        "Volume":"sum"})
        data.index = data.index.strftime("%Y-%m")
    return data