
#TODO: Global variables
VERSION = 'v3'

## Data TimeFrame
TIME_FRAME = '5min'
BACKTEST_START = '2010-01-04'
BACKTEST_END = '2022-08-19'

## Macro Trend Indicator
DAY_EMA_S = 60
DAY_EMA_L = 120

## Super Trend Indicator
ATR_WIN_S = 5
STD_MULTIPLIER_S = 2

ATR_WIN_L = 10
STD_MULTIPLIER_L = 3

ATR_WIN_P = 5
STD_MULTIPLIER_P = 2

## Indicator Filter
FILTER = ['FLUCT_filter']

## BackTest & Simulation Parameters
PADJ = False # using adj price or not
ACCOUNT = 1e6
INIT_CAP = 1e8
REWARD_RATIO = 0.15
SLIPPAGE = 0


