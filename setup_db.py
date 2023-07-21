from dashboard import connection, pd, option, category, stock_candle_data

try:
    pd.read_csv("create table daily_bars(varchar(10) date, decimal(5,2) open, decimal(5,2) high, decimal(5,2) low, decimal(5,2) close)")
except:
    print("Table already exists.")

if option == 'Data':
    if category == 'Candle Split':
        for i in range(len(stock_candle_data['t'])):
            pd.read_sql("""insert into daily_bars values(date(t), o, h, l, c) """, connection, params={'t':stock_candle_data['t'][i], 'c':stock_candle_data['c'][i],'h':stock_candle_data['h'][i],'l':stock_candle_data['l'][i],'o':stock_candle_data['o'][i]})

        
    