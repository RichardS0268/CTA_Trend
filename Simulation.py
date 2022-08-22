from __init__ import *
from utils import *
from Setting import *
from Strategy import Feature_and_Trigger

def BUY_Trade(Symbol, tick, logger):
    
    BUY_trigger_list = list(Symbol['trigger'].loc[Symbol['trigger']== 1].index)
    SELL_trigger_list = list(Symbol['trigger'].loc[Symbol['trigger']==-1].index)

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
        profit_cut = Symbol.loc[open_bar]['OPEN'] * (1 + REWARD_RATIO) 

        if Symbol['CLOCK'].loc[t:].loc[Symbol['trigger']==-1].shape[0]: # fork change coming, interrupt the simulation
            close_bar =  clock_rank[min(clock_rank.index(Symbol['CLOCK'].loc[t:].loc[Symbol['trigger']== -1][0])+1, len(clock_rank)-1)]
        else:
            close_bar = clock_rank[-1]

        for i in range(1, int((pd.to_datetime(close_bar) - pd.to_datetime(t)).total_seconds()/60)):
            observation_bar = clock_rank[min(clock_rank.index(open_bar)+i, len(clock_rank)-1)]

            if observation_bar in BUY_trigger_list:
                loss_cut = Symbol.loc[observation_bar]['LB_S']
                del BUY_trigger_list[BUY_trigger_list.index(observation_bar)]

            if observation_bar in SELL_trigger_list:
                loss_cut = Symbol.loc[observation_bar]['UB_S']            

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
    
    BUY_trigger_list = list(Symbol['trigger'].loc[Symbol['trigger']== 1].index)
    SELL_trigger_list = list(Symbol['trigger'].loc[Symbol['trigger']==-1].index)

    SELL_log = pd.DataFrame(columns=['open_bar', 'close_bar', 'open_price', 'close_price'])
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
        profit_cut = Symbol.loc[open_bar]['OPEN'] * (1 - REWARD_RATIO) 

        if Symbol['CLOCK'].loc[t:].loc[Symbol['trigger']== 1].shape[0]: # fork change coming, interrupt the simulation
            close_bar =  clock_rank[min(clock_rank.index(Symbol['CLOCK'].loc[t:].loc[Symbol['trigger']== 1][0])+1, len(clock_rank)-1)]
        else:
            close_bar = clock_rank[-1]

        for i in range(1, int((pd.to_datetime(close_bar) - pd.to_datetime(t)).total_seconds()/60)):
            observation_bar = clock_rank[min(clock_rank.index(open_bar)+i, len(clock_rank)-1)]

            if observation_bar in SELL_trigger_list:
                loss_cut = Symbol.loc[observation_bar]['UB_S']
                del SELL_trigger_list[SELL_trigger_list.index(observation_bar)]

            if observation_bar in BUY_trigger_list:
                loss_cut = Symbol.loc[observation_bar]['LB_S']            

            if (Symbol['HIGH'].loc[observation_bar] >= loss_cut) or (Symbol['LOW'].loc[observation_bar] <= profit_cut):
                close_bar = clock_rank[min(clock_rank.index(observation_bar)+1,len(clock_rank)-1)]
                break

        close_price = Symbol['OPEN'].loc[close_bar] + tick

        SELL_log.loc[SELL_log.shape[0]] = [open_bar, close_bar, open_price, close_price]

    SELL_log['gain'] = SELL_log['open_price'] - SELL_log['close_price']
    SELL_log['signal']= 'SELL'

    return SELL_log


def log_patch(trading_log):
    ## Drop NaN error dates
    for d1 in trading_log.loc[trading_log['close_price'].apply(lambda x: np.isnan(x))].index:
        trading_log.drop(d1, inplace=True)

    ## Drop Date collapse
    for d2 in trading_log.loc[trading_log['open_bar']<trading_log['close_bar'].shift(1)].index:
        trading_log.drop(d2, inplace=True)

    return trading_log


def Trading_trace(COM_5, tick, COM_5_VTD):
    ## trigger execution
    BUY_log = BUY_Trade(COM_5, tick, logger=False) 
    SELL_log = SELL_Trade(COM_5, tick, logger=False)

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
            return COM_5_VTD[min(COM_5_VTD.index(clock[:10])+1, len(COM_5_VTD)-1)]

    trading_log_buy['open_date'] = trading_log_buy['open_bar'].apply(lambda x: Date_Belong(x))
    trading_log_buy['close_date'] = trading_log_buy['close_bar'].apply(lambda x: Date_Belong(x))

    trading_log_sell['open_date'] = trading_log_sell['open_bar'].apply(lambda x: Date_Belong(x))
    trading_log_sell['close_date'] = trading_log_sell['close_bar'].apply(lambda x: Date_Belong(x))

    trading_log_all['open_date'] = trading_log_all['open_bar'].apply(lambda x: Date_Belong(x))
    trading_log_all['close_date'] = trading_log_all['close_bar'].apply(lambda x: Date_Belong(x))

    return [trading_log_buy, trading_log_sell, trading_log_all]


def Dominant_change(scom, COM_5_VTD):
    Dominant = get_dominant_contracts(f"R.CN.{commodities[scom]['exchange']}.{scom}.0004", COM_5_VTD[0], COM_5_VTD[-1])

    Dominant['last_dc'] = Dominant['ProductCode'].shift(1)
    Dominant['Date'] = Dominant['Date'].apply(lambda x: x[:4]+'-'+x[4:6]+'-'+x[6:8])

    return Dominant.loc[(Dominant['ProductCode']!=Dominant['last_dc'])][1:]


