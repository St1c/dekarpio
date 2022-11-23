import numpy as np
import pandas as pd
import sys
import os
import pickle
import pyomo.environ as pyo
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
from pathlib import Path

PACKAGE_PARENT = '../../..'
PACKAGE_PARENT = ''
DOOM_DIR = 'pi_framework'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT, DOOM_DIR)))
import DOOM.classes as dc
import DOOM.auxiliary as da


# # Existing Units
# # ================================================================================================================

inv_var_gb = 0*89000   # €/MW
inv_fix_gb = 0*5000    # €

# Gas boiler 1
cap_gb1 = 10           # [MW], capacity
eff_gb1 = 0.95        # [-], efficiency

# Gas boiler 2
cap_gb2 = 5           # [MW], capacity
eff_gb2 = 0.9501      # [-], efficiency

# Gas boiler 3
cap_gb3 = 5           # [MW], capacity
eff_gb3 = 0.95        # [-], efficiency

# # Potential New Units
# # ================================================================================================================

# Biomass boiler
inv_var_bmb = 1e6      # €/MWth
inv_fix_bmb = 0        # €
max_cap_bmb1 = 20           # [MW], capacity
eff_bmb1 = 0.9             # [-], efficiency

# Electrode boiler
inv_var_eb = 106250       # €/MW, currently higher by factor 1e2 for testing reasons
inv_fix_eb = 0           # €
max_cap_eb1 = 20           # [MW], capacity
eff_eb1 = 0.98             # [-], efficiency

# High temperature heat pump
inv_fix_hthp = 30e3        # €
inv_var_hthp = 1e6         # €/MW 1e6 actual value, currently adapted for testing reasons
max_cap_hthp = 100         # [MW], capacity
T_sink_in_hthp = 80        # [°C], incoming temperature of heat sink stream
T_sink_out_hthp = 117      # [°C], target temperature of steam
T_source_in_hthp = 50      # [°C], incoming temperature of heat source stream
T_source_out_hthp = 30     # [°C], outgoing temperature of heat source stream

# Low temperature heat pump
inv_fix_lthp = 30e3         # €
inv_var_lthp = 550000       # €/MW
max_cap_lthp = 10           # [MW], capacity
T_sink_in_lthp = 70         # [°C], incoming temperature of heat sink stream
T_sink_out_lthp = 90        # [°C], target temperature of sink stream
T_source_in_lthp = 30       # [°C], incoming temperature of heat source stream
T_source_out_lthp = 15      # [°C], outgoing temperature of heat source stream

# Mechanical vapor compression units
inv_fix_mvr = 5e3              # €
T_in_mvr1 =  T_sink_out_hthp   # [°C], feed temperature
P_in_mvr1 = 2e5                # [Pa], feed pressure
T_out_mvr1 = 144               # [°C], target temperature (steam 3)
P_out_mvr1 = 3.5e5             # [Pa], target pressure (steam 3)
FW_T_in_mvr1 = 32              # [°C], temperature of added freshwater
FW_P_in_mvr1 = 1e5             # [Pa], pressure of added freshwater
efficiency_mvr1 = 0.9          # [-]
max_cap_mvr1 = 100             # [MW]

# Mechanical vapor compression units
T_in_mvr2 =  T_out_mvr1        # [°C], feed temperature
P_in_mvr2 = P_out_mvr1         # [Pa], feed pressure
T_out_mvr2 = 160               # [°C], target temperature (steam 2)
P_out_mvr2 = 5.5e5             # [Pa], target pressure (steam 2)
FW_T_in_mvr2 = 32              # [°C], temperature of added freshwater
FW_P_in_mvr2 = 1e5             # [Pa], pressure of added freshwater
efficiency_mvr2 = 0.9          # [-]
max_cap_mvr2 = 100             # [MW]

# Gas Turbine
inv_var_gt = 88889*10             # €/MW, todo check this, I think factor 10 higher (SK)
inv_fix_gt = 0                 # €
max_cap_gt1 = 20               # MWel
eff_gt1 = 0.35                 # [-]

# Heat Recovery Boiler
inv_var_hrb = 80000            # €/MW
inv_fix_hrb = 0                # €
max_cap_hrb1 = 20              # MWth
eff_hrb1 = 0.9                # [-]

# Steam Turbine
inv_var_st = 350000            # €/MW
inv_fix_st = 0                 # €
cap_st1 = 6                   # MWel, todo: remove to existing units
eff_st1 = 0.2                  # [-]
eta_th= 0.8                     # [-] efficiency for thermal steam output related to energy_in - power_produced

