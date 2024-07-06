import streamlit as st
from utils import *
from prediction import *
import time
from datetime import datetime, timedelta
import pytz
import yfinance as yf

st.set_page_config(layout='wide')
st.markdown("""<style>
                div.modebar {
                    left:3%;
                }
                button[title='View fullscreen'] {
                    position: absolute; left: -5%;
                }
                [data-testid="stMetricValue"] {
                    font-size: 28px;
                }
                [data-testid="stHeading"] {
                    text-align: center;
                }
            </style>""", unsafe_allow_html=True)

jkt_tz = pytz.timezone('Asia/Jakarta')
jkt_date = datetime.now(jkt_tz)
jkt_hour = int(jkt_date.strftime("%H"))
jkt_day = jkt_date.strftime("%A")

def main() :
    
    #Session states
    if "chart_type" not in st.session_state : st.session_state.chart_type = "Candlestick"
    if "period_filter" not in st.session_state : st.session_state.period_filter = "1d"
    if "interval_filter" not in st.session_state : st.session_state.interval_filter = "5m"
    if "code" not in st.session_state : st.session_state.code = "IHSG"
    if "moving_avgs" not in st.session_state : st.session_state.moving_avgs = []
    if "horizontals" not in st.session_state : st.session_state.horizontals = []
    if "color" not in st.session_state : st.session_state.color = []
    if "ma_disable" not in st.session_state : st.session_state.ma_disable = True
    if "h_disable" not in st.session_state : st.session_state.h_disable = True
    if "realtime" not in st.session_state : st.session_state.realtime = True

    def new_code():
        if st.session_state.new_code[:4] != st.session_state.code:
            st.session_state.code = st.session_state.new_code[:4]
            st.session_state.horizontals = []
    
    # Forecasting
    if st.session_state.code == "IHSG":
        daily_data = get_stock("^JKSE", "5y", "1d", for_predict=True)
    elif st.session_state.code == "LQ45":
        daily_data = get_stock("^JKLQ45", "5y", "1d", for_predict=True)
    else:
        daily_data = get_stock(st.session_state.code+".JK", "5y", "1d", for_predict=True)
    model = get_model()
    forecast = predict(model, daily_data)
    dates = get_forecast_date()

    st.markdown("<h1 style='text-align: center'>Indonesian LQ45 Dashboard</h1>", unsafe_allow_html=True)
    option = st.selectbox("Stock Codes",
                          get_codes(), key="new_code",
                          on_change=new_code)
    code = option[:4]
    name = option[5:]
    
    dashboard, news, download = st.tabs(["Dashboard", "News", "Download Tabular Data"])
    
    with dashboard :
        realtime = st.toggle("Auto Update", value=True)
        
        placeholder = st.empty()

        def update_data(ma_arr, colors, h_lines) :
            
            global stock_data, stock_metric, util, datebreaks, fig
            
            with placeholder.container():
                graph, util = st.columns([0.7, 0.3], gap='small')
            
                with graph :
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader(code)
                        st.write(name)
                    
                    if st.session_state.code == "IHSG":
                        stock_data, datebreaks = get_stock("^JKSE",
                                                           st.session_state.period_filter,
                                                           st.session_state.interval_filter)
                    elif st.session_state.code == "LQ45":
                        stock_data, datebreaks = get_stock("^JKLQ45",
                                                           st.session_state.period_filter,
                                                           st.session_state.interval_filter)
                    else :
                        stock_data, datebreaks = get_stock(st.session_state.code+".JK",
                                                           st.session_state.period_filter,
                                                           st.session_state.interval_filter)

                    stock_metric = get_metric(stock_data, forecast)
                    
                    col2.metric(label="Close Price",
                                value="Rp {0}".format(stock_metric['Close']),
                                delta="{0} ({1} %)".format(stock_metric['Diff'],
                                                           stock_metric['Percent']))

                    fig = make_graph(stock_data, datebreaks,
                                     st.session_state.interval_filter,
                                     st.session_state.chart_type, ma_arr, colors)
                                     
                    if st.session_state.interval_filter == "m" or st.session_state.interval_filter == "h" :
                        for h in h_lines :
                            fig.add_hline(h, line_color='white',
                                          annotation_text=h,
                                          annotation_position='bottom right',
                                          annotation_font_color='white')
                    else :
                        for h in h_lines :
                            fig.add_hline(h, line_color='white',
                                          annotation_text=h,
                                          annotation_position='bottom right',
                                          annotation_font_color='white', row=1, col=1)
                    hover_bg_color = ["green" if close > open else "red" for open, close in zip(stock_data["Open"].values, stock_data["Close"].values) ]
                    fig.update_traces(hoverlabel=dict(bgcolor=hover_bg_color), selector=dict(type="candlestick"))
                    fig.update_traces(hoverinfo="none", selector=dict(type="scatter"))
                    if st.session_state.interval_filter == "1d" :
                        fig.add_trace(go.Scatter(x=dates, y=forecast, mode='lines', line=dict(color='white', width=3), name="Predicted Close Prices"))
                    st.plotly_chart(fig, use_container_width=True)
                
        update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals)
        
        with util :
            time_dict = {"5m":"5 Minutes", "1h":"1 Hour",
                        "1d":"1 Day", "1wk":"1 Week",
                        "1mo":"1 Month", "1y":"1 Year", "1mo":"1 Month",
                        "3y":"3 Years", "5y":"5 Years"}

            def format_func(choice):
                return time_dict[choice]
            
            def update_period():
                if st.session_state.new_period != st.session_state.period_filter:
                    st.session_state.period_filter = st.session_state.new_period
                
                if st.session_state.period_filter == "1d":
                    st.session_state.interval_filter = "5m"
                else:
                    st.session_state.interval_filter = "1d"
            
            def update_interval():
                if st.session_state.new_interval != st.session_state.interval_filter:
                    st.session_state.interval_filter = st.session_state.new_interval

            def update_chart_type():
                if st.session_state.update_chart_type != st.session_state.chart_type:
                    st.session_state.chart_type = st.session_state.update_chart_type
                    
            def add_ma():
                if st.session_state.add_moving_avgs != st.session_state.moving_avgs:
                    st.session_state.moving_avgs = st.session_state.add_moving_avgs

            st.selectbox("Chart Type", ["Candlestick", "Line"],
                        key="update_chart_type", on_change=update_chart_type)

            st.selectbox("Period", ["1d", "1mo", "1y", "3y", "5y"], format_func=format_func,
                        key="new_period", on_change=update_period)

            intervals = ["5m", "1h", "1d", "1wk", "1mo"]
            if st.session_state.period_filter == "1d" :
                intervals = intervals[:2]
            elif st.session_state.period_filter == "1mo" :
                intervals = intervals[2:-1]
            else :
                intervals = intervals[-3:]
            st.selectbox("Interval", intervals, format_func=format_func,
                        key="new_interval", on_change=update_interval)
            
            st.divider()
            
            add_ma, add_line = st.columns(2, gap='small')
            with add_ma :
                with st.form(key='add-ma-form', clear_on_submit=True) :
                    ma = st.number_input(label="Add MA", format="%d", step=1, value=None, min_value=3)
                    if st.form_submit_button("Add", use_container_width=True) :
                        color_arr = getcolor()
                        color = np.random.choice(color_arr, replace=False)
                        st.session_state.moving_avgs.append(ma)
                        st.session_state.color.append(color)
                        st.session_state.ma_disable = False
                        update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals)
            
            with add_line :
                with st.form(key='horizontal-form', clear_on_submit=True) :
                    h = st.number_input(label="Add HLine", format="%d", step=1, value=None, min_value=3)
                    if st.form_submit_button("Add", use_container_width=True) :
                        st.session_state.horizontals.append(h)
                        st.session_state.h_disable = False
                        update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals)
            
            st.divider()
            
            def clear_ma() :
                st.session_state.moving_avgs = []
                st.session_state.color = []
                st.session_state.ma_disable = True
                update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals)
            
            def clear_horizontals() :
                st.session_state.horizontals = []
                st.session_state.h_disable = True
                update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals)
            
            button1, button2 = st.columns(2)
            with button1 :
                st.button("Clear MA", use_container_width=True, disabled = st.session_state.ma_disable, on_click=clear_ma)
            
            with button2 :
                st.button("Clear Lines", use_container_width=True, disabled = st.session_state.h_disable, on_click=clear_horizontals)
        
        st.markdown("<h3 style='text-align:center; margin: 3px 0px;'>Predictions</h3>", unsafe_allow_html=True)
        
        predictions = st.columns(5)
        for i in range(5) :
            with predictions[i] :
                st.metric(label=dates[i],
                          value="Rp {0:.2f}".format(forecast[i]),
                          delta="{0} ({1} %)".format(stock_metric['Diff Forecast'][i], stock_metric['Percent Forecast'][i]))
                st.metric(label=dates[i+5],
                          value="Rp {0:.2f}".format(forecast[i+5]),
                          delta="{0} ({1} %)".format(stock_metric['Diff Forecast'][i+5], stock_metric['Percent Forecast'][i+5]))
        
    with news :
        news_arr = get_news(code)
        for news in news_arr :
            container = st.container(border=True)
            with container :
                st.markdown(f"<h3><a href='{news[3]}' style='text-decoration: none;'>{news[1]}</a></h3>", unsafe_allow_html=True)
                st.write(news[2])
                st.markdown(f"""<p style='color: gray;'>{news[4]}</p>""", unsafe_allow_html=True)
                
    with download :
        st.markdown("<h3 style='text-align:center;'>Download as CSV</h3>", unsafe_allow_html=True)
        table_placeholder = st.empty()
        def update_table() :
            with table_placeholder :
                st.dataframe(stock_data, use_container_width=True)
        
        update_table()

    while (jkt_hour >= 9 and jkt_hour <= 16) and realtime and not (jkt_day == "Saturday" or jkt_day == "Sunday") :
        with dashboard :
            update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals)
        with download :
            update_table()
        time.sleep(30)

def timer(placeholder) :
    jkt_tz = pytz.timezone('Asia/Jakarta')
    with placeholder :
        jkt_now = datetime.now(jkt_tz)
        open_time = datetime(jkt_now.year, jkt_now.month, jkt_now.day, 9, 15, 0)
        jkt_now = jkt_now.replace(tzinfo=None)
        diff = open_time - jkt_now
        minutes_diff = divmod(diff.seconds, 60)
        st.header("Market will be open in 00:{:02d}:{:02d}".format(minutes_diff[0], minutes_diff[1]))
        time.sleep(1)

if __name__ == "__main__":
    if len(yf.Ticker("^JKSE").history("1d")) == 0 :
        timer_placeholder = st.empty()
        while jkt_hour < 10 :
            timer(timer_placeholder)
    else :
        main()