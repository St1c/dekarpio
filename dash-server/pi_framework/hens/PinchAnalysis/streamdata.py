import os 
import sys
framework_path = '../..'

osp = os.path
sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), framework_path))) # find root dic

import pandas as pd
import numpy as np
import scipy.linalg
import pi_framework.hens.PinchAnalysis.targets as targets
import pi_framework.hens.Calculations.estimate_storage_size as estimate_storage_size
import pi_framework.hens.Models.lin_funct as lin_funct

def excel_reader(settings, filename):
    """

    :param Tstart:
    :param Tend:
    :param m:
    :param cp:
    :param kwargs:
    """
    raw_data = pd.ExcelFile(filename).parse(0)  # read data from xls file
    mod_data = raw_data.copy()

    col_names = {
        'stream nr': {
            'alternative': ['stream', 'Stream Nr'],
            'required': 1,
        },
        'requirement nr': {
            'alternative': ['requirement'],
            'required': 0,
            'default': 1,
        },
        # 'interval nr': {
        #     'alternative': ['interval'],
        #     'required': 0,
        #     'default': settings['defaults']['interval'],
        # },
        'T in': {
            'alternative': ['Start T', 'Tin'],
            'required': 1,
        },
        'T out': {
            'alternative': ['End T', 'Tout'],
            'required': 1,
        },
        'cp': {
            'alternative': ['Specific heat capacity', 'cp'],
            'required': 0,
            'default': 1,

        },
        'm': {
            'alternative': ['Mass flow', 'm', 'massflow (kW/K)'],
            'required': 1,
        },
        'duration': {
            'alternative': ['duration'],
            'required': 0,
            'default': settings['defaults']['duration'],
        },
        't start': {
            'alternative': ['t start'],
            'required': 0,
            'default': 0,
        },
        'soft': {
            'alternative': ['soft'],
            'required': 0,
            'default': 0,
        },
        'h': {
            'alternative': ['h'],
            'required': 0,
            'default': settings['defaults']['h'],
            
        },
        'Medium': {
            'alternative': ['medium', 'Medium'],
            'required': 0,
            'default': settings['defaults']['Medium'],
            
        },
        'Stream_Name': {
            'alternative': ['Stream_Name', 'stream_name'],
            'required': 0,
            'default': None,
            
        },
    }


    required_cols = [key for key in col_names.keys() if col_names[key]['required']]


    if np.isnan(mod_data[set(col_names['stream nr']['alternative']) & set(raw_data.keys())].iloc[0].values):
        mod_data.drop(0, inplace=True)

    for key in required_cols:
        if not set(col_names[key]['alternative']) & set(mod_data.keys()):
            print('Required column "{}" is missing. Cannot proceed.'.format(key))
            streamdata = None

    for key in col_names.keys():
        if not set(col_names[key]['alternative']) & set(mod_data.keys()):
            print('No corresponding column name for "{}" found in data frame!'.format(key))
            print('User-defined default values will be used instead.')

            mod_data.insert(len(mod_data.keys()), key, [col_names[key]['default'] for i in range(len(mod_data.index))]) # np.ones(len(mod_data.index)) * col_names[key]['default']
        else:
            mod_data.rename(columns={(set(col_names[key]['alternative']) & set(mod_data.keys())).pop(): key}, inplace=True)


    def add_req(mod_data, i, keys):
        req = {}
        for k in keys:
            req[k] = mod_data.loc[i][k]
            if k in ['t start', 'duration']:
                if type(req[k]) == str:
                    string = req[k]
                    string = string.replace(',', '.').split(';')
                    numeric = [float(i) for i in string]
                    req[k] = numeric
        return req

    reqs = [add_req(mod_data, i, col_names.keys()) for i in mod_data.index]


    return reqs

def dict_to_df(reqs):
    reqs_df = pd.DataFrame.from_dict(reqs)
    for n in ['duration', 't start']:
        reqs_df[n] = reqs_df[n].astype(object)
        for i, v in reqs_df[n].items():
            if not type(v) is list:
                reqs_df.at[i, n] = [v]

    reqs_df['stream nr'] = reqs_df['stream nr'].astype(int)
    reqs_df['requirement nr'] = reqs_df['requirement nr'].astype(int)

    hot_cold = []
    for i in reqs_df.index:
        if reqs_df.loc[i, 'T in'] > reqs_df.loc[i, 'T out']:
            hot_cold += ['hot']
        else:
            hot_cold += ['cold']

    reqs_df.insert(len(reqs_df.keys()), 'type', hot_cold)

    return reqs_df