# Stratified multilayer storage
inv_var_ssml = 100              # €/MWh
inv_fix_ssml = 100              # €

# Electrical Energy storage
inv_var_ees = 500000            # €/MWh
inv_fix_ees = 0                 # €

# Photovoltaic
eta_pv = 0.2                    # [-]
min_area_pv = 10                # m^2, before 100, now 10
max_area_pv = 10000             # m^2
inv_var_pv = 206                # €/m^2
inv_fix_pv = 0

def build_system(sysParam):

    res = dc.System(sysParam)

    # # ================================================================================================================
    # # Supplies
    # # ================================================================================================================

    # Gas Supply
    tempParam = {
        'classname': 'Supply',
        'name': 'supply_gas',
        'seq': sysParam['seq']['price_gas']
    }
    res.add_unit(tempParam)

    # Hydrogen Supply
    tempParam = {
        'classname': 'Supply',
        'name': 'supply_h2',
        'seq': sysParam['seq']['price_h2']
    }
    res.add_unit(tempParam)

    # Biomass Supply
    tempParam = {
        'classname': 'Supply',
        'name': 'supply_biomass',
        'seq': sysParam['seq']['price_biomass'],
    }
    res.add_unit(tempParam)

    # Biogas Supply
    tempParam = {
        'classname': 'Supply',
        'name': 'supply_biogas',
        'seq': sysParam['seq']['price_biogas'],
    }
    res.add_unit(tempParam)

    # Electricity Buy Supply
    tempParam = {
        'classname': 'Supply',
        'name': 'supply_el_buy',
        'seq': sysParam['seq']['price_el'],
    }
    res.add_unit(tempParam)

    # # ================================================================================================================
    # # Components
    # # ================================================================================================================

    # Gas Boiler
    tempParam = {
        'classname': 'GasBoiler',
        'name': 'gb1',
        'lim_q': (0, 1),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'exists': True,
        'lim_f': (0, 1/eff_gb1),      # relative limits to q for f in MW, second entry is optional
        'cap_q': (0, cap_gb1),           # capacity limits for q in MW, first and second entry are optional
        'inv_var': inv_var_gb, # * (1 + 0.0325 * sysParam['depreciation_period']),  # €/MW
        'inv_fix': inv_fix_gb,               # € induces binary variable for existence of unit
        'opex_fix': 0,              # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),        # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),         # €/kWh, induces binary variable for existence of unit
        'ramp_q': (1, 1),           # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),      # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': 40,                 # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': 160,                # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure': 5.5e5,         # minimum uptime/downtime in hours, induces commitment binary variable
        'medium': 'Water',          # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('gas boiler defined')

    # Gas Boiler
    tempParam = {
        'classname': 'GasBoiler',
        'name': 'gb2',
        'lim_q': (0, 1),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'exists': True,
        'lim_f': (0, 1 / eff_gb2),      # relative limits to q for f in MW, second entry is optional
        'cap_q': (0, cap_gb2),           # capacity limits for q in MW, first and second entry are optional
        'inv_var': inv_var_gb, # * (1 + 0.0325 * sysParam['depreciation_period']),  # €/MW
        'inv_fix': inv_fix_gb,               # € induces binary variable for existence of unit
        'opex_fix': 0,              # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),        # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),         # €/kWh, induces binary variable for existence of unit
        'ramp_q': (1, 1),           # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),      # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': 40,                 # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': 160,                # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure': 5.5e5,         # minimum uptime/downtime in hours, induces commitment binary variable
        'medium': 'Water',          # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('gas boiler defined')

    # Gas Boiler
    tempParam = {
        'classname': 'GasBoiler',
        'name': 'gb3',
        'lim_q': (0, 1),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'exists': True,
        'lim_f': (0, 1 / eff_gb3),      # relative limits to q for f in MW, second entry is optional
        'cap_q': (0, cap_gb3),           # capacity limits for q in MW, first and second entry are optional
        'inv_var': inv_var_gb, # * (1 + 0.0325 * sysParam['depreciation_period']),  # €/MW
        'inv_fix': inv_fix_gb,               # € induces binary variable for existence of unit
        'opex_fix': 0,              # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),        # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),         # €/kWh, induces binary variable for existence of unit
        'ramp_q': (1, 1),           # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),      # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': 40,                 # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': 160,                # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure': 5.5e5,         # minimum uptime/downtime in hours, induces commitment binary variable
        'medium': 'Water',          # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('gas boiler defined')

    # Electrode Boiler
    tempParam = {
        'classname': 'ElectrodeBoiler',
        'name': 'eb1',
        'lim_q': (0, 1),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'lim_p': (0, 1 / eff_eb1),  # relative limits to q for f in MW, second entry is optional
        'cap_q': (1, max_cap_eb1),  # capacity limits for q in MW, first and second entry are optional
        'inv_var': inv_var_eb, # * (1 + 0.0325 * sysParam['depreciation_period']),  # €/MW
        'inv_fix': inv_fix_eb,  # € induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': 40,  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': 160,  # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure': 550000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('electrode boiler defined')

    # Biomass Boiler
    tempParam = {
        'classname': 'GasBoiler',
        'name': 'bmb1',
        'lim_q': (0, 1),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'lim_f': (0, 1 / eff_bmb1),      # relative limits to q for f in MW, second entry is optional
        'cap_q': (1, max_cap_bmb1),           # capacity limits for q in MW, first and second entry are optional
        'inv_var': inv_var_bmb, # * (1 + 0.0325 * sysParam['depreciation_period']),  # €/MW
        'inv_fix': inv_fix_bmb,  # € induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),        # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),         # €/kWh, induces binary variable for existence of unit
        'ramp_q': (1, 1),           # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),      # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': 40,                 # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': 160,                # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure': 100000,         # minimum uptime/downtime in hours, induces commitment binary variable
        'medium': 'Water',          # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('biomass boiler defined')

    # High Temperature Heat Pump
    tempParam = {
        'classname': 'HeatPump',
        'name': 'hthp1',
        'lim_q_sink': (0, 1),
        'cap_q_sink': (0, max_cap_hthp),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'inv_var': inv_var_hthp, # * (1 + 0.028 * sysParam['depreciation_period']) / ((273.15 + 140) / 70 * 0.5),  # €/kW
        'inv_fix': inv_fix_hthp,  # €/MW, induces binary variable for existence of unit
        'opex_fix': 0,  # €/MW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q_sink': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_sink_in': (T_sink_in_hthp,),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_sink_out': T_sink_out_hthp,  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_source_in': (T_source_in_hthp,),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_source_out': T_source_out_hthp,  # minimum uptime/downtime in hours, induces commitment binary variable
        'delta_T_sink': (7, 10),  # minimum uptime/downtime in hours, induces commitment binary variable
        'delta_T_source': (7, 10),  # minimum uptime/downtime in hours, induces commitment binary variable
        'eta_comp': (0.5, 0.5),  # capacity limits for f in MW, first and second entry are optional
        'pressure_sink': 200000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure_source': 200000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium_sink': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium_source': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('hp steam defined')

    # Mechanical Vapor Compression
    tempParam = {
        'classname': 'VapourCompression',
        'name': 'mvr1',
        'lim_q': (0, 1),
        'cap_q': (0, max_cap_mvr1),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'inv_var': 0, # * (1 + 0.028 * sysParam['depreciation_period']) / ((273.15 + 140) / 70 * 0.5),  # €/kW
        'inv_fix': inv_fix_mvr,  # €/kW, induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q_sink': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': T_in_mvr1,  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': T_out_mvr1,  # minimum uptime/downtime in hours, induces commitment binary variable
        'P_in': P_in_mvr1,  # minimum uptime/downtime in hours, induces commitment binary variable
        'P_out': P_out_mvr1,  # minimum uptime/downtime in hours, induces commitment binary variable
        'FW T_in': FW_T_in_mvr1,  # minimum uptime/downtime in hours, induces commitment binary variable
        'FW P_in': FW_P_in_mvr1,  # minimum uptime/downtime in hours, induces commitment binary variable
        'eta': efficiency_mvr1,  # capacity limits for f in MW, first and second entry are optional
    }
    # res.add_unit(tempParam)
    print('MVR1 defined')

    # Mechanical Vapor Compression
    tempParam = {
        'classname': 'VapourCompression',
        'name': 'mvr2',
        'lim_q': (0, 1),
        'cap_q': (0, max_cap_mvr2),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'inv_var': 0, # * (1 + 0.028 * sysParam['depreciation_period']) / ((273.15 + 140) / 70 * 0.5),  # €/kW
        'inv_fix': inv_fix_mvr,  # €/kW, induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q_sink': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': T_in_mvr2,  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': T_out_mvr2,  # minimum uptime/downtime in hours, induces commitment binary variable
        'P_in': P_in_mvr2,  # minimum uptime/downtime in hours, induces commitment binary variable
        'P_out': P_out_mvr2,  # minimum uptime/downtime in hours, induces commitment binary variable
        'FW T_in': FW_T_in_mvr2,  # minimum uptime/downtime in hours, induces commitment binary variable
        'FW P_in': FW_P_in_mvr2,  # minimum uptime/downtime in hours, induces commitment binary variable
        'eta': efficiency_mvr2,  # capacity limits for f in MW, first and second entry are optional
        }
    # res.add_unit(tempParam)
    print('MVR2 defined')

    # Stratified Storage
    tempParam = {
        'classname': 'StratifiedMultiLayer',
        'name': 'ssml1',
        'cap_soc': (0, 850 * 3600),
        'lim_c/d': (1000, 1000),
        'inv_var': inv_var_ssml, # 1e4,
        'inv_fix': inv_fix_ssml, # 1e5,
        'T': (70, 150),
        'pressure':  6 * 1e5,
        'medium': 'Water',
    }
    res.add_unit(tempParam)
    print('strat storage defined')

    # Battery - electrical energy storage
    tempParam = {
        'classname': 'Storage',
        'name': 'ees1',
        'cap_soc': (0, 50),
        # 'exists': False,
        'lim_c/d': (10, 10),
        'eta_c/d': (0.99, 0.99),
        'loss_soc': 0.01,  # relative losses proportional to soc per hour
        'lim_soc': [0.1, 1],
        'inv_var': inv_var_ees, # * (1 + 0.01 * sysParam['depreciation_period']),
        'inv_fix': inv_fix_ees,
    }
    res.add_unit(tempParam)
    print('ees defined')

    # PV
    tempParam = {
        'classname': 'Photovoltaic',
        'name': 'pv1',
        'cap_area': (min_area_pv, max_area_pv),
        'exists': False,
        'eta': eta_pv,  # capacity limits for f in MW, first and second entry are optional
        'inv_var': inv_var_pv, # * (1 + sysParam['depreciation_period'] * 0.0131),  # €/m^2
        'inv_fix': inv_fix_pv,  # €, induces binary variable for existence of unit
    }
    res.add_unit(tempParam)
    print('pv defined')

    # Gas Turbine
    tempParam = {
        'classname': 'GasTurbine',
        'name': 'gt1',
        'lim_p': (0, 1),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'lim_f': (0, 1 / eff_gt1),      # relative limits to p for f in MW, second entry is optional
        'cap_p': (0, max_cap_gt1),      # capacity limits for p in MW, first and second entry are optional
        'inv_var': inv_var_gt, # * (1 + 0.0325 * sysParam['depreciation_period']),  # €/MW
        'inv_fix': inv_fix_gt,               # € induces binary variable for existence of unit
        'opex_fix': 0,              # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),        # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),         # €/kWh, induces binary variable for existence of unit
        'ramp_p': (1, 1),           # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),      # minimum uptime/downtime in hours, induces commitment binary variable
        }
    res.add_unit(tempParam)
    print('gas turbine defined')

    # Heat Recovery Boiler
    tempParam = {
        'classname': 'HeatRecoveryBoiler',
        'name': 'hrb1',
        'lim_q_out': (0.5, 1),
        'cap_q_out': (0, max_cap_hrb1),  # capacity limits for p in MW, first and second entry are optional
        'eta': eff_hrb1,
        'inv_var': inv_var_hrb,         # * (1 + 0.0325 * sysParam['depreciation_period']),  # €/MW
        'inv_fix': inv_fix_hrb,         # € induces binary variable for existence of unit
        'opex_fix': 0,              # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),        # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),         # €/kWh, induces binary variable for existence of unit
        'ramp_p': (1, 1),           # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),      # minimum uptime/downtime in hours, induces commitment binary variable
        }
    res.add_unit(tempParam)
    print('heat recovery boiler defined')

    # Back Pressure Steam Turbine
    tempParam = {
        'classname': 'BackPressureSteamTurbine',
        'name': 'st1',
        'exists': True,
        'lim_p': (0, 1),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'lim_q_in': (0, 1 / eff_st1),      # relative limits to p for q_in in MW, second entry is optional
        'eta_th': eta_th,                   # forces losses in turbine, todo adapt later in a more physical way
        'cap_p': (cap_st1, cap_st1),           # capacity limits for p in MW, first and second entry are optional
        'inv_var': inv_var_st, # * (1 + 0.0325 * sysParam['depreciation_period']),  # €/MW
        'inv_fix': inv_fix_st,               # € induces binary variable for existence of unit
        'opex_fix': 0,              # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),        # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),         # €/kWh, induces binary variable for existence of unit
        'ramp_p': (1, 1),           # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),      # minimum uptime/downtime in hours, induces commitment binary variable
        }
    res.add_unit(tempParam)
    print('back pressure steam turbine defined')


    # # ================================================================================================================
    # # Demands & Waste supplies
    # # ================================================================================================================

    # Steam Demand
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'demand_steam_2',
        'seq': sysParam['seq']['demand_steam_2'],
        'T_in': (160,),
        'T_out': (100,),
        'pressure': 5.5 * 1e5,
        'medium': 'Water',
    }
    res.add_unit(tempParam)

    # Electricity Demand
    tempParam = {
        'classname': 'Demand',
        'name': 'demand_el',
        'seq': sysParam['seq']['demand_el'],
    }
    res.add_unit(tempParam)

    # Gas Demand
    tempParam = {
        'classname': 'Demand',
        'name': 'demand_gas',
        'seq': sysParam['seq']['demand_gas'],
    }
    res.add_unit(tempParam)

    # Waste heat supply
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'supply_waste_heat_1',
        'seq': sysParam['seq']['supply_waste_heat_1'],
        'T_in': (90,),
        'T_out': (30,),
        'pressure': 0.7 * 1e5,
        'medium': 'Water',
    }
    res.add_unit(tempParam)

    # # ================================================================================================================
    # # Couplers
    # # ================================================================================================================

    tempParam = {
        'classname': 'Coupler',
        'name': 'h2_to_gb2',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'gas_to_gb2',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'biogas_to_gb2',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'h2_to_gb3',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'gas_to_gb3',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'biogas_to_gb3',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'h2_to_gt1',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'gas_to_gt1',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'biogas_to_gt1',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'h2_to_hrb1',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'gas_to_hrb1',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'biogas_to_hrb1',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'hrb1_q_to_steam_demand',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'hrb1_q_to_steam_turbine',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    # # ================================================================================================================
    # # Nodes
    # # ================================================================================================================

    # Gas
    tempParam = {
        'classname': 'Node',
        'name': 'node_gas',
        'lhs': [['supply_gas', 's']],
        'rhs': [['gb1', 'f'], ['gas_to_gb2', 'in_1'], ['gas_to_gb3', 'in_1'], ['gas_to_gt1', 'in_1'],
                ['gas_to_hrb1', 'in_1'], ['demand_gas', 'd']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Hydrogen
    tempParam = {
        'classname': 'Node',
        'name': 'node_h2',
        'lhs': [['supply_h2', 's']],
        'rhs': [['h2_to_gb2', 'in_1'], ['h2_to_gb3', 'in_1'], ['h2_to_gt1', 'in_1'], ['h2_to_hrb1', 'in_1']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Biogas
    tempParam = {
        'classname': 'Node',
        'name': 'node_biogas',
        'lhs': [['supply_biogas', 's']],
        'rhs': [['biogas_to_gb2', 'in_1'], ['biogas_to_gb3', 'in_1'], ['biogas_to_gt1', 'in_1'],
                ['biogas_to_hrb1', 'in_1']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Electricity
    tempParam = {
        'classname': 'Node',
        'name': 'node_electricity',
        'lhs': [['supply_el_buy', 's'], ['ees1', 'd'], ['pv1', 'p'], ['gt1', 'p'], ['st1', 'p']],
        'rhs': [['hthp1', 'p'], ['eb1', 'p'], ['demand_el', 'd'], ['ees1', 'c']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Biomass
    tempParam = {
        'classname': 'Node',
        'name': 'node_biomass',
        'lhs': [['supply_biomass', 's']],
        'rhs': [['bmb1', 'f']],
        'type': '==',
    }
    res.add_node(tempParam)

    # gb2 fuel node
    tempParam = {
        'classname': 'Node',
        'name': 'node_gb2_fuel',
        'lhs': [['h2_to_gb2', 'out_1'], ['gas_to_gb2', 'out_1'], ['biogas_to_gb2', 'out_1']],
        'rhs': [['gb2', 'f']],
        'type': '>=',
    }
    res.add_node(tempParam)

    # gb3 fuel node
    tempParam = {
        'classname': 'Node',
        'name': 'node_gb3_fuel',
        'lhs': [['h2_to_gb3', 'out_1'], ['gas_to_gb3', 'out_1']],
        'rhs': [['gb3', 'f']],
        'type': '>=',
    }
    res.add_node(tempParam)

    # gt1 fuel node
    tempParam = {
        'classname': 'Node',
        'name': 'node_gt1_fuel',
        'lhs': [['h2_to_gt1', 'out_1'], ['gas_to_gt1', 'out_1'], ['biogas_to_gt1', 'out_1']],
        'rhs': [['gt1', 'f']],
        'type': '>=',
    }
    res.add_node(tempParam)

    # hrb1 fuel node
    tempParam = {
        'classname': 'Node',
        'name': 'node_hrb1_fuel',
        'lhs': [['h2_to_hrb1', 'out_1'], ['gas_to_hrb1', 'out_1'], ['biogas_to_hrb1', 'out_1']],
        'rhs': [['hrb1', 'f']],
        'type': '>=',
    }
    res.add_node(tempParam)

    # hrb1 heat out node
    tempParam = {
        'classname': 'Node',
        'name': 'node_hrb1_heat',
        'lhs': [['hrb1', 'q_out']],
        'rhs': [['hrb1_q_to_steam_demand', 'in_1'], ['hrb1_q_to_steam_turbine', 'in_1']],
        'type': '==',
    }
    res.add_node(tempParam)

    # gt1 waste heat node
    tempParam = {
        'classname': 'Node',
        'name': 'node_gt1_waste_heat',
        'lhs': [['hrb1', 'q_in']],
        'rhs': [['gt1', 'q_waste']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Steam demand
    tempParam = {
        'classname': 'Node',
        'name': 'node_steam_demand_2',
        'lhs': [['hthp1', 'q_sink'], ['gb2', 'q'], ['gb3', 'q'], ['eb1', 'q'], ['st1', 'q_out'],
                ['hrb1_q_to_steam_demand', 'out_1']],
        'rhs': [['demand_steam_2', 'q']],
        'type': '>=',
    }
    res.add_node(tempParam)

    # Steam Turbine Steam in
    tempParam = {
        'classname': 'Node',
        'name': 'node_steam_turbine_in',
        'lhs': [['gb1', 'q'], ['bmb1', 'q'], ['hrb1_q_to_steam_turbine', 'out_1']],
        'rhs': [['st1', 'q_in']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Waste heat supply
    tempParam = {
        'classname': 'Node',
        'name': 'node_hthp_source_heat',
        'lhs': [['hthp1', 'q_source']],
        'rhs': [['supply_waste_heat_1', 'q']],
        'type': '<=',
    }
    res.add_node(tempParam)

    # # Additional constraints
    # def con_rule(m, s, t):
    #     # IMPORTANT: only 1 T_sink_in, otherwise weighting by mass fractions would be necessary --> nonlinear
    #     # from q_sink = m_sink * (h_sink_out-h_sink_in) --> q_sink_fraction = m_sink_fraction * (h_sink_out-h_sink_in)
    #     # q_sink from heat pump is in MW,
    #     return ( res.unit['mvr1'].port['m_in'][s, t] ==         #achtung ich bin nicht sicher ob das nicht probleme macht --> mvr erzwingt, müsste <= sein todo
    #              res.unit['hthp1'].port['q_sink'][s, t] /
    #              (res.unit['hthp1'].param['h_sink_out'] -
    #               np.array(list(res.unit['hthp1'].param['h_sink_in'].values())).item())  # throws error if not 1x1 array
    #            )
    # res.model.con_m_fraction_hthp_to_mvr1 = pyo.Constraint(res.model.set_sc, res.model.set_t, rule=con_rule)
    #
    # def con_rule(m, s, t):
    #     # formula comes from dependence of m_out on q_out of MVR --> see class file
    #     return ( res.unit['mvr2'].port['m_in'][s, t] ==
    #              res.unit['mvr1'].port['q'][s, t] *
    #              (res.unit['mvr1'].param['FW fraction'] + 1) / res.unit['mvr1'].param['dh_out']
    #            )
    # res.model.con_m_and_q_balance_mvr1_to_mvr2 = pyo.Constraint(res.model.set_sc, res.model.set_t, rule=con_rule)

    def con_rule(m, s, t):
        # limit biomass supply
        return res.unit['supply_biomass'].port['s'][s, t] <= 4
    res.model.con_max_biomass_supply = pyo.Constraint(res.model.set_sc, res.model.set_t, rule=con_rule)

    def con_rule(m, s, t):
        # limit biogas supply
        return res.unit['supply_biogas'].port['s'][s, t] <= 1
    res.model.con_max_biogas_supply = pyo.Constraint(res.model.set_sc, res.model.set_t, rule=con_rule)

    def con_rule(m, s, t):
        # limit hydrogen supply
        return res.unit['supply_h2'].port['s'][s, t] <= 5
    res.model.con_max_h2_supply = pyo.Constraint(res.model.set_sc, res.model.set_t, rule=con_rule)

    res = add_scenario_constraints(res, sysParam['scenario'])

    res.build_model()

    units = {
        'MW': ['gb1', 'gb2', 'gb3', 'eb1' ,'bmb1', 'hthp1', 'gt1', 'hrb1', 'st1'],
        'MWh': ['ssml1'],
        'm³': [],
        'solar': ['pv1']
    }

    unit_port = {
        'gb1': 'q',
        'gb2': 'q',
        'gb3': 'q',
        'eb1': 'q',
        'bmb1': 'q',
        'hthp1': 'q_sink',
        # 'mvr1': 'q',
        # 'mvr2': 'q',
        'gt1': 'p',
        'st1': 'p'
    }

    units_energy_plot = {'q': {'gb1': ['q'], 'gb2': ['q'], 'gb3': ['q'], 'eb1': ['q'], 'bmb1': ['q'],
                               'hthp1': ['q_sink'], 'hrb1': ['q_out'], 'st1': ['q_out']},
                         'f': {'gb1': ['f'], 'gb2': ['f'], 'gb3': ['f'], 'bmb1': ['f'], 'gt1': ['f'],
                               'hrb1': ['f']},
                         'p': {'eb1': ['p'],
                               'hthp1': ['p'],
                               # 'mvr1': ['p'],
                               # 'mvr2': ['p'],
                               'supply_el_buy': ['s'],
                               'pv1': ['p'],
                               'gt1': ['p'],
                               'st1': ['p']
                               }
                         }

    return res, units, unit_port, units_energy_plot

def make_simple_timeseries(scenario_nr):
    # 1 year long timeseries
    start = pd.to_datetime('1st of January, 2022, 0:00')
    end = pd.to_datetime('1st of January, 2022, 23:00')
    T = pd.to_timedelta(end-start).total_seconds()
    ts = pd.date_range(start, end, freq='H')
    df = pd.DataFrame({'Datetime': ts,
                       'seconds': (ts-start).total_seconds()})
    df['sinewave'] = 1 + np.sin(df['seconds'] / T * 2 * np.pi)
    df['half_sinewave'] = np.sin(0.5*df['seconds'] / T * 2 * np.pi)

    # Period
    period = np.ones(len(df.Datetime))
    df['period'] = period

    # Heat demands
    dm2 = 15 # Steam demand 2, [MW]
    df['demand_steam_2'] = np.ones(len(df.Datetime)) * dm2

    # Plant electricity demand
    dm_el = 9
    df['demand_el'] = np.ones(len(df.Datetime)) * dm_el

    # Process gas demand (?)
    dm_gas = 0.5
    df['demand_gas'] = np.ones(len(df.Datetime)) * dm_gas

    # Waste heat supplies
    wh1 = 10.6 # Waste heat supply 1, [MW]
    df['supply_waste_heat_1'] = np.ones(len(df.Datetime)) * wh1

    # Supplies
    [price_el, price_gas, price_h2, price_biomass, price_biogas] = get_scenario_prices(scenario_nr)

    df['price_el'] = np.ones(len(df.Datetime)) * price_el
    df['price_gas'] = np.ones(len(df.Datetime)) * price_gas
    df['price_h2'] = np.ones(len(df.Datetime)) * price_h2
    df['price_biomass'] = np.ones(len(df.Datetime)) * price_biomass
    df['price_biogas'] = np.ones(len(df.Datetime)) * price_biogas

    # Solar irradiance

    # IGH_max = 1000 / 1e6  # [MW/m2], maximale Einstrahlung
    IGH_max = 179.3 / 1e6 # [MW/m2], fiktive dauerhafte Einstrahlung am sonnenintensivsten Tag des Jahres, sodass ...
    # ... int ( half_sinewave * IGH_max ) == 1000 kWh/m2 (gesamte Jahreseinstrahlung)
    solar1 = df['half_sinewave'] * IGH_max

    # Wetterdaten aus Traun
    folder = ( Path("P:\SGP-18574") / "data" / "2.04.01671.1.0 DekarPIO I (Drexler-Schmid)" /
               "AP2 - Energiebedarf- und versorgungsanalyse" / "0 Sonstige Daten" / "Wetterdaten")
    solar2 = pd.read_csv(folder / "traun_wetterdaten_2019.csv", sep=";").loc[:,"Globalstrahlung horizontal in Wh/m²"] / 1e6

    # solar 1 ... gemittelte tägliche Einstrahlung, solar 2 ... gemessene Wetterdaten
    df['solar'] = solar2
    # Miscellaneous
    df['zero_sequence'] = np.zeros(len(df.Datetime))

    return df

def get_scenario_prices(scenario_nr):
    scenarios = [
        [   # scenario 0
            400,                   # [€/MWh], electricity price
            170 + 0.20196 * 70,    # [€/MWh], natural gas price + Certificate price (CO2)
            300,                   # [€/MWh], hydrogen price
            50,                    # [€/MWh], biomass price
            140,                   # [€/MWh], biogas (biomethane) price
         ],

        [   # scenario 1
            400,                   # electricity price
            170 + 0.20196 * 1e5,   # natural gas price
            300,                   # hydrogen price
            50,                    # biomass price
            140,                   # biogas (biomethane) price
         ],

        [   # scenario 2
            400,                   # electricity price
            170 + 0.20196 * 70,    # natural gas price
            300,                   # hydrogen price
            50,                    # biomass price
            140,                   # biogas (biomethane) price
         ],

        [  # scenario 3
            400,                   # electricity price
            170 + 0.20196 * 1e5,   # natural gas price
            300,                   # hydrogen price
            50,                    # biomass price
            140,                   # biogas (biomethane) price
        ],

        [  # scenario 4
            150,                   # electricity price
            200 + 0.20196 * 70,    # natural gas price
            300,                   # hydrogen price
            50,                    # biomass price
            140,                   # biogas (biomethane) price
        ],
        [  # scenario 5
            400,                   # electricity price
            170 + 0.20196 * 1e5,   # natural gas price
            300,                   # hydrogen price
            50,                    # biomass price
            140,                   # biogas (biomethane) price
        ],

        [   # scenario 6
            285,                   # [€/MWh], electricity price
            170 + 0.20196 * 70,    # [€/MWh], natural gas price + Certificate price (CO2)
            300,                   # [€/MWh], hydrogen price
            50,                    # [€/MWh], biomass price
            140,                   # [€/MWh], biogas (biomethane) price
         ],

        [  # scenario 7
            150,                   # electricity price
            200 + 0.20196 * 70,    # natural gas price
            300,                   # hydrogen price
            50,                    # biomass price
            140,                   # biogas (biomethane) price
        ],

        [   # scenario 8
            400,                   # [€/MWh], electricity price
            170 + 0.20196 * 70,    # [€/MWh], natural gas price + Certificate price (CO2)
            184,                   # [€/MWh], hydrogen price
            50,                    # [€/MWh], biomass price
            140,                   # [€/MWh], biogas (biomethane) price
         ],

        [  # scenario 9
            150,  # electricity price
            170 + 0.20196 * 70,  # natural gas price
            100,  # hydrogen price
            50,  # biomass price
            140,  # biogas (biomethane) price
        ],

    ]

    [price_el, price_gas, price_h2, price_biomass, price_biogas] = scenarios[scenario_nr]

    return [price_el, price_gas, price_h2, price_biomass, price_biogas]

def add_scenario_constraints(system, scenario):

    if (scenario == 2 or scenario == 3):
        def con_rule(m, s, t):
            # limit electrical load
            return system.unit['supply_el_buy'].port['s'][s, t] <= 20
        system.model.con_max_el_load = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

    if (scenario == 5):
        def con_rule(m, s, t):
            # limit electrical load
            return system.unit['supply_el_buy'].port['s'][s, t] <= 12
        system.model.con_max_el_load = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

    if (scenario == 7):
        def con_rule(m, s, t):
            # limit electrical load
            return system.unit['supply_el_buy'].port['s'][s, t] <= 12
        system.model.con_max_el_load = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

    return system
