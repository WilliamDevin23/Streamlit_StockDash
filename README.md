# Auto Update Dashboard for LQ45 Stock Index

Tools used :
- Tensorflow
- Streamlit
- Plotly
- Neon Serverless PostgreSQL

The data is retrieved with YFinance library, so the data must be delayed for around 15 minutes from the real-time market data.

The model uses LSTM layers to capture longer dependencies between data across the time.

There will be some improvements, but for the general overview, here is the app link :

https://stockdash-live.streamlit.app