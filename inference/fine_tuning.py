from inference.data_preprocessing import *
from inference.prediction import *
from utils.utils import make_graph, line_coloring
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import tensorflow as tf

def windowed_dataset(data, n_past, n_future, batch_size):
    dataset = tf.data.Dataset.from_tensor_slices(data)
    dataset = dataset.window(n_past+n_future, shift=1, drop_remainder=True)
    dataset = dataset.flat_map(lambda window: window.batch(n_past+n_future))
    dataset = dataset.map(lambda window: (window[:n_past], window[n_past:, :1]))
    dataset = dataset.batch(batch_size).prefetch(1)
    return dataset

def clone_model(model) :
    cloned_model = tf.keras.models.clone_model(model)
    cloned_model.set_weights(model.get_weights())
    return cloned_model

def compile_cloned_model(model) :
    model.compile(loss=tf.keras.losses.MeanAbsoluteError(),
                  optimizer=tf.keras.optimizers.Adam(0.001))

@st.cache_data(ttl=3600)
def fine_tuning(_model, daily_data) :
    callback = get_callback()
    daily_data = prepare_data(daily_data)
    normalized_data = normalize_data(daily_data, daily_data.max(axis=0), daily_data.min(axis=0))
    windowed_data = windowed_dataset(normalized_data[-200:, :],
                                     100, 10, 64)
    compile_cloned_model(_model)
    _model.fit(windowed_data, epochs=20, callbacks=[callback], verbose=0)
    forecast = predict(_model, daily_data)
    return forecast

@st.cache_data(ttl=3600)
def show_prediction_chart(daily_data, forecast, datebreaks) :
	dates = get_forecast_date()
	prediction_chart = make_graph(daily_data, datebreaks, "1d",
								  "Candlestick", [], [], [])
	
	prediction_chart.add_trace(go.Scatter(x=dates, y=forecast, mode='lines',
										  line=dict(color=line_coloring(forecast), width=2),
										  name="Predicted", showlegend=False))
										  
	return prediction_chart

@st.cache_data(ttl=3600)
def show_prediction_table(forecast) :
	dates = get_forecast_date()
	pred_df = pd.DataFrame({"Date":dates,
							"Predicted Close Price":forecast})
	pred_df.set_index("Date", inplace=True)
	return pred_df

@st.cache_resource
def get_callback() :
    class myCallback(tf.keras.callbacks.Callback) :
        def on_epoch_end(self, epoch, logs=None) :
            if (logs.get('loss') <= 0.02) :
                self.model.stop_training = True
    mycallback = myCallback()
    return mycallback