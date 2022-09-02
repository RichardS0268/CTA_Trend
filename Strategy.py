from __init__ import *
import utils as _U
reload(_U)
import Setting as _C
reload(_C)
import Features as _F
reload(_F)
import Dataloader as _D
reload(_D)

def Double_STD_trigger(stmp):
    tmp = 0.5*(2-np.abs(stmp['STD_S']+stmp['STD_S'].shift(1)))/stmp['STD_S']
    stmp['STD_S_Fork'] = tmp
    stmp['trigger'] = np.zeros(stmp.shape[0])
    
    buy_trigger_condition = (stmp['STD_S_Fork']== 1) & (stmp['STD_L']== 1)
    buy_observation_condition = (stmp['STD_S_Fork']==-1) & (stmp['STD_L']== 1)
    stmp['trigger'].loc[buy_trigger_condition] = 2
    stmp['trigger'].loc[buy_observation_condition] = 1

    sell_trigger_condition = (stmp['STD_S_Fork']==-1) & (stmp['STD_L']==-1)
    sell_observation_condition = (stmp['STD_S_Fork']== 1) & (stmp['STD_L']==-1)
    stmp['trigger'].loc[sell_trigger_condition] = -2
    stmp['trigger'].loc[sell_observation_condition] = -1
   
    return stmp


## EMA Filter
def EMA_filter(_stmp_d):
    # param: Day bars data
    _stmp_d['EMA_S'] = _stmp_d['CLOSE'].ewm(span=_C.DAY_EMA_S, adjust=False).mean()
    _stmp_d['EMA_L'] = _stmp_d['CLOSE'].ewm(span=_C.DAY_EMA_L, adjust=False).mean()
    d_down = _stmp_d.loc[_stmp_d['EMA_S']<_stmp_d['EMA_L']]['CLOCK'].to_list()
    d_up = _stmp_d.loc[_stmp_d['EMA_S']>_stmp_d['EMA_L']]['CLOCK'].to_list()

    return d_down, d_up


