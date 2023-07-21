import streamlit as st
import pandas as pd
import finnhub
import datetime, time
#import tweepy - requires higher access level for displaying user tweets
import praw
import plotly.graph_objects as go
from config import API_KEY, CLIENT_ID, SECRET, DB_HOST, DB_USER, DB_PASS, DB_NAME
import MySQLdb
connection = MySQLdb.Connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, database=DB_NAME)
db_cursor = connection.cursor()
# tweepy_auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET_KEY)
# tweepy_auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
# api = tweepy.API(tweepy_auth)
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=SECRET,
    username='Southern-Rest-1359',
    password='$Nylonkitties$',
    user_agent='Finance Dashboard'
)

finnhub_client = finnhub.Client(api_key=API_KEY)
symbol, start_timestamp, end_timestamp, stock_candle_data = (None, None, None, None)
option = st.sidebar.selectbox("Which Dashboard?", ('Company News', 'Data', 'Chart', 'Patterns'))
st.header(option)

if option == 'Company News':
    symbol = st.sidebar.text_input("Select Symbol", value='AAPL', max_chars=5)
    st.subheader(f"{symbol}")
    st.write(finnhub_client.company_news(symbol, _from="2023-06-01", to="2023-06-10"))

if option == 'Chart':
    symbol = st.text_input("Select Symbol", value='AAPL', max_chars=5)
    data = pd.read_sql(""" 
        select date(day) as day, open, high, low, close
        from daily_bars
        where stock_id = (select id from stock where UPPER(symbol) = %s) 
        order by day asc""", connection, params=(symbol.upper(),))
    fig = go.Figure(data=[go.Candlestick(x=data['day'],
                    open=data['open'],
                    high=data['high'],
                    low=data['low'],
                    close=data['close'],
                    name=symbol)])
    fig.update_xaxes(type='category')
    fig.update_layout(height=700)
    st.subheader(f'{symbol} chart data')
    chart_url = f"https://charts2.finviz.com/chart.ashx?t={symbol}"
    st.image(chart_url)
    st.plotly_chart(fig, use_container_width=True)
    st.write(data)

if option == 'Data':
    ticker = st.text_input("Symbol", value='AAPL', max_chars=5)
    st.subheader(f'Data for {ticker}')
    data_categories = ["Quote","Candle Split"]
    category = st.sidebar.selectbox("Stock Data Type:",(data_categories[0], data_categories[1]))
    if category == data_categories[0]:
        st.write(finnhub_client.quote(ticker))
    else:
        split = st.sidebar.selectbox("Pick time frame:",("1", "5", "15", "30", "60", "D", "W", "M"))
        date_from = st.sidebar.text_input("Start Date (eight-digit Y-M-D)", "20210228", max_chars=8)
        start_timestamp = time.mktime(datetime.datetime(year=int(date_from[:4]), month=int(date_from[4:6]), day=int(date_from[6:])).timetuple())
        end_date_category = st.sidebar.selectbox("End date (now or custom):",("Now","Custom"))
        end_timestamp = ""
        if end_date_category == "Custom":
            date_to = st.sidebar.text_input("End Date (eight-digit Y-M-D)", "20210228", max_chars=8)
            end_timestamp = time.mktime(datetime.datetime(year=int(date_to[:4]), month=int(date_to[4:6]), day=int(date_to[6:])).timetuple())
        else:
            end_timestamp = datetime.datetime.now().timestamp()
        stock_candle_data = finnhub_client.stock_candles(ticker, split, int(start_timestamp), int(end_timestamp))
        st.write(stock_candle_data)

if option == 'Patterns':
    pass
    


