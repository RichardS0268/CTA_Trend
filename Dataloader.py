from __init__ import *
import os

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


def Download_data(timeframe, start_date, end_date):
    F_data = {}
    VTD = []

    if timeframe == '1min':
        for symbol in tqdm(commodities.keys(), desc='Downloading API 1 min data'):
            c = f"R.CN.{commodities[symbol]['exchange']}.{symbol}.0004"

            com_1min = get_price(c, start_date, end_date, 'minute1')
            com_1min[['OPEN', 'HIGH', 'CLOSE', 'LOW']] = com_1min[['OPEN', 'HIGH', 'CLOSE', 'LOW']].astype('float64')
            com_1min[['SYMBOL', 'CLOCK']] =  com_1min[['SYMBOL', 'CLOCK']].astype('string')

            com_1min['DATE'] = com_1min['CLOCK'].apply(lambda x: x[:10])
            com_vtd = com_1min['DATE'].loc[~com_1min['DATE'].duplicated()].to_list()
            VTD = com_vtd if len(com_vtd) > len(VTD) else VTD

            F_data[symbol] = com_1min

        F_data['VTD'] = VTD

        with open('dataset/F_data_1min.pkl', 'wb') as f:
            pickle.dump(F_data, f)

    elif timeframe == '5min':
        for symbol in tqdm(commodities.keys(), desc='Downloading API 5 min data'):
            c = f"R.CN.{commodities[symbol]['exchange']}.{symbol}.0004"

            com_5min = get_price(c, start_date, end_date, 'minute5')
            com_5min[['OPEN', 'HIGH', 'CLOSE', 'LOW']] = com_5min[['OPEN', 'HIGH', 'CLOSE', 'LOW']].astype('float64')
            com_5min[['SYMBOL', 'CLOCK']] =  com_5min[['SYMBOL', 'CLOCK']].astype('string')

            com_5min['DATE'] = com_5min['CLOCK'].apply(lambda x: x[:10])
            com_vtd = com_5min['DATE'].loc[~com_5min['DATE'].duplicated()].to_list()
            VTD = com_vtd if len(com_vtd) > len(VTD) else VTD

            F_data[symbol] = com_5min

        F_data['VTD'] = VTD

        with open('dataset/F_data_5min.pkl', 'wb') as f:
            pickle.dump(F_data, f)

    elif timeframe == '15min':
        for symbol in tqdm(commodities.keys(), desc='Downloading API 15 min data'):
            c = f"R.CN.{commodities[symbol]['exchange']}.{symbol}.0004"

            com_15min = get_price(c, start_date, end_date, 'minute15')
            com_15min[['OPEN', 'HIGH', 'CLOSE', 'LOW']] = com_15min[['OPEN', 'HIGH', 'CLOSE', 'LOW']].astype('float64')
            com_15min[['SYMBOL', 'CLOCK']] =  com_15min[['SYMBOL', 'CLOCK']].astype('string')

            com_15min['DATE'] = com_15min['CLOCK'].apply(lambda x: x[:10])
            com_vtd = com_15min['DATE'].loc[~com_15min['DATE'].duplicated()].to_list()
            VTD = com_vtd if len(com_vtd) > len(VTD) else VTD

            F_data[symbol] = com_15min

        F_data['VTD'] = VTD

        with open('dataset/F_data_15min.pkl', 'wb') as f:
            pickle.dump(F_data, f)

    elif timeframe == 'D':
        for symbol in tqdm(commodities.keys(), desc='Downloading API Daily data'):
            c = f"R.CN.{commodities[symbol]['exchange']}.{symbol}.0004"

            com_D = get_price(c, start_date, end_date) # API default timeframe is daily data
            com_D[['OPEN', 'HIGH', 'CLOSE', 'LOW']] = com_D[['OPEN', 'HIGH', 'CLOSE', 'LOW']].astype('float64')
            com_D[['SYMBOL', 'CLOCK']] =  com_D[['SYMBOL', 'CLOCK']].astype('string')

            com_D['DATE'] = com_D['CLOCK'].apply(lambda x: x[:10])
            com_vtd = com_D['DATE'].loc[~com_D['DATE'].duplicated()].to_list()
            VTD = com_vtd if len(com_vtd) > len(VTD) else VTD

            F_data[symbol] = com_D

        F_data['VTD'] = VTD

        with open('dataset/F_data_D.pkl', 'wb') as f:
            pickle.dump(F_data, f)
    else: 
        print("Non Valid TimeFrame in ['1min', '5min', '15min', 'D']")

    return F_data


def Dataset(timeframe, start_date='2010-01-01', end_date='2022-08-19'):
    T_delta = {'1min': 1, '5min': 5, '15min': 15, 'D': 1440}
    F_data = {}
    local_file = f'F_data_{timeframe}.pkl'
    if local_file in os.listdir('dataset'):
        F_data = pd.read_pickle('dataset/'+local_file)
        VTD = F_data['VTD']

        start_date_delta = (pd.to_datetime(start_date) - pd.to_datetime(VTD[0])).total_seconds()/(60*60*24) # s->min->h->d
        end_date_delta = (pd.to_datetime(end_date) - pd.to_datetime(VTD[-1])).total_seconds()/(60*60*24) # s->min->h->d

        if (np.abs(start_date_delta) < 5) and (np.abs(end_date_delta) < 5):
            time_delta = (pd.to_datetime(F_data['rb']['CLOCK'][1])-pd.to_datetime(F_data['rb']['CLOCK'][0])).total_seconds()/60

            if time_delta != T_delta[timeframe]:
                print(f'Error: Time Frame is not {timeframe}!')
                F_data = Download_data(timeframe, start_date, end_date)
            else:
                print(f"Using Local {timeframe:5} Data | BackTest VTD: {VTD[0]}--{VTD[-1]}")

        else:
            print(f'VTD Bias | Local Data VTD: {VTD[0]}--{VTD[-1]}')
            F_data = Download_data(timeframe, start_date, end_date)
    else:
        print(f'No Local Data of {timeframe}')
        F_data = Download_data(timeframe, start_date, end_date)

    return F_data