def FLUCT_filter(_stmp):
    scom = _stmp['SYMBOL'][0].split('.')[-2]

    COM_1 = _D.Dataset('1min', _C.BACKTEST_START, _C.BACKTEST_END)
    COM_1 = COM_1[scom]
    COM_1 = COM_1.set_index('CLOCK', drop=False)
    COM_1['FLUCT'] = COM_1['CLOSE'].ewm(span=15, min_periods=1).mean().rolling(30, min_periods=1).std()
    COM_1['FLUCT_quantile_L'] = COM_1['FLUCT'].rolling(300, min_periods=1).quantile(0.05)
    COM_1['FLUCT_quantile_H'] = COM_1['FLUCT'].rolling(300, min_periods=1).quantile(0.45)
    t_slice_con = list((COM_1['FLUCT'] > COM_1['FLUCT_quantile_L']) & (COM_1['FLUCT'] < COM_1['FLUCT_quantile_H']))
    signal_mask = [t_slice_con[i*5-1] for i in range(len(t_slice_con)//5)]
    signal_mask = pd.Series(signal_mask, index=_stmp.index)
    
    return signal_mask


## All in one Function
def Feature_and_Trigger(COM_ID, COM_D, filter, f_save):

    COM_ID = _F.technical_analysis(COM_ID, PADJ=_C.PADJ, logger=False)
    COM_ID =  Double_STD_trigger(COM_ID)

    if len(filter):
        for f in filter:
            if f == 'EMA':
                # print('EMA filter')
                D_DOWN, D_UP = EMA_filter(COM_D)
                COM_ID['Date'] = COM_ID['CLOCK'].apply(lambda x: x[:10])
                for t in COM_ID.loc[COM_ID['trigger']>0.1]['CLOCK']:
                    if COM_ID.loc[t]['Date'] in D_DOWN:
                        COM_ID['trigger'].loc[t] = 0.0
                        assert COM_ID.loc[t]['trigger'] == 0.0, 'No change?'

                for t in COM_ID.loc[COM_ID['trigger']<-0.1]['CLOCK']:
                    if COM_ID.loc[t]['Date'] in D_UP:
                        COM_ID['trigger'].loc[t] = 0.0
                        assert COM_ID.loc[t]['trigger'] == 0.0, 'No change?'
  
            elif f == 'FLUCT':
                # print('FLUCT filter')
                SM = FLUCT_filter(COM_ID)
                COM_ID['trigger'].loc[~SM] = 0.0
            else:
                print('No Such Filter')
    # else:
    #     print('No filter')

    if f_save:
        scom = COM_ID['SYMBOL'][0].split('.')[-2]
        COM_ID.to_csv(f'output/features/{_C.VERSION}/{scom}_features.csv')

    return COM_ID, COM_D


def BUY_Trade(Symbol, tick, logger):
    
    BUY_trigger_list = list(Symbol['trigger'].loc[Symbol['trigger']== 2.].index)
    BUY_observation_list = list(Symbol['trigger'].loc[Symbol['trigger']== 1.].index)

    BUY_log = pd.DataFrame(columns=['open_bar', 'close_bar', 'open_price', 'close_price', 'close_reason'])
    clock_rank = Symbol['CLOCK'].to_list()
    
    cal_count = 0

    for i in range(len(BUY_trigger_list)):
        if i >= len(BUY_trigger_list): break # some triggers are deleted during simulation, so we need this check

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

        loss_cut = Symbol.loc[open_bar]['LB_S']*1e8*-1
        profit_cut = Symbol.loc[open_bar]['OPEN'] * (1 + _C.REWARD_RATIO) 

        if Symbol['CLOCK'].loc[t:].loc[Symbol['STD_L']==-1.].shape[0]: # fork change coming, interrupt the simulation
            close_bar = clock_rank[min(clock_rank.index(Symbol['CLOCK'].loc[t:].loc[Symbol['STD_L']==-1.][0])+1, len(clock_rank)-1)]
        else:
            close_bar = clock_rank[-1]

        for i in range(1, int((pd.to_datetime(close_bar) - pd.to_datetime(t)).total_seconds()/(60*_C.TIME_FRAME_MUL))):
            observation_bar = clock_rank[min(clock_rank.index(open_bar)+i, len(clock_rank)-1)]
            if observation_bar > close_bar:
                break

            if observation_bar in BUY_trigger_list:
                loss_cut = Symbol.loc[observation_bar]['LB_S'] # Ask for more
                del BUY_trigger_list[BUY_trigger_list.index(observation_bar)]
                continue

            if observation_bar in BUY_observation_list: 
                loss_cut = Symbol.loc[observation_bar]['LB_L'] # Caution!   
                continue 

            if (Symbol['LOW'].loc[observation_bar] <= loss_cut):
                close_bar = clock_rank[min(clock_rank.index(observation_bar)+1, len(clock_rank)-1)]
                close_reason = 'Loss_Cut'
                break

            if (Symbol['HIGH'].loc[observation_bar] >= profit_cut):
                close_bar = clock_rank[min(clock_rank.index(observation_bar)+1, len(clock_rank)-1)]
                close_reason = 'Profit_Cut'
                break

        close_reason = 'non'
        close_price = Symbol['OPEN'].loc[close_bar] - tick

        BUY_log.loc[BUY_log.shape[0]] = [open_bar, close_bar, open_price, close_price, close_reason]

    BUY_log['gain'] = BUY_log['close_price'] - BUY_log['open_price']
    BUY_log['signal'] = 'BUY'

    return BUY_log


def SELL_Trade(Symbol, tick, logger):
    
    SELL_trigger_list = list(Symbol['trigger'].loc[Symbol['trigger']==-2.].index)
    SELL_observation_list = list(Symbol['trigger'].loc[Symbol['trigger']==-1.].index)

    SELL_log = pd.DataFrame(columns=['open_bar', 'close_bar', 'open_price', 'close_price', 'close_reason'])
    clock_rank = Symbol['CLOCK'].to_list()
    cal_count = 0

    # for t in tqdm(BUY_trigger_list[:], desc='BUY Simulation'):
    for i in range(len(SELL_trigger_list)):
        if i >= len(SELL_trigger_list): break # some triggers are deleted during simulation, so we need this check

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

        loss_cut = Symbol.loc[open_bar]['UB_S']*1e8
        profit_cut = Symbol.loc[open_bar]['OPEN'] * (1 - _C.REWARD_RATIO) 

        if Symbol['CLOCK'].loc[t:].loc[Symbol['STD_L']== 1].shape[0]: # fork change coming, interrupt the simulation
            close_bar =  clock_rank[min(clock_rank.index(Symbol['CLOCK'].loc[t:].loc[Symbol['STD_L']== 1][0])+1, len(clock_rank)-1)]
        else:
            close_bar = clock_rank[-1]

        for i in range(1, int((pd.to_datetime(close_bar) - pd.to_datetime(t)).total_seconds()/(60*_C.TIME_FRAME_MUL))):
            observation_bar = clock_rank[min(clock_rank.index(open_bar)+i, len(clock_rank)-1)]
            if observation_bar > close_bar:
                break

            if observation_bar in SELL_trigger_list:
                loss_cut = Symbol.loc[observation_bar]['UB_S'] # Ask for more
                del SELL_trigger_list[SELL_trigger_list.index(observation_bar)]
                continue

            if observation_bar in SELL_observation_list:
                loss_cut = Symbol.loc[observation_bar]['UB_L'] # Caution! 
                continue     

            if Symbol['HIGH'].loc[observation_bar] >= loss_cut:
                close_bar = clock_rank[min(clock_rank.index(observation_bar)+1,len(clock_rank)-1)]
                close_reason = 'Loss_Cut'
                break

            if Symbol['LOW'].loc[observation_bar] <= profit_cut:
                close_bar = clock_rank[min(clock_rank.index(observation_bar)+1,len(clock_rank)-1)]
                close_reason = 'Profit_Cut'
                break

        close_reason = 'non'
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


def Trading_trace(COM_ID, tick, COM_ID_VTD, logger):
    ## trigger execution
    with _U.timer('BUY Trading trace', 25, logger):
        BUY_log = BUY_Trade(COM_ID, tick, logger=False) 

    with _U.timer('SELL Trading trace', 25, logger):
        SELL_log = SELL_Trade(COM_ID, tick, logger=False)

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
