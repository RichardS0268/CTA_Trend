from __init__ import *

#TODO: Data
## Basic Info of Commodities
commodities = {
            'rb':{'multiplier':10,'mintick':1,'exchange':'SHF'},
            'hc':{'multiplier':10,'mintick':1,'exchange':'SHF'},
            'i':{'multiplier':100,'mintick':0.5,'exchange':'DCE'},
            'm':{'multiplier':10,'mintick':1,'exchange':'DCE'},
            'pp':{'multiplier':5,'mintick':1,'exchange':'DCE'},
            'MA':{'multiplier':10,'mintick':1,'exchange':'CZC'},
            'bu':{'multiplier':10,'mintick':2,'exchange':'SHF'},
            'l':{'multiplier':5,'mintick':5,'exchange':'DCE'},
            'p':{'multiplier':10,'mintick':2,'exchange':'DCE'},
            'v':{'multiplier':5,'mintick':5,'exchange':'DCE'},
            'CF':{'multiplier':5,'mintick':5,'exchange':'CZC'},
            'OI':{'multiplier':10,'mintick':1,'exchange':'CZC'},
            'SR':{'multiplier':10,'mintick':1,'exchange':'CZC'},
            'TA':{'multiplier':5,'mintick':2,'exchange':'CZC'},
            'SA':{'multiplier':20,'mintick':1,'exchange':'CZC'},
} 

F_data_1min = pd.read_pickle('./dataset/F_data_1min.pkl')
F_data_5min = pd.read_pickle('./dataset/F_data_5min.pkl')
F_data_15min = pd.read_pickle('./dataset/F_data_15min.pkl')
F_data_D = pd.read_pickle('./dataset/F_data_D.pkl')

BACKTEST_VTD = np.load('./dataset/BACKTEST_VTD.npy')
BACKTEST_VTD = BACKTEST_VTD.tolist()

#TODO: Global variables
## Macro Trend Indicator
DAY_EMA_S = 60
DAY_EMA_L = 120

## Super Trend Indicator
ATR_WIN_S = 5
STD_MULTIPLIER_S = 2

ATR_WIN_L = 10
STD_MULTIPLIER_L = 3

## BackTest & Simulation Parameters
ACCOUNT = 1e6
INIT_CAP = 1e8
REWARD_RATIO = 0.15

## Plot Settings
COLORS = ['darkorange', 'cyan', 'royalblue', 'deeppink', 'indianred', 'limegreen']

