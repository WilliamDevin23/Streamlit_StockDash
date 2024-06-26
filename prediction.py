import numpy as np
import tensorflow as tf
import pandas as pd
from data_preprocessing import *
from datetime import datetime, timedelta
import pytz

def get_model():
    model = tf.keras.models.load_model("stock_5prediction.keras")
    return model

def model_forecast(model, data):
    data = np.expand_dims(data, axis=0)
    data = tf.convert_to_tensor(data)
    forecast = model.predict(data)
    return forecast

def predict(model, data):
    data_size = len(data)
    scaled_data = normalize_data(data, data.max(axis=0), data.min(axis=0))
    pred = model_forecast(model, scaled_data[-21:-1, :])
    pred = np.reshape(pred, (-1,))
    stock_pred = reverse_transform(pred, data[:, 0].max(), data[:, 0].min())
    return stock_pred

def get_forecast_date() :
    jkt_tz = pytz.timezone('Asia/Jakarta')
    jkt_date = datetime.now(jkt_tz)
    
    # Last Friday if now is weekend
    if jkt_date.strftime("%A") == "Saturday" :
        jkt_date = jkt_date - timedelta(days=1)
    elif jkt_date.strftime("%A") == "Sunday" :
        jkt_date = jkt_date - timedelta(days=2)
    dates = []
    i = 0
    while len(dates) < 5 :
        if (jkt_date + timedelta(days=1*i)).strftime("%A") not in ['Sunday', 'Saturday'] :
            dates.append((jkt_date + timedelta(days=1*i)).strftime("%Y-%m-%d"))
            i += 1
        else :
            jkt_date = jkt_date + timedelta(days=1)
    return dates