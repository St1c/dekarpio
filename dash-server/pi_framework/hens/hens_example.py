import pi_framework.hens.Models.HENS as HENS
import pi_framework.hens.Models as Models
import pi_framework.hens.Plots as Plots
import pi_framework.hens.Plots.plots
import pi_framework.hens.Calculations.actual_values as actual_values
import pi_framework.hens.Auxiliary.checks as checks
from pyomo.environ import *
import pi_framework.hens.Calculations as Calculations
import pi_framework.hens.PinchAnalysis.streamdata as streamdata
import pi_framework.hens.PinchAnalysis.targets as targets

import numpy as np
import pandas as pd

import os

################################################################################################################
#    PRE SETTINGS

# fixme: Gehört ausgelagert!
settings = {}
# HEX costs
settings['COSTS'] = {
    'beta': 0.9,  # cost exponent for HEX area (0 - 1)
    'HEX fix': 24000,  # cost for HEX installation
    'HEX var': 167,  # cost for HEX area
    'annualization': 5  # years for annualization
}

# Linearization settings
settings['OPT'] = {
    'timelimit': 60,  # seconds
}

# Linearization settings
settings['LIN'] = {
    'rel_err': 0.05,  # sets max. rel. error for LMTD approximation (0 - 1)
    'num_eq': 5,  # sets number of eq. used to approximate A^beta (default = 5)
    'res': 150,  # resolution for data points
}

# Tightening
settings['TIGHT'] = {
    'set': True,
    'LMTD': True,  # adds additional constraints for LMTD
    'zmin': True,  # adds additional constraints for minimum HEX units
    'dup': True  # adds additional constraints to avoid redundant networks
}

# Simplifications
settings['SIMP'] = {
    'min HR': 0,  # minimum percentage of maximum HR (0 - 1, 0 = off)
    'min HR TAM': 0,  # minimum percentage of maximum HR (0 - 1, 0 = off)
    'max_pair_hex': True,  # allow only one HEX per stream pair, # TODO: cannot be turned off for retrofit problems!!
    'equal z': True  # no HEX by-passing
}

# Retrofit
settings['RETROFIT'] = {
    # 'max_changes': 6,  # number of changes allowed within the the HEN   # FIXME: die Optionen macht noch nichts!
    'reuse': True,  # reuse HEX elsewhere in the HEN
    'add_hex': 0.05  # factor for add HEX area to existing HEX (0 - )
}

# HEN settings
settings['HEN'] = {
    'stages': 5,  # number of temperature stages (including utility states & storage)  (ideal (5)6-7)
    'dTmin': 5,  # minimum temperature differences in the HEN (default = 5)
    'soft': True,  # allow for 'soft' streams
}

settings['SCHED'] = {
    'active': 1,    # enables rescheduling
}

settings['defaults'] = {
    'h': 0.2,
    'duration': 1,
    'interval': 1,
}


########################################################################################################################
#    Instantiate HEN
########################################################################################################################
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, '../../example cases/Stream table examples/batch/Lit_Ex_RS_4.xls')

filenames_base = 'C:/Users/BeckA/PycharmProjects/sinfonies/example cases/Stream table examples/continuous/Stream Data/'
filenames = [x for x in os.listdir(filenames_base)]
file_nr = 9  # WP Integration möglich:
             # 0, ca. 0 -> 40 °C
             # 2, ca. 15 -> 50 °C
             # 5, ca. 50 -> 120 °C
             # 8, ca. 35 -> 160 °C
             # 9, ca. 30 -> 150 °C

filename = os.path.join('C:/Users/BeckA/PycharmProjects/sinfonies/example cases/Stream table examples/batch/Lit_Ex_RS_4.xls')
filename = filenames_base + filenames[file_nr]



# if settings['SCHED']['active']:
filename = 'C:/Users/BeckA/PycharmProjects/sinfonies/example cases/Stream table examples/continuous/Requirements Test.xlsx'
filename = 'C:/Users/BeckA/PycharmProjects/sinfonies/example cases/Stream table examples/continuous/Requirements Test_2.xlsx'

reader_fun = streamdata.excel_reader
data_input = streamdata.prep_input(reader_fun(settings, filename))

targ = targets.calc_targets(data_input, settings)

########################################################################################################################
#    Plots
########################################################################################################################


# Plots.plots.plot_CCs(targ, 'GCCs', 1, 1, 1)
# Plots.plots.plot_CCs(targ, 'CCs', 1, 1, 1)

########################################################################################################
# Set conversion units
########################################################################################################
conversion_units = {}

