from datetime import date
from __init__ import *
import utils as _U
reload(_U)
import Setting as _C
reload(_C)
import Strategy as _S
reload(_S)
import Dataloader as _D
reload(_D)

def BUY_Trade(Symbol, tick, logger):
    
    BUY_trigger_list = list(Symbol['trigger'].loc[Symbol['trigger']== 2].index)
    BUY_observation_list = list(Symbol['trigger'].loc[Symbol['trigger']== 1].index)

    BUY_log = pd.DataFrame(columns=['open_bar', 'close_bar', 'open_price', 'close_price', 'close_reason'])
    clock_rank = Symbol['CLOCK'].to_list()
    
    cal_count = 0

    for i in range(len(BUY_trigger_list)):
        if i >= len(BUY_trigger_list):
            break
        t = BUY_trigger_list[i]

        if logger:
            cal_count += 1
            if cal_count % 10 == 1:
                process = f'{cal_count}/{len(BUY_trigger_list)}'
                print(f"{'[' + process + ']' :12} | {time.strftime('%Y-%m-%d %H:%M:%S')} Done ")
            if cal_count % 100 == 0:
                clear_output()

        open_bar = clock_rank[clock_rank.index(t)+1]
        open_price = Symbol['OPEN'].loc[open_bar] + tick

        loss_cut = Symbol.loc[open_bar]['LB_S']
        profit_cut = Symbol.loc[open_bar]['OPEN'] * (1 + _C.REWARD_RATIO) 

        if Symbol['CLOCK'].loc[t:].loc[Symbol['STD_L']==-1].shape[0]: # fork change coming, interrupt the simulation
            close_bar =  clock_rank[min(clock_rank.index(Symbol['CLOCK'].loc[t:].loc[Symbol['STD_L']==-1][0])+1, len(clock_rank)-1)]
        else:
            close_bar = clock_rank[-1]

        for i in range(1, int((pd.to_datetime(close_bar) - pd.to_datetime(t)).total_seconds()/60)):
            observation_bar = clock_rank[min(clock_rank.index(open_bar)+i, len(clock_rank)-1)]

            if observation_bar in BUY_trigger_list:
                loss_cut = Symbol.loc[observation_bar]['LB_S']
                del BUY_trigger_list[BUY_trigger_list.index(observation_bar)]

            if observation_bar in BUY_observation_list:
                loss_cut = Symbol.loc[observation_bar]['LB_S']            

            if (Symbol['LOW'].loc[observation_bar] <= loss_cut):
                close_bar = clock_rank[clock_rank.index(observation_bar)+1]
                close_reason = 'Loss_Cut'
                break

            if (Symbol['HIGH'].loc[observation_bar] >= profit_cut):
                close_bar = clock_rank[clock_rank.index(observation_bar)+1]
                close_reason = 'Profit_Cut'
                break

        close_price = Symbol['OPEN'].loc[close_bar] - tick

        BUY_log.loc[BUY_log.shape[0]] = [open_bar, close_bar, open_price, close_price, close_reason]

    BUY_log['gain'] = BUY_log['close_price'] - BUY_log['open_price']
    BUY_log['signal'] = 'BUY'

    return BUY_log