def calc_intervals(reqs_df):
    t = []
    for v1, v2 in zip(reqs_df['t start'].values, reqs_df['duration'].values):
        t += v1
        t += [v1_el + v2_el for v1_el, v2_el in zip(v1, v2)]
    t = np.round(t, 2)

    t_unique = np.unique(t)

    intervals = {
        't': [t for t in t_unique],
        'durations': [np.round(t_unique[t] - t_unique[t-1],6) for t in range(1, t_unique.__len__())],
        'index': [t for t in range(len(t_unique)-1)],
        'number': len(t_unique)-1
    }

    return intervals

def calc_activity(reqs_df, intervals):
    activity_list = []
    for v1, v2 in zip(reqs_df['t start'].values, reqs_df['duration'].values):
        active_intervals = np.zeros(intervals['durations'].__len__())
        try:
            for v1_indv, v2_indv in zip(v1, v2):
                active_intervals += ((v1_indv <= np.array(intervals['t'])) & (np.round(v1_indv + v2_indv,6) > np.array(intervals['t'])))[:-1]
        except:
            v1_indv = v1
            v2_indv = v2
            active_intervals += [i for i in ((v1_indv <= np.array(intervals['t'])) & (
                        v1_indv + v2_indv > np.array(intervals['t'])))[:-1]]

        activity_list += [active_intervals]

    reqs_activity = reqs_df[['stream nr', 'requirement nr']].copy()
    reqs_activity['activity'] = activity_list

    return reqs_activity

def calc_TAM(reqs_df):
    reqs_df_tam = reqs_df.copy()
    for i in reqs_df_tam.index:
        reqs_df_tam.loc[i, 'duration'] = [1]
        reqs_df_tam.loc[i, 't start'] = [0]
        reqs_df_tam.loc[i, 'm'] = reqs_df['m'][i] * sum(reqs_df['duration'][i])

    return reqs_df_tam



def prep_input(reqs):
    reqs_df = dict_to_df(reqs)
    reqs_df_TAM = calc_TAM(reqs_df)
    intervals = calc_intervals(reqs_df)
    reqs_activity = calc_activity(reqs_df, intervals)
    reqs_activity_TAM = calc_activity(reqs_df_TAM, intervals)

    streams_hot = np.unique([reqs_df['stream nr'].loc[i] for i in reqs_df['stream nr'].index if reqs_df['T in'][i] > reqs_df['T out'][i]])
    streams_cold = np.unique([reqs_df['stream nr'].loc[i] for i in reqs_df['stream nr'].index if reqs_df['T in'][i] < reqs_df['T out'][i]])

    streams_hot_dict = {
        i: list(reqs_df.loc[reqs_df['stream nr'] == i, 'requirement nr'].values) for i in streams_hot
    }
    requirements_hot_dict = [(reqs_df.loc[i, 'stream nr'], reqs_df.loc[i, 'requirement nr']) for i in reqs_df.index if reqs_df.loc[i, 'type'] == 'hot']

    streams_cold_dict = {
        i: list(reqs_df.loc[reqs_df['stream nr'] == i, 'requirement nr'].values) for i in streams_cold
    }
    requirements_cold_dict = [(reqs_df.loc[i, 'stream nr'], reqs_df.loc[i, 'requirement nr']) for i in reqs_df.index if reqs_df.loc[i, 'type'] == 'cold']

    data_input = {
        'streamdata': reqs_df,
        'streamdata TAM': reqs_df_TAM,
        'intervals': intervals,
        'activity': reqs_activity,
        'activity TAM': reqs_activity_TAM,
        'indices': {
            'hot streams': streams_hot_dict,
            'cold streams': streams_cold_dict,
            'hot requirements': requirements_hot_dict,
            'cold requirements': requirements_cold_dict
        }}

    return data_input

    #     self.Tstart = Tstart
    #     self.Tend = Tend
    #     self.m = m
    #     self.cp = cp
    #     self.mcp = m*cp
    #     self.Qdot = abs(Tstart - Tend)*self.mcp
    #     self.duration = settings['streamdata']['default duration']
    #     self.interval = 1
    #     self.soft = 0
    #     self.duration = settings['streamdata']['default h']
    #     self.medium = settings['streamdata']['default medium']
    #
    #     for keys, values in kwargs.items():
    #         if keys == 'duration':
    #             self.duration = values
    #         elif keys == 'interval':
    #             self.interval = values
    #         elif keys == 'soft':
    #             if (type(values) == bool) or (values in [1, 0]):
    #                 self.soft = values
    #             else:
    #                 self.soft = None
    #                 print('to specify soft stream, use either 0, 1 or False, True')
    #         elif keys == 'h':
    #             self.h = values
    #         elif keys == 'medium':
    #             self.medium = values
    #         else:
    #             print('keyworded argument {} not specified!'.format(keys))
    #
    #     self.type = 'hot' if self.Tstart > self.Tend else 'cold'
    #     self.Q = self.Qdot * self.duration
    #
    # def change_attribute(self, attrname, value):
    #     if attrname in self.__dir__():
    #         setattr(self, attrname, value)
    #     else:
    #         print('no such attribute')
    #         print('available attributes:')
    #         print(self.__dir__())


