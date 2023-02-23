import json
import time

# import pandas as pd
import numpy as np
import pyomo.environ as pyo
import classes as dc
import auxiliary as da
import CoolProp.CoolProp as CP

def read_timelines(path):
    with open(path) as f:
        all = json.load(f)
    with open('tool_dekarpio_timeline_map.json') as f:
        timeline_map = json.load(f)
    timelines = all['Medoid-Zeitreihen']

    labels = all['Label-Sequenz']

    def delete_minus_one(d):
        d2 = d.copy()
        for key in d.keys():
            if d[key] == -1:
                del d2[key]
        return d2

    labels = delete_minus_one(labels)
    label_list = [str(x) for x in labels.values()]
    period_list = [str(x) for x in np.unique(label_list)]

    no_timesteps = 0
    for day in timelines:
        for k in day.values():
            if len(k) > no_timesteps:
                no_timesteps = len(k)

    return timelines, period_list, label_list, no_timesteps, timeline_map


def return_results_dict(system, filepath=None):
    resultsdict = {}
    resultsdict.update({'objectives': {}})
    for ok, ov in system.obj.items():
        resultsdict['objectives'].update({ok: pyo.value(ov)})
    resultsdict.update({'units': {}})
    for uk, uv in system.unit.items():
        resultsdict['units'].update({uk: {}})
        resultsdict['units'][uk].update({#'param': uv.param,
                                        'obj': {},
                                        'var': {'seq': {},
                                                'scalar': {}}
                                        })
        for ok, ov in uv.obj.items():
            resultsdict['units'][uk]['obj'].update({ok: pyo.value(ov)})
        if 'seq' in uv.var.keys():
            for vk, vv in uv.var['seq'].items():
                resultsdict['units'][uk]['var']['seq'].update({vk: {}})
                periods = []
                tempdict = vv.get_values()
                # todo: get periods from global parameters or timeline info
                for tuple_ in tempdict.keys():
                    if isinstance(tuple_, tuple) and len(tuple_) == 2:          # syntax (period_name, time_step)
                        periods.append(str(tuple_[0]))
                    elif isinstance(tuple_, tuple) and len(tuple_) == 3:        # syntax (period_name, time_step, level)
                        periods.append(str(tuple_[0]))
                    elif isinstance(tuple_, int):        # syntax (period_number) --> soc_p from period storages
                        periods.append(str(tuple_))
                    else:
                        raise TypeError('Unknown Variable type {} in unit {} (classname {}). Check input file.'.format(
                            vk, uk, uv.param['classname']
                        ))
                periods = set(periods)
                for period in periods:
                    resultsdict['units'][uk]['var']['seq'][vk].update({period: {}})
                    resultsdict['units'][uk]['var']['seq'][vk][period].update({'timesteps': [],
                                                                               'values': []})
                for tuple_, value in tempdict.items():
                    if isinstance(tuple_, tuple) and len(tuple_) == 2:         # syntax (period_name, time_step)
                        period = str(tuple_[0])
                        timestep = tuple_[1]
                        resultsdict['units'][uk]['var']['seq'][vk][period]['timesteps'].append(timestep)
                        resultsdict['units'][uk]['var']['seq'][vk][period]['values'].append(value)
                    elif isinstance(tuple_, int):
                        resultsdict['units'][uk]['var']['seq'][vk][period]['values'].append(value)

        if 'scalar' in uv.var.keys():
            for vk, vv in uv.var['scalar'].items():
                resultsdict['units'][uk]['var']['scalar'].update({vk: vv.value})

    resultsdict.update({'nodes': {}})
    for nk, nv in system.node.items():
        resultsdict['nodes'].update({nk: {}})
        resultsdict['nodes'][nk].update({'lhs': {},
                                         'rhs': {}})

        for side in ['lhs', 'rhs']:
            for j in nv.param[side]:
                [unit_name, port, _] = j
                unit_port_name = unit_name + '_' + port
                resultsdict['nodes'][nk][side].update({unit_port_name: {}})

                periods = []
                tempdict = system.unit[unit_name].port[port].get_values()
                for tuple_ in tempdict.keys():
                    periods.append(str(tuple_[0]))
                periods = set(periods)
                for period in periods:
                    resultsdict['nodes'][nk][side][unit_port_name].update({period: {}})
                    resultsdict['nodes'][nk][side][unit_port_name][period].update({'timesteps': [],
                                                                                   'values': []})
                for tuple_, value in tempdict.items():
                    period = str(tuple_[0])
                    timestep = tuple_[1]
                    resultsdict['nodes'][nk][side][unit_port_name][period]['timesteps'].append(timestep)
                    resultsdict['nodes'][nk][side][unit_port_name][period]['values'].append(value)

            pass

    if filepath == None:
        return resultsdict
    else:
        with open(filepath, 'w') as f:
            json.dump(resultsdict, f, indent=2)


def get_active_units(system):
    caps = ['cap_s', 'cap_p', 'cap_q', 'cap_q_sink', 'cap_soc', 'cap_area']
    units_active = {}
    for unit in system.unit:
        if 'coupler' not in unit:
            if any(x in unit for x in ['eso', 'ecu', 'esu']):
                for param_name, param in system.unit[unit].param.items():
                    if param_name in caps and param[1] > 0:
                        units_active.update({unit: param})
            elif 'dem' in unit:
                if max(max(day) for day in system.unit[unit].param['seq'].values()) > 0:
                    units_active.update({unit:
                                             max(max(day) for day in system.unit[unit].param['seq'].values())})
    return units_active


def print_active_units(system):
    active_units = get_active_units(system)
    strings = [list(active_units.keys())[i] + ': ' + str(list(active_units.keys())[i])
               for i in range(len(active_units))]
    print("""Active units are:
    {}""".format("\n    ".join(strings))
          )


def print_active_nodes(system):
    active_nodes = []
    active_nodes_max_vals = []
    for node_name, node in system.node.items():
        if any(
            any(var.get_values()>0) for var in node.param[side] for side in ['lhs', 'rhs']
        ):
            active_nodes.append(node_name)
            active_nodes_max_vals.append(max())


def read_structure(path):
    with open(path, 'r') as f:
        structure = json.load(f)
    return structure


