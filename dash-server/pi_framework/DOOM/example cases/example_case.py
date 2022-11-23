import sys
import os
import numpy as np
import pandas as pd
import pickle
import pyomo.environ as pyo

PACKAGE_PARENT = '../..'
DOOM_DIR = 'pi_framework'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT, DOOM_DIR)))

import DOOM.classes as dc
import DOOM.auxiliary as da

def run_case():
    print('import finished')
    # Get Data

    filename = os.path.abspath('data_periods.csv')
    df = pd.read_csv(filename)
    print('data imported')

    df.rename(columns={'G_Gh': 'solar',
                       'HT': 'demand_w90',
                       'MT': 'demand_w70',
                       'CT': 'demand_cooling',
                       'Tamb': 'T_amb',
                       'Power': 'demand_el',
                       # 'steam_demand': 'demand_steam',
                       'Dampfleistung in MW': 'demand_steam',
                       'gas_price': 'price_gas',
                       'electricity_price': 'price_el',
                       'dh_price': 'price_dh',
                       }, inplace=True)

    keys = ['demand_w90', 'demand_w70', 'demand_cooling', 'demand_steam', 'demand_el']

    df['demand_w90'] = 5 * df['demand_w90'].values + np.sqrt(df['demand_w70'].values)

    for i in keys:
        df[i] = df[i].values / df[i].mean()
    df['demand_el'] = df['demand_el'] * 0.2
    df['price_el_sell'] = df['price_el'].values * -1 / 4
    df['solar'] = df['solar'] / 1e6

    filename = os.path.abspath(r'result_repr_period.pkl')
    f = open(filename, 'rb')
    u_w_dict = pickle.load(f)
    f.close()
    sum_weight = sum(u_w_dict.values())
    for i in u_w_dict.keys():
        u_w_dict[i] = [u_w_dict[i] / sum_weight, u_w_dict[i]]

    # Create system and ConcreteModel

    sysParam = {'sc': u_w_dict, 'tss': 1 / 4, 'n_ts_sc': 24 * 4 * 7, 'interest_rate': 0.05, 'depreciation_period': 10,
                'opt': {
                    'timelimit': 600,
                }, 'seq': dict()}

    for j in df.columns.to_list()[3:]:
        sysParam['seq'][j] = dict()
        for i in u_w_dict.keys():
            sysParam['seq'][j][i] = df.loc[df['period'] == i][j].values

    res = dc.System(sysParam)
    print('system defined')

    # Units

    # Gas Boiler
    tempParam = {
        'classname': 'GasBoiler',
        'name': 'gb1',
        'lim_q': (0, 1),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'lim_f': (0, 1 / 0.9),  # relative limits to q for f in MW, second entry is optional
        'cap_q': (0, 10),  # capacity limits for q in MW, first and second entry are optional
        'inv_var': 60000 * (1 + 0.0325 * sysParam['depreciation_period']),  # €/MW
        'inv_fix': 0,  # € induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': 40,  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': 90,  # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure': 100000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('gas boiler defined')

    # CHP
    tempParam = {
        'classname': 'CHP',
        'name': 'chp1',
        'lim_q': (0, 1),
        'lim_p': (0, 1),
        'lim_f': (0, 2 / 0.88),  # relative limits to q for f in MW, second entry is optional
        'cap_q': (0, 10),  # capacity limits for q in MW, first and second entry are optional
        'inv_var': 880000 * (1 + 0.0103 * sysParam['depreciation_period']),  # €/MW
        'inv_fix': 0,  # € induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'ramp_f': (),  # ramp limit for f in MW/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),
        # minimum uptime/downtime in hours, induces commitment binary variable (min values: (1,1))
        'dist': (0.5, 0.5),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': (40, 110),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': (90, 130),  # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure': (100000, 200000),  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium': ('Water', 'Water'),  # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('chp defined')

    # Heat Pump steam
    tempParam = {
        'classname': 'HeatPump',
        'name': 'hp_steam',
        'lim_q_sink': (0, 1),
        'cap_q_sink': (0, 10),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'inv_var': 2230000 * (1 + 0.028 * sysParam['depreciation_period']) / ((273.15 + 140) / 70 * 0.5),  # €/kW
        'inv_fix': 0,  # €/kW, induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q_sink': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_sink_in': (110,),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_sink_out': 130,  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_source_in': (90,),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_source_out': 80,  # minimum uptime/downtime in hours, induces commitment binary variable
        'delta_T_sink': (7, 10),  # minimum uptime/downtime in hours, induces commitment binary variable
        'delta_T_source': (7, 10),  # minimum uptime/downtime in hours, induces commitment binary variable
        'eta_comp': (0.5, 0.6),  # capacity limits for f in MW, first and second entry are optional
        'pressure_sink': 200000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure_source': 200000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium_sink': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium_source': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('hp steam defined')

    # Heat Pump water
    tempParam = {
        'classname': 'HeatPump',
        'name': 'hp_water',
        'lim_q_sink': (0, 1),
        'cap_q_sink': (0, 10),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'inv_var': 2230000 * (1 + 0.028 * sysParam['depreciation_period']) / ((273.15 + 100) / 70 * 0.5),  # €/kW
        'inv_fix': 0,  # €/kW, induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q_sink': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_sink_in': (80, 70),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_sink_out': 90,  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_source_in': (50,),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_source_out': 40,  # minimum uptime/downtime in hours, induces commitment binary variable
        'delta_T_sink': (7, 10),  # minimum uptime/downtime in hours, induces commitment binary variable
        'delta_T_source': (7, 10),  # minimum uptime/downtime in hours, induces commitment binary variable
        'eta_comp': (0.5, 0.6),  # capacity limits for f in MW, first and second entry are optional
        'pressure_sink': 200000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure_source': 200000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium_sink': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium_source': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('hp water defined')

    # Chiller
    tempParam = {
        'classname': 'HeatPump',
        'name': 'chiller',
        'lim_q_sink': (0, 1),
        'cap_q_sink': (0, 10),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'inv_var': 2230000 * (1 + 0.028 * sysParam['depreciation_period']) / ((273.15 + 60) / 85 * 0.5),  # €/kW
        'inv_fix': 0,  # €/kW, induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q_sink': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_sink_in': (40,),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_sink_out': 50,  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_source_in': (0,),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_source_out': (-15),  # minimum uptime/downtime in hours, induces commitment binary variable
        'delta_T_sink': (7, 10),  # minimum uptime/downtime in hours, induces commitment binary variable
        'delta_T_source': (7, 10),  # minimum uptime/downtime in hours, induces commitment binary variable
        'eta_comp': (0.5, 0.6),  # capacity limits for f in mw, first and second entry are optional
        'pressure_sink': 100000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure_source': 100000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium_sink': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium_source': 'Ammonia',  # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('chiller defined')

    # PV
    tempParam = {
        'classname': 'Photovoltaic',
        'name': 'pv1',
        'cap_area': (1000, 5000),
        'exists': True,
        'eta': 0.2,  # capacity limits for f in MW, first and second entry are optional
        'inv_var': 200 * (1 + sysParam['depreciation_period'] * 0.0131),  # €/m^2
        'inv_fix': 0,  # €, induces binary variable for existence of unit
    }
    res.add_unit(tempParam)
    print('pv defined')

    # Solar Thermal System

    def dist_solar_thermal(system, demand):
        heat_dist = dict()
        Q_max = np.max([demand[s] for s in system.model.set_sc])
        for s in system.model.set_sc:
            heat_dist[s] = dict()
            Q = demand[s] / Q_max
            thr1 = 0.1
            thr2 = 0.3
            Q[Q < thr1] = thr1
            Q[Q > thr2] = thr2
            heat_dist[s][50] = (thr2 - Q) / (thr2 - thr1)
            heat_dist[s][70] = (Q - thr1) / (thr2 - thr1)
        return heat_dist


    tempParam = {'classname': 'SolarThermal',
                 'name': 'st1',
                 'cap_area': (1000, 5000),
                 'exists': True,
                 'eta': 0.75,
                 'T_in': (40,),
                 'T_out': (50, 70),
                 'pressure': 100000,
                 'medium': 'Water',
                 'inv_var': 400 * (1 + sysParam['depreciation_period'] * 0.0012),
                 'inv_fix': 0,
                 'solar': res.param['seq']['solar'],
                 'm_out_dist': dist_solar_thermal(res, res.param['seq']['solar'])}

    res.add_unit(tempParam)
    print('st defined')

    # Heat Recovery Steam-HT
    tempParam = {
        'classname': 'HeatRecovery',
        'name': 'hr_steam_w90',
        'cap_q': (0, 10),
        'max_recovery': 0.3,  # capacity limits for f in MW, first and second entry are optional
        'T_in': 70,  # capacity limits for f in MW, first and second entry are optional
        'T_out': 90,  # capacity limits for f in MW, first and second entry are optional
        'pressure': 100000,  # capacity limits for f in MW, first and second entry are optional
        'medium': 'Water',  # capacity limits for f in MW, first and second entry are optional
        'inv_var': 40000,  # €/MW
        'inv_fix': 0,  # €, induces binary variable for existence of unit
        'source': res.param['seq']['demand_steam'],
    }
    res.add_unit(tempParam)
    print('hr steam w90 defined')

    # Heat Recovery w90-w70
    tempParam = {
        'classname': 'HeatRecovery',
        'name': 'hr_w90_w70',
        'cap_q': (0, 10),
        'max_recovery': 0.3,  # capacity limits for f in MW, first and second entry are optional
        'T_in': 40,  # capacity limits for f in MW, first and second entry are optional
        'T_out': 70,  # capacity limits for f in MW, first and second entry are optional
        'pressure': 100000,  # capacity limits for f in MW, first and second entry are optional
        'medium': 'Water',  # capacity limits for f in MW, first and second entry are optional
        'inv_var': 20000,  # €/MW
        'inv_fix': 0,  # €, induces binary variable for existence of unit
        'source': res.param['seq']['demand_w90'],
    }
    res.add_unit(tempParam)
    print('hr w90 w70 defined')

    # Cooler MT
    tempParam = {
        'classname': 'Cooler',
        'name': 'cooler_MT',
        'lim_q': (0, 1),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'lim_p': (0 * 0.02, 1 * 0.02),  # relative limits to q for f in MW, second entry is optional
        'cap_q': (0, 10),  # capacity limits for q in MW, first and second entry are optional
        'inv_var': 220000 * (1 + 0.04 * sysParam['depreciation_period']) * 0.02,  # €/MW
        'inv_fix': 0,  # € induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'ramp_f': (),  # ramp limit for f in MW/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': 70,  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': 50,  # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure': 100000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('cooler MT defined')

    # Cooler LT
    tempParam = {
        'classname': 'Cooler',
        'name': 'cooler_LT',
        'lim_q': (0, 1),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'lim_p': (0 * 0.025, 1 * 0.025),  # relative limits to q for f in MW, second entry is optional
        'cap_q': (0, 10),  # capacity limits for q in MW, first and second entry are optional
        'inv_var': 220000 * (1 + 0.04 * sysParam['depreciation_period']) * 0.025,  # €/MW
        'inv_fix': 0,  # € induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'ramp_f': (),  # ramp limit for f in MW/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': 50,  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': 40,  # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure': 100000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('cooler LT defined')

    # TES steam
    tempParam = {
        'classname': 'Storage',
        'name': 'tes_steam',
        'cap_soc': (0, 1000),
        'exists': True,
        'lim_c/d': (1000, 1000),
        'eta_c/d': (1, 1),
        'loss_soc': 0.01,  # relative losses proportional to soc per hour
        'inv_var': 60000 * (1 + 0.01 * sysParam['depreciation_period']),
        'inv_fix': 0,
    }
    res.add_unit(tempParam)
    print('tes steam defined')

    # TES cooling
    tempParam = {
        'classname': 'Storage',
        'name': 'tes_cooling',
        'cap_soc': (0, 1000),
        'lim_c/d': (1000, 1000),
        'eta_c/d': (1, 1),
        'loss_soc': 0.01,  # relative losses proportional to soc per hour
        'inv_var': 42000,
        'inv_fix': 0,
    }
    res.add_unit(tempParam)
    print('tes cooling defined')

    # Stratified Storage
    tempParam = {
        'classname': 'StratifiedMultiLayer',
        'name': 'ssml1',
        'cap_soc': (0, 1000 * 100),
        'lim_c/d': (1000, 1000),
        'inv_var': 1,
        'inv_fix': 0,
        'T': (40, 50, 70, 80, 90),
        'pressure': 100000,
        'medium': 'Water',
    }
    res.add_unit(tempParam)
    print('strat storage defined')

    # EES
    tempParam = {
        'classname': 'Storage',
        'name': 'ees1',
        'cap_soc': (0.2, 5),
        'exists': True,
        'lim_c/d': (10, 10),
        'eta_c/d': (1, 1),
        'loss_soc': 0.01,  # relative losses proportional to soc per hour
        'inv_var': 400000 * (1 + 0.01 * sysParam['depreciation_period']),
        'inv_fix': 0,
    }
    res.add_unit(tempParam)
    print('ees defined')

    # Steam Demand
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'demand_steam',
        'seq': sysParam['seq']['demand_steam'],
        'T_in': (150,),
        'T_out': (120,),
        'pressure': 2 * 1e5,
        'medium': 'Water',
    }
    res.add_unit(tempParam)

    # w90 Demand

    def dist_demand_w90(system, demand):
        heat_dist = dict()
        dT_hex_max = 10
        T_source_in = 90
        T_sink_in = 60
        T_sink_out = 80
        Q_max = np.max([demand[s] for s in system.model.set_sc])
        for s in system.model.set_sc:
            heat_dist[s] = dict()
            Q = demand[s]
            kA_max = Q_max / dT_hex_max
            kA = np.sqrt(Q / Q_max) * kA_max + 1e-10  # Annahme!!!
            dT_hex = Q / kA
            nan_index = np.isnan(dT_hex)
            dT_hex[nan_index] = 0
            T_source_out = T_sink_out + dT_hex - Q / Q_max * (T_source_in - (T_sink_in + dT_hex_max))
            T_source_out1 = T_source_out.copy()
            T_source_out2 = T_source_out.copy()
            T_source_out3 = T_source_out.copy()
            T_source_out1[T_source_out1 > 80] = 80
            T_source_out3[T_source_out3 < 80] = 80
            heat_dist[s][70] = (80 - T_source_out1) / (80 - 70)
            heat_dist[s][80] = (T_source_out2 - 70) / (80 - 70) - (1 + (90 - 80) / (80 - 70)) * (T_source_out3 - 80) / (
                90 - 80)
            heat_dist[s][90] = (T_source_out3 - 80) / (90 - 80)
        return heat_dist


    tempParam = {'classname': 'HeatDemand', 'name': 'demand_w90', 'seq': sysParam['seq']['demand_w90'], 'T_in': (90,),
                 'T_out': (70, 80, 90), 'pressure': 1 * 1e5, 'medium': 'Water',
                 'm_out_dist': dist_demand_w90(res, res.param['seq']['demand_w90'])}

    res.add_unit(tempParam)

    # w70 Demand

    def dist_demand_w70(system, demand):
        heat_dist = dict()
        dT_hex_max = 10
        T_source_in = 70
        T_sink_in = 30
        T_sink_out = 60
        Q_max = np.max([demand[s] for s in system.model.set_sc])
        for s in system.model.set_sc:
            heat_dist[s] = dict()
            Q = demand[s]
            kA_max = Q_max / dT_hex_max
            kA = np.sqrt(Q / Q_max) * kA_max  # Annahme!!!
            dT_hex = Q / kA
            nan_index = np.isnan(dT_hex)
            dT_hex[nan_index] = 0
            T_source_out = T_sink_out + dT_hex - Q / Q_max * (T_source_in - (T_sink_in + dT_hex_max))
            T_source_out1 = T_source_out.copy()
            T_source_out2 = T_source_out.copy()
            T_source_out3 = T_source_out.copy()
            T_source_out1[T_source_out1 > 50] = 50
            T_source_out3[T_source_out3 < 50] = 50
            heat_dist[s][40] = (50 - T_source_out1) / (50 - 40)
            heat_dist[s][50] = (T_source_out2 - 40) / (50 - 40) - (1 + (70 - 50) / (50 - 40)) * (T_source_out3 - 50) / (
                70 - 50)
            heat_dist[s][70] = (T_source_out3 - 50) / (70 - 50)
        return heat_dist


    tempParam = {'classname': 'HeatDemand', 'name': 'demand_w70', 'seq': sysParam['seq']['demand_w70'],
                 'T_in': (70, 80, 90), 'T_out': (40, 50, 70), 'pressure': 1 * 1e5, 'medium': 'Water',
                 'm_out_dist': dist_demand_w70(res, res.param['seq']['demand_w70'])}

    res.add_unit(tempParam)

    # Cooling Demand
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'demand_cooling',
        'seq': sysParam['seq']['demand_cooling'],
        'T_in': (0,),  # in and out is exchanged, due to positive definition of cooling demand
        'T_out': (-15,),
        'pressure': 1 * 1e5,
        'medium': 'Ammonia',
    }
    res.add_unit(tempParam)

    # Non-modeled Electricity Demand
    tempParam = {
        'classname': 'Demand',
        'name': 'demand_el',
        'seq': sysParam['seq']['demand_el'],
    }
    res.add_unit(tempParam)

    print('demands defined')

    # Gas Supply
    tempParam = {
        'classname': 'Supply',
        'name': 'supply_gas',
        'seq': sysParam['seq']['price_gas'],
        'cap_s': (0, 10),
        'cost_max_s': 3800,
    }
    res.add_unit(tempParam)

    # DH Supply
    tempParam = {
        'classname': 'DistrictHeating',
        'name': 'dh1',
        'T_in': 70,
        'T_out': 90,
        'medium': 'Water',
        'pressure': 1e5,
        'cap_q': (0, 10),
        'cost_max_q': 3800,
        'seq': sysParam['seq']['price_dh'],
    }
    res.add_unit(tempParam)

    # Electricity Buy Supply
    tempParam = {
        'classname': 'Supply',
        'name': 'supply_el_buy',
        'cap_s': (0, 100),
        'cost_max_s': 50000,
        'seq': sysParam['seq']['price_el'],
    }
    res.add_unit(tempParam)

    # Electricity Sell Supply
    tempParam = {
        'classname': 'Supply',
        'name': 'supply_el_sell',
        'seq': sysParam['seq']['price_el_sell'],
    }
    res.add_unit(tempParam)

    print('supplies defined')

    # NODES ----------------------------------------------------------------------
    # Steam
    tempParam = {
        'classname': 'Node',
        'name': 'node_steam',
        'lhs': [['gb1', 'q'], ['chp1', 'q_110'], ['hp_steam', 'q_sink'], ['tes_steam', 'd']],
        'rhs': [['demand_steam', 'q'], ['tes_steam', 'c']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Water 90°C
    tempParam = {
        'classname': 'Node',
        'name': 'node_w90',
        'lhs': [['demand_w90', 'm_out_90'], ['chp1', 'm_40'], ['hp_water', 'm_sink_out'], ['dh1', 'm'],
                   ['hr_steam_w90', 'm'], ['ssml1', 'm_d_90']],
        'rhs': [['demand_w90', 'm_in'], ['demand_w70', 'm_in_90'], ['ssml1', 'm_c_90'],
                    ['hp_steam', 'm_source_in']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Water 80°C
    tempParam = {
        'classname': 'Node',
        'name': 'node_w80',
        'lhs': [['demand_w90', 'm_out_80'], ['hp_steam', 'm_source_out'], ['ssml1', 'm_d_80']],
        'rhs': [['ssml1', 'm_c_80'], ['hp_water', 'm_sink_in_80'], ['demand_w70', 'm_in_80']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Water 70°C
    tempParam = {
        'classname': 'Node',
        'name': 'node_w70',
        'lhs': [['st1', 'm_out_70'], ['demand_w90', 'm_out_70'], ['ssml1', 'm_d_70'], ['hr_w90_w70', 'm'],
                   ['demand_w70', 'm_out_70']],
        'rhs': [['cooler_MT', 'm'], ['hp_water', 'm_sink_in_70'], ['ssml1', 'm_c_70'], ['demand_w70', 'm_in_70'],
                    ['dh1', 'm'], ['hr_steam_w90', 'm']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Water 50°C
    tempParam = {
        'classname': 'Node',
        'name': 'node_w50',
        'lhs': [['st1', 'm_out_50'], ['cooler_MT', 'm'], ['chiller', 'm_sink_out'], ['ssml1', 'm_d_50'],
                   ['demand_w70', 'm_out_50']],
        'rhs': [['hp_water', 'm_source_in'], ['cooler_LT', 'm'], ['ssml1', 'm_c_50']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Water 40°C
    tempParam = {
        'classname': 'Node',
        'name': 'node_w40',
        'lhs': [['hp_water', 'm_source_out'], ['cooler_LT', 'm'], ['ssml1', 'm_d_40'], ['demand_w70', 'm_out_40']],
        'rhs': [['st1', 'm_in'], ['chp1', 'm_40'], ['ssml1', 'm_c_40'], ['chiller', 'm_sink_in'],
                    ['hr_w90_w70', 'm']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Cooling
    tempParam = {
        'classname': 'Node',
        'name': 'node_cooling',
        'lhs': [['chiller', 'q_source'], ['tes_cooling', 'd']],
        'rhs': [['demand_cooling', 'q'], ['tes_cooling', 'c']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Electricity
    tempParam = {
        'classname': 'Node',
        'name': 'node_electricity',
        'lhs': [['chp1', 'p'], ['supply_el_buy', 's'], ['pv1', 'p'], ['ees1', 'd']],
        'rhs': [['demand_el', 'd'], ['hp_steam', 'p'], ['hp_water', 'p'], ['chiller', 'p'], ['supply_el_sell', 's'],
                    ['ees1', 'c']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Gas
    tempParam = {
        'classname': 'Node',
        'name': 'node_gas',
        'lhs': [['supply_gas', 's']],
        'rhs': [['gb1', 'f'], ['chp1', 'f']],
        'type': '==',
    }
    res.add_node(tempParam)

    print('nodes defined')

    res.build_model()

    # Additional Constraints
    expr = res.unit['st1'].var['scalar']['cap'] + res.unit['pv1'].var['scalar']['cap'] <= 5000
    res.model.con_pv_st1_area = pyo.Constraint(expr=expr)

    expr = res.unit['hp_steam'].var['scalar']['cap'] * 2.5 == res.unit['tes_steam'].var['scalar']['cap']
    res.model.con_hp_to_tes = pyo.Constraint(expr=expr)


    def con_rule(m, s, t):
        return res.unit['tes_steam'].var['seq']['c'][s, t] * 2.5 <= res.unit['tes_steam'].var['scalar']['cap']


    res.model.co_power_cap_ratio_tes = pyo.Constraint(res.model.set_sc, res.model.set_t, rule=con_rule)


    def con_rule(m, s, t):
        return res.unit['tes_steam'].var['seq']['d'][s, t] * 2.5 <= res.unit['tes_steam'].var['scalar']['cap']


    res.model.co_power_cap_ratio_tes2 = pyo.Constraint(res.model.set_sc, res.model.set_t, rule=con_rule)

    res = da.solve_model(res)

    filename = 'res_case_edcs'
    # da.save_object(res, filename)
    # res = da.import_object(filename)

    da.plot_unit_port(res)

    da.plot_node_slack(res)

    unit_port = {
        'gb1': 'q',
        'chp1': 'q',
        'hp_steam': 'q_sink',
        'hp_water': 'q_sink',
        'chiller': 'q_sink',
        'st1': 'q',
        'pv1': 'p',
        'cooler_MT': 'q',
        'cooler_LT': 'q',
        'dh1': 'q',
        'hr_steam_w90': 'q',
        'hr_w90_w70': 'q',
    }

    da.plot_full_load_hours(res, unit_port)

    unit = {
        'MW': ['gb1', 'chp1', 'hp_steam', 'hp_water', 'chiller', 'cooler_MT', 'cooler_LT', 'hr_steam_w90', 'hr_w90_w70'],
        'MWh': ['tes_steam', 'tes_cooling', 'ees1'],
        'm³': ['ssml1'],
        'solar': ['pv1', 'st1'],
    }

    da.plot_unit_sizes(res, unit)

    da.plot_strat_soc(res, 'ssml1')

    da.plot_time_series(res)

    unit = ['gb1', 'chp1', 'hp_steam', 'hp_water', 'chiller', 'cooler_MT', 'cooler_LT', 'hr_steam_w90', 'hr_w90_w70', 'tes_steam', 'tes_cooling', 'ees1', 'ssml1', 'pv1', 'st1']
    da.plot_unit_inv_cost(res, unit)

    unit = {
        'q': {
            'gb1': 'q',
            'chp1': 'q',
            'hp_steam': 'q_sink',
            'hp_water': 'q_sink',
            'chiller': 'q_sink',
            'cooler_MT': 'q',
            'cooler_LT': 'q',
            'hr_steam_w90': 'q',
            'hr_w90_w70': 'q',
            'st1': 'q',
        },
        'p': {
            'chp1': 'p',
            'hp_steam': 'p',
            'hp_water': 'p',
            'chiller': 'p',
            'cooler_MT': 'p',
            'cooler_LT': 'p',
            'pv1': 'p',
        },
        'f': {
            'gb1': 'q',
            'chp1': 'q',
        },
    }
#    da.plot_energy_provided(res, unit)

    da.plot_es_soc(res)

    da.plot_node(res)

    da.plot_heat_demand(res)

    TAC_total = pyo.value(res.obj['total_real'])
    TAC_gas = pyo.value(res.unit['supply_gas'].obj['total'])
    TAC_el = pyo.value(res.unit['supply_el_buy'].obj['total'])
    TAC_inv = sum(pyo.value(res.unit[n].obj['inv']) for n in res.unit if 'inv' in res.unit[n].obj)

    print('TAC_total: %20.2f' % TAC_total)
    print('TAC_gas:   %20.2f' % TAC_gas)
    print('TAC_el:    %20.2f' % TAC_el)
    print('TAC_inv:   %20.2f' % TAC_inv)


if __name__ == '__main__':
    run_case()
