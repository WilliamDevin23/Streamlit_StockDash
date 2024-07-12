import numpy as np

def ma_for_predict(data) :
    data = data.copy()
    data["5MA"] = data["Close"].rolling(window=5).mean()
    data["10MA"] = data["Close"].rolling(window=10).mean()
    return data
    
def stochastic(data, period=None, k=None, d=None, for_predict=True) :
    stock_history = data.copy()
    if for_predict :
        stock_history["FastK-Stochastic"] = 100*(stock_history["Close"] - stock_history["Low"].rolling(window=20).min())\
                                            /(stock_history["High"].rolling(window=20).max() - stock_history["Low"].rolling(window=20).min())
        stock_history["K-Stochastic"] = stock_history["FastK-Stochastic"].rolling(window=5).mean()
        stock_history["D-Stochastic"] = stock_history["K-Stochastic"].rolling(window=5).mean()
        stock_history.drop(columns=["FastK-Stochastic"], axis=1, inplace=True)
    else :
        stock_history["FastK-Stochastic"] = 100*(stock_history["Close"] - stock_history["Low"].rolling(window=period).min())\
                                            /(stock_history["High"].rolling(window=period).max() - stock_history["Low"].rolling(window=period).min())
        stock_history["K-Stochastic"] = stock_history["FastK-Stochastic"].rolling(window=k).mean()
        stock_history["D-Stochastic"] = stock_history["K-Stochastic"].rolling(window=d).mean()
        stock_history.drop(columns=["FastK-Stochastic"], axis=1, inplace=True)
    return stock_history

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
    stock_data = stock_data[["Close", "High", "Low", "Volume"]]
    stock_data = ma_for_predict(stock_data)
    stock_data = stochastic(stock_data)
    stock_data = clean_data(stock_data)
    stock_data = stock_data[["Close", "Volume", "5MA", "10MA", "K-Stochastic", "D-Stochastic"]]
    data_arr = np.array(stock_data.values)
    return data_arr