def read_parameters(param_dict, period_list, label_list, no_timesteps):
    # ==================================================================================================================
    # HELPER FUNCTIONS
    # ==================================================================================================================
    def check_integrate_steam_level():
        if steam_dict['param'][0]['integrate'] == "True":
            return True
        else:
            return False

    # ==================================================================================================================
    # FUNCTION BODY
    # ==================================================================================================================
    sum_weight = len(label_list)        # days per year

    u_w_dict = dict()
    for i in period_list:
        no_of_occurrences = label_list.count(i)
        u_w_dict[i] = [no_of_occurrences / sum_weight, no_of_occurrences]     # [weight, nr. of occurances]

    sysParam = {#'cf': 1000,  # conversion factor for coefficient scaling (Energy, Power)
        #'cf_co2': 0.23,  # conversion factor for kg co2/kWh
        'set_period': period_list,
        'scenario': 0,
        'seq': [],#seq,
        'sc': u_w_dict,  # sc: unique scenario/period - period name: [weight, nr. of occurances]
        'tss': 24 / no_timesteps,  # tss: timestep length in hours
        'n_ts_sc': no_timesteps,  # n_ts_sc: nr. of timesteps per scenario/period

        'interest_rate': 0.0,               # from global parameters
        'depreciation_period': 10,          # from global parameters
        'opt': {'timelimit': 600,
                'optimality_gap': 0.00},
        'expansion_costs': 5e4      # todo: €/MW ???
    }


    steam_parameters = {}
    for steam_key, steam_dict in param_dict.items():

        if check_integrate_steam_level():
            ## entries from .json hash
            steam_level_name = steam_dict['param'][0]['description']
            steam_level_dict = ({
                # --- :             steam_dict['name']                      # is not relevant
                # --- :             steam_dict['type']                      # is not relevant
                # --- :             steam_dict['ID']                        # is not relevant
                # --- :             steam_dict['inp']                       # is not relevant
                'temperature':      steam_dict['param'][0]['temp'],         # deg Celsius
                'pressure':         steam_dict['param'][0]['pressure'] * 1e5    # Pascal
            })

            steam_parameters.update({steam_level_name: steam_level_dict})

    sysParam.update(dict(steam_parameters=steam_parameters))

    return sysParam


def initialize_model(sysParam):
    tic = time.time()
    res = dc.System(sysParam)
    toc = time.time()
    out_str = "Initialized model in {:.2f} seconds.".format(toc-tic)
    return out_str, res


