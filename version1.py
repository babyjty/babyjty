# import required libraries
import pandas as pd
import yfinance as yf
import numpy as np
import math 

# input ticker and parameters
ticker = 'TQQQ'
start_date = '2009-01-01'
end_date = '2022-01-01'
df = yf.download(ticker, start_date, end_date, threads= False)
df = df.reset_index()

# parameter setup (default values in the original indicator)
length = 20
mult = 2
length_KC = 20
mult_KC = 1.5


# calculate Bollinger Bands
# moving average
m_avg = df['Close'].rolling(window=length).mean()
# standard deviation
m_std = df['Close'].rolling(window=length).std(ddof=0)
# upper Bollinger Bands
df['upper_BB'] = m_avg + mult * m_std
# lower Bollinger Bands 
df['lower_BB'] = m_avg - mult * m_std


# calculate Keltner Channel
# first we need to calculate True Range
df['tr0'] = abs(df["High"] - df["Low"])
df['tr1'] = abs(df["High"] - df["Close"].shift())
df['tr2'] = abs(df["Low"] - df["Close"].shift())
df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
# moving average of the TR
range_ma = df['tr'].rolling(window=length_KC).mean()
# upper Keltner Channel
df['upper_KC'] = m_avg + range_ma * mult_KC
# lower Keltner Channel
df['lower_KC'] = m_avg - range_ma * mult_KC


# calculate momentum value***
highest = df['High'].rolling(window = length_KC).max()
lowest = df['Low'].rolling(window = length_KC).min()
m1 = (highest + lowest) / 2
df['value'] = (df['Close'] - (m1 + m_avg)/2)
fit_y = np.array(range(0,length_KC))
df['value'] = df['value'].rolling(window = length_KC).apply(lambda x : np.polyfit(fit_y, x, 1)[0] * (length_KC-1) + np.polyfit(fit_y, x, 1)[1], raw=True)

# add the change of momentum value***
df['change'] = df['value'].diff()

# entry point for long TQQQ:
# when value increases in the negative range (eg. from -10 to -9)
df['enter1_long'] = (df['change'] > 0) & (df['value'] < 0)
# exit point for long TQQQ:
# 1. when value decreases from positive to negative
df['exit1_long'] = (df['change'] < 0) & (df['value'].shift() > 0) & (df['value'] < 0)
# 2. when value decreases in the negative range (eg. from -9 to -10)
df['exit2_long'] = (df['change'] < 0) & (df['value'].shift() < 0 ) & (df['value'] < 0)


# entry point for long SQQQ:
# 1. when value decreases from positive to negative
df['enter1_short'] = df['exit1_long']
# 2. when value decreases in the nagtive range
df['enter2_short'] = (df['change'] < 0) & (df['value'] < 0)
# exit point for long SQQQ:
df['exit1_short'] = (df['change'] > 0) & (df['value'] < 0)

# simplification
df['buy_long'] = (df['enter1_long'].shift() == False) & (df['enter1_long'] == True)
df['close_long'] = (df['exit1_long'].shift() == False) & (df['exit1_long'] == True) | (df['exit2_long'].shift() == False) & (df['exit2_long'] == True)


df['buy_short'] = (df['enter1_short'].shift() == False) & (df['enter1_short'] == True) | (df['enter2_short'].shift() == False) & (df['enter2_short'] == True)
df['close_short'] = (df['exit1_short'].shift() == False) & (df['exit1_short'] == True) 

df = df.dropna()
df.head()


capital = 1000
stop_loss = -0.05
take_profit = 0.06 # for shorting

nav = capital
trades = []

for i in range(len(df)):
    if df['buy_long'].iloc[i] == True:
        open_price = df['Open'].iloc[i + 1]
        open_date = df['Date'].iloc[i + 1]

        for j in range(i + 1, len(df)):
            
#             current_price = df['Open'].iloc[j]
#             change = current_price - open_price
#             change_per = round(change / open_price, 2)
            
#             if(change_per < stop_loss):
#                 close_price = df['Open'].iloc[j + 1]
#                 close_date = df['Date'].iloc[j + 1]
#                 change = close_price - open_price
#                 change_per = round(change / open_price, 2)     
#                 nav = round(nav * (1 + change_per), 2)
                
