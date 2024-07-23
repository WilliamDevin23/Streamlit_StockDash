import numpy as np
import tensorflow as tf
import streamlit as st
from inference.data_processing import *
import numpy as np
import os

@st.cache_resource
def get_model():
    model_path = os.path.join("model", "multivariate_10prediction.h5")
    model = tf.keras.models.load_model(model_path)
    return model

@st.cache_data(ttl=3600)
def model_forecast(_model, data):
    data = np.expand_dims(data, axis=0)
    data = tf.convert_to_tensor(data)
    forecast = _model.predict(data)
    return forecast

@st.cache_data(ttl=3600)
def predict(_model, data):
    scaled_data = normalize_data(data, data.max(axis=0), data.min(axis=0))
    pred = model_forecast(_model, scaled_data[-101:-1, :])
    pred = np.reshape(pred, (-1,))
    stock_pred = reverse_transform(pred, data[:, 0].max(), data[:, 0].min())
    return stock_pred