def add_units_and_nodes(system, structure, tl, tl_map):
    # ==================================================================================================================
    # HELPER FUNCTIONS
    # ==================================================================================================================
    def add_supplies(sys, supply_dict, tl, tl_map):
        # ==================================================================================================================
        # HELPER FUNCTIONS
        # ==================================================================================================================
        def check_eso_integration(temp_param):
            if not esoobj['param'][0]['integrate'] == "True":
                for cap in ['cap_s', 'cap_area']:
                    if cap in temp_param.keys():
                        temp_param[cap] = (0, 0)

        def get_eso_classname(eso_object):
            if eso_object['param'][0]['description'] in ["electricity pv", "electricity ppa pv"]:
                return "Photovoltaic"
            else:
                return "Supply"

        def parse_eso_type(name_string, eso_object, temp_param):
            eso_param = eso_object['param'][0]

            if name_string == 'Photovoltaic':
                temp_param.update({
                    ## entries from .json hash
                    'cap_area':     (0, eso_param['lim_technical']),  # maximum available area for PV in m^2
                    'eta':          0.2                               # standard value
                })
                if eso_param['description'] == 'electricity ppa pv':
                    temp_param.update({
                        'ppa_mode': 1,
                        # 'cap_existing':   eso_param['lim_actual'],      # todo: implement this for PV?
                        'inv_fix': 0,  # has to be zero for PV
                        'inv_var': 0,  # has to be zero for PV
                        # --- :             eso_param['inv_energy']       # todo: implement this for PV?

                    })
                elif eso_param['description'] == 'electricity pv':
                    temp_param.update({
                        # 'cap_existing':   eso_param['lim_actual'],      # todo: implement this for PV?
                        'inv_fix':          eso_param['inv_fix'],         # should be zero for PV
                        'inv_var':          eso_param['inv_power'],       # should be in €/m^2 for PV (see example_case)
                        # --- :             eso_param['inv_energy']       # todo: implement this for PV?
                    })

            elif name_string == 'WindTurbine':
                temp_param.update({
                    ## entries from .json hash
                    # --- :                    # class not implemented yet
                })

            elif name_string == 'Supply':
                temp_param.update({
                    'cost_max_ex':             sys.param['expansion_costs'],  # inv_var in .json, €/MW Zubau
                    'cost_fix_ex':             0,                                # todo: inv_fix in .json hinzufügen (Sophie?); Fixkosten wenn zugebaut wird
                    'cap_s':                   (0, esoparam['lim_technical']),   #
                    'cap_existing':            esoparam['lim_actual']            #


                })
        # ==================================================================================================================
        # FUNCTION BODY
        # ==================================================================================================================
        for esoobj in supply_dict.values():
            classname = get_eso_classname(esoobj)

            esoparam = esoobj['param'][0]

            tempParam = {
                'classname': classname,  # energy sources are energy supplies
                'seq': {},  # filled in the loop below

                ## entries from .json hash
                # --- :                    esoobj['name']                 # is not relevant
                'energy_type':             esoobj['type'],                # probably not relevant
                'name':                    esoobj['ID'],

                # --- :                    esoparam['integrate']          # used in check_eso_integration function
                # --- :                    esoparam['grid']               # is not relevant
                # --- :                    esoparam['energy']             # used in the loop below
                # --- :                    esoparam['lim_technical']      # handled in parse_eso_type
                # --- :                    esoparam['lim_actual']         # handled in parse_eso_type
                # --- :                    esoparam['inv_fix']            # handled in parse_eso_type
                # --- :                    esoparam['inv_power']          # handled in parse_eso_type
                'grid_energy':              esoparam['grid_energy']
            }

            mapkey = tl_map[esoobj['ID']]
            # todo: in timelines esostring, esoobj['name'] or esoobj['ID']?
            # todo: tl mit key "timeline_map[esoobj['ID']]" abspeichern/einlesen anstatt Umweg über timeline_map

            for period_no, period_dict in enumerate(tl):
                period_str = str(period_no)
                fee_costs = 10      #todo automatisieren aus json input (loop ueber grid_energy)
                energy_costs = np.array(tl[period_no][mapkey]) * esoparam['energy']    # scaling normalized timeline values
                tempParam['seq'].update({
                    period_str: fee_costs + energy_costs
                })

            parse_eso_type(classname, esoobj, tempParam)

            check_eso_integration(tempParam)

            sys.add_unit(tempParam)

        return sys

    def add_energy_conversion_units(sys, unit_dict):        # todo: add input output info to params
        # ==================================================================================================================
        # HELPER FUNCTIONS
        # ==================================================================================================================
        def check_ecu_integration(temp_param):
            if ecuobj['param'][0]['integrate'] == "False":
                for cap in ['cap_p', 'cap_q', 'cap_q_sink']:
                    if cap in temp_param.keys():
                        temp_param[cap] = (0, 0)

        def get_ecu_classname(ecu_object):
            if ecu_object['description'] == "solid boiler":
                return "GasBoiler"
            elif ecu_object['description'] == "single-/multi-fuel-boiler":
                return "GasBoiler"
            elif ecu_object['description'] == "gas turbine":
                return "GasTurbine"
            elif ecu_object['description'] == "backpressure steam turbine":
                return "BackPressureSteamTurbine"
            elif ecu_object['description'] == "water heat pump":
                return "HeatPump"
            elif ecu_object['description'] == "steam heat pump":
                return "HeatPump"
            elif ecu_object['description'] == "condensation steam turbine":
                return "CondensingSteamTurbine"
            else:
                raise TypeError('Unknown Energy Conversion Unit. Check the input file.')

        def parse_ecu_type(name_string, ecu_object, temp_param):
            ecu_param = ecu_object['param'][0]

            if name_string == 'GasBoiler':
                temp_param.update({
                    ## entries from .json hash
                    'cap_q': (ecu_param['min_capacity'],  #
                              ecu_param['max_capacity']),  #
                    'lim_q': (ecu_param['minload'] / 100, 1),  #
                    'lim_f': ((ecu_param['minload'] / 100) / (ecu_param['minload_efficiency'] / 100),
                              1 / (ecu_param['fullload_efficiency'] / 100)),

                    ## other entries needed for unit definition
                    'T_in': 40,  # minimum uptime/downtime in hours, induces commitment binary variable
                    'T_out': 160,  # minimum uptime/downtime in hours, induces commitment binary variable
                    'pressure': 5.5e5,  # minimum uptime/downtime in hours, induces commitment binary variable
                    'medium': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
                })

            elif name_string == 'GasTurbine':
                temp_param.update({
                    ## entries from .json hash
                    'cap_p': (ecu_param['min_capacity'],  #
                              ecu_param['max_capacity']),  #
                    'lim_p': (ecu_param['minload'] / 100, 1),  #
                    'lim_f': ((ecu_param['minload'] / 100) / (ecu_param['minload_efficiency'] / 100),
                              1 / (ecu_param['fullload_efficiency'] / 100)),

                    ## other entries needed for unit definition
                    # --- none
                })

            elif name_string == 'BackPressureSteamTurbine':
                temp_param.update({
                    ## entries from .json hash
                    'cap_p': (ecu_param['min_capacity'],  #
                              ecu_param['max_capacity']),  #
                    'lim_p': (ecu_param['minload'] / 100, 1),  #
                    'lim_q_in': (ecu_param['minload'] / 100 / (ecu_param['minload_efficiency'] / 100),
                                 1 / (ecu_param['fullload_efficiency'] / 100)),  #
                    ## other entries needed for unit definition
                    'eta_th': 0.9       # todo how to handle minload_efficiency, fullload_efficiency, eta???
                })

            elif name_string == 'CondensingSteamTurbine':
                temp_param.update({
                    ## entries from .json hash
                    'cap_p': (ecu_param['min_capacity'],  #
                              ecu_param['max_capacity']),  #
                    'lim_p': (ecu_param['minload'] / 100, 1),  #
                    'lim_q_in': (ecu_param['minload'] / 100 / (ecu_param['minload_efficiency'] / 100),
                                 1 / (ecu_param['fullload_efficiency'] / 100)),  #

                    ## other entries needed for unit definition
                    'T_cond': 50,
                    'T_in': 200,
                    'P_in': 10,
                    'eta_el': 0.38      # todo how to handle minload_efficiency, fullload_efficiency, eta???
                })
            elif name_string == 'HeatPump':
                temp_param.update({
                    ## entries from .json hash
                    'cap_q_sink': (ecu_param['min_capacity'],  # note: min_capacity does nothing in DOOM
                                   ecu_param['max_capacity']),  #
                    # --- :                    ecuparam['minload']            # todo add_op_lim?
                    'eta_comp': (ecu_param['fullload_efficiency']/100,  # class definition needs two values & makes
                                 ecu_param['fullload_efficiency']/100),  # two COPs. Why?
                    # --- :                    ecuparam['minload_efficiency'] # todo class needs to adapted to accept this

                    ## other entries needed for unit definition
                    'lim_q_sink': (0, 1),
                    'T_sink_in': (80,),  #
                    'T_sink_out': 120,  # m
                    'T_source_in': (50,),
                    'T_source_out': 30,
                    'delta_T_sink': (7, 7),  # one value for each side of the heat exchanger
                    'delta_T_source': (7, 7),  # one value for each side of the heat exchanger
                    'pressure_sink': 200000,  # minimum uptime/downtime in hours, induces commitment binary variable
                    'pressure_source': 200000,  # minimum uptime/downtime in hours, induces commitment binary variable
                    'medium_sink': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
                    'medium_source': 'Water',  # minimum uptime/downtime in hours, induces commitment binary variable
                })

        # ==================================================================================================================
        # FUNCTION BODY
        # ==================================================================================================================
        for ecuobj in unit_dict.values():
            classname = get_ecu_classname(ecuobj)

            ecuparam = ecuobj['param'][0]
            tempParam = {
                'classname': classname,  #
                'name': ecuobj['ID'],  # todo: ecustring, ecuobj['name'] or ecuobj['ID']?

                ## entries from .json hash
                # --- :         ecuobj['name']              # is not relevant
                # --- :         ecuobj['type']              # is not relevant
                # --- :         ecuobj['description']       # is used by method get_ecu_classname
                # --- :         ecuobj['ID']                # is not relevant

                'exists':       ecuparam['exist'],          # if it exists, inv costs are set to zero
                # --- :         ecuparam['integrate']       # is used by check_ecu_integration function
                'ramp': (ecuparam['ramp'],
                         ecuparam['ramp']),  #
                'min_utdt_ts': (ecuparam['min_on'],
                                ecuparam['min_off']),  #
                'max_susd': (ecuparam['start_up'],  #
                             ecuparam['shut_down']),  #
                'inv_fix': ecuparam['inv_fix'],  #
                'inv_var': ecuparam['inv_cap'],  #
                # --- :         ecuparam['opex_main']       # todo add to doom
                'opex_fix': ecuparam['opex_fix'],  # [€/Betriebsstunde]
                'cost_susd': (ecuparam['opex_start'], 0),  # [€/Startvorgang] todo: needs to be added
            }

            parse_ecu_type(classname, ecuobj, tempParam)

            check_ecu_integration(tempParam)

            sys.add_unit(tempParam)

        return sys

    def add_demands(sys, process_dict, tl, tl_map):
        # ==================================================================================================================
        # HELPER FUNCTIONS
        # ==================================================================================================================
        def get_input_type(element):
            string = element.split('_')[-1]
            map = {'nga': 'gas', 'mis2': 'mis', 'los2': 'los', 'his2': 'his', 'ele2': 'ele'}
            return map[string]

        def check_process_integration(max_p):
            if not processobj['param'][0]['integrate'] == "True":
                return 0.0
            else:
                return max_p

        def get_output_type(element):
            return element.split('_')[-1]

        def calc_waste_heat_q(medium, mass_flow, temp, pressure):
            # mass flow in kg/s
            # temp in degC
            # pressure in bar absolute
            # output in MW
            cp = dict({'hua': CP.HAPropsSI('Cha', 'T', temp + 273.15, 'P', pressure * 1e5, 'R', 1),
                       'owh': CP.PropsSI('C', 'T', temp + 273.15, 'P', pressure * 1e5, 'Water')})
            return mass_flow * (temp-0) * cp[medium] / 1e6

        # ==================================================================================================================
        # FUNCTION BODY
        # ==================================================================================================================
        for processstr, processobj in process_dict.items():
            # todo: how to integrate days_off into timelines? periods are set beforehand?
            # todo: make timelines for waste heat, humid air --> positive or negative demands? depends +/- sign in node?
            for demandstr, demandobj in processobj['inp'].items():
                input_element = demandobj['element']
                input_name = processobj['ID'] + '_' + demandstr
                input_type = get_input_type(input_element)
                input_max_p_string = 'p_' + input_type + '_max'
                input_max_p = processobj['param'][0][input_max_p_string]
                tempParam = {
                    'classname': 'Demand',
                    'name': input_name,
                    'seq': {},
                    # note: inputs are saved one level lower than in other units (for example ecu)
                    'inp': processobj['inp'][demandstr]
                }

                max_p = check_process_integration(input_max_p)

                mapkey = tl_map[input_name]
                # todo: in timelines esostring, esoobj['name'] or esoobj['ID']?
                # todo: tl mit key "timeline_map[esoobj['ID']]" abspeichern/einlesen anstatt Umweg über timeline_map

                for period_no, period_dict in enumerate(tl):
                    period_str = str(period_no)
                    tempParam['seq'].update({
                        period_str: np.array(tl[period_no][mapkey]) * max_p
                        # todo: in timelines processstr, processobj['name'] or processobj['ID']?
                    })
                sys.add_unit(tempParam)

            for pseudodemandstr, pseudodemandobj in processobj['out'].items():
                output_element = pseudodemandobj['element']
                output_type = get_output_type(output_element)
                output_name = processobj['ID'] + '_' + pseudodemandstr
                try:
                    pressure = processobj['param'][0]['pressure_' + output_type]
                except KeyError:
                    pressure = 1.01325
                output_max_p = calc_waste_heat_q(
                    output_type,
                    processobj['param'][0]['massflow_'+output_type],
                    processobj['param'][0]['temp_' + output_type],
                    pressure
                )
                tempParam = {
                    'classname': 'Demand',
                    'name': output_name,
                    'seq': {},
                    # note: inputs are saved one level lower than in other units (for example ecu)
                    # note: is input saving necessary?
                    'out': processobj['out'][pseudodemandstr]
                }

                max_p = check_process_integration(output_max_p)
                mapkey = tl_map[output_name]

                for period_no, period_dict in enumerate(tl):
                    period_str = str(period_no)
                    tempParam['seq'].update({
                        period_str: np.array(tl[period_no][mapkey]) * max_p
                        # todo: in timelines processstr, processobj['name'] or processobj['ID']?
                    })
                sys.add_unit(tempParam)

        return sys

    def add_storage_units(sys, storage_dict):
        # ==================================================================================================================
        # HELPER FUNCTIONS
        # ==================================================================================================================
        def check_esu_integration(tempParam):
            if not esuobj['param'][0]['integrate'] == "True":
                for cap in ['cap_soc']:
                    if cap in tempParam.keys():
                        tempParam[cap] = (0, 0)

        def get_esu_classname(esuobj):
            if esuobj['description'] == "battery for electricity storing":
                return "Storage"
            elif esuobj['description'] == "steam storage":
                return "Storage"
            elif esuobj['description'] == "hot water storage":
                return "Storage"
            elif esuobj['description'] == "warm water storage":
                return "Storage"
            else:
                raise TypeError('Unknown Energy Storage Unit. Check the input file.')

        def parse_esu_type(sys, classname, esuobj, tempParam):
            esuparam = esuobj['param'][0]

            if classname == 'PeriodStorage':
                tempParam.update({
                    ## entries from .json hash
                    # --- :                 esuparam['integrate']       # is used by check_esu_integration function
                    'exists': esuparam['exist'],  # if it exists, inv costs are set to zero
                    'cap_soc': (esuparam['cap_min'],  # note: min_capacity does nothing in DOOM
                                esuparam['cap_max']),  #
                    'lim_soc': (esuparam['soc_min']/100, 1),  # minimum and maximum state of charge in %
                    'lim_c/d': (esuparam['power_max'],
                                esuparam['power_max']),
                    'eta_c/d': (esuparam['eta_char']/100,  # todo: needs to be added
                                esuparam['eta_dis']/100),
                    'loss_soc': (100-esuparam['eta_stor'])/100,  # todo: in json: 99, in metadata unit %loss/hr?
                    'inv_fix': esuparam['inv_fix'],  #
                    'inv_var': esuparam['invest_cap'],  #
                    # --- :                 esuparam['inv_power']       # todo class or da.add_inv needs to be adapted

                    ## other entries needed for unit definition
                    'set_period': sys.param['set_period']  # todo: should be given by timelines
                })

            elif classname == 'PeriodStorageSimple_CETES':
                tempParam.update({
                    ## entries from .json hash
                    # --- :                 esuparam['integrate']       # is used by check_esu_integration function
                    'exists': esuparam['exist'],  # if it exists, inv costs are set to zero
                    'cap_soc': (esuparam['cap_min'],  # note: min_capacity does nothing in DOOM
                                esuparam['cap_max']),  #
                    'lim_soc': (esuparam['soc_min']/100, 1),  # minimum and maximum state of charge in %
                    'lim_c/d': (esuparam['power_max'],
                                esuparam['power_max']),
                    'eta_c/d': (esuparam['eta_char']/100,  # todo: needs to be added
                                esuparam['eta_dis']/100),
                    'loss_soc': (100-esuparam['eta_stor'])/100,  # todo: in json: 99, in metadata unit %loss/hr?
                    'inv_fix': esuparam['inv_fix'],  #
                    'inv_var_cap': esuparam['invest_cap'],  #
                    'inv_var_load': esuparam['inv_power'],       # todo class or da.add_inv needs to be adapted

                    ## other entries needed for unit definition
                    'set_period': sys.param['set_period']  # todo: should be given by timelines
                })

            elif classname == 'Storage':
                tempParam.update({
                    ## entries from .json hash
                    # --- :                 esuparam['integrate']       # is used by check_esu_integration function
                    'exists': esuparam['exist'],  # if it exists, inv costs are set to zero
                    'cap_soc': (esuparam['cap_min'],  # note: min_capacity does nothing in DOOM
                                esuparam['cap_max']),  #
                    'lim_soc': (esuparam['soc_min']/100, 1),  # minimum and maximum state of charge in %
                    'lim_c/d': (esuparam['power_max'],
                                esuparam['power_max']),
                    'eta_c/d': (esuparam['eta_char']/100,  # todo: needs to be added
                                esuparam['eta_dis']/100),
                    'loss_soc': (100-esuparam['eta_stor'])/100,  # todo: in json: 99, in metadata unit %loss/hr?
                    'inv_fix': esuparam['inv_fix'],  #
                    'inv_var': esuparam['invest_cap'],  #
                    # --- :                 esuparam['inv_power']       # todo class or da.add_inv needs to be adapted

                    ## other entries needed for unit definition
                })
        # ==================================================================================================================
        # FUNCTION BODY
        # ==================================================================================================================
        for esustring, esuobj in storage_dict.items():
            classname = get_esu_classname(esuobj)

            tempParam = {
                'classname': classname,  #
                'name': esuobj['ID'],  # todo: ecustring, ecuobj['name'] or ecuobj['ID']?

                ## entries from .json hash
                # --- :                    esuobj['name']                 # is not relevant
                # --- :                    esuobj['type']                 # is not relevant
                # --- :                    esuobj['description']          # is used by method get_esu_classname
                # --- :                    esuobj['ID']                   # is not relevant
                'inp':                     esuobj['inp'],
                'out':                     esuobj['out'],
            }

            parse_esu_type(sys, classname, esuobj, tempParam)

            check_esu_integration(tempParam)

            sys.add_unit(tempParam)

        return sys

    def add_nodes(sys, struct):
        # ==============================================================================================================
        # HELPER FUNCTIONS
        # ==============================================================================================================
        def get_eso_out_port(eso_name):
            if sys.unit[eso_name].param['classname'] == 'Supply':
                return 's'
            elif sys.unit[eso_name].param['classname'] == 'Photovoltaic':
                return 'p'

        def get_ecu_in_ports(ecu_name):
            if sys.unit[ecu_name].param['classname'] == 'GasBoiler':
                return dict({'fuel': 'f'})
            elif sys.unit[ecu_name].param['classname'] == 'GasTurbine':
                return dict({'fuel': 'f'})
            elif sys.unit[ecu_name].param['classname'] == 'BackPressureSteamTurbine':
                return dict({'heat': 'q_in'})
            elif sys.unit[ecu_name].param['classname'] == 'CondensingSteamTurbine':
                return dict({'heat': 'q_in'})
            elif sys.unit[ecu_name].param['classname'] == 'HeatPump':
                return dict({'heat': 'q_source', 'power': 'p'})

        def get_ecu_out_ports(ecu_name):
            if sys.unit[ecu_name].param['classname'] == 'GasBoiler':
                return dict({'heat': 'q'})
            elif sys.unit[ecu_name].param['classname'] == 'GasTurbine':
                return dict({'heat': 'q', 'power': 'p'})
            elif sys.unit[ecu_name].param['classname'] == 'BackPressureSteamTurbine':
                return dict({'heat': 'q_out', 'power': 'p'})
            elif sys.unit[ecu_name].param['classname'] == 'CondensingSteamTurbine':
                return dict({'heat': 'q_out', 'power': 'p'})
            elif sys.unit[ecu_name].param['classname'] == 'HeatPump':
                return dict({'heat': 'q_sink'})

        def get_collector_type(collector_name):
            if any([x in collector_name for x in ['lis', 'his', 'mis', 'los', 'owh', 'hua']]):
                return 'heat'
            elif any([x in collector_name for x in ['ele']]):
                return 'power'
            else:
                KeyError('Unknown collector type {}. Check input file.'.format(
                    collector_name
                ))

        def get_eso_type(eso_name):
            if struct['eso'][eso_name.split('_')[1]]['type'] == 'gaseous':
                return 'fuel'
            elif struct['eso'][eso_name.split('_')[1]]['type'] == 'liquid':
                return 'fuel'
            elif struct['eso'][eso_name.split('_')[1]]['type'] == 'solid':
                return 'fuel'
            elif struct['eso'][eso_name.split('_')[1]]['type'] == 'electricity':
                return 'power'
            elif struct['eso'][eso_name.split('_')[1]]['type'] == 'heat':
                return 'heat'
            else:
                KeyError('Unknown energy source type {}. Check input file.'.format(
                    struct['eso'][eso_name]['type']
                ))

        def get_storage_type(esu_name):
            if any([x in esu_name for x in ['ste', 'how', 'wwa']]):
                return 'heat'
            elif any([x in esu_name for x in ['bat']]):
                return 'power'
            else:
                KeyError('Unknown storage type {}. Check input file.'.format(
                    esu_name
                ))

        # ==============================================================================================================
        # FUNCTION BODY
        # ==============================================================================================================

        # ----
        # make list of all node IDs - this needs to be done more or less by hand!
        nodes = {}
        # 1 out node for each energy source - distributes to conversion units, demands, collectors, storage units
        for eso in struct['eso']:
            eso_name = struct['eso'][eso]['ID']
            eso_out_port = get_eso_out_port(eso_name)
            node_name = eso_name + '_out_node'
            nodes.update({node_name: {
                'lhs': [[eso_name, eso_out_port]],
                'rhs': [],
                'type': '=='
            }})

        # 1 node for each collector
        for col in struct['col']:
            node_name = struct['col'][col]['ID'] + '_node'
            nodes.update({node_name: {
                'lhs': [],
                'rhs': [],
                'type': '=='
            }})

        # 1 in node for each conversion unit - collects from energy source (fuel, power) or collector
        # (electricity, steam for turbines)
        for ecu in struct['ecu']:
            ecu_name = struct['ecu'][ecu]['ID']
            ecu_in_ports = get_ecu_in_ports(ecu_name)
            for port_type, port_name in ecu_in_ports.items():
                node_name = ecu_name + '_' + port_type + '_in_node'
                nodes.update({node_name: {
                    'lhs': [],
                    'rhs': [[ecu_name, port_name]],
                    'type': '=='
                }})

        # 1 out node for each conversion unit - distributes to other conversion units (steam),
        # collectors (steam, power), and demands
        for ecu in struct['ecu']:
            ecu_name = struct['ecu'][ecu]['ID']
            ecu_out_ports = get_ecu_out_ports(ecu_name)
            for port_type, port_name in ecu_out_ports.items():
                node_name = ecu_name + '_' + port_type + '_out_node'
                nodes.update({node_name: {
                    'lhs': [[ecu_name, port_name]],
                    'rhs': [],
                    'type': '=='
                }})

        # 1 in node for each storage unit - collects from sources, conversion units, collectors
        for esu in struct['esu']:
            esu_name = struct['esu'][esu]['ID']
            esu_in_port = 'c'
            node_name = esu_name + '_in_node'
            nodes.update({node_name: {
                'lhs': [],
                'rhs': [[esu_name, esu_in_port]],
                'type': '=='
            }})

        # 1 out node for each storage unit - distributes to conversion units, collectors, pseudo-sources (district heat)
        # collectors (steam, power), and demands
        for esu in struct['esu']:
            esu_name = struct['esu'][esu]['ID']
            esu_out_port = 'd'
            node_name = esu_name + '_out_node'
            nodes.update({node_name: {
                'lhs': [[esu_name, esu_out_port]],
                'rhs': [],
                'type': '=='
            }})

        # 1 in node for each demand - collects from collectors and conversion units (steam turbines, gas turbines)
        for processstr, processobj in struct['dem'].items():

            # these are real demands -- consume energy from other units
            for demandstr, demandobj in processobj['inp'].items():
                input_name = processobj[
                                 'ID'] + '_' + demandstr  # note: this has to shadow the method in add_demands()
                node_name = input_name + '_in_node'
                input_in_port = 'd'
                nodes.update({node_name: {
                    'lhs': [],
                    'rhs': [[input_name, input_in_port]],
                    'type': '=='
                }})

            # these are pseudo demands -- provide waste heat to other units (i.e. negative demand)
            for pseudodemandstr, pseudodemandobj in processobj['out'].items():
                output_name = processobj[
                                  'ID'] + '_' + pseudodemandstr # note: this has to shadow the method in add_demands()
                node_name = output_name + '_in_node'            # note: "in node" to keep naming system intact
                output_in_port = 'd'
                nodes.update({node_name: {
                    'lhs': [],
                    'rhs': [[output_name, output_in_port]],
                    'type': '<='
                }})

        # ----
        # make couplers where n-to-n connections need to be made, but classes only allow 1-to-n or n-to-1 connections
        # currently for eso-to-ecu, eso-to-col, ecu-to-ecu, ecu-to-col
        for con_name, con_obj in struct['con'].items():
            _, left, right = con_obj['ID'].split('-')
            if 'eso' in left:
                eso_type = get_eso_type(left)
                # connector which connects an energy source with other units/collectors. Make a coupler from the energy
                # source's out node to right side
                if 'ecu' in right:
                    # coupler goes from the energy source's out node to the conversion unit's in node
                    eso_out_node_name = left + '_out_node'
                    ecu_in_node_name = right + '_' + eso_type + '_in_node'
                    coupler_name = 'coupler_' + eso_out_node_name + '_to_' + ecu_in_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [eso_out_node_name],
                        'out': [ecu_in_node_name]
                    })
                    # find energy source's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + eso_out_node_name
                    nodes[eso_out_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find conversion unit's in node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + ecu_in_node_name
                    nodes[ecu_in_node_name]['lhs'].append([coupler_name, out_port_name])

                elif 'col' in right:
                    # coupler goes from the energy source's out node to the collector, e.g. steam or electricity
                    eso_out_node_name = left + '_out_node'
                    col_node_name = right + '_node'
                    coupler_name = 'coupler_' + eso_out_node_name + '_to_' + col_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [eso_out_node_name],
                        'out': [col_node_name]
                    })
                    # find energy source's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + eso_out_node_name
                    nodes[eso_out_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find collector node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + col_node_name
                    nodes[col_node_name]['lhs'].append([coupler_name, out_port_name])

                elif 'esu' in right:
                    # coupler goes from the energy source's out node to energy storage unit, e.g. hot water
                    eso_out_node_name = left + '_out_node'
                    esu_in_node_name = right + '_in_node'
                    coupler_name = 'coupler_' + eso_out_node_name + '_to_' + esu_in_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [eso_out_node_name],
                        'out': [esu_in_node_name]
                    })
                    # find energy source's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + eso_out_node_name
                    nodes[eso_out_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find collector node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + esu_in_node_name
                    nodes[esu_in_node_name]['lhs'].append([coupler_name, out_port_name])

                elif 'dem' in right:
                    # coupler goes from the energy source's out node directly to the demand. Only for natural gas
                    _, mid, _ = right.split('_')
                    for inpstr, inpobj in struct['dem'][mid]['inp'].items():
                        if left in inpobj['element']:                        # this is the right port for the gas supply
                            # note: this has to shadow the naming convention in add_nodes()
                            inp_name = struct['dem'][mid]['ID'] + '_' + inpstr
                    eso_out_node_name = left + '_out_node'
                    dem_in_node_name = inp_name + '_in_node'
                    coupler_name = 'coupler_' + eso_out_node_name + '_to_' + dem_in_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [eso_out_node_name],
                        'out': [dem_in_node_name]
                    })
                    # find energy source's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + eso_out_node_name
                    nodes[eso_out_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find demand node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + dem_in_node_name
                    nodes[dem_in_node_name]['lhs'].append([coupler_name, out_port_name])

                else:
                    raise KeyError('Connector {} does not match model logic. Check input file'.format(
                        con_name
                    ))

            elif 'ecu' in left:
                # connector which connects an energy source with other units/collectors. Make a coupler from the energy
                # source's out node to right side
                if 'col' in right:
                    # coupler goes from the conversion unit's out node to the collector, e.g. steam or electricity
                    collector_type = get_collector_type(right)
                    ecu_out_node_name = left + '_' + collector_type + '_out_node'
                    col_node_name = right + '_node'
                    coupler_name = 'coupler_' + ecu_out_node_name + '_to_' + col_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [ecu_out_node_name],
                        'out': [col_node_name]
                    })
                    # find conversion unit's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + ecu_out_node_name
                    nodes[ecu_out_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find collector node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + col_node_name
                    nodes[col_node_name]['lhs'].append([coupler_name, out_port_name])

                elif 'ecu' in right:
                    # coupler goes from the conversion unit's out node to another conversion unit's in node, e.g. gas turbine
                    # power output to heat pump power input
                    coupler_name = 'coupler_' + left + '_out_node_to_' + right + '_in_node'
                    # is a steam turbine, therefore take the q port
                    if any([x in right for x in ['lis', 'his', 'mis', 'los']]):
                        ecu_out_node_name = left + 'q_out_node'
                    elif 'ele' in right:  # is an electricity collector, therefore take the p port
                        ecu_out_node_name = left + 'p_out_node'
                    else:
                        raise KeyError('Connector {} does not match model logic. Check input file'.format(
                            con_name
                        ))
                    col_node_name = right + '_node'
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [ecu_out_node_name],
                        'out': [col_node_name]
                    })
                    # find conversion unit's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + ecu_out_node_name
                    nodes[ecu_out_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find conversion unit's in node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + col_node_name
                    nodes[col_node_name]['lhs'].append([coupler_name, out_port_name])

                elif 'esu' in right:
                    # coupler goes from the conversion unit's out node to energy storage unit, e.g. hot water
                    storage_type = get_storage_type(right)
                    eso_out_node_name = left + '_' + storage_type + '_out_node'
                    esu_in_node_name = right + '_in_node'
                    coupler_name = 'coupler_' + eso_out_node_name + '_to_' + esu_in_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [eso_out_node_name],
                        'out': [esu_in_node_name]
                    })
                    # find energy source's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + eso_out_node_name
                    nodes[eso_out_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find collector node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + esu_in_node_name
                    nodes[esu_in_node_name]['lhs'].append([coupler_name, out_port_name])

                elif 'eso' in right:
                    # coupler goes from the conversion unit's out node to pseudo source, e.g. a demand with defined price over time

                    # eso only has one type, therefore gives information about the type of port (power, heat, ...)
                    eso_type = get_eso_type(right)
                    ecu_out_node_name = left + '_' + eso_type + '_out_node'

                    # note: although it's a pseudo source, its node is named "out node" as with all other sources
                    eso_out_node_name = right + '_out_node'

                    coupler_name = 'coupler_' + ecu_out_node_name + '_to_' + eso_out_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [ecu_out_node_name],
                        'out': [eso_out_node_name]
                    })
                    # find conversion unit's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + ecu_out_node_name
                    nodes[ecu_out_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find eso node name; appended to rhs although it is not a real energy source
                    out_port_name = 'out_' + eso_out_node_name
                    nodes[eso_out_node_name]['rhs'].append([coupler_name, out_port_name])

                else:
                    raise KeyError('Connector {} does not match model logic. Check input file'.format(
                        con_name
                    ))

            elif 'col' in left:
                if 'col' in right:
                    # make coupler between two collectors
                    left_col_node_name = left + '_node'
                    right_col_node_name = right + '_node'
                    coupler_name = 'coupler_' + left_col_node_name + '_to_' + right_col_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [left_col_node_name],
                        'out': [right_col_node_name]
                    })
                    # find first collector's node name and add coupler's incoming part to right hand side
                    in_port_name = 'in_' + left_col_node_name
                    nodes[left_col_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find second collector's node name and add coupler's outgoing part to left hand side
                    out_port_name = 'out_' + right_col_node_name
                    nodes[right_col_node_name]['lhs'].append([coupler_name, out_port_name])

                elif 'ecu' in right:
                    collector_type = get_collector_type(left)

                    # note: boiler class needs to be adapted to accept electricity/power input
                    if 'boi' in right or 'sbo' in right:
                        collector_type = 'fuel'

                    col_node_name = left + '_node'
                    ecu_in_node_name = right + '_' + collector_type + '_in_node'
                    coupler_name = 'coupler_' + col_node_name + '_to_' + ecu_in_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [col_node_name],
                        'out': [ecu_in_node_name]
                    })
                    # find collector's node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + col_node_name
                    nodes[col_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find collector node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + ecu_in_node_name
                    nodes[ecu_in_node_name]['lhs'].append([coupler_name, out_port_name])

                elif 'esu' in right:
                    # coupler goes from the collector's out node to energy storage unit, e.g. steam
                    col_node_name = left + '_node'
                    esu_in_node_name = right + '_in_node'
                    coupler_name = 'coupler_' + col_node_name + '_to_' + esu_in_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [col_node_name],
                        'out': [esu_in_node_name]
                    })
                    # find collector's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + col_node_name
                    nodes[col_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find collector node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + esu_in_node_name
                    nodes[esu_in_node_name]['lhs'].append([coupler_name, out_port_name])

                elif 'dem' in right:
                    # coupler goes from the energy source's out node directly to the demand. Only for natural gas
                    _, mid, _ = right.split('_')
                    for inpstr, inpobj in struct['dem'][mid]['inp'].items():
                        if left in inpobj['element']:  # this is the right port for the
                            inp_name = struct['dem'][mid][
                                           'ID'] + '_' + inpstr  # note: this has to shadow the method in add_nodes()
                    col_node_name = left + '_node'
                    dem_in_node_name = inp_name + '_in_node'
                    coupler_name = 'coupler_' + col_node_name + '_to_' + dem_in_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [col_node_name],
                        'out': [dem_in_node_name]
                    })
                    # find collector's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + col_node_name
                    nodes[col_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find demand node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + dem_in_node_name
                    nodes[dem_in_node_name]['lhs'].append([coupler_name, out_port_name])

                elif 'eso' in right:
                    # coupler goes from the collector's node to pseudo source, e.g. a demand with defined price over time
                    col_node_name = left + '_node'
                    # note: although it's a pseudo source, its node is named "out node" as with all other sources
                    eso_out_node_name = right + '_out_node'
                    coupler_name = 'coupler_' + col_node_name + '_to_' + eso_out_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [col_node_name],
                        'out': [eso_out_node_name]
                    })
                    # find conversion unit's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + col_node_name
                    nodes[col_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find eso node name; appended to rhs although it is not a real energy source
                    out_port_name = 'out_' + eso_out_node_name
                    nodes[eso_out_node_name]['rhs'].append([coupler_name, out_port_name])

                else:
                    raise KeyError('Connector {} does not match model logic. Check input file'.format(
                        con_name
                    ))

            elif 'esu' in left:
                if 'ecu' in right:
                    esu_out_node_name = left + '_out_node'
                    storage_type = get_storage_type(left)
                    ecu_in_node_name = right + '_' + storage_type + '_in_node'
                    coupler_name = 'coupler_' + esu_out_node_name + '_to_' + ecu_in_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [esu_out_node_name],
                        'out': [ecu_in_node_name]
                    })
                    # find storage unit's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + esu_out_node_name
                    nodes[esu_out_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find conversion unit's in node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + ecu_in_node_name
                    nodes[ecu_in_node_name]['lhs'].append([coupler_name, out_port_name])

                elif 'col' in right:
                    # coupler goes from the storage unit's out node to the collector, e.g. steam or electricity
                    esu_out_node_name = left + '_out_node'
                    col_node_name = right + '_node'
                    coupler_name = 'coupler_' + esu_out_node_name + '_to_' + col_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [esu_out_node_name],
                        'out': [col_node_name]
                    })
                    # find conversion unit's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + esu_out_node_name
                    nodes[esu_out_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find collector node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + col_node_name
                    nodes[col_node_name]['lhs'].append([coupler_name, out_port_name])

                elif 'eso' in right:
                    # coupler goes from the storage unit's out node to pseudo source, e.g. a demand with defined price over time
                    esu_out_node_name = left + '_out_node'

                    # note: although it's a pseudo source, its node is named "out node" as with all other sources
                    eso_out_node_name = right + '_out_node'

                    coupler_name = 'coupler_' + esu_out_node_name + '_to_' + eso_out_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [esu_out_node_name],
                        'out': [eso_out_node_name]
                    })
                    # find conversion unit's out node and add coupler's incoming port to right hand side
                    in_port_name = 'in_' + esu_out_node_name
                    nodes[esu_out_node_name]['rhs'].append([coupler_name, in_port_name])
                    # find eso node name; appended to rhs although it is not a real energy source
                    out_port_name = 'out_' + eso_out_node_name
                    nodes[eso_out_node_name]['rhs'].append([coupler_name, out_port_name])

                else:
                    raise KeyError('Connector {} does not match model logic. Check input file'.format(
                        con_name
                    ))

            elif 'dem' in left:
                # pseudo-demand (= excess heat)
                if 'col' in right:
                    _, dem, _ = left.split('_')
                    _, _, typ = right.split('_')
                    out_name = None
                    for outstr, outobj in struct['dem'][dem]['out'].items():
                        if typ in outobj['element']:  # this is the right port for the
                            out_name = struct['dem'][dem][
                                           'ID'] + '_' + outstr
                    # note: although it is a pseudo demand, called output, the node is named "in node"
                    if not out_name:
                        raise KeyError('Type {} not found in process output.'.format(typ))
                    dem_in_node_name = out_name + '_in_node'
                    col_node_name = right + '_node'
                    coupler_name = 'coupler_' + dem_in_node_name + '_to_' + col_node_name
                    sys.add_unit({
                        'classname': 'Coupler',
                        'name': coupler_name,
                        'in': [dem_in_node_name],
                        'out': [col_node_name]
                    })
                    # find pseudo demand's in node and add coupler's incoming port to left hand side
                    # other way around compared the way it usually works
                    in_port_name = 'in_' + dem_in_node_name
                    nodes[dem_in_node_name]['lhs'].append([coupler_name, in_port_name])
                    # find demand node and add coupler's outgoing port to left hand side
                    out_port_name = 'out_' + col_node_name
                    nodes[col_node_name]['lhs'].append([coupler_name, out_port_name])

                else:
                    raise KeyError('Connector {} does not match model logic. Check input file'.format(
                        con_name
                    ))
            else:
                raise KeyError('Connector {} does not match model logic. Check input file'.format(
                    con_name
                ))

        for node, node_dict in nodes.items():
            sys.add_node({
                'classname': 'Node',
                'name': node,
                'lhs': node_dict['lhs'],
                'rhs': node_dict['rhs'],
                'type': node_dict['type']
            })

        return sys

    # # ==================================================================================================================
    # # FUNCTION BODY
    # # ==================================================================================================================

    tic = time.time()
    # READ ENERGY SOURCES FROM .JSON
    system = add_supplies(system, structure['eso'], tl, tl_map)
    # READ ENERGY CONVERSION UNITS FROM .JSON
    system = add_energy_conversion_units(system, structure['ecu'])
    # READ ENERGY DEMANDS FROM .JSON
    system = add_demands(system, structure['dem'], tl, tl_map)
    # READ ENERGY STORAGE UNITS FROM .JSON
    system = add_storage_units(system, structure['esu'])
    # ADD NODES BASED ON CONNECTORS
    system = add_nodes(system, structure)
    toc = time.time()

    out_str = "Added units and nodes in {:.2f} seconds.".format(toc-tic)

    return out_str, system


