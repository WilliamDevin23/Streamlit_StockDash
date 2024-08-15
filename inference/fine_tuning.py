from inference.data_processing import *
from inference.prediction import *
from data_collecting.data_collecting import get_forecast_date
from utils.utils import make_graph, line_coloring
import plotly.graph_objects as go
import pandas as pd
import tensorflow as tf

def clone_model(model) :
    cloned_model = tf.keras.models.clone_model(model)
    cloned_model.set_weights(model.get_weights())
    return cloned_model

def compile_cloned_model(model) :
    model.compile(loss=tf.keras.losses.MeanAbsoluteError(),
                  optimizer=tf.keras.optimizers.Adam(0.0001))

@st.cache_data(ttl=3600)
def fine_tuning(code, _model0, _data) :
    
    normalized_data = normalize_data(_data, _data.max(axis=0), _data.min(axis=0))
    windowed_data = windowed_dataset(normalized_data,
                                     20, 1, 64)
    
    result0 = _model0.evaluate(windowed_data)

    if result0[0] > 0.02 :
        _cloned_model = clone_model(_model0)
        callback = get_callback()

        compile_cloned_model(_cloned_model)
        _cloned_model.fit(windowed_data, epochs=10,
                          callbacks=[callback], verbose=1,
                          use_multiprocessing=True)
        
        result1 = _cloned_model.evaluate(windowed_data)
        
        if result0[0] > result1 :
            cloned_model_prediction = predict(code, _cloned_model, _data)
            return cloned_model_prediction
        
    base_model_prediction = predict(code, _model0, _data)
    return base_model_prediction

@st.cache_data(ttl=3600)
def show_prediction_chart(code, _data, _forecast, _datebreaks) :
    prediction_date = get_forecast_date()
    prediction_dates = np.append(_data.index.values, prediction_date)
    prediction_chart = make_graph(_data[-100:], _datebreaks[-100:], "1wk",
								  "Candlestick", [], [], [])
    prediction_chart.add_trace(go.Scatter(x=prediction_dates[-100:], y=_forecast[-100:], mode='lines',
										  line=dict(color='cyan', width=2),
										  name="Predicted", showlegend=False))
    prediction_chart.update_traces(hoverlabel=dict(bgcolor='black'), selector=dict(type='scatter'))
    
    return prediction_chart, prediction_date

def metric_prediction(code, _data, _forecast) :
    pred_diff = round((_forecast - _data), 2)
    pred_diff_percent = round(100*(pred_diff/_data), 2)
    return pred_diff, pred_diff_percent
    
@st.cache_resource
def get_callback() :
    class myCallback(tf.keras.callbacks.Callback) :
        def on_epoch_end(self, epoch, logs=None) :
            if (logs.get('loss') <= 0.02) :
                self.model.stop_training = True
    mycallback = myCallback()
    return mycallback