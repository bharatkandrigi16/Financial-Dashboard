from dashboard import connection, db_cursor, pd, option, category, stock_candle_data

try:
    db_cursor.execute("""
            CREATE TABLE daily_bars (
            date VARCHAR(10),
            open DECIMAL(5,2),
            high DECIMAL(5,2),
            low DECIMAL(5,2),
            close DECIMAL(5,2)
        )""")
except:
    print("Table already exists.")

if option == 'Data':
   if category == 'Candle Split':
      for i in range(len(stock_candle_data['t'])):
        t = stock_candle_data['t'][i]
        o = stock_candle_data['o'][i]
        h = stock_candle_data['h'][i]
        l = stock_candle_data['l'][i]
        c = stock_candle_data['c'][i]

        sql_insert_query = """
            INSERT INTO daily_bars (date, open, high, low, close)
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (t, o, h, l, c)

        db_cursor.execute(sql_insert_query, values)
      # Commit the changes to the database after the loop finishes
      connection.commit()

        
    