# Hot utilities
conversion_units['UH'] = {
    'Steam HP': {
        'Tin': 500,             # Inlet Temperature °C
        'Tout': 450,            # Outlet Temperature °C
        'dTmin': 5,             # minimum temperature difference °C
        'h': 0.2,               # Heat transfer coefficient kW/m²K
        'costs': 252,           # specific energy costs per year €/kWh/y
    },
    # 'Steam MP': {
    #     'Tin': 400,             # Inlet Temperature °C
    #     'Tout': 350,            # Outlet Temperature °C
    #     'dTmin': 5,             # minimum temperature difference °C
    #     'h': 0.2,               # Heat transfer coefficient kW/m²K
    #     'costs': 0.04*24*52*7,  # specific energy costs per year €/kWh/y # FIXME: ist für testzwecke auf einen sehr hohen wert gestellt
    # }
}

# Cold utilities
conversion_units['UC'] = {
    'Cooling Water': {
        'Tin': -10,               # Inlet Temperature °C
        'Tout': -5,             # Outlet Temperature °C
        'dTmin': 5,             # minimum temperature difference °C
        'h': 0.2,               # Heat transfer coefficient kW/m²K
        'costs': 0.005*24*52*7, # specific energy costs per year €/kWh/y # FIXME: ist für testzwecke auf einen sehr hohen wert gestellt
    }
}

# Cold internal utilities
conversion_units['UIC'] = {
    'District heating': {
        'Tin': 70,               # Inlet Temperature °C
        'Tout': 80,             # Outlet Temperature °C
        'dTmin': 5,             # minimum temperature difference °C
        'h': 0.2,               # Heat transfer coefficient kW/m²K
        'costs': -0.005*24*52*7, # specific energy costs per year €/kWh/y # FIXME: ist für testzwecke auf einen sehr hohen wert gestellt
    }
}

# Hot internal utilities
conversion_units['CU'] = {
    'Compression Heat Pump': {
        'Tmax': 120,            # Maximum Condenser Temperature °C
        'Tmin': 30,             # Minimum Evaporator Temperature °C
        'dTmin': 5,             # minimum temperature difference °C
        'eta_c': 0.5,           # Carnot efficiency factor
        'dT lift max': 70,      # maximum Temperature lift °C
        'dT lift min': 30,      # minimum temperature difference °C
        'h': 0.2,               # Heat transfer coefficient kW/m²K
        'phase change': 1,      # determines whether a phase change takes place in the HEX
        'costs': 0.1*24*52*7/10,  # specific electricity costs per year €/kWh/y #fixme: muss angepasst werden, nur für testzwecke so niedrig
    },
    'Two-Tank Storage': {
        'Tmax': 100,            # Maximum Condenser Temperature °C
        'Tmin': 30,             # Minimum Evaporator Temperature °C
        'dTmin': 5,             # minimum temperature difference °C
        'dT lift min': 30,      # minimum temperature difference °C
        'h': 0.2,               # Heat transfer coefficient kW/m²K
        'phase change': 0,      # determines whether a phase change takes place in the HEX
        'costs var': 0.3*24,    # specific storage costs €/kg  #fixme: muss angepasst werden, nur für testzwecke so niedrig
        'costs fix': 25000,     # step fixed storage costs €  #fixme: muss angepasst werden, nur für testzwecke so niedrig
        'annualization': 20,    # years for annualization
    }
}

########################################################################################################################
#    set existing HEX
########################################################################################################################

retrofit = {
    'existing HEX': {
        'UH': {
            1: {'location': (0, 8, 1), 'area': 100},
        },
        'Direct': {
            1: {'location': (1, 6, 3), 'area': 1000},
            2: {'location': (2, 8, 2), 'area': 1000}
        },
    }
}

for u in conversion_units.keys():
    data_input['indices'][u] = [tuple((i, 1)) for i in range(len(conversion_units[u]))]

########################################################################################################################
#    Calculations
########################################################################################################################

model = HENS.HENS(settings, data_input, targ, conversion_units, retrofit)

result = model.solve(600)

# opt = pyomo.environ.SolverFactory('cplex')
# result = opt.solve(model, warmstart=False, tee=True, timelimit=60)


########################################################################################################################
#    Control
########################################################################################################################
set_values = 0
A_check = actual_values.A_actual(model, set_values)
for u in list(model.coeffs['A_beta_x']['type'].unique()):
    print(u + ' ------------------')
    print(A_check[u])
    print()
# if 'CUH' in list(model.coeffs['A_beta_x']['type'].unique()):
#     if 'Compression Heat Pump' in model.conversion_units['CU']['Name'].values:
#         checks.check_COP(demand)
#         checks.check_lin(demand)

set_values = 1
actual_values.A_actual(model, set_values)

########################################################################################################################
#    Plots
########################################################################################################################

# Plots.plots.plot_CCs(demand, 'GCCs', 1, 1, 1)
# Plots.plots.plot_CCs(demand, 'CCs', 1, 1, 1)
Plots.plots.plot_HEN(model)
Plots.plots.plot_Costs(model, model.model)
Plots.plots.plot_HR(model, model.model)