#                 trade = []
#                 trade.append("STOPLOSS")
#                 trade.append("Long")
#                 trade.append(nav)
#                 trade.append(change_per)
#                 trade.append(nav)
#                 trade.append(open_date)
#                 trade.append(close_date)
#                 trades.append(trade)
#                 break
                
            if df['close_long'].iloc[j] == True:

                
                close_price = df['Open'].iloc[j + 1]
                close_date = df['Date'].iloc[j + 1]
                change = close_price - open_price
                change_per = round(change / open_price, 2)     
                nav = round(nav * (1 + change_per), 2)
                
                trade = []
                trade.append("LONG")
                trade.append("NORMAL")
                trade.append(nav)
                trade.append(change_per)
                trade.append(nav)
                trade.append(open_date)
                trade.append(close_date)
                trades.append(trade)
                break
                
    if df['buy_short'].iloc[i] == True:
        open_price = df['Open'].iloc[i+1]
        open_date = df['Date'].iloc[i+1]
        
        for j in range(i + 1, len(df)):
            current_price = df['Open'].iloc[j]
            change = open_price - current_price
            change_per = round(change / open_price, 2)

            if change_per < stop_loss:

                close_price = df['Open'].iloc[j + 1]
                close_date = df['Date'].iloc[j+1]
                change = open_price - close_price
                change_per = round(change / open_price, 2)
                nav = round(nav * (1 + change_per), 2)
                
                trade = []
                trade.append("SHORT")
                trade.append("STOPLOSS")
                trade.append(nav)   
                trade.append(change_per)
                trade.append(nav)
                trade.append(open_date)
                trade.append(close_date)
                trades.append(trade)
                break
                
            if change_per > take_profit:
                close_price = df['Open'].iloc[j + 1]
                close_date = df['Date'].iloc[j+1]
                change = open_price - close_price
                change_per = round(change / open_price, 2)
                nav = round(nav * (1 + change_per), 2)
                
                trade = []
                trade.append("SHORT")
                trade.append("TAKEPROFIT")
                trade.append(nav)   
                trade.append(change_per)
                trade.append(nav)
                trade.append(open_date)
                trade.append(close_date)
                trades.append(trade)
                break                
        
            
            if df['close_short'].iloc[j] == True:

                
                close_price = df['Open'].iloc[j + 1]
                close_date = df['Date'].iloc[j+1]
                change = open_price - close_price
                change_per = round(change / open_price, 2)
                nav = round(nav * (1 + change_per), 2)
                
                trade = []
                trade.append("SHORT")
                trade.append("NORMAL")
                trade.append(nav)   
                trade.append(change_per)
                trade.append(nav)
                trade.append(open_date)
                trade.append(close_date)
                trades.append(trade)
                break

first_date = trades[0][5]
last_date = trades[len(trades)-1][6]
returns = nav - capital
returns_per = round(returns / capital * 100, 1)
years = (last_date - first_date).days/365
annualized_returns = round((pow((returns / capital),1/years)-1)*100,2)

print("========== performance ==========")
print("ticker: ", ticker)
print("start date:", first_date.strftime('%Y-%m-%d'))
print("end date:", last_date.strftime('%Y-%m-%d'))
print("start amount: $", capital)
print("final amount: $", nav)
print("returns: $", returns)
print("returns_per:", returns_per, "%")
print("annualized returns:", annualized_returns, "%")
print("=================================")
        
print(" ")

win_count = 0
lose_count = 0
long_win_count = 0
long_lose_count = 0
short_win_count = 0
short_lose_count = 0

for each in range(len(trades)):
    if(trades[each][3] > 0):
        win_count += 1
        if(trades[each][0] == 'LONG'):
            long_win_count += 1
        else:
            short_win_count += 1
    else:
        lose_count += 1
        if(trades[each][0] == 'LONG'):
            long_lose_count += 1
        else:
            short_lose_count += 1
        
win_rate = round(win_count / (win_count + lose_count) * 100, 1)
long_win_rate = round(long_win_count / (long_win_count + long_lose_count) * 100, 1)
short_win_rate = round(short_win_count / (short_win_count + short_lose_count) * 100, 1)

print("========== overall trades ==========")
print("win count:", win_count)
print("lose count:", lose_count)
print("win rate:", win_rate, "%")

print("========== long trades ==========")
print("win count:", long_win_count)
print("lose count:", long_lose_count)
print("win rate:", long_win_rate, "%")

print("========== short trades ==========")
print("win count:", short_win_count)
print("lose count:", short_lose_count)
print("win rate:", short_win_rate, "%")
print(" ")