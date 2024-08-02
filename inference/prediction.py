import numpy as np
import tensorflow as tf
import streamlit as st
from inference.data_processing import *
import numpy as np
import os
    
@st.cache_resource
def get_model():
    model_path = os.path.join("model", "20_window_model.h5")
    model = tf.keras.models.load_model(model_path)
    return model

@st.cache_data(ttl=3600)
def model_forecast(_model, data):
    data = windowed_dataset(data, 20, 1, 64, for_forecast=True)
    forecast = _model.predict(data)
    return forecast

@st.cache_data(ttl=3600)
def predict(code, _model, data):
    scaled_data = normalize_data(data, data.max(axis=0), data.min(axis=0))
    pred = model_forecast(_model, scaled_data)
    pred = np.reshape(pred, (-1,))
    stock_pred = reverse_transform(pred, data[:, 0].max(), data[:, 0].min())
    return stock_pred