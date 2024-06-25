import streamlit as st
from utils import *
from prediction import *
import time
from datetime import datetime
import pytz

st.set_page_config(layout='wide')
st.markdown("<style>div.modebar { left:3%; } button[title='View fullscreen'] { position: absolute; left: -5%; }</style>", unsafe_allow_html=True)

def main() :
    
    jkt_tz = pytz.timezone('Asia/Jakarta')
    jkt_hour = int(datetime.now(jkt_tz).strftime("%H"))
    jkt_day = datetime.now(jkt_tz).strftime("%A")
    
    #Session states
    if "chart_type" not in st.session_state : st.session_state.chart_type = "Candlestick"
    if "period_filter" not in st.session_state : st.session_state.period_filter = "1d"
    if "interval_filter" not in st.session_state : st.session_state.interval_filter = "5m"
    if "code" not in st.session_state : st.session_state.code = "IHSG"
    if "moving_avgs" not in st.session_state : st.session_state.moving_avgs = []
    if "horizontals" not in st.session_state : st.session_state.horizontals = []

    def new_code():
        if st.session_state.new_code[:4] != st.session_state.code:
            st.session_state.code = st.session_state.new_code[:4]
            st.session_state.horizontals = []
    
    # Forecasting
    if st.session_state.code == "IHSG":
        daily_data = get_stock("^JKSE", "5y", "1d", close_only=True)
    else:
        daily_data = get_stock(st.session_state.code+".JK", "5y", "1d", close_only=True)
    model = get_model()
    scaler = get_scaler()
    scaled_data = minmax_data(daily_data, scaler)
    forecast = int(model_forecast(scaler, model, scaled_data[-51:-1]))

    st.markdown("<h1 style='text-align: center'>Indonesian Stock Exchange Dashboard</h1>", unsafe_allow_html=True)
    option = st.selectbox("IDX Stocks",
                          get_idx(), key="new_code",
                          on_change=new_code)
    code = option[:4]
    name = option[5:]
    
    placeholder = st.empty()

    def update_data(ma_arr, h_lines) :
        
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
                                 st.session_state.chart_type, ma_arr)
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

                st.plotly_chart(fig, use_container_width=True)
    
    update_data(st.session_state.moving_avgs, st.session_state.horizontals)
            
    with util :
        time_dict = {"5m":"5 Minutes", "1h":"1 Hour",
                    "1d":"1 Day", "1wk":"1 Week",
                    "1mo":"1 Month", "1y":"1 Year", "1mo":"1 Month",
                    "5y":"5 Years", "max":"All"}

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

        st.selectbox("Period", ["1d", "1mo", "1y", "5y", "max"], format_func=format_func,
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
                    st.session_state.moving_avgs.append(ma)
                    update_data(st.session_state.moving_avgs, st.session_state.horizontals)
        
        with add_line :
            with st.form(key='horizontal-form', clear_on_submit=True) :
                h = st.number_input(label="Add HLine", format="%d", step=1, value=None, min_value=3)
                if st.form_submit_button("Add", use_container_width=True) :
                    st.session_state.horizontals.append(h)
                    update_data(st.session_state.moving_avgs, st.session_state.horizontals)
        
        st.divider()
        
        button1, button2 = st.columns(2)
        with button1 :
            if st.button("Clear MA", use_container_width=True) :
                st.session_state.moving_avgs = []
                update_data(st.session_state.moving_avgs, st.session_state.horizontals)
        
        with button2 :
            if st.button("Clear Lines", use_container_width=True) :
                st.session_state.horizontals = []
                update_data(st.session_state.moving_avgs, st.session_state.horizontals)
    
    st.markdown("<h3 style='text-align:center; margin: 3px 0px;'>Predictions</h3>", unsafe_allow_html=True)
    st.metric(label="Predicted Close Price Today",
              value="Rp {0}".format(forecast),
              delta="{0} ({1} %)".format(stock_metric['Diff Forecast'], stock_metric['Percent Forecast']))
    
    st.markdown("<h3 style='text-align:center;'>Download as CSV</h3>", unsafe_allow_html=True)
    
    table_placeholder = st.empty()
    def update_table() :
        with table_placeholder :
            st.dataframe(stock_data)
    
    update_table()
    
    while jkt_hour >= 9 and jkt_hour <= 16 and not (jkt_day == "Saturday" or jkt_day == "Sunday") :
        update_data(st.session_state.moving_avgs, st.session_state.horizontals)
        update_table()
        time.sleep(30)
        

if __name__ == "__main__":
    main()