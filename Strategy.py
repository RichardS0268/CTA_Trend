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
def EMA_filter(_stmp_id, _stmp_d):
    # param: Day bars data
    _stmp_d['EMA_S'] = _stmp_d['CLOSE'].ewm(span=_C.DAY_EMA_S, adjust=False).mean()
    _stmp_d['EMA_L'] = _stmp_d['CLOSE'].ewm(span=_C.DAY_EMA_L, adjust=False).mean()
    Buy_signal_mask  = (_stmp_d['EMA_S']<_stmp_d['EMA_L']) & (_stmp_id['trigger'] >  0.5)
    Sell_signal_mask = (_stmp_d['EMA_S']>_stmp_d['EMA_L']) & (_stmp_id['trigger'] < -0.5)

    return Buy_signal_mask, Sell_signal_mask


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
            if f == 'EMA_filter':
                BSM_EMA, SSM_EMA = EMA_filter(COM_ID, COM_D)
                COM_ID['trigger'].loc[BSM_EMA] = 0.0
                COM_ID['trigger'].loc[SSM_EMA] = 0.0
            elif f == 'FLUCT_filter':
                SM = FLUCT_filter(COM_ID)
                COM_ID['trigger'].loc[~SM] = 0.0
            else:
                print('No Such Filter')

    if f_save:
        scom = COM_ID['SYMBOL'][0].split('.')[-2]
        COM_ID.to_csv(f'output/features/{_C.VERSION}/{scom}_features.csv')

    return COM_ID, COM_D