def build_pyomo_model(system: dc.System):
    tic = time.time()
    system.build_model()
    toc = time.time()
    out_str = "Built model in {:.2f} seconds.".format(toc-tic)
    return out_str, system


def solve_pyomo_model(system: dc.System):
    tic = time.time()
    solver = 'highs'
    system = da.solve_model(system, solver=solver)
    toc = time.time()
    out_str = "Solved model with {} in {:.2f} seconds.".format(solver, toc-tic)
    return out_str, system

# # ==================================================================================================================
# # ==================================================================================================================
# # FUNCTION BODY
# # ==================================================================================================================
# with open(path) as f:
#     structure = json.load(f)
#
# sum_weight = len(label_list)        # days per year
#
# u_w_dict = dict()
# for i in period_list:
#     no_of_occurrences = label_list.count(i)
#     u_w_dict[i] = [no_of_occurrences / sum_weight, no_of_occurrences]     # [weight, nr. of occurances]
#
# # ==================================================================================================================
# # PARAMETER DEFINITION - TO BE REPLACED BY CLEAN PARAMETER IMPORT FROM .JSON FILE
# # ==================================================================================================================
#
# sysParam = {#'cf': 1000,  # conversion factor for coefficient scaling (Energy, Power)
#     #'cf_co2': 0.23,  # conversion factor for kg co2/kWh
#     'set_period': period_list,
#     'scenario': 0,
#     'seq': [],#seq,
#     'sc': u_w_dict,  # sc: unique scenario/period - period name: [weight, nr. of occurances]
#     'tss': 24 / no_timesteps,  # tss: timestep length in hours
#     'n_ts_sc': no_timesteps,  # n_ts_sc: nr. of timesteps per scenario/period
#
#     'interest_rate': 0.0,               # from global parameters
#     'depreciation_period': 10,          # from global parameters
#     'opt': {'timelimit': 600,
#             'optimality_gap': 0.01},
#     'expansion_costs': 5e4      # todo: €/MW ???
# }
#
# res = dc.System(sysParam)
#
# tic = time.time()
# # READ PARAMETERS FROM .JSON
# read_parameters(structure['par'])
# # READ ENERGY SOURCES FROM .JSON
# add_supplies(res, timelines, structure['eso'])
# # READ ENERGY CONVERSION UNITS FROM .JSON
# add_energy_conversion_units(res, structure['ecu'])
# # READ ENERGY DEMANDS FROM .JSON
# add_demands(res, timelines, structure['dem'])
# # READ ENERGY STORAGE UNITS FROM .JSON
# add_storage_units(res, structure['esu'])              # todo: add input output info to params
# toc = time.time()
# print("""
# Reading and adding units took {:.2f} seconds.
# """.format(toc-tic))
#
# # note: this is to create nodes by hand
# tic = time.time()
# add_nodes()
# toc = time.time()
# print("""
# Adding nodes took {:.2f} seconds.
# """.format(toc - tic))
#
# tic = time.time()
# res.build_model()
# toc = time.time()
# print("""
# Building the pyomo model took {:.2f} seconds.
# """.format(toc - tic))
#
# return res