def SELL_Trade(Symbol, tick, logger):
    
    SELL_trigger_list = list(Symbol['trigger'].loc[Symbol['trigger']==-2].index)
    SELL_observation_list = list(Symbol['trigger'].loc[Symbol['trigger']==-1].index)

    SELL_log = pd.DataFrame(columns=['open_bar', 'close_bar', 'open_price', 'close_price', 'close_reason'])
    clock_rank = Symbol['CLOCK'].to_list()
    cal_count = 0

    # for t in tqdm(BUY_trigger_list[:], desc='BUY Simulation'):
    for i in range(len(SELL_trigger_list)):
        if i >= len(SELL_trigger_list):
            break
        t = SELL_trigger_list[i]
        
        if logger:
            cal_count += 1
            if cal_count % 10 == 1:
                process = f'{cal_count}/{len(SELL_trigger_list)}'
                print(f"{'[' + process + ']' :12} | {time.strftime('%Y-%m-%d %H:%M:%S')} Done ")
            if cal_count % 100 == 0:
                clear_output()

        open_bar = clock_rank[clock_rank.index(t)+1]
        open_price = Symbol['OPEN'].loc[open_bar] - tick

        loss_cut = Symbol.loc[open_bar]['UB_S']
        profit_cut = Symbol.loc[open_bar]['OPEN'] * (1 - _C.REWARD_RATIO) 

        if Symbol['CLOCK'].loc[t:].loc[Symbol['STD_L']== 1].shape[0]: # fork change coming, interrupt the simulation
            close_bar =  clock_rank[min(clock_rank.index(Symbol['CLOCK'].loc[t:].loc[Symbol['STD_L']== 1][0])+1, len(clock_rank)-1)]
        else:
            close_bar = clock_rank[-1]

        for i in range(1, int((pd.to_datetime(close_bar) - pd.to_datetime(t)).total_seconds()/60)):
            observation_bar = clock_rank[min(clock_rank.index(open_bar)+i, len(clock_rank)-1)]

            if observation_bar in SELL_trigger_list:
                loss_cut = Symbol.loc[observation_bar]['UB_S']
                del SELL_trigger_list[SELL_trigger_list.index(observation_bar)]

            if observation_bar in SELL_observation_list:
                loss_cut = Symbol.loc[observation_bar]['UB_S']            

            if Symbol['HIGH'].loc[observation_bar] >= loss_cut:
                close_bar = clock_rank[min(clock_rank.index(observation_bar)+1,len(clock_rank)-1)]
                close_reason = 'Loss_Cut'
                break

            if Symbol['LOW'].loc[observation_bar] <= profit_cut:
                close_bar = clock_rank[min(clock_rank.index(observation_bar)+1,len(clock_rank)-1)]
                close_reason = 'Profit_Cut'
                break

        close_price = Symbol['OPEN'].loc[close_bar] + tick

        SELL_log.loc[SELL_log.shape[0]] = [open_bar, close_bar, open_price, close_price, close_reason]

    SELL_log['gain'] = SELL_log['open_price'] - SELL_log['close_price']
    SELL_log['signal']= 'SELL'

    return SELL_log


def log_patch(trading_log):
    assert trading_log.shape[0], "Empty trading_log"
    ## Drop NaN error dates
    if trading_log.loc[trading_log['close_price'].apply(lambda x: np.isnan(x))].shape[0]:
        for d1 in trading_log.loc[trading_log['close_price'].apply(lambda x: np.isnan(x))].index:
            trading_log = trading_log.drop(d1)

    ## Drop Date collapse
    if trading_log.loc[trading_log['open_bar']<trading_log['close_bar'].shift(1)].shape[0]:
        for d2 in trading_log.loc[trading_log['open_bar']<trading_log['close_bar'].shift(1)].index:
            trading_log = trading_log.drop(d2)

    return trading_log


