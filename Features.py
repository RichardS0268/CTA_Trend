from __init__ import *
# from utils import *
import utils as _U
reload(_U)
import Setting as _C
reload(_C)

def price_adj(stmp, PADJ):
    if PADJ:
        stmp['OPEN_adj'] = round(stmp['OPEN'] * stmp['ADJ'], 2)
        stmp['CLOSE_adj'] = round(stmp['CLOSE'] * stmp['ADJ'], 2)
        stmp['HIGH_adj'] = round(stmp['HIGH'] * stmp['ADJ'], 2)
        stmp['LOW_adj'] = round(stmp['LOW'] * stmp['ADJ'], 2)
    else:
        stmp['OPEN_adj'] = stmp['OPEN'] 
        stmp['CLOSE_adj'] = stmp['CLOSE'] 
        stmp['HIGH_adj'] = stmp['HIGH'] 
        stmp['LOW_adj'] = stmp['LOW'] 

    return stmp


def technical_analysis(stmp, PADJ, logger = True):
    stmp = stmp.loc[~stmp['CLOCK'].duplicated()]
    stmp = price_adj(stmp.copy(deep=True), PADJ)

    with _U.timer('TR', 20, logger):
        ## TR
        TR = []
        TR.append(stmp['HIGH_adj'][0] - stmp['LOW_adj'][0])
        for i in range(1, stmp.shape[0]): 
            TR.append( max( stmp['HIGH_adj'][i]-stmp['LOW_adj'][i], np.abs(stmp['HIGH_adj'][i]-stmp['CLOSE_adj'][i-1]), np.abs(stmp['LOW_adj'][i]-stmp['CLOSE_adj'][i-1])) )

        stmp['TR'] = TR

    ## ATR
    def STD_CAL(atr_win, std_mul, _stmp):
        _stmp['ATR'] = _stmp['TR'].rolling(atr_win, min_periods=1).mean() 

        ## Super Trend
        _stmp['h12'] = (_stmp['HIGH_adj'] + _stmp['LOW_adj'])/2
        _stmp['bub'] = _stmp['h12'] + std_mul*_stmp['ATR']
        _stmp['blb'] = _stmp['h12'] - std_mul*_stmp['ATR']

        UB = []
        LB = []
        UB.append(_stmp['bub'][0])
        LB.append(_stmp['blb'][0])

        for i in range(1, _stmp.shape[0]):
            if _stmp['CLOSE_adj'][i-1] > LB[i-1]:
                LB.append(max(_stmp['blb'][i], LB[i-1]))
            else:
                LB.append(_stmp['blb'][i])
            
            if _stmp['CLOSE'][i-1] < UB[i-1]:
                UB.append(min(_stmp['bub'][i], UB[i-1]))
            else:
                UB.append(_stmp['bub'][i])

        STD = []
        STD.append(np.sign(_stmp['CLOSE_adj'][0] - _stmp['OPEN_adj'][0]))

        for i in range(1, _stmp.shape[0]):
            if _stmp['CLOSE_adj'][i] > UB[i]:
                STD.append(1.0)
            elif _stmp['CLOSE_adj'][i] < LB[i]:
                STD.append(-1.0)
            else:
                STD.append(STD[i-1])

        _stmp['UB'] = UB
        _stmp['LB'] = LB
        _stmp['STD'] = STD
        
        return _stmp['UB'], _stmp['LB'], _stmp['STD']
    
    with _U.timer('Short Super Trend', 20, logger):
        stmp['UB_S'], stmp['LB_S'], stmp['STD_S'] = STD_CAL(_C.ATR_WIN_S, _C.STD_MULTIPLIER_S, stmp.copy(deep=True))

    with _U.timer('Long Super Trend', 20, logger):
        stmp['UB_L'], stmp['LB_L'], stmp['STD_L'] = STD_CAL(_C.ATR_WIN_L, _C.STD_MULTIPLIER_L, stmp.copy(deep=True))

    with _U.timer('Plus Super Trend', 20, logger):
        stmp['UB_P'], stmp['LB_P'], stmp['STD_P'] = STD_CAL(_C.ATR_WIN_P, _C.STD_MULTIPLIER_P, stmp.copy(deep=True))

    return stmp