def Simulation(scom, Balance, COM_5, trading_log, SYM_VTD, dc_change):
    # for i in tqdm(range(trading_log.shape[0]), desc='Simulation...'):
    for i in range(trading_log.shape[0]):
        entry = trading_log.iloc[i]

        if entry['open_date'] == entry['close_date']: # open and close position in the same day
            OPEN_POS_VOL = int(INIT_CAP/(entry['open_price']*commodities[scom]['multiplier'])) # setting the allocatable money
            Balance['interday_profit'].loc[entry['open_date']] += entry['gain'] * OPEN_POS_VOL * commodities[scom]['multiplier']

        else:# holding position for a period
            pos_dir = 1 if entry['signal'] == 'BUY' else -1
            OPEN_POS_VOL = int(INIT_CAP/(entry['open_price']*commodities[scom]['multiplier'])) 

            period_start = entry['open_date']
            period_end   = SYM_VTD[SYM_VTD.index(entry['close_date'])-1]

            # gain or loss caused by position open
            delta_price = COM_5['CLOSE'].loc[period_start+' 15:00:00'] - entry['open_price']
            Balance['holding_pos'].loc[entry['open_date']] = pos_dir * OPEN_POS_VOL
            Balance['holding_profit'].loc[entry['open_date']] += pos_dir * OPEN_POS_VOL * delta_price * commodities[scom]['multiplier']


            # holding period value fluctuation
            for i in range(SYM_VTD.index(entry['open_date'])+1, SYM_VTD.index(entry['close_date'])):
                delta_price = COM_5['CLOSE'].loc[SYM_VTD[i]+' 15:00:00'] - COM_5['CLOSE'].loc[SYM_VTD[i-1]+' 15:00:00'] 
                Balance['holding_pos'].loc[SYM_VTD[i]] = pos_dir * OPEN_POS_VOL
                Balance['holding_profit'].loc[SYM_VTD[i]] += pos_dir * OPEN_POS_VOL * delta_price * commodities[scom]['multiplier']

            delta_price = entry['close_price'] - COM_5['CLOSE'].loc[period_end+' 15:00:00']
            Balance['holding_pos'].loc[entry['close_date']] = pos_dir * OPEN_POS_VOL
            Balance['holding_profit'].loc[entry['close_date']] += pos_dir * OPEN_POS_VOL * delta_price * commodities[scom]['multiplier']

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
            continue # some data is ommited which is not contained in COM_5 either, so just ignore them

    # dc change has no effect
    # Balance['holding_pos'].loc[(Balance['holding_pos']!=0) & (pd.Series(Balance.index).apply(lambda x: x in dc_change['Date'].to_list()))]

    return Balance
 

## Simulate Single Symbol
def Simulation_all_in_one(scom, sig_filter, backtest_tick, logger, f_save):

    Balance = pd.DataFrame()
    Balance = Balance.reindex(BACKTEST_VTD)
    # import numpy as np # VM BUG
    Balance['Account']  = np.zeros(Balance.shape[0])
    Balance['interday_profit'] = np.zeros(Balance.shape[0])
    Balance['holding_profit'] = np.zeros(Balance.shape[0])
    Balance['holding_pos'] = np.zeros(Balance.shape[0])
    Balance['dc_change_gap'] = np.zeros(Balance.shape[0])

    if logger:
        rank = list(commodities.keys()).index(scom)+1
        print(f'======= {scom}:{rank}/{len(list(commodities.keys()))} =======')
    ## 5 MINs Data Preparation
    COM_5 = F_data_5min[scom]
    COM_D = F_data_D[scom]

    COM_5 = COM_5.set_index('CLOCK', drop=False)
    COM_5 = COM_5.ffill()

    COM_D = COM_D.set_index('CLOCK', drop=False)

    COM_5['DATE'] = COM_5['CLOCK'].apply(lambda x: x[:10])

    COM_5_VTD = []

    for name, g in COM_5.groupby('DATE'):
        COM_5_VTD.append(name)
    with timer('Feature and Trigger', 25, logger):
        COM_5, COM_D = Feature_and_Trigger(COM_5, COM_D, filter=sig_filter, f_save=f_save)

    TICK = commodities[scom]['mintick'] * backtest_tick

    with timer('Trading trace', 25, logger):
        logs = Trading_trace(COM_5, TICK, COM_5_VTD)

    dc_change = Dominant_change(scom, COM_5_VTD)
    with timer('Trading Simulation', 25, logger):
        Balance['holding_pos'] = np.zeros(Balance.shape[0])
        Balance = Simulation(scom=scom, Balance=Balance, COM_5=COM_5, trading_log=logs[2], SYM_VTD=COM_5_VTD, dc_change=dc_change)

    Balance['d_gain'] = Balance['interday_profit'] + Balance['holding_profit'] +  Balance['dc_change_gap']
    Balance['Pnl'] = Balance['d_gain'].cumsum()/INIT_CAP + 1
    
    return Balance, logs


## wrapper for multi-process running
def wrapper_simulation(scom_, sig_filter_, backtest_tick_, logger_, f_save=True):
    balance, sym_logs = Simulation_all_in_one(scom_, sig_filter_, backtest_tick_, logger_, f_save)
    ## save files
    balance.to_csv(f'./output/balance_sheet/{scom_}_balance.csv')
    sym_logs = np.array(sym_logs)
    np.save(f'./output/trading_logs/{scom_}_logs.npy', sym_logs)