def Trading_trace(COM_ID, tick, COM_ID_VTD):
    ## trigger execution
    BUY_log = BUY_Trade(COM_ID, tick, logger=True) 
    SELL_log = SELL_Trade(COM_ID, tick, logger=True)

    buy = BUY_log.set_index('open_bar', drop=False)
    sell = SELL_log.set_index('open_bar', drop=False)

    trading_log_buy = buy.sort_index()
    trading_log_sell = sell.sort_index()

    trading_log_all = buy.append(sell)
    trading_log_all = trading_log_all.sort_index()

    ## patch some potential error
    trading_log_buy = log_patch(trading_log_buy)
    trading_log_sell = log_patch(trading_log_sell)
    trading_log_all = log_patch(trading_log_all)

    ## create trade date columns
    def Date_Belong(clock):
        if clock[11:] < '21:00:00':
            return clock[:10]
        else:
            return COM_ID_VTD[min(COM_ID_VTD.index(clock[:10])+1, len(COM_ID_VTD)-1)]

    trading_log_buy['open_date'] = trading_log_buy['open_bar'].apply(lambda x: Date_Belong(x))
    trading_log_buy['close_date'] = trading_log_buy['close_bar'].apply(lambda x: Date_Belong(x))

    trading_log_sell['open_date'] = trading_log_sell['open_bar'].apply(lambda x: Date_Belong(x))
    trading_log_sell['close_date'] = trading_log_sell['close_bar'].apply(lambda x: Date_Belong(x))

    trading_log_all['open_date'] = trading_log_all['open_bar'].apply(lambda x: Date_Belong(x))
    trading_log_all['close_date'] = trading_log_all['close_bar'].apply(lambda x: Date_Belong(x))

    return [trading_log_buy, trading_log_sell, trading_log_all]


def Dominant_change(scom, COM_ID_VTD):
    Dominant = get_dominant_contracts(f"R.CN.{_D.commodities[scom]['exchange']}.{scom}.0004", COM_ID_VTD[0], COM_ID_VTD[-1])

    Dominant['last_dc'] = Dominant['ProductCode'].shift(1)
    Dominant['Date'] = Dominant['Date'].apply(lambda x: x[:4]+'-'+x[4:6]+'-'+x[6:8])

    return Dominant.loc[(Dominant['ProductCode']!=Dominant['last_dc'])][1:]


def Simulation(scom, Balance, COM_ID, trading_log, SYM_VTD, dc_change):
    # for i in tqdm(range(trading_log.shape[0]), desc='Simulation...'):
    for i in range(trading_log.shape[0]):
        entry = trading_log.iloc[i]

        if entry['open_date'] == entry['close_date']: # open and close position in the same day
            OPEN_POS_VOL = int(_C.INIT_CAP/(entry['open_price']*_D.commodities[scom]['multiplier'])) # setting the allocatable money
            Balance['interday_profit'].loc[entry['open_date']] += entry['gain'] * OPEN_POS_VOL * _D.commodities[scom]['multiplier']

        else:# holding position for a period
            pos_dir = 1 if entry['signal'] == 'BUY' else -1
            OPEN_POS_VOL = int(_C.INIT_CAP/(entry['open_price']*_D.commodities[scom]['multiplier'])) 

            period_start = entry['open_date']
            period_end   = SYM_VTD[SYM_VTD.index(entry['close_date'])-1]

            # gain or loss caused by position open
            delta_price = COM_ID['CLOSE'].loc[period_start+' 15:00:00'] - entry['open_price']
            Balance['holding_pos'].loc[entry['open_date']] = pos_dir * OPEN_POS_VOL
            Balance['holding_profit'].loc[entry['open_date']] += pos_dir * OPEN_POS_VOL * delta_price * _D.commodities[scom]['multiplier']


            # holding period value fluctuation
            for i in range(SYM_VTD.index(entry['open_date'])+1, SYM_VTD.index(entry['close_date'])):
                delta_price = COM_ID['CLOSE'].loc[SYM_VTD[i]+' 15:00:00'] - COM_ID['CLOSE'].loc[SYM_VTD[i-1]+' 15:00:00'] 
                Balance['holding_pos'].loc[SYM_VTD[i]] = pos_dir * OPEN_POS_VOL
                Balance['holding_profit'].loc[SYM_VTD[i]] += pos_dir * OPEN_POS_VOL * delta_price * _D.commodities[scom]['multiplier']

            delta_price = entry['close_price'] - COM_ID['CLOSE'].loc[period_end+' 15:00:00']
            Balance['holding_pos'].loc[entry['close_date']] = pos_dir * OPEN_POS_VOL
            Balance['holding_profit'].loc[entry['close_date']] += pos_dir * OPEN_POS_VOL * delta_price * _D.commodities[scom]['multiplier']

    # for i in tqdm(range(dc_change.shape[0]), desc='Dominant Contracts Change'):
    for i in range(dc_change.shape[0]):
        try:
            entry = dc_change.iloc[i]
            nc = get_price(entry['ProductCode'], entry['Date'], entry['Date'])
            np = nc['OPEN'] # new contract price

            oc = get_price(entry['last_dc'], entry['Date'], entry['Date'])
            op = oc['OPEN'] # old contract price

            Balance['dc_change_gap'].loc[entry['Date']] += (op - np)*Balance['holding_pos'].loc[entry['Date']]
        except:
            continue # some data is ommited which is not contained in COM_ID either, so just ignore them

    return Balance
 

