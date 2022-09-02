from __init__ import *
import utils as _U
reload(_U)
import Setting as _C
reload(_C)
import Strategy as _S
reload(_S)
import Dataloader as _D
reload(_D)

def Dominant_change(scom, COM, VTD):
    dc_change = pd.DataFrame(columns=['CLOCK', 'old_c_price', 'new_c_price'])

    def old_new_contract_price(dif_clock):
        time_clock = dif_clock[-8:]
        date = dif_clock[:10]

        if time_clock[:2] == '09': # change in the morning market
            yesterday = VTD[VTD.index(date)-1]
            contract_log = get_dominant_contracts(f"R.CN.{_D.commodities[scom]['exchange']}.{scom}.0004", yesterday, date)
            old_contract = contract_log.iloc[0]['ProductCode']
            new_contract = contract_log.iloc[1]['ProductCode']

            old_c_open_price = float(get_price(str(old_contract), date, date)['OPEN'])
            new_c_open_price = float(get_price(str(new_contract), date, date)['OPEN'])

        elif time_clock[:2] == '21': # change in the night market
            tomorrow = VTD[VTD.index(date)+1]
            contract_log = get_dominant_contracts(f"R.CN.{_D.commodities[scom]['exchange']}.{scom}.0004", date, tomorrow)
            old_contract = contract_log.iloc[0]['ProductCode']
            new_contract = contract_log.iloc[1]['ProductCode']

            old_c_open_price = get_price(str(old_contract), date, date, 'minute1').set_index('CLOCK', drop=False).loc[date+' 21:01:00']['OPEN']
            new_c_open_price = get_price(str(new_contract), date, date, 'minute1').set_index('CLOCK', drop=False).loc[date+' 21:01:00']['OPEN']

        else:
            print(f'Unexpected Time Clock: {time_clock}')
            exit(1)

        return [dif_clock, old_c_open_price, new_c_open_price]

    COM['dc_change'] = COM['ADJ'].diff().fillna(0)
    change_log = COM['CLOCK'].loc[COM['dc_change']!=0].to_list()

    for t in change_log:
        dc_change.loc[dc_change.shape[0]] = old_new_contract_price(t)

    dc_change = dc_change.set_index('CLOCK', drop=False)
    return dc_change


