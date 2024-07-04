import numpy as np

def ma_for_predict(data) :
    data = data.copy()
    data["10MA"] = data["Close"].rolling(window=10).mean()
    data["20MA"] = data["Close"].rolling(window=20).mean()
    return data

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
    stock_data = stock_data[["Close"]]
    stock_data = ma_for_predict(stock_data)
    stock_data = clean_data(stock_data)
    data_arr = np.array(stock_data.values)
    return data_arr