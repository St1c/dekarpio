import numpy as np
import pandas as pd
import sys
import os
import pickle
import pyomo.environ as pyo
import matplotlib.pyplot as plt
import CoolProp.CoolProp as cp

PACKAGE_PARENT = '../..'
DOOM_DIR = 'pi_framework'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT, DOOM_DIR)))
import DOOM.classes as dc
import DOOM.auxiliary as da


# # Existing Units
# # ================================================================================================================

inv_var_gb = 89000   # €/MW
inv_fix_gb = 5000    # €

# Gas boiler 1
cap_gb1 = 10           # [MW], capacity
eff_gb1 = 0.9        # [-], efficiency

# Gas boiler 2
cap_gb2 = 5           # [MW], capacity
eff_gb2 = 0.95        # [-], efficiency

# Gas boiler 3
cap_gb3 = 5           # [MW], capacity
eff_gb3 = 0.9        # [-], efficiency

# # Potential New Units
# # ================================================================================================================

# Biomass boiler
inv_var_bmb = 1.5e6      # €/MW
inv_fix_bmb = 5e3        # €
max_cap_bmb1 = 23           # [MW], capacity
eff_bmb1 = 0.9             # [-], efficiency

# Electrode boiler
inv_var_eb = 106.5e3       # €/MW
inv_fix_eb = 5e3           # €
max_cap_eb1 = 10           # [MW], capacity
eff_eb1 = 0.98             # [-], efficiency

# High temperature heat pump
inv_fix_hthp = 30e3        # €
inv_var_hthp = 1e6         # €/MW
max_cap_hthp = 100         # [MW], capacity
T_sink_in_hthp = 80        # [°C], incoming temperature of heat sink stream
T_sink_out_hthp = 117      # [°C], target temperature of steam
T_source_in_hthp = 50      # [°C], incoming temperature of heat source stream
T_source_out_hthp = 30     # [°C], outgoing temperature of heat source stream

# Low temperature heat pump
inv_fix_lthp = 30e3         # €
inv_var_lthp = 500e3        # €/MW
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
inv_var_gt = 10000             # €/MW
inv_fix_gt = 3e6               # €

# Heat Recovery Boiler
inv_var_hrb = 10000            # €/MW
inv_fix_hrb = 3e6              # €

# Steam Turbine
inv_var_st = 95000             # €/MW
inv_fix_st = 3e6               # €

# Stratified multilayer storage
inv_fix_ssml = 100              # €/MWh
inv_var_ssml = 100              # €

# Electrical Energy storage
inv_fix_ees = 150                # €/MWh
inv_var_ees = 100                # €

