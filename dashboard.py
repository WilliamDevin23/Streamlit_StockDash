import streamlit as st
from utils import *
import time

def main() :
    
    #Session states
    if "chart_type" not in st.session_state : st.session_state.chart_type = "Candlestick"
    if "period_filter" not in st.session_state : st.session_state.period_filter = "1d"
    if "interval_filter" not in st.session_state : st.session_state.interval_filter = "5m"
    if "code" not in st.session_state : st.session_state.code = "IHSG"

    def new_code():
        if st.session_state.new_code[:4] != st.session_state.code:
            st.session_state.code = st.session_state.new_code[:4]
            
    st.header("Indonesian Stock Exchange Dashboard")
    option = st.selectbox("IDX Stocks",
                get_idx(), key="new_code",
                on_change=new_code)
    code = option[:4]
    name = option[5:]
    
    placeholder = st.empty()

    with placeholder.container():
        col1, col2 = st.columns([0.6, 0.4])
        
        with col1:
            st.subheader(code)
            st.write(name)
        
        if st.session_state.code == "IHSG":
                stock_data, datebreaks = get_stock("^JKSE", st.session_state.period_filter,
                                                    st.session_state.interval_filter)
        else :
            stock_data, datebreaks = get_stock(st.session_state.code+".JK", st.session_state.period_filter,
                                                st.session_state.interval_filter)
        stock_metric = get_metric(stock_data)

        col2.metric(label="Close Price",
                value="Rp {0}".format(stock_metric['Close']),
                delta="{0} ({1} %)".format(stock_metric['Diff'], stock_metric['Percent']))

        fig = make_graph(stock_data, datebreaks, st.session_state.interval_filter, st.session_state.chart_type)
        st.write(fig)

    filter1, filter2, filter3 = st.columns(3)
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

    with filter1:
        st.selectbox("Chart Type", ["Candlestick", "Line"],
            key="update_chart_type", on_change=update_chart_type)

    with filter2:
        st.selectbox("Period", ["1d", "1mo", "1y", "5y", "max"], format_func=format_func,
            key="new_period", on_change=update_period)

    with filter3:
        intervals = ["5m", "1h", "1d", "1wk", "1mo"]
        if st.session_state.period_filter == "1d" :
            intervals = intervals[:2]
        elif st.session_state.period_filter == "1mo" :
            intervals = intervals[2:-1]
        else :
            intervals = intervals[-3:]
        st.selectbox("Interval", intervals, format_func=format_func,
            key="new_interval", on_change=update_interval)

    while True:
        with placeholder.container():
            col1, col2 = st.columns([0.6, 0.4])
            
            with col1:
                st.subheader(code)
                st.write(name)
            
            if st.session_state.code == "IHSG":
                    stock_data, datebreaks = get_stock("^JKSE", st.session_state.period_filter,
                                                        st.session_state.interval_filter)
            else :
                stock_data, datebreaks = get_stock(st.session_state.code+".JK", st.session_state.period_filter,
                                                    st.session_state.interval_filter)
            stock_metric = get_metric(stock_data)

            col2.metric(label="Close Price",
                    value="Rp {0}".format(stock_metric['Close']),
                    delta="{0} ({1} %)".format(stock_metric['Diff'], stock_metric['Percent']))

            fig = make_graph(stock_data, datebreaks, st.session_state.interval_filter, st.session_state.chart_type)
            st.write(fig)
        time.sleep(10)
if __name__ == "__main__":
    main()