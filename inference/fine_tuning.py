from inference.data_processing import *
from inference.prediction import *
from data_collecting.data_collecting import get_forecast_date
from utils.utils import make_graph, line_coloring
import plotly.graph_objects as go
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
                  optimizer=tf.keras.optimizers.Adam(0.0005))

@st.cache_data(ttl=3600)
def fine_tuning(code, _model0, _daily_data) :
    
    daily_data = prepare_data(_daily_data)
    normalized_data = normalize_data(daily_data, daily_data.max(axis=0), daily_data.min(axis=0))
    windowed_data = windowed_dataset(normalized_data,
                                     100, 10, 64)
    
    result0 = _model0.evaluate(windowed_data)

    if result0[0] > 0.02 :
        _cloned_model = clone_model(_model0)
        callback = get_callback()

        compile_cloned_model(_cloned_model)
        _cloned_model.fit(windowed_data, epochs=2,
                          callbacks=[callback], verbose=1,
                          use_multiprocessing=True)
        
        result1 = _cloned_model.evaluate(windowed_data)
        
    if result0[0] > result1 :
        cloned_model_prediction = predict(code, _cloned_model, daily_data)
        return cloned_model_prediction
        
    else :
        base_model_prediction = predict(code, _model0, daily_data)
        return base_model_prediction

@st.cache_data(ttl=3600)
def show_prediction_chart(code, daily_data, forecast, datebreaks) :
	dates = get_forecast_date(code)
	prediction_chart = make_graph(daily_data, datebreaks, "1d",
								  "Candlestick", [], [], [])
	
	prediction_chart.add_trace(go.Scatter(x=dates, y=forecast, mode='lines',
										  line=dict(color=line_coloring(forecast), width=2),
										  name="Predicted", showlegend=False))
										  
	return prediction_chart

@st.cache_data(ttl=3600)
def show_prediction_table(code, forecast) :
	dates = get_forecast_date(code)
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