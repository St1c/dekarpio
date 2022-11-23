import pandas as pd
import numpy as np
import scipy.linalg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import cloudpickle
import os
import sys
import time
import warnings
import pyomo.environ as pyo
import delfort_system_simple
import delfort_system


PACKAGE_PARENT = '../../..'
PACKAGE_PARENT = ''
DOOM_DIR = 'pi_framework'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT, DOOM_DIR)))
import DOOM.classes as dc
import DOOM.auxiliary as da


def run_case():

    scenario_nr = 0

    # OPTIMIZATION
    # ==================================================================================================================
    # ==================================================================================================================

    # ==================================================================================================================
    # General settings
    # ==================================================================================================================

    settings = {
        'optimization type': 'linear',  # 'linear', 'quadratic'
        'time limit': 18000,
    }

    # ==================================================================================================================
    # Prepare Case-Study
    # ==================================================================================================================

    timeseries = delfort_system_simple.make_simple_timeseries(scenario_nr)

    # DOOM -------------------------------------------------------------------------------
    print('import finished')

    sum_weight = 1
    u_w_dict = dict()
    period_list = [1]
    for i in period_list:
        u_w_dict[i] = [1 / sum_weight, 1]

    # Get Data
    seq = dict()
    for j in timeseries.columns.to_list()[3:]:
        seq[j] = dict()
        for i in u_w_dict.keys():
            seq[j][i] = timeseries.loc[timeseries['period'] == i][j].values

    sysParam = {'cf': 1000,  # conversion factor for coefficient scaling (Energy, Power)
                #'cf_co2': 0.23,  # conversion factor for kg co2/kWh
                # 'set_period': period_list,
                'scenario': scenario_nr,
                'seq': seq,
                'sc': u_w_dict,  # sc: unique scenario/period - period name: [weight, nr. of occurances]
                'tss': 0.25,  # tss: timestep
                'n_ts_sc': len(timeseries),  # n_ts_sc: nr. of timesteps per scenario/period

                'interest_rate': 0.0,
                'depreciation_period': 10,
                'opt': {
                    'timelimit': settings['time limit'],
                }
                }

    # ==================================================================================================================
    # ENERGY SYSTEM
    # ==================================================================================================================

    # generate energy system
    tic = time.perf_counter()
    res, units, unit_port, units_energy_plot = delfort_system_simple.build_system(sysParam)
    toc = time.perf_counter()
    print(f"System building took {toc - tic:0.4f} seconds")

    # ==================================================================================================================
    # Solve
    # ==================================================================================================================
    tic = time.perf_counter()
    res = da.solve_model(res)
    toc = time.perf_counter()
    da.write_full_results(res, 'long_res.txt')
    da.write_results_summary(res, 'short_res.txt')
    print(f"Solving took {toc - tic:0.4f} seconds")


    # ==================================================================================================================
    # Visualize
    # ==================================================================================================================

    scenario_folder_path = os.path.join(os.getcwd(), 'S' + str(scenario_nr))
    with open(os.path.join(scenario_folder_path, 'results.cp'), 'wb') as f:
        cloudpickle.dump(res, f)

    da.plot_unit_port(res)
    fig2 = da.plot_unit_sizes(res, units)
    fig2.savefig(os.path.join(scenario_folder_path, 'Figure_2.png'))
    da.plot_full_load_hours(res, unit_port)
    da.plot_strat_soc(res, 'ssml1')
    da.plot_energy(res, units_energy_plot)
    # da.plot_node(res)
    # da.plot_nodes_from_list(res, ['node_h2', 'node_gas', 'node_biomass', 'node_biogas'])
    # da.plot_nodes_from_list(res, ['node_gb2_fuel', 'node_gb3_fuel', 'node_gt1_fuel', 'node_hrb1_fuel'])
    fig6 = da.plot_nodes_from_list(res, ['node_steam_demand_2', 'node_steam_turbine_in', 'node_hrb1_heat'])
    fig6.savefig(os.path.join(scenario_folder_path, 'Figure_6.png'))
    fig7 = da.plot_nodes_from_list(res, ['node_electricity', 'node_gas', 'node_h2'])
    fig7.savefig(os.path.join(scenario_folder_path, 'Figure_7.png'))
    # da.plot_nodes_from_list(res, ['node_q_hthp1', 'node_q_mvr1', 'node_hthp_source_heat', 'node_lthp_source_heat'])
    plt.show()
    pass


if __name__ == '__main__':
    run_case()
