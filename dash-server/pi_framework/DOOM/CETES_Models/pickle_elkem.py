import numpy as np
from pyomo.environ import *

import Models
from cost_fun import *
import data_handling_elkem as dh
import auxiliary_functions as aux
import copy
import pickle

import xlwt
from xlwt import Workbook

import pandas as pd

seconds = 10

settings = {
    'solver': 'cplex',  # 'cplex', 'cbc', 'ipopt', etc.
    'optimization type': 'linear',  # 'linear', 'quadratic'

    'project_name': 'ELKEM_storage_intergration',  # fixme: not used yet
    'results_name': '130_160',  # fixme: not used yet

    'stepsize': 1/3600*seconds,  # h
}


new_profile = 2
if new_profile == 1:
    cut_days = 1

    print('reading excel...')
    file = r'.\time series\Elkem\excess_steam_mdot_new_january.xlsx'
    excess_steam_mdot_january = dh.Profile(settings, file)
    excess_steam_mdot_january_profile = excess_steam_mdot_january.resampled_data.iloc[:, 0].to_numpy()

    with open('excess_steam_mdot_january_profile_new_profile.pickle', 'wb') as handle:
        pickle.dump(excess_steam_mdot_january_profile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print('... complete')
    print('')

    print('reading excel...')
    file = r'.\time series\Elkem\excess_steam_mdot_new_november.xlsx'
    excess_steam_mdot_november = dh.Profile(settings, file)
    excess_steam_mdot_november_profile = excess_steam_mdot_november.resampled_data.iloc[:, 0].to_numpy()
    excess_steam_mdot_november_profile = excess_steam_mdot_november_profile[int(cut_days * 24 / settings['stepsize']):]

    with open('excess_steam_mdot_november_profile_new_profile.pickle', 'wb') as handle:
        pickle.dump(excess_steam_mdot_november_profile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print('... complete')
    print('')

    print('reading excel...')
    file = r'.\time series\Elkem\turbine_mdot_new_january.xlsx'
    hp_turbine_mdot_january = dh.Profile(settings, file)
    hp_turbine_mdot_january_profile = hp_turbine_mdot_january.resampled_data.iloc[:, 0].to_numpy()

    with open('hp_turbine_mdot_january_profile_new_profile.pickle', 'wb') as handle:
        pickle.dump(hp_turbine_mdot_january_profile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print('... complete')
    print('')

    print('reading excel...')
    file = r'.\time series\Elkem\turbine_mdot_new_november.xlsx'
    hp_turbine_mdot_november = dh.Profile(settings, file)
    hp_turbine_mdot_november_profile = hp_turbine_mdot_november.resampled_data.iloc[:, 0].to_numpy()
    hp_turbine_mdot_november_profile = hp_turbine_mdot_november_profile[int(cut_days * 24 / settings['stepsize']):]

    with open('hp_turbine_mdot_november_profile_new_profile.pickle', 'wb') as handle:
        pickle.dump(hp_turbine_mdot_november_profile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print('... complete')
    print('')

elif new_profile == 2:

    print('reading excel...')
    file = r'.\time series\Elkem\2020 week 48, dumpedamp calculated_new.xlsx'
    excess_steam_mdot = dh.Profile(settings, file)
    lt_stokk_mdot_profile = excess_steam_mdot.resampled_data.iloc[:, 0]
    dumpedamp_mdot_profile = excess_steam_mdot.resampled_data.iloc[:, 1]
    extraction_mdot_profile = excess_steam_mdot.resampled_data.iloc[:, 2]

    with open('lt_stokk_mdot_new_week48_{}.pickle'.format(seconds), 'wb') as handle:
        pickle.dump(lt_stokk_mdot_profile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('dumpedamp_mdot_new_week48_{}.pickle'.format(seconds), 'wb') as handle:
        pickle.dump(dumpedamp_mdot_profile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('extraction_mdot_new_week48_{}.pickle'.format(seconds), 'wb') as handle:
        pickle.dump(extraction_mdot_profile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print('... complete')
    print('')

    print('reading excel...')
    file = r'.\time series\Elkem\turbine_mdot_new_week48.xlsx'
    hp_turbine_mdot = dh.Profile(settings, file)
    hp_turbine_mdot_profile = hp_turbine_mdot.resampled_data.iloc[:, 0]

    with open('hp_turbine_mdot_new_week48_{}.pickle'.format(seconds), 'wb') as handle:
        pickle.dump(hp_turbine_mdot_profile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print('... complete')
    print('')


else:
    # file = r'.\Process data\Dairy.xlsx'
    print('reading excel...')
    file = r'.\time series\Elkem\excess_steam_mdot.xlsx'
    # file = r'.\Process data\Brewery summer.xlsx'
    excess_steam_mdot = dh.Profile(settings, file)
    excess_steam_mdot_profile = excess_steam_mdot.resampled_data.iloc[:, 0].to_numpy()
    with open('excess_steam_mdot_profile.pickle', 'wb') as handle:
        pickle.dump(excess_steam_mdot_profile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print('... complete')
    print('')

    print('reading excel...')
    file = r'.\time series\Elkem\turbine_mdot.xlsx'
    hp_turbine_mdot = dh.Profile(settings, file)
    hp_turbine_mdot_profile = hp_turbine_mdot.resampled_data.iloc[:, 0].to_numpy()
    with open('hp_turbine_mdot_profile_{}.pickle'.format(seconds), 'wb') as handle:
        pickle.dump(hp_turbine_mdot_profile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print('... complete')
    print('')