#
#
# class Streamdata:
#     def __init__(self, filename):
#         """
#         :param datafile: url to file
#         :param utility: specifies utilities
#         """
#
#         ################################################################################################################
#         #    read data
#
#         self.filename = filename
#         data = pd.ExcelFile(filename).parse(0)          # read data from xls file
#
#         if 'Stream Nr' in data.keys():
#             data = data.drop(0).reset_index()
#
#             change = {
#                 'Stream Nr': 'stream',
#                 'Start T': 'Tin',
#                 'End T': 'Tout',
#                 'Mass flow': 'm',
#                 'Specific heat capacity': 'cp',
#             }
#
#             data = data.rename(columns=change)
#
#
#             data.insert(loc=0, column='interval', value=np.ones(data['stream'].__len__()).astype(int))
#             data.insert(loc=0, column='h', value=np.ones(data['stream'].__len__())*0.2)
#             data.insert(loc=0, column='soft', value=np.ones(data['stream'].__len__())*0)
#             data.insert(loc=0, column='duration', value=np.ones(data['stream'].__len__())*1)
#
#
#         self.streams_total = max(data['stream'])  # number of individual process streams
#
#         self.intervals = np.unique(data['interval'])  # number of individual process streams
#         self.durations = data[['interval', 'duration']].drop_duplicates()['duration'].values
#
#         hot_cold = np.sign(data['Tin'] - data['Tout'])    # identify hot streams (1) and cold streams (-1)
#         self.streams_hot = np.unique(data['stream'][hot_cold == 1]).astype(int)    # hot stream numbers according to data
#         self.streams_cold = np.unique(data['stream'][hot_cold == -1]).astype(int)  # cold stream numbers according to data
#
#         if self.settings['SCHED']['active']:
#             self.requirements_hot = np.unique(data['requirement'][hot_cold == 1]).astype(
#                 int)  # hot requirement numbers according to data
#             self.requirements_cold = np.unique(data['requirement'][hot_cold == -1]).astype(
#                 int)  # cold requirement numbers according to data
#
#             subset = list(set([tuple((int(i), int(r))) for i, r in zip(data['stream'][hot_cold == 1], data['requirement'][hot_cold == 1])]))
#             self.streams_hot_requirements = subset  # hot stream numbers according to data
#             self.streams_hot_requirements.sort()
#
#             subset = list(set([tuple((int(i), int(r))) for i, r in zip(data['stream'][hot_cold == -1], data['requirement'][hot_cold == -1])]))
#             self.streams_cold_requirements = subset  # cold stream numbers according to data
#             self.streams_cold_requirements.sort()
#
#             data.set_index(['interval', 'stream'], inplace=True)    # set multiindexing
#
#         self.streamdata = data