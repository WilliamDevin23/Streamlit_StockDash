import streamlit as st

# Streamlit Wide Layout
st.set_page_config(layout='wide')

from utils import *
from prediction import *
import time
import yfinance as yf

# Plotly ModeBar Buttons, Streamlit Metric and Heading Positioning
st.markdown("""<style>
                div.modebar {
                    left:40%;
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

# Main Application
def main() :
    
    global date, day, hour, minute
    
    #Session states
    if "chart_type" not in st.session_state : st.session_state.chart_type = "Candlestick"
    if "period_filter" not in st.session_state : st.session_state.period_filter = "1d"
    if "interval_filter" not in st.session_state : st.session_state.interval_filter = "5m"
    if "code" not in st.session_state : st.session_state.code = "IHSG"
    if "moving_avgs" not in st.session_state : st.session_state.moving_avgs = []
    if "stochastic" not in st.session_state : st.session_state.stochastic = []
    if "horizontals" not in st.session_state : st.session_state.horizontals = []
    if "color" not in st.session_state : st.session_state.color = []
    if "ma_disable" not in st.session_state : st.session_state.ma_disable = True
    if "h_disable" not in st.session_state : st.session_state.h_disable = True
    if "realtime" not in st.session_state : st.session_state.realtime = True
    
    # Function to handle code choice
    def new_code():
        if st.session_state.new_code[:4] != st.session_state.code:
            st.session_state.code = st.session_state.new_code[:4]
            st.session_state.horizontals = []
    
    # Get the daily data spans for 10 years.
    if st.session_state.code == "IHSG":
        daily_data = get_stock("^JKSE", "10y", "1d", for_predict=True)
    elif st.session_state.code == "LQ45":
        daily_data = get_stock("^JKLQ45", "10y", "1d", for_predict=True)
    else:
        daily_data = get_stock(st.session_state.code+".JK", "10y", "1d", for_predict=True)
    
    # Forecast the next 10 days prices.
    model = get_model()
    forecast = predict(model, daily_data)
    dates = get_forecast_date()

    # Title
    st.markdown("<h1 style='text-align: center'>Indonesian LQ45 Dashboard</h1>", unsafe_allow_html=True)
    
    # Code SelectBox
    option = st.selectbox("Stock Codes",
                          get_codes(), key="new_code",
                          on_change=new_code)
    
    # Selected Company's Name
    name = option[5:]
    
    # Defining Three Tabs
    dashboard, news, download = st.tabs(["Dashboard", "News", "Download Tabular Data"])
    
    # First Tab : Dashboard
    with dashboard :
        
        #Toggle Button to Activate/Deactivate Auto Update
        realtime = st.toggle("Auto Update", value=True)
        
        # Placeholder for the Candlestick Chart and the Price Metric
        placeholder = st.empty()
        
        # Function to Update Metric and the Candlestick Chart
        def update_data(ma_arr: list, colors: list, h_lines: list, stochastic: list) :
            
            # Global variables for further use outside the function
            global stock_data, stock_metric, util, datebreaks, fig
            
            # Inside the Placeholder
            with placeholder.container():
                
                # Two columns : First part for the chart, second part for the tools and filter
                graph, util = st.columns([0.7, 0.3], gap='small')
            
                # Inside the Graph
                with graph :
                    
                    # Make 2 columns : first for code name, second for the metric
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"<h3>{st.session_state.code}</h3>", unsafe_allow_html=True)
                        st.write(name)
                    
                    # Handle the selected code due to code alias
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
                    
                    # Get the closed price metric
                    stock_metric = get_metric(stock_data, forecast)
                    
                    # Show the metric in column 2
                    col2.metric(label="Close Price",
                                value="Rp {0}".format(stock_metric['Close']),
                                delta="{0} ({1} %)".format(stock_metric['Diff'],
                                                           stock_metric['Percent']))
                    
                    # Make the candlestick chart
                    fig = make_graph(stock_data, datebreaks,
                                     st.session_state.interval_filter,
                                     st.session_state.chart_type,
                                     ma_arr, colors, stochastic)
                    
                    # Draw horizontal lines on the chart if the list isn't empty.
                    if len(h_lines) > 0 :
                        for h in h_lines :
                            fig.add_hline(h, line_color='white',
                                          annotation_text=h,
                                          annotation_position='bottom right',
                                          annotation_font_color='white', row=1, col=1)
                    
                    # List that stores hoverinfo background colors corresponding to each data.
                    hover_bg_color = ["green" if close > open else "red" for open, close in zip(stock_data["Open"].values, stock_data["Close"].values)]
                    
                    # Handle candlestick hoverinfo background color.
                    fig.update_traces(hoverlabel=dict(bgcolor=hover_bg_color), selector=dict(type="candlestick"))
                    
                    # Disable hoverinfo for Moving Average line(s).
                    fig.update_traces(hoverinfo="none", selector=dict(type="scatter"))
                    
                    # If interval is daily, then plot the forecasted prices.
                    if st.session_state.interval_filter == "1d" :
                        fig.add_trace(go.Scatter(x=dates, y=forecast, mode='lines',
                                                 line=dict(color=line_coloring(forecast), width=2),
                                                 name="Predicted Close Prices"))
                    
                    # Display the plot.
                    st.plotly_chart(fig, use_container_width=True)
        
        # Run update_data() for the first time.
        update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals, st.session_state.stochastic)
        
        # utils column.
        with util :
            
            # Dictionary that maps interval abbreviation.
            time_dict = {"5m":"5 Minutes", "1h":"1 Hour",
                        "1d":"1 Day", "1wk":"1 Week",
                        "1mo":"1 Month", "1y":"1 Year", "1mo":"1 Month",
                        "3y":"3 Years", "5y":"5 Years"}
            
            # Return the corresponding choice based on the time_dict. Triggered since the selectboxes are rendered.
            def format_func(choice: str) -> str:
                return time_dict[choice]
            
            # Updating period session states. Triggered when the selected period in the selectbox is changed.
            def update_period():
                if st.session_state.new_period != st.session_state.period_filter:
                    st.session_state.period_filter = st.session_state.new_period
                
                if st.session_state.period_filter == "1d":
                    st.session_state.interval_filter = "5m"
                else:
                    st.session_state.interval_filter = "1d"
            
            # Updating interval session states. Triggered when the selected interval in the selectbox is changed.
            def update_interval():
                if st.session_state.new_interval != st.session_state.interval_filter:
                    st.session_state.interval_filter = st.session_state.new_interval
            
            # Updating chart type session states. Triggered when the selected chart type in the selectbox is changed.
            def update_chart_type():
                if st.session_state.update_chart_type != st.session_state.chart_type:
                    st.session_state.chart_type = st.session_state.update_chart_type
            
            # Updating moving average session states. Triggered when the Moving Average form is submitted.
            def add_ma():
                if st.session_state.add_moving_avgs != st.session_state.moving_avgs:
                    st.session_state.moving_avgs = st.session_state.add_moving_avgs
            
            # Chart type selectbox.
            st.selectbox("Chart Type", ["Candlestick", "Line"],
                        key="update_chart_type", on_change=update_chart_type)
            
            # Period selectbox.
            st.selectbox("Period", ["1d", "1mo", "1y", "3y", "5y"], format_func=format_func,
                        key="new_period", on_change=update_period)
            
            # List that stores intervals abbreviation.
            intervals = ["5m", "1h", "1d", "1wk", "1mo"]
            
            # Handling the supported intervals based on the period.
            if st.session_state.period_filter == "1d" :
                intervals = intervals[:2]
            elif st.session_state.period_filter == "1mo" :
                intervals = intervals[2:-1]
            else :
                intervals = intervals[-3:]
                
            # Interval selectbox.
            st.selectbox("Interval", intervals, format_func=format_func,
                        key="new_interval", on_change=update_interval)
            
            # Streamlit's Horizontal line as a divider.
            st.divider()
            
            # Get color list.
            color_arr = getcolor()
            
            # Popover that includes the Moving Average and Horizontal Line forms.
            with st.popover("Moving Average and Horizontal Lines", use_container_width=True) :
                
                # Make 2 columns. One for Moving Average form and another for Horizontal Line form.
                add_ma, add_line = st.columns(2, gap='small')
                
                # First column.
                with add_ma :
                    
                    # The Moving Average form.
                    with st.form(key='add-ma-form', clear_on_submit=True) :
                        # Number input for Moving Average period.
                        ma = st.number_input(label="Add MA", format="%d", step=1, value=None, min_value=3)
                        
                        # Handle invalid inputs.
                        if ma is None or ma < 3 :
                            ma = 3
                        
                        # If the form is submitted.
                        if st.form_submit_button("Add", disabled=len(st.session_state.color) >= 2, use_container_width=True) :
                            # Sampling color randomly without replacement.
                            color = np.random.choice(color_arr, replace=False)
                            
                            # Append the inputted MA period to the moving averages session states.
                            st.session_state.moving_avgs.append(ma)
                            
                            # Append the randomly selected color to the color session states.
                            st.session_state.color.append(color)
                            
                            # Set the "Clear MA" disabled to False.
                            st.session_state.ma_disable = False
                            
                            # Replotting the chart with the moving average.
                            update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals, st.session_state.stochastic)
                
                # Add Horizontal Line form.
                with add_line :
                    # Horizontal Line form.
                    with st.form(key='horizontal-form', clear_on_submit=True) :
                        # Number input for Horizontal Line y-axis value.
                        h = st.number_input(label="Add HLine", format="%d", step=10, value=None)
                        
                        # If the form is submitted.
                        if st.form_submit_button("Add", use_container_width=True) :
                            # Append the inputted horizontal line y-axis value to the horizontals session states.
                            st.session_state.horizontals.append(h)
                            
                            # Set the "Clear Lines" disabled to False.
                            st.session_state.h_disable = False
                            
                            # Replotting the chart with the horizontal line.
                            update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals, st.session_state.stochastic)
                
                # Streamlit's Horizontal line as a divider.
                st.divider()
                
                # Clear Moving Average(s). Triggered when the Clear MA button is clicked.
                def clear_ma() :
                    st.session_state.moving_avgs = []
                    st.session_state.color = []
                    st.session_state.ma_disable = True
                    update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals, st.session_state.stochastic)
                
                # Clear Horizontal Line(s). Triggered when the Clear Lines button is clicked.
                def clear_horizontals() :
                    st.session_state.horizontals = []
                    st.session_state.h_disable = True
                    update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals, st.session_state.stochastic)
                
                # Make two columns.
                button1, button2 = st.columns(2)
                
                # First column.
                with button1 :
                    # Clear MA button.
                    st.button("Clear MA", use_container_width=True,
                              disabled = st.session_state.ma_disable, on_click=clear_ma)
                
                # Clear Lines button.
                with button2 :
                    st.button("Clear Lines", use_container_width=True,
                              disabled = st.session_state.h_disable, on_click=clear_horizontals)
            
            # Streamlit's Horizontal line as a divider.
            st.divider()
            
            # Popover that includes the Stochastic form.
            with st.popover("Stochastic", use_container_width=True) :
                # Stochastic form.
                with st.form(key='stochastic_form', clear_on_submit=True, border=False) :
                    #Make 3 columns.
                    period, k_smoothing, d_smoothing = st.columns(3, gap='small')
                    
                    # First column.
                    with period :         
                        # Number input for stochastic period.
                        period = st.number_input(label="Period", format="%d", step=1, value=None, min_value=5)
                        
                        # Handle invalid inputs.
                        if period is None or period < 5 :
                            period = 5
                    
                    # Second column.
                    with k_smoothing :
                        # Number input for %K Stochastic.
                        k = st.number_input(label="%K", format="%d", step=1, value=None, min_value=3)
                        
                        # Handle invalid inputs.
                        if k is None or k < 3 :
                            k = 3
                            
                    # Third column.   
                    with d_smoothing :      
                        # Number input for %D Stochastic.
                        d = st.number_input(label="%D", format="%d", step=1, value=None, min_value=3)
                        
                        #Handle invalid inputs.
                        if d is None or d < 3 :
                            d = 3
                    
                    # If the form is submitted.
                    if st.form_submit_button("Set", use_container_width=True) :
                        # Append the inputted values as a list.
                        st.session_state.stochastic = [period, k, d]
                        
                        # Replotting the chart with the Stochastic Oscillator.
                        update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals, st.session_state.stochastic)
                
                # Delete Stochastic plot. Triggered when the Delete button is clicked.
                def clear_stochastic() :
                    st.session_state.stochastic = []
                
                # Delete Stochastic button.
                clear_stoch = st.button("Delete Stochastic", use_container_width=True,
                                        disabled = len(st.session_state.stochastic) == 0, on_click=clear_stochastic)
        
        # Predictions Section.
        st.markdown("<h3 style='text-align:center; margin: 3px 0px;'>Predictions</h3>", unsafe_allow_html=True)
        
        # Display the 10 predictions.
        predictions = st.columns(5)
        for i in range(5) :
            with predictions[i] :
                st.metric(label=dates[i],
                          value="Rp {0:.2f}".format(forecast[i]),
                          delta="{0} ({1} %)".format(stock_metric['Diff Forecast'][i], stock_metric['Percent Forecast'][i]))
                st.metric(label=dates[i+5],
                          value="Rp {0:.2f}".format(forecast[i+5]),
                          delta="{0} ({1} %)".format(stock_metric['Diff Forecast'][i+5], stock_metric['Percent Forecast'][i+5]))
    
    # News tab. Displaying the news based on the selected stock code.
    with news :
        news_arr = get_news(st.session_state.code)
        for news in news_arr :
            container = st.container(border=True)
            with container :
                st.markdown(f"<h3><a href='{news[3]}' style='text-decoration: none;'>{news[1]}</a></h3>", unsafe_allow_html=True)
                st.write(news[2])
                st.markdown(f"""<p style='color: gray;'>{news[4]}</p>""", unsafe_allow_html=True)
    
    # Download tab. Download the tabular data as CSV based on the period and interval filter.
    with download :
        st.markdown("<h3 style='text-align:center;'>Download as CSV</h3>", unsafe_allow_html=True)
        
        # Preserve a place for the table.
        table_placeholder = st.empty()
        
        def update_table() :
            with table_placeholder :
                st.dataframe(stock_data, use_container_width=True)
        
        # Automatically update the data.
        update_table()
        
        # Download button.
        st.download_button("Download as CSV", data=stock_data.to_csv(index=False),
                           file_name="{}_{}.csv".format(st.session_state.code, date), mime="text/csv")

    # If it's not weekend and the hour is within the active market time. Use UTC+7 timezone.
    while (hour >= 9 and hour <= 16) and realtime and not (day == "Saturday" or day == "Sunday") :
        _, day, hour, minute = get_today()
        with dashboard :
            update_data(st.session_state.moving_avgs, st.session_state.color, st.session_state.horizontals, st.session_state.stochastic)
        with download :
            update_table()
        time.sleep(30)

if __name__ == "__main__":

    # Get current time based on timezone
    date, day, hour, minute = get_today()
    
    market_close = (8 <= hour < 9) or (minute <= 15 and hour == 9)
    if market_close :
        timer_placeholder = st.empty()
    while market_close :
        _, _, hour, minute = get_today()
        timer(timer_placeholder)
        market_close = (8 <= hour < 9) or (minute <= 15 and hour == 9)
    main()