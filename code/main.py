from investAtLows import backtest_strategy, tickers_close_to_low
import pandas as pd
from datetime import datetime, date
import sys

# Yahoo tickers of stocks in TSX 60
tsx60 = ['ABX.TO','AEM.TO','AQN.TO','ATD.TO','BAM.TO','BCE.TO','BIP-UN.TO','BMO.TO','BN.TO','BNS.TO','CAE.TO',
         'CAR-UN.TO','CCL-B.TO','CCO.TO','CM.TO','CNQ.TO','CNR.TO','CP.TO','CSU.TO','CTC-A.TO','CVE.TO','DOL.TO',
         'EMA.TO','ENB.TO','RM.TO','FNV.TO','FSV.TO','FTS.TO','GIB-A.TO','GILTO','H.TO','IFC.TO','IMO.TO','K.TO',
         'L.TO','MFC.TO','MG.TO','MRU.TO','NA.TO','NTR.TO','OTEX.TO','POW.TO','PPL.TO','QSR.TO','RCI-B.TO','RY.TO',
         'SAP.TO','SHOP.TO','SLF.TO','SU.TO','T.TO','TD.TO','TECK-B.TO','TOU.TO','TRI.TO','TRP.TO','WCN.TO','WN.TO',
         'WPM.TO','WSP.TO']

# Top 100 stocks by weight in the S&P 500 - https://www.slickcharts.com/sp500 - Updated 12/29/2023
top100FromSP500 = ['AAPL','MSFT','AMZN','NVDA','GOOGL','META','TSLA','GOOG','BRK.B','AVGO','JPM','UNH','LLY','V','XOM',
                   'JNJ','MA','HD','PG','COST','MRK','ABBV','ADBE','CVX','CRM','AMD','BAC','PEP','KO','WMT','ACN','NFLX',
                   'INTC','MCD','TMO','CSCO','LIN','ABT','WFC','CMCSA','INTU','ORCL','DIS','QCOM','PFE','VZ','TXN','AMGN',
                   'DHR','CAT','UNP','IBM','BA','PM','NOW','SPGI','COP','GE','HON','AMAT','NKE','UBER','LOW','GS','NEE',
                   'PLD','BKNG','RTX','ISRG','T','MS','BLK','UPS','MDT','ELV','SBUX','AXP','DE','TJX','VRTX','LRCX','BMY',
                   'SCHW','CVS','AMT','SYK','GILD','ADI','LMT','C','MDLZ','ETN','ADP','MU','BX','REGN','MMC','PANW','PGR',
                   'CB']

allTkrs = tsx60 + top100FromSP500

flagCheckCurrentLow = False

csv_file_path = '../data/'
stocks_to_test = allTkrs
start_date = datetime(2018,1,1)
holding_period_days = [5, 10, 15, 20]  # Adjust the holding period as needed
minPeriod = 252 # in days, 252 business days is approx a year
startInv = 10000
stopLossFlag = True
stopLossPer = 0.01

# Input for checking tickers close to low
if flagCheckCurrentLow:
    priceTol = 0.05
    tickers_close_to_low(csv_file_path, start_date, stocks_to_test,
                         priceTol, minPeriod)

else: # Run backtest
    summaryDF = pd.DataFrame()
    for h in holding_period_days:
        print('\nRunning holding period ' + str(h))
        for stock in stocks_to_test:
            print('Running ticker ' + stock)
            fn = csv_file_path + stock + '.csv'
            trades, stats = backtest_strategy(fn, minPeriod, stock, h,
                                              start_date, startInv,
                                              stopLossFlag, stopLossPer)
            if trades is not None:
                stats['stock'] = stock
                stats['holdingPeriod'] = h
                summaryDF = summaryDF._append(stats, ignore_index=True)

    fn = '../results/' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '_Summary.xlsx'
    summaryDF.sort_values('AnnReturn', ascending=False, inplace=True)
    summaryDF.to_excel(fn)




