from inference.data_preprocessing import *
from inference.prediction import *
from utils.utils import make_graph, line_coloring
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import tensorflow as tf

@st.cache_data
def fine_tuning(_model, daily_data) :
    callback = get_callback()
    daily_data = prepare_data(daily_data)
    normalized_data = normalize_data(daily_data, daily_data.max(axis=0), daily_data.min(axis=0))
    retrain_data = np.expand_dims(normalized_data[-111:-11, :], axis=0)
    retrain_label = np.expand_dims(normalized_data[-11:-1, 0], axis=0)
    _model.fit(x=retrain_data, y=retrain_label,
               epochs=8, callbacks=[callback])
    forecast = predict(_model, daily_data)
    return forecast

@st.cache_data
def show_prediction_chart(daily_data, forecast, datebreaks) :
	dates = get_forecast_date()
	prediction_chart = make_graph(daily_data, datebreaks, "1d",
								  "Candlestick", [], [], [])
	
	prediction_chart.add_trace(go.Scatter(x=dates, y=forecast, mode='lines',
										  line=dict(color=line_coloring(forecast), width=2),
										  name="Predicted"))
										  
	return prediction_chart

@st.cache_data
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
            if (logs.get('loss') <= 0.015) :
                self.model.stop_training = True
    mycallback = myCallback()
    return mycallback