## Simulate Single Symbol
def Simulation_all_in_one(scom, logger, f_save):

    if logger:
        rank = list(_D.commodities.keys()).index(scom)+1
        print(f'======= {scom}:{rank}/{len(list(_D.commodities.keys()))} =======')

    ## Different TimeFrame of (I)nter(D)ay Data Preparation
    DATA_ID = _D.Dataset(_C.TIME_FRAME, _C.BACKTEST_START, _C.BACKTEST_END)
    DATA_D = _D.Dataset('D', _C.BACKTEST_START, _C.BACKTEST_END)

    COM_ID = DATA_ID[scom]
    COM_ID = COM_ID.set_index('CLOCK', drop=False)
    COM_ID = COM_ID.ffill()
    COM_ID_VTD = DATA_ID['VTD'] # not natural dates but valid trading dates are beeded

    COM_D = DATA_D[scom]
    COM_D = COM_D.set_index('CLOCK', drop=False)
    COM_D = COM_D.ffill()

    with _U.timer('Feature and Trigger', 25, logger):
        COM_ID, COM_D = _S.Feature_and_Trigger(COM_ID, COM_D, filter=_C.FILTER, f_save=f_save)

    TICK = _D.commodities[scom]['mintick'] * _C.SLIPPAGE

    with _U.timer('Trading trace', 25, logger):
        logs = Trading_trace(COM_ID, TICK, COM_ID_VTD)

    dc_change = Dominant_change(scom, COM_ID_VTD)
    
    Balance = pd.DataFrame()
    Balance = Balance.reindex(COM_ID_VTD )
    # import numpy as np # VM BUG
    Balance['Account']  = np.zeros(Balance.shape[0])
    Balance['interday_profit'] = np.zeros(Balance.shape[0])
    Balance['holding_profit'] = np.zeros(Balance.shape[0])
    Balance['holding_pos'] = np.zeros(Balance.shape[0])
    Balance['dc_change_gap'] = np.zeros(Balance.shape[0])

    with _U.timer('Trading Simulation', 25, logger):
        Balance['holding_pos'] = np.zeros(Balance.shape[0])
        Balance = Simulation(scom=scom, Balance=Balance, COM_ID=COM_ID, trading_log=logs[2], SYM_VTD=COM_ID_VTD, dc_change=dc_change)

    Balance['d_gain'] = Balance['interday_profit'] + Balance['holding_profit'] +  Balance['dc_change_gap']
    Balance['Pnl'] = Balance['d_gain'].cumsum()/_C.INIT_CAP + 1
    
    return Balance, logs


## wrapper for multi-process running
def wrapper_simulation(scom_, logger_, f_save=True):
    balance, sym_logs = Simulation_all_in_one(scom_, logger_, f_save)
    ## save files
    balance.to_csv(f'./output/balance_sheet/{_C.VERSION}/{scom_}_balance.csv')
    sym_logs = np.array(sym_logs)
    np.save(f'./output/trading_logs/{_C.VERSION}/{scom_}_logs.npy', sym_logs)
