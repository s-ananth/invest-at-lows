import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math

def tickers_close_to_low(csv_file_path, start_date, tkrList,
                         priceTol, minPeriod):
    breachedList = []
    notYetBreachedList = []
    for tkr in tkrList:
        print('Running ticker ' + tkr)
        fn = csv_file_path + tkr + '.csv'
        df = pd.read_csv(fn)
        df['Date'] = pd.to_datetime(df['Date'])  # Make sure the 'Date' column is in datetime format
        df = df[df['Date'] >= start_date]  # Limit trading to desired period
        df.reset_index(drop=True, inplace=True)
        df['Period_Low'] = df['Close'].rolling(window=minPeriod, min_periods=minPeriod).min()
        if df.empty:
            print('Not enough data, skipping ticker ' + tkr)
        else:
            cur = df.iloc[-1]['Close']
            low = df.iloc[-1]['Period_Low']
            if abs((cur-low)) / low < priceTol:
                if cur > low:
                    notYetBreachedList.append(tkr)
                else:
                    breachedList.append(tkr)
    print('The following tickers are within the tolerance but have not breached period lows')
    print(notYetBreachedList)
    print('The following tickers have breached period lows')
    print(breachedList)
    fn = '../results/' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '_Stocks_Near_Lows.xlsx'
    res = pd.DataFrame({'Not Yet Breached': notYetBreachedList, 'Breached': breachedList}, index=[0])
    res.to_excel(fn)
    print('Lists saved to ' + fn)

def calculate_summary_stats(trades, startInv):

    summaryStats = {}
    trades['return'] = (trades['sellPrc'] - trades['buyPrc']) / trades['buyPrc']

    trades['winning_trade'] = trades['return'] > 0
    trades['losing_trade'] = trades['return'] <= 0

    summaryStats['winPct'] = (trades['return'] > 0).mean()
    summaryStats['avgWinReturn'] = trades.loc[trades['return'] > 0, 'return'].mean()
    summaryStats['avgLostReturn'] = trades.loc[trades['return'] < 0, 'return'].mean()
    summaryStats['maxLostTrdRet'] = trades.loc[trades['return'] < 0, 'return'].min()
    summaryStats['maxWinTrdRet'] = trades.loc[trades['return'] > 0, 'return'].max()

    num_winning_trades = trades['winning_trade'].sum()
    num_losing_trades = trades['losing_trade'].sum()

    summaryStats['NumWinTrades'] = num_winning_trades
    summaryStats['NumLoseTrades'] = num_losing_trades

    # For this strategy which has long periods of no trades per ticker when the price has already
    # bounced off of the low, simple cumulative return is a better proxy rather than geometric return
    trades['cum_return'] = trades['return'].cumsum()
    summaryStats['CumRet'] = trades.iloc[-1]['cum_return']

    trades['drawdown'] = trades['cum_return'] - trades['cum_return'].cummax()
    summaryStats['MaxDD'] = trades['drawdown'].min()

    st = trades.iloc[0]['buyDate']
    ed = trades.iloc[-1]['sellDate']
    numYears = (ed-st).days / 365.25

    summaryStats['TotalYears'] = numYears
    summaryStats['AnnReturn'] = trades.iloc[-1]['cum_return'] / numYears
    return summaryStats

def shares_transacted(buyPrc, sellPrc, curPortVal):
    shares = math.floor(curPortVal / buyPrc) # Not using fractional shares
    newPortVal = curPortVal + shares * (sellPrc - buyPrc)
    return shares, newPortVal

def backtest_strategy(csv_file, minPeriod, stock, holding_period,
                      start_date, startInv,
                      SLFlag=False, SLPer=0.01):

    df = pd.read_csv(csv_file)
    df['Date'] = pd.to_datetime(df['Date'])  # Make sure the 'Date' column is in datetime format
    df = df[df['Date'] >= start_date] # Limit trading to desired period
    df.reset_index(drop=True, inplace=True)
    df['52_Week_Low'] = df['Close'].rolling(window=minPeriod, min_periods=minPeriod).min()
    buy_signals = df[df['Close'] == df['52_Week_Low']]
    df['buy_signals'] = (df['Close'] == df['52_Week_Low']).astype(int)

    fn = '../results/' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '_Res_' + stock + '_' + str(holding_period) + '_Data.xlsx'
    df.to_excel(fn)

    listSignal = list(df['buy_signals'])
    listClose = list(df['Close'])
    listDate = list(df['Date'])
    assert len(listSignal) == len(listClose), 'Length mismatch of Close and Signal'
    try: # Handle cases where there is no drop to low or insufficient history
        curIdx = listSignal.index(1)
    except:
        print('No initial low found for ticker ' + stock)
        return None, None
    ttlDays = len(listClose)

    resDct = {}
    trdCtr = 0

    while curIdx + holding_period < ttlDays:

        resDct[trdCtr] = {}
        resDct[trdCtr]['buyDate'] = listDate[curIdx]
        buyPrc = listClose[curIdx]
        resDct[trdCtr]['buyPrc'] = buyPrc   # Buy at/near close, this is an approximation since you might not be able
                                            # to perfectly transact at the close price
        resDct[trdCtr]['sellDate'] = listDate[curIdx + holding_period]
        sellPrc = listClose[curIdx + holding_period]
        resDct[trdCtr]['sellPrc'] = sellPrc

        resDct[trdCtr]['retPerTrade'] = (sellPrc - buyPrc) / buyPrc

        # Update index to value after previous closing day and when the next breach of the period low occurs
        # Another break may not occur in the remaining period, hence the need for the error handling
        try:

            # Method 1 - one trade per low, no new trades during holding period
            #idxUpToHoldPerPlus1 = curIdx + holding_period + 1
            #nextBreachIndex = listSignal[idxUpToHoldPerPlus1:].index(1) + idxUpToHoldPerPlus1

            # Method 2 - multiple trades during period near lows
            idxUpToHoldPerPlus1 = curIdx + 1
            nextBreachIndex = listSignal[idxUpToHoldPerPlus1:].index(1) + curIdx + 1

            curIdx = nextBreachIndex # Update curIdx
            trdCtr += 1

        except: # No more trades to book, exit loop
            break

    # Save off all trades
    trades = pd.DataFrame(resDct).T
    if trades.empty: # case where there low is found too close to the end of the dataset, the while loop is not entered
        return None, None
    else:
        fn = '../results/' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '_Res_' + stock + '_' + str(holding_period) + '.xlsx'
        trades.to_excel(fn)
        stats = calculate_summary_stats(trades, startInv)
    return trades, stats