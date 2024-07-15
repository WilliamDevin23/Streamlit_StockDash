# Auto-Updated Dashboard for LQ45 Stock Index
 
## What is this?
Hi! This is the implementation of an LSTM model that I've been built. The dashboard let you to see the live candlestick chart, draw horizontal lines, draw Moving Averages up to 3, draw Stochastic Oscillator, see the trading volume, and see the top 10 newest news for the stock codes.

## LQ45
LQ45 is an index consists of top 45 most liquid stocks in IDX market.

## Tools and Languages
![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue) ![Tensorflow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white) ![Numpy](https://img.shields.io/badge/Numpy-777BB4?style=for-the-badge&logo=numpy&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-2C2D72?style=for-the-badge&logo=pandas&logoColor=white) ![Plotly](https://img.shields.io/badge/Plotly-239120?style=for-the-badge&logo=plotly&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white) ![Git](https://img.shields.io/badge/GIT-E44C30?style=for-the-badge&logo=git&logoColor=white)

## Limitations
- The data is retrieved with YFinance library, so the data must be delayed for around 15 minutes from the real-time market data.
- The model uses only LSTM layers to capture longer dependencies between data across the time.
- Technical Indicators involved Moving Average and Stochastic Oscillator.

## Notes
There will be some improvements, but for the general overview, here is the app link :

https://stockdash-live.streamlit.app