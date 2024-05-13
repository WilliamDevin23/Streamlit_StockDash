import streamlit as st
from utils import *

def main() :
    if "chart_type" not in st.session_state : st.session_state.chart_type = "Candlestick"
    if "period_filter" not in st.session_state : st.session_state.period_filter = "1d"
    if "interval_filter" not in st.session_state : st.session_state.interval_filter = "5m"
    
    st.header("Indonesian Stock Exchange Dashboard")
    col1, col2, col3 = st.columns(3)

    with col1:
        option = st.selectbox("IDX Stocks",
                get_idx())
        code = option[:4]
        name = option[5:]
    
    with col2:
        st.subheader(code)
        st.write(name)
    
    with col3:
        if option[:4] == "IHSG":
            stock_data, datebreaks = get_stock("^JKSE", st.session_state.period_filter,
                                                st.session_state.interval_filter)
        else :
            stock_data, datebreaks = get_stock(code+".JK", st.session_state.period_filter,
                                                st.session_state.interval_filter)
        stock_metric = get_metric(stock_data)
        st.metric(label="Close Price",
                value="Rp {0}".format(stock_metric['Close']),
                delta="Rp {0} ({1} %)".format(stock_metric['Diff'], stock_metric['Percent']))

    fig = make_graph(stock_data, datebreaks, st.session_state.interval_filter, st.session_state.chart_type)
    st.plotly_chart(fig)

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


if __name__ == "__main__":
    main()