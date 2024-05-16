import numpy as np
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import tensorflow as tf
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def get_model():
    model = tf.keras.models.load_model("stock_prediction.keras")
    return model

def get_scaler():
    return MinMaxScaler()

def minmax_data(df: pd.DataFrame, scaler: MinMaxScaler):
    df = np.reshape(df, (-1, 1))
    scaled_data = scaler.fit_transform(df)
    scaled_data = scaled_data.squeeze()
    return scaled_data

def model_forecast(scaler: MinMaxScaler, model, series: list | np.ndarray):
    series = tf.expand_dims(series, axis=-1)
    series = tf.expand_dims(series, axis=0)
    forecast = model.predict(series)
    forecast = scaler.inverse_transform(forecast).squeeze()
    return forecast