# Photovoltaic
eta_pv = 0.2                    # [-]
min_area_pv = 10                # m^2
max_area_pv = 10000             # m^2
inv_fix_pv = 206                # €/m^2
inv_var_pv = 0

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
        'cap_q': (0, max_cap_eb1),  # capacity limits for q in MW, first and second entry are optional
        'inv_var': inv_var_eb, # * (1 + 0.0325 * sysParam['depreciation_period']),  # €/MW
        'inv_fix': inv_fix_eb,  # € induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': 40,  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': 120,  # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure': 100000,  # minimum uptime/downtime in hours, induces commitment binary variable
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
        'cap_q': (0, max_cap_bmb1),           # capacity limits for q in MW, first and second entry are optional
        'inv_var': inv_var_bmb, # * (1 + 0.0325 * sysParam['depreciation_period']),  # €/MW
        'inv_fix': inv_fix_bmb,  # € induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),        # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),         # €/kWh, induces binary variable for existence of unit
        'ramp_q': (1, 1),           # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),      # minimum uptime/downtime in hours, induces commitment binary variable
        'T_in': 40,                 # minimum uptime/downtime in hours, induces commitment binary variable
        'T_out': 90,                # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure': 100000,         # minimum uptime/downtime in hours, induces commitment binary variable
        'medium': 'Water',          # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('biomass boiler defined')

    # Heat Pump
    tempParam = {
        'classname': 'HeatPump',
        'name': 'hthp1',
        'lim_q_sink': (0, 1),
        'cap_q_sink': (0, max_cap_hthp),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'inv_var': inv_var_hthp, # * (1 + 0.028 * sysParam['depreciation_period']) / ((273.15 + 140) / 70 * 0.5),  # €/kW
        'inv_fix': inv_fix_hthp,  # €/kW, induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
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

    # Heat Pump
    tempParam = {
        'classname': 'HeatPump',
        'name': 'lthp1',
        'lim_q_sink': (0, 1),
        'cap_q_sink': (0, max_cap_lthp),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'inv_var': inv_var_lthp, # * (1 + 0.028 * sysParam['depreciation_period']) / ((273.15 + 140) / 70 * 0.5),  # €/kW
        'inv_fix': inv_fix_lthp,  # €/kW, induces binary variable for existence of unit
        'opex_fix': 0,  # €/kW, induces binary variable for existence of unit
        'cost_susd': (0, 0),  # €/kWh, induces binary variable for existence of unit
        'max_susd': (1, 1),  # €/kWh, induces binary variable for existence of unit
        'ramp_q_sink': (1, 1),  # ramp limit for q in %/h, no ramp constraints if empty
        'min_utdt_ts': (1, 1),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_sink_in': (T_sink_in_lthp,),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_sink_out': T_sink_out_lthp,  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_source_in': (T_source_in_lthp,),  # minimum uptime/downtime in hours, induces commitment binary variable
        'T_source_out': T_source_out_lthp,  # minimum uptime/downtime in hours, induces commitment binary variable
        'delta_T_sink': (7, 7),  # minimum uptime/downtime in hours, induces commitment binary variable
        'delta_T_source': (7, 7),  # minimum uptime/downtime in hours, induces commitment binary variable
        'eta_comp': (0.5, 0.5),  # capacity limits for f in MW, first and second entry are optional
        'pressure_sink': 200000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'pressure_source': 200000,  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium_sink': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
        'medium_source': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
    }
    res.add_unit(tempParam)
    print('hp low temp defined')

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
    res.add_unit(tempParam)
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
    res.add_unit(tempParam)
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
        'eta_c/d': (1, 1),
        'loss_soc': 0.01,  # relative losses proportional to soc per hour
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

    # # ================================================================================================================
    # # Demands & Waste supplies
    # # ================================================================================================================

    # Steam Demand
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'demand_steam_1',
        'seq': sysParam['seq']['demand_steam_1'],
        'T_in': (130,),
        'T_out': (100,),
        'pressure': 4 * 1e5,
        'medium': 'Water',
    }
    res.add_unit(tempParam)

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

    # Steam Demand
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'demand_steam_3',
        'seq': sysParam['seq']['demand_steam_3'],
        'T_in': (144,),
        'T_out': (120,),
        'pressure': 3.5 * 1e5,
        'medium': 'Water',
    }
    res.add_unit(tempParam)

    # Steam Demand
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'demand_steam_4',
        'seq': sysParam['seq']['demand_steam_4'],
        'T_in': (125,),
        'T_out': (100,),
        'pressure': 2 * 1e5,
        'medium': 'Water',
    }
    res.add_unit(tempParam)

    # Low temperature Heat Demand
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'demand_low_temp_heat',
        'seq': sysParam['seq']['demand_low_temp_heat'],
        'T_in': (80,),
        'T_out': (40,),
        'pressure': 1 * 1e5,
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

    # Waste heat supply
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'supply_waste_heat_2',
        'seq': sysParam['seq']['supply_waste_heat_2'],
        'T_in': (32,),
        'T_out': (25,),
        'pressure': 1 * 1e5,
        'medium': 'Water',
    }
    res.add_unit(tempParam)

    # Waste heat supply
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'supply_waste_heat_3',
        'seq': sysParam['seq']['supply_waste_heat_3'],
        'T_in': (35,),
        'T_out': (15,),
        'pressure': 1 * 1e5,
        'medium': 'Air',
    }
    res.add_unit(tempParam)

    # Waste heat supply
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'supply_waste_heat_4',
        'seq': sysParam['seq']['supply_waste_heat_4'],
        'T_in': (40,),
        'T_out': (20,),
        'pressure': 1 * 1e5,
        'medium': 'Water',
    }
    res.add_unit(tempParam)

    # Waste heat supply
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'supply_waste_heat_5',
        'seq': sysParam['seq']['supply_waste_heat_5'],
        'T_in': (50,),
        'T_out': (15,),
        'pressure': 1 * 1e5,
        'medium': 'Air',
    }
    res.add_unit(tempParam)

    # # ================================================================================================================
    # # Couplers
    # # ================================================================================================================

    tempParam = {
        'classname': 'Coupler',
        'name': 'hthp_q_to_mvr1',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'hthp_q_to_steam4',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'mvr1_q_to_steam3',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'mvr1_q_to_mvr2',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

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
        'name': 'gb2_to_steam2',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'gb2_to_low_temp_heat',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'gb3_to_steam2',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'gb3_to_low_temp_heat',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'eb1_to_steam2',
        'in': [1],
        'out': [1],
    }
    res.add_unit(tempParam)

    tempParam = {
        'classname': 'Coupler',
        'name': 'eb1_to_low_temp_heat',
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
        'rhs': [['gb1', 'f'], ['gas_to_gb2', 'in_1'], ['gas_to_gb3', 'in_1'], ['demand_gas', 'd']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Hydrogen
    tempParam = {
        'classname': 'Node',
        'name': 'node_h2',
        'lhs': [['supply_h2', 's']],
        'rhs': [['h2_to_gb2', 'in_1'], ['h2_to_gb3', 'in_1']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Electricity
    tempParam = {
        'classname': 'Node',
        'name': 'node_electricity',
        'lhs': [['supply_el_buy', 's'], ['ees1', 'd'], ['pv1', 'p']],
        'rhs': [['hthp1', 'p'], ['lthp1', 'p'], ['eb1', 'p'], ['demand_el', 'd'], ['ees1', 'c'], ['mvr1', 'p'],
                ['mvr2', 'p']],
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

    # HTHP1 nodes
    tempParam = {
        'classname': 'Node',
        'name': 'node_q_hthp1',
        'lhs': [['hthp1', 'q_sink']],
        'rhs': [['hthp_q_to_mvr1', 'in_1'], ['hthp_q_to_steam4', 'in_1']],
        'type': '==',
    }
    res.add_node(tempParam)

    # MVR1 node
    tempParam = {
        'classname': 'Node',
        'name': 'node_q_mvr1',
        'lhs': [['mvr1', 'q']],
        'rhs': [['mvr1_q_to_mvr2', 'in_1'], ['mvr1_q_to_steam3', 'in_1']],
        'type': '==',
    }
    res.add_node(tempParam)

    # gb2 fuel node
    tempParam = {
        'classname': 'Node',
        'name': 'node_gb2_fuel',
        'lhs': [['h2_to_gb2', 'out_1'], ['gas_to_gb2', 'out_1']],
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

    # gb2 heat node
    tempParam = {
        'classname': 'Node',
        'name': 'node_gb2_heat',
        'lhs': [['gb2', 'q']],
        'rhs': [['gb2_to_steam2', 'in_1'], ['gb2_to_low_temp_heat', 'in_1']],
        'type': '>=',
    }
    res.add_node(tempParam)

    # gb3 heat node
    tempParam = {
        'classname': 'Node',
        'name': 'node_gb3_heat',
        'lhs': [['gb3', 'q']],
        'rhs': [['gb3_to_steam2', 'in_1'], ['gb3_to_low_temp_heat', 'in_1']],
        'type': '>=',
    }
    res.add_node(tempParam)

    # eb1 heat node
    tempParam = {
        'classname': 'Node',
        'name': 'node_eb1_heat',
        'lhs': [['eb1', 'q']],
        'rhs': [['eb1_to_steam2', 'in_1'], ['eb1_to_low_temp_heat', 'in_1']],
        'type': '>=',
    }
    res.add_node(tempParam)

    # Steam
    tempParam = {
        'classname': 'Node',
        'name': 'node_steam_demand_1',
        'lhs': [['gb1', 'q'], ['bmb1', 'q']],
        'rhs': [['demand_steam_1', 'q']],
        'type': '>=',
    }
    res.add_node(tempParam)

    tempParam = {
        'classname': 'Node',
        'name': 'node_steam_demand_2',
        'lhs': [['mvr2', 'q'], ['gb2_to_steam2', 'out_1'], ['gb3_to_steam2', 'out_1'],
                ['eb1_to_steam2', 'out_1']],
        'rhs': [['demand_steam_2', 'q']],
        'type': '>=',
    }
    res.add_node(tempParam)

    tempParam = {
        'classname': 'Node',
        'name': 'node_steam_demand_3',
        'lhs': [['mvr1_q_to_steam3', 'out_1']],
        'rhs': [['demand_steam_3', 'q']],
        'type': '>=',
    }
    res.add_node(tempParam)

    tempParam = {
        'classname': 'Node',
        'name': 'node_steam_demand_4',
        'lhs': [['hthp_q_to_steam4', 'out_1']],
        'rhs': [['demand_steam_4', 'q']],
        'type': '>=',
    }
    res.add_node(tempParam)

    # Low temperature heat demand
    tempParam = {
        'classname': 'Node',
        'name': 'node_low_temp_heat',
        'lhs': [['lthp1', 'q_sink'], ['ssml1', 'm_d_70'], ['gb2_to_low_temp_heat', 'out_1'],
                ['gb3_to_low_temp_heat', 'out_1'], ['eb1_to_low_temp_heat', 'out_1']],
        'rhs': [['demand_low_temp_heat', 'q'], ['ssml1', 'm_c_70']],
        'type': '>=',
    }
    res.add_node(tempParam)

    # Waste heat supply
    tempParam = {
        'classname': 'Node',
        'name': 'node_hthp_source_heat',
        'lhs': [['hthp1', 'q_source']],
        'rhs': [['supply_waste_heat_5', 'q']],
        'type': '<=',
    }
    res.add_node(tempParam)

    tempParam = {
        'classname': 'Node',
        'name': 'node_lthp_source_heat',
        'lhs': [['lthp1', 'q_source']],
        'rhs': [['supply_waste_heat_2', 'q'], ['supply_waste_heat_3', 'q'], ['supply_waste_heat_4', 'q']],
        'type': '<=',
    }
    res.add_node(tempParam)

    # Additional constraints
    def con_rule(m, s, t):
        # IMPORTANT: only 1 T_sink_in, otherwise weighting by mass fractions would be necessary --> nonlinear
        # from q_sink = m_sink * (h_sink_out-h_sink_in) --> q_sink_fraction = m_sink_fraction * (h_sink_out-h_sink_in)
        # q_sink from heat pump is in MW,
        return ( res.unit['mvr1'].port['m_in'][s, t] ==
                 res.unit['hthp_q_to_mvr1'].port['out_1'][s, t] /
                 (res.unit['hthp1'].param['h_sink_out'] -
                  np.array(list(res.unit['hthp1'].param['h_sink_in'].values())).item()) # throws error if not 1x1 array
               )
    res.model.con_m_fraction_hthp_to_mvr1 = pyo.Constraint(res.model.set_sc, res.model.set_t, rule=con_rule)

    def con_rule(m, s, t):
        # formula comes from dependence of m_out on q_out of MVR --> see class file
        return ( res.unit['mvr2'].port['m_in'][s, t] ==
                 res.unit['mvr1_q_to_mvr2'].port['out_1'][s, t] *
                 (res.unit['mvr1'].param['FW fraction'] + 1) / res.unit['mvr1'].param['dh_out']
               )
    res.model.con_m_and_q_balance_mvr1_to_mvr2 = pyo.Constraint(res.model.set_sc, res.model.set_t, rule=con_rule)

    res.build_model()

    units = {
        'MW': ['gb1', 'gb2', 'gb3', 'eb1' ,'bmb1', 'hthp1', 'lthp1'],
        'MWh': ['ssml1'],
        'm³': [],
        'solar': []
    }

    unit_port = {
        'gb1': 'q',
        'gb2': 'q',
        'gb3': 'q',
        'eb1': 'q',
        'bmb1': 'q',
        'hthp1': 'q_sink',
        'lthp1': 'q_sink'
    }

    units_energy_plot = {'q': {'gb1': ['q'], 'gb2': ['q'], 'gb3': ['q'], 'eb1': ['q'], 'bmb1': ['q'],
                               'hthp1': ['q_sink'], 'lthp1': ['q_sink']},
                         'f': {'gb1': ['f'], 'gb2': ['f'], 'gb3': ['f'], 'bmb1': ['f']},
                         'p': {'eb1': ['p'],
                               'hthp1': ['p'],
                               'lthp1': ['p'],
                               'supply_el_buy': ['s'],
                               }
                         }

    return res, units, unit_port, units_energy_plot

def make_simple_timeseries():
    # 1 year long timeseries
    start = pd.to_datetime('1st of January, 2022, 0:00')
    end = pd.to_datetime('1st of January, 2023, 0:00')
    T = pd.to_timedelta(end-start).total_seconds()
    ts = pd.date_range(start, end, freq='D')
    df = pd.DataFrame({'Datetime': ts,
                       'seconds': (ts-start).total_seconds()})
    df['sinewave'] = 1 + np.sin(df['seconds'] / T * 2 * np.pi)
    df['half_sinewave'] = np.sin(0.5*df['seconds'] / T * 2 * np.pi)

    # Period
    period = np.ones(len(df.Datetime))
    df['period'] = period

    # Heat demands
    dm1 = 1.5 # Steam demand 1, [MW]
    df['demand_steam_1'] = np.ones(len(df.Datetime)) * dm1
    dm2 = 15 # Steam demand 2, [MW]
    df['demand_steam_2'] = np.ones(len(df.Datetime)) * dm2
    dm3 = 5 # Steam demand 3, [MW]
    df['demand_steam_3'] = np.ones(len(df.Datetime)) * dm3
    dm4 = 1 # Steam demand 3, [MW]
    df['demand_steam_4'] = np.ones(len(df.Datetime)) * dm4
    dmlth = 0.5 # Low temperature heat demand, [MW]
    df['demand_low_temp_heat'] = df['sinewave'] * dmlth

    # Plant electricity demand
    dm_el = 3
    df['demand_el'] = np.ones(len(df.Datetime)) * dm_el

    # Process gas demand (?)
    dm_gas = 0.5
    df['demand_gas'] = np.ones(len(df.Datetime)) * dm_gas

    # Waste heat supplies
    wh1 = 0.4 # Waste heat supply 1, [MW]
    df['supply_waste_heat_1'] = np.ones(len(df.Datetime)) * wh1
    wh2 = 1.9 # Waste heat supply 1, [MW]
    df['supply_waste_heat_2'] = np.ones(len(df.Datetime)) * wh2
    wh3 = 0.8 # Waste heat supply 1, [MW]
    df['supply_waste_heat_3'] = np.ones(len(df.Datetime)) * wh3
    wh4 = 1 # Waste heat supply 1, [MW]
    df['supply_waste_heat_4'] = np.ones(len(df.Datetime)) * wh4
    wh5 = 6.5 # Waste heat supply 1, [MW]
    df['supply_waste_heat_5'] = np.ones(len(df.Datetime)) * wh5

    # Supplies
    price_el = 92.  # [EUR / MWh]
    # df['price_el'] = np.ones(len(df.Datetime)) * price_el
    df['price_el'] = df['sinewave'] * price_el

    price_gas = 41.  # [EUR / MWh]
    df['price_gas'] = np.ones(len(df.Datetime)) * price_gas

    price_h2 = 200.  # [EUR / MWh]
    df['price_h2'] = np.ones(len(df.Datetime)) * price_h2

    price_biomass = 50.  # [EUR / MWh]
    df['price_biomass'] = np.ones(len(df.Datetime)) * price_biomass

    price_biogas = 85    # [€/MWh]

    # Solar irradiance
    IGH_max = 1 / 1e3  # [MW/m2], maximale Einstrahlung
    df['solar'] = df['half_sinewave'] * IGH_max

    # Miscellaneous
    df['zero_sequence'] = np.zeros(len(df.Datetime))

    return df

