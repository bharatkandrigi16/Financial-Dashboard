import streamlit as st
import pandas as pd
import finnhub
import datetime, time
import praw
import plotly.graph_objects as go
from config import API_KEY, CLIENT_ID, SECRET, DB_HOST, DB_USER, DB_PASS, DB_NAME
import MySQLdb
connection = MySQLdb.Connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, database=DB_NAME)
db_cursor = connection.cursor()
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=SECRET,
    username='Southern-Rest-1359',
    password='$Nylonkitties$',
    user_agent='Finance Dashboard'
)

finnhub_client = finnhub.Client(api_key=API_KEY)
stock_candle_data, category = (None, None)
ticker = None
option = st.sidebar.selectbox("Which Dashboard?", ('Company News', 'Data', 'Predictions'), 0)
st.header(option)

if option == 'Company News':
    symbol = st.sidebar.text_input("Select Symbol", value='AAPL', max_chars=5)
    st.subheader(f"{symbol}")
    date_from = st.sidebar.text_input("Start Date (eight-digit Y-M-D)", "2023-08-15", max_chars=10)
    date_to = st.sidebar.text_input("End Date (eight-digit Y-M-D)", "2023-08-16", max_chars=10)
    news_articles = finnhub_client.company_news(symbol, _from=date_from, to=date_to)
    #st.sidebar.subheader("Filter News")
    # min_score = st.sidebar.slider("Minimum Score", min_value=0, max_value=100, value=0)
    # filtered_news = [news for news in news_articles if news['score'] >= min_score]
    # Input field for time increment
    time_increment = st.sidebar.selectbox("Time Increment:", ('Hourly', 'Daily', 'Weekly', 'Monthly'), 0)
    # Convert date inputs to timestamps
    start_timestamp = time.mktime(datetime.datetime.strptime(date_from, '%Y-%m-%d').timetuple())
    end_timestamp = time.mktime(datetime.datetime.strptime(date_to, '%Y-%m-%d').timetuple())
    # Generate list of time intervals based on the selected time increment
    time_intervals = []
    if time_increment == 'Hourly':
        interval = 3600  # One hour in seconds
    elif time_increment == 'Daily':
        interval = 86400  # One day in seconds
    elif time_increment == 'Weekly':
        interval = 604800  # One week in seconds
    elif time_increment == 'Monthly':
        interval = 2629800  # Approximately one month in seconds

    current_time = start_timestamp
    while current_time <= end_timestamp:
        time_intervals.append(current_time)
        current_time += interval

    # Fetch news data within each time interval
    news_articles = []
    for i in range(len(time_intervals) - 1):
        interval_start = time_intervals[i]
        interval_end = time_intervals[i + 1]
        interval_news = finnhub_client.company_news(symbol,_from=datetime.datetime.fromtimestamp(interval_start).strftime('%Y-%m-%d'),to=datetime.datetime.fromtimestamp(interval_end).strftime('%Y-%m-%d'))
        news_articles.extend(interval_news)

    for news in news_articles:
        st.markdown("---")
        if 'image' in news and news['image']:
            st.image(news['image'], width=150)
        st.write(f"**Source**: {news['source']}")
        st.write(f"**Related**: {news['related']}")
        st.write(f"**Date**: {datetime.datetime.fromtimestamp(news['datetime']).strftime('%Y-%m-%d')}")
        st.write(f"**Headline**: {news['headline']}")
        st.write(f"**Summary**: {news['summary']}")
        st.write(f"**URL**: {news['url']}")       

