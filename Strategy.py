from __init__ import *
import utils as _U
import Setting as _C
import Features as _F

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
def EMA_filter(_stmp):
    # param: Day bars data
    _stmp['EMA_S'] = _stmp['CLOSE'].ewm(span=_C.DAY_EMA_S, adjust=False).mean()
    _stmp['EMA_L'] = _stmp['CLOSE'].ewm(span=_C.DAY_EMA_L, adjust=False).mean()
    Buy_signal_mask = _stmp.loc[_stmp['EMA_S']<_stmp['EMA_L']]['CLOCK'].to_list()
    Sell_signal_mask = _stmp.loc[_stmp['EMA_S']>_stmp['EMA_L']]['CLOCK'].to_list()

    return Buy_signal_mask, Sell_signal_mask


## All in one Function
def Feature_and_Trigger(COM_5, COM_D, filter, f_save):

    COM_5 = _F.technical_analysis(COM_5, logger=False, PADJ=False, save=f_save)
    COM_5 =  Double_STD_trigger(COM_5)

    if filter:
        BSM_EMA, SSM_EMA = EMA_filter(COM_D)
        COM_5['trigger'].loc[(COM_5['DATE'].apply(lambda x: x in BSM_EMA)) & (COM_5['trigger']==1)] = 0.0
        COM_5['trigger'].loc[(COM_5['DATE'].apply(lambda x: x in SSM_EMA)) & (COM_5['trigger']==-1)] = 0.0

    return COM_5, COM_D