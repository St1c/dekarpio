
import numpy as np
import pandas as pd
import sys
import os
import pickle
import pyomo.environ as pyo
import matplotlib.pyplot as plt

PACKAGE_PARENT = '../..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
sys.path

import pi_framework.DOOM.classes as dc
import pi_framework.DOOM.auxiliary as da

def run_case():
    print('import finished')
    # Get Data
    n_tsp = 24

    df = pd.DataFrame()
    per1 = 1 + np.sin(np.linspace(0, 2 * np.pi, n_tsp))
    per2 = 2 + np.sin(np.linspace(0, 2 * 2 * np.pi, n_tsp))
    per3 = 3 + np.sin(np.linspace(0, 3 * 2 * np.pi, n_tsp))

    df['per1'] = per1
    df['per2'] = per2
    df['per3'] = per3

    set_period = ['per1', 'per1', 'per1', 'per1', 'per1', 'per2', 'per2',
                  'per1', 'per1', 'per1', 'per1', 'per1', 'per2', 'per2',
                  'per1', 'per1', 'per1', 'per1', 'per1', 'per2', 'per2',
                  'per3', 'per3', 'per3', 'per3', 'per3', 'per2', 'per2',
                  'per3', 'per3', 'per3', 'per3', 'per3', 'per2', 'per2',
                  'per1', 'per2', 'per3', 'per1', 'per2', 'per3', 'per3',
                  ]

    # set_period = list()
    # for i in range(50):
    #     b = 0.2
    #     rand = (1-b) * np.random.random() + b + b/2 * np.sin(i/364*2*np.pi)
    #     if rand > 2/3:
    #         set_period.append('per1')
    #     elif rand > 1/3:
    #         set_period.append('per2')
    #     else:
    #         set_period.append('per3')

    sum_weight = len(set_period)
    u_w_dict = dict()
    for i in df.keys():
        u_w_dict[i] = [set_period.count(i) / sum_weight, set_period.count(i)]

    # Create system and ConcreteModel

    sysParam = {'sc': u_w_dict, 'tss': 1, 'n_ts_sc': 24, 'interest_rate': 0.05, 'depreciation_period': 10,
                'opt': {
                    'timelimit': 60,
                }, 'seq': dict()}

    j = 'demand'
    sysParam['seq'][j] = dict()
    for i in u_w_dict.keys():
        sysParam['seq'][j][i] = df[i].values

    j = 'price_gas'
    sysParam['seq'][j] = dict()
    for i in u_w_dict.keys():
        sysParam['seq'][j][i] = np.ones(sysParam['n_ts_sc']) * 40

    res = dc.System(sysParam)

    # Units

    # Gas Boiler
    tempParam = {
        'classname': 'GasBoiler',
        'name': 'gb1',
        'lim_q': (0.2, 1),
        # proportional limits for q in MW, second entry is optional and induces commitment binary variable
        'lim_f': (0.2/0.7, 1 / 0.9),  # relative limits to q for f in MW, second entry is optional
        'cap_q': (0, 10),  # capacity limits for q in MW, first and second entry are optional
        'inv_var': 600000 * (1 + 0.0325 * sysParam['depreciation_period']),  # €/MW
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

    # period storage
    tempParam = {
        'classname': 'PeriodStorage',
        'name': 'ps',
        'cap_soc': (0, 100000),
        'set_period': set_period,
        'exists': True,
        'lim_c/d': (10, 10),
        'eta_c/d': (1, 1),
        'loss_soc': 0.001,  # relative losses proportional to soc per hour
        'inv_var': 50 * (1 + 0.01 * sysParam['depreciation_period']),
        'inv_fix': 0,
    }
    res.add_unit(tempParam)
    print('tes steam defined')

    # Demand
    tempParam = {
        'classname': 'HeatDemand',
        'name': 'demand',
        'seq': sysParam['seq']['demand'],
        'T_in': (150,),
        'T_out': (120,),
        'pressure': 2 * 1e5,
        'medium': 'Water',
    }
    res.add_unit(tempParam)

    # Gas Supply
    tempParam = {
        'classname': 'Supply',
        'name': 'supply_gas',
        'seq': sysParam['seq']['price_gas'],
        'cap_s': (0, 10),
        'cost_max_s': 3800,
    }
    res.add_unit(tempParam)

    # NODES ----------------------------------------------------------------------
    # Steam
    tempParam = {
        'classname': 'Node',
        'name': 'node_steam',
        'lhs': [['gb1', 'q'], ['ps', 'd']],
        'rhs': [['demand', 'q'], ['ps', 'c']],
        'type': '==',
    }
    res.add_node(tempParam)

    # Gas
    tempParam = {
        'classname': 'Node',
        'name': 'node_fuel',
        'lhs': [['supply_gas', 's']],
        'rhs': [['gb1', 'f']],
        'type': '==',
    }
    res.add_node(tempParam)

    res.build_model()

    # Additional Constraints

    res = da.solve_model(res)

    da.plot_unit_port(res)

    da.plot_node_slack(res)

    unit_port = {
        'gb1': 'q',
    }

    da.plot_full_load_hours(res, unit_port)

    unit = {
        'MW': ['gb1'],
    }

    da.plot_time_series(res)

    unit = ['gb1', 'ps']
    da.plot_unit_inv_cost(res, unit)

    plt.figure()
    plt.plot(list(res.unit['ps'].var['seq']['soc_p'][:].value))

    TAC_total = pyo.value(res.obj['total_real'])
    TAC_gas = pyo.value(res.unit['supply_gas'].obj['total'])
    TAC_inv = sum(pyo.value(res.unit[n].obj['inv']) for n in res.unit if 'inv' in res.unit[n].obj)

    period_ordered = []
    for i in set_period:
        period_ordered = np.concatenate([period_ordered, df[i].values])

    plt.figure()
    plt.plot(period_ordered)

    soc_ordered = []
    for i, n in enumerate(set_period):
        soc_ordered = np.concatenate([soc_ordered, res.unit['ps'].var['seq']['soc_p'][i].value + np.asarray(list(res.unit['ps'].var['seq']['soc'][n, :].value))])

    plt.figure()
    plt.plot(soc_ordered)
    plt.show()

    print('TAC_total: %20.2f' % TAC_total)
    print('TAC_gas:   %20.2f' % TAC_gas)
    print('TAC_inv:   %20.2f' % TAC_inv)


if __name__ == '__main__':
    run_case()