if option == 'Data':
    ticker = st.text_input("Symbol", value='AAPL',  max_chars=5)
    st.subheader(f'Data for {ticker}')
    data_categories = ["Quote","Candle Split"]
    category = st.sidebar.selectbox("Stock Data Type:",(data_categories[0], data_categories[1]))
    if category == data_categories[0]:
        quote = finnhub_client.quote(ticker)
        st.markdown("---")
        st.write(f"**Current Price**:\t{quote['c']}")
        st.write(f"**Open**:\t{quote['o']}")
        st.write(f"**Low**:\t{quote['l']}")
        st.write(f"**High**:\t{quote['h']}")
        st.write(f"**Previous Close**:\t{quote['pc']}")
        st.write(f"**Change/Percent Change**:\t{quote['d']}/{quote['dp']}") 
        st.write(f"**Current Time**:\t{datetime.datetime.fromtimestamp(quote['t'])}")
        st.markdown("---") 
    else:
        split = st.sidebar.selectbox("Pick time frame:", ('1', '5', '15', '30', '60', 'D', 'W', 'M'), 6)
        date_from = st.sidebar.text_input("Start Date (eight-digit Y-M-D)", "20230228", max_chars=8)
        start_timestamp = time.mktime(datetime.datetime(year=int(date_from[:4]), month=int(date_from[4:6]), day=int(date_from[6:])).timetuple())
        end_date_category = st.sidebar.selectbox("End date (now or custom):", ('Now','Custom'))
        end_timestamp = ""
        if end_date_category == "Custom":
            date_to = st.sidebar.text_input("End Date (eight-digit Y-M-D)", "20230728", max_chars=8)
            end_timestamp = time.mktime(datetime.datetime(year=int(date_to[:4]), month=int(date_to[4:6]), day=int(date_to[6:])).timetuple())
        else:
            end_timestamp = datetime.datetime.now().timestamp()
        stock_candle_data = finnhub_client.stock_candles(ticker, split, int(start_timestamp), int(end_timestamp))
        candle_data = []
        for i in range(len(stock_candle_data['t'])):
            ts = stock_candle_data['t'][i]
            try:
                t = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            except ValueError:
                # Print an error message and skip this iteration
                print(f"Invalid timestamp: {ts}, skipping record")
                continue  
            o = stock_candle_data['o'][i]
            h = stock_candle_data['h'][i]
            l = stock_candle_data['l'][i]
            c = stock_candle_data['c'][i]
            candle_data.append((t, o, h, l, c))
            sql_insert_query = """
                INSERT IGNORE INTO daily_bars (date, open, high, low, close, symbol, timestamp) values (%s,%s,%s,%s,%s,%s,%s)
            """
            sql_insert_query_2 = """
                INSERT IGNORE INTO stocks (symbol) VALUES (%s)
            """
            values = (t, o, h, l, c, ticker, ts)
            val = (ticker,)
            db_cursor.execute(sql_insert_query, values)
            db_cursor.execute(sql_insert_query_2, val)
        # Sort candle data based on date
        sorted_candle_data = sorted(candle_data, key=lambda x: x[0])
        
        # Separate the sorted data into individual lists for plotting
        sorted_dates, sorted_open, sorted_high, sorted_low, sorted_close = zip(*sorted_candle_data)
        
        # Plot the data
        fig = go.Figure(data=[go.Candlestick(x=sorted_dates,
                                            open=sorted_open,
                                            high=sorted_high,
                                            low=sorted_low,
                                            close=sorted_close,
                                            name=ticker)])
        data = pd.read_sql(""" 
        select date, open, high, low, close, symbol, timestamp
        from daily_bars where timestamp >= %s and timestamp <= %s and symbol=%s""", connection, params=[int(start_timestamp), int(end_timestamp), ticker])
        fig.update_xaxes(type='category')
        fig.update_layout(height=700)
        st.subheader(f'{ticker} chart')
        chart_url = f"https://charts2.finviz.com/chart.ashx?t={ticker}"
        st.image(chart_url)
        st.plotly_chart(fig, use_container_width=True)
        st.write(data)

        # Commit the changes to the database after the loop finishes
        connection.commit()
        db_cursor.close()
        connection.close()

if option == 'Predictions':
    st.subheader("Coming Soon!!")
    


