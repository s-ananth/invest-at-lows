from investAtLows import *
import pandas as pd
from itertools import product
from datetime import datetime, date
import sys
sys.path.append("../..")
from utils.utils import tsx60, top100FromSP500

runBacktestPerTicker = False
runCheckCurrentLow = True
flags = [runBacktestPerTicker, runCheckCurrentLow]
assert sum(flags) == 1, 'Only one run type can be True'

# Strategy Input Variables
data_path = '../data/'
results_path = '../results/'
results_fn = '2024-02-17_15-07-36_Summary.xlsx' # Most recent full run results
allTkrs = tsx60 + top100FromSP500
tkrs_to_test = allTkrs
start_date = datetime(2019,1,1)
holding_period_days = [5, 10, 15, 20]  # Adjust the holding period as needed
minPeriod = 252 # in days, 252 business days is approx a year
startInv = 10000
SLFlagList = [True, False]
stopLossPer = 0.05

if runCheckCurrentLow: # Check if tickers are close to low
    backTestResFile = ''
    priceTol = 0.02
    breached, notBreached = tickers_close_to_low(data_path, start_date, tkrs_to_test, priceTol, minPeriod)
    bactest_results_on_current_low_tickers(breached + notBreached, results_path + results_fn)

else: # Run Strategy
    summaryDF = pd.DataFrame()
    numRuns = len(list(product(holding_period_days, tkrs_to_test, SLFlagList)))
    ctr = 1
    for h in holding_period_days:
        #print('\nRunning holding period ' + str(h))
        for tkr in tkrs_to_test:
            for slFlag in SLFlagList:
                #print('Running ticker ' + tkr)
                print('Running ' + str(ctr) + ' of ' + str(numRuns))
                fn = data_path + tkr + '.csv'
                trades, stats = backtest_strategy(fn, minPeriod, tkr, h, start_date, startInv, slFlag, stopLossPer)
                if trades is not None:
                    stats['ticker'] = tkr
                    stats['holdingPeriod'] = h
                    summaryDF = summaryDF._append(stats, ignore_index=True)
                ctr += 1

    fn = '../results/' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '_Summary.xlsx'
    summaryDF.sort_values('AnnReturn', ascending=False, inplace=True)
    summaryDF.to_excel(fn)