def Simulation(scom, Balance, COM_ID, trading_log, SYM_VTD, dc_change, save_pos):
    # for i in tqdm(range(trading_log.shape[0]), desc='Simulation...'):
    COM_ID['position'] = np.zeros(COM_ID.shape[0])
    for i in range(trading_log.shape[0]):
        entry = trading_log.iloc[i]

        # record the position
        pos_dir = 1 if entry['signal'] == 'BUY' else -1
        OPEN_POS_VOL = int(_C.INIT_CAP/(entry['open_price']*_D.commodities[scom]['multiplier']))
        COM_ID['position'].loc[entry['open_bar']:entry['close_bar']] = pos_dir * OPEN_POS_VOL

        if entry['open_date'] == entry['close_date']: # open and close position in the same day
            # setting the allocatable money
            Balance['interday_profit'].loc[entry['open_date']] += entry['gain'] * OPEN_POS_VOL * _D.commodities[scom]['multiplier']

        else:# holding position for a period
            period_start = entry['open_date']
            period_end   = SYM_VTD[SYM_VTD.index(entry['close_date'])-1]

            # gain or loss caused by position open
            try:
                delta_price = COM_ID['CLOSE'].loc[COM_ID['Date']==period_start].iloc[-1] - entry['open_price']
            except:
                print(f"Error 1")
                continue # some trades cannot be executed

            Balance['holding_pos'].loc[entry['open_date']] = pos_dir * OPEN_POS_VOL
            Balance['holding_profit'].loc[entry['open_date']] += pos_dir * OPEN_POS_VOL * delta_price * _D.commodities[scom]['multiplier']

            # holding period value fluctuation
            for i in range(SYM_VTD.index(entry['open_date'])+1, SYM_VTD.index(entry['close_date'])):
                try:
                    delta_price = COM_ID['CLOSE'].loc[COM_ID['Date']==SYM_VTD[i]].iloc[-1] - COM_ID['CLOSE'].loc[COM_ID['Date']==SYM_VTD[i-1]].iloc[-1] 
                    Balance['holding_profit'].loc[SYM_VTD[i]] += pos_dir * OPEN_POS_VOL * delta_price * _D.commodities[scom]['multiplier']
                except:
                    print(f"Error 2")
                    continue # some trades cannot be executed  

            try:
                delta_price = entry['close_price'] - COM_ID['CLOSE'].loc[COM_ID['Date']==period_end].iloc[-1]
                Balance['interday_profit'].loc[entry['close_date']] += pos_dir * OPEN_POS_VOL * delta_price * _D.commodities[scom]['multiplier']
            except:
                print(f'Error 3')
                continue # some trades cannot be executed

    # consider dominant contract change
    for i in range(dc_change.shape[0]):
        entry = dc_change.iloc[i]
        date = entry['CLOCK'][:10]
        time_clock = entry['CLOCK'][-8:]
        holding_pos = COM_ID.loc[date+' '+time_clock]['position'] 

        Balance['dc_change_gap'].loc[entry['CLOCK'][:10]] += (entry['old_c_price']-entry['new_c_price'])*holding_pos

    if save_pos:
        COM_ID.to_csv(f'output/features/{_C.VERSION}/{scom}_features.csv')

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
    COM_ID['Date'] = COM_ID['CLOCK'].apply(lambda x: x[:10])
    COM_ID_VTD = COM_ID['Date'].drop_duplicates().to_list()

    COM_D = DATA_D[scom]
    COM_D = COM_D.set_index('CLOCK', drop=False)
    COM_D = COM_D.ffill()

    with _U.timer('Feature and Trigger', 25, logger):
        COM_ID, COM_D = _S.Feature_and_Trigger(COM_ID, COM_D, filter=_C.FILTER, f_save=f_save)

    TICK = _D.commodities[scom]['mintick'] * _C.SLIPPAGE
    logs = _S.Trading_trace(COM_ID, TICK, COM_ID_VTD, logger)

    Balance_dict = {}
    keys = ['buy_balance', 'sell_balance', 'all_balance']

    with _U.timer('Trading Simulation', 25, logger):
        dc_change = Dominant_change(scom, COM_ID, COM_ID_VTD) 

        for i in range(3):
            Balance = pd.DataFrame()
            Balance = Balance.reindex(COM_ID_VTD)
            Balance['Account']  = np.zeros(Balance.shape[0])
            Balance['interday_profit'] = np.zeros(Balance.shape[0])
            Balance['holding_profit'] = np.zeros(Balance.shape[0])
            Balance['holding_pos'] = np.zeros(Balance.shape[0])
            Balance['dc_change_gap'] = np.zeros(Balance.shape[0])

            Balance = Simulation(scom=scom, Balance=Balance, COM_ID=COM_ID, trading_log=logs[i], SYM_VTD=COM_ID_VTD, dc_change=dc_change, save_pos=True)

            Balance['d_gain'] = Balance['interday_profit'] + Balance['holding_profit'] +  Balance['dc_change_gap']
            Balance['Pnl'] = Balance['d_gain'].cumsum()/_C.INIT_CAP + 1
            
            Balance_dict[keys[i]] = Balance

    return Balance_dict, logs


## wrapper for multi-process running
def wrapper_simulation(scom_, logger_, f_save=True):
    Balance_dict, sym_logs = Simulation_all_in_one(scom_, logger_, f_save)
    ## save files
    with open(f'./output/balance_sheet/{_C.VERSION}/{scom_}_balance.npy', 'wb') as f:
        pickle.dump(Balance_dict, f)

    np.save(f'./output/trading_logs/{_C.VERSION}/{scom_}_logs.npy', np.array(sym_logs))