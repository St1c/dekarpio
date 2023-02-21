import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import cloudpickle
from matplotlib import gridspec
import pyomo.environ as pyo
from pathlib import Path


def init_uvwi_param(unit):
    unit.param['u_active'] = False
    unit.param['v_w_active'] = False
    unit.param['i_active'] = False

    # opex_fix
    if 'opex_fix' in unit.param:
        if unit.param['opex_fix'] > 0:
            unit.param['u_active'] = True

    # cost_susd
    if 'cost_susd' in unit.param:
        if unit.param['cost_susd'][0] > 0 or unit.param['cost_susd'][1] > 0:
            unit.param['u_active'] = True
            unit.param['v_w_active'] = True

    # min_utdt_ts
    if 'min_utdt_ts' in unit.param:
        if unit.param['min_utdt_ts'][0] > 1 or unit.param['min_utdt_ts'][1] > 1:
            unit.param['u_active'] = True
            unit.param['v_w_active'] = True

    # inv_fix
    if 'inv_fix' in unit.param: #ist klar - sobald es fixe invests gibt braucht man i_active
        if unit.param['inv_fix'] > 0:
            unit.param['i_active'] = True

    # exists
    if 'exists' in unit.param:  # bin mir nicht sicher ob das stimmt
        if unit.param['exists']:
            unit.param['i_active'] = True


def set_general_param(system, unit):
    if 'depreciation_period' not in unit.param:
        unit.param['depreciation_period'] = system.param['depreciation_period']
    if 'interest_rate' not in unit.param:
        unit.param['interest_rate'] = system.param['interest_rate']


def add_var_to_model(system, unit):
    if 'seq' in unit.var.keys():
        for v in unit.var.get('seq'):
            namestr = 'var_' + unit.name + '_' + v
            system.model.add_component(namestr, unit.var['seq'][v])
    if 'scalar' in unit.var.keys():
        for v in unit.var.get('scalar'):
            namestr = 'var_' + unit.name + '_' + v
            system.model.add_component(namestr, unit.var['scalar'][v])


def add_var_uvwi(system, unit):
    if unit.param['u_active']:
        unit.var['seq']['u'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.Binary)
    if unit.param['v_w_active']:
        unit.var['seq']['v'] = pyo.Var(system.model.set_sc, system.model.set_t, bounds=(0, 1))
        unit.var['seq']['w'] = pyo.Var(system.model.set_sc, system.model.set_t, bounds=(0, 1))
    if unit.param['i_active']: #pre-requisite: i-active has been activated above in init_uvwi
        if 'exists' in unit.param:  # is exists in dictionary? --> yes: go ahead, no: go to else
            if unit.param['exists']:    # is key true or false --> true: i is fixed on 1, otherwise 0-1
                unit.var['scalar']['i'] = pyo.Var(bounds=(1, 1))
            else:
                unit.var['scalar']['i'] = pyo.Var(bounds=(0, 1)) #why not binary? wir vermuten dass bei False das nicht richtig is
        else: #if unit has no exist in dictionary --> binary needed
            unit.var['scalar']['i'] = pyo.Var(domain=pyo.Binary) #todo if unit param i active --> letzte zeile, dann if exitst true --> bounds auf 1

def add_var_a_v(unit):
    if 'a_req' in unit.param:
        unit.var['scalar']['area'] = pyo.Var(domain=pyo.NonNegativeReals)
    if 'v_req' in unit.param:
        unit.var['scalar']['volume'] = pyo.Var(domain=pyo.NonNegativeReals)

def add_con_a_v(unit, depend=None):
    dependency = 'cap'

    if depend is not None:
        dependency = depend

    if 'a_req' in unit.param:
        def con_rule(m):
            return unit.var['scalar']['area'] == unit.var['scalar']['i']*unit.param['a_req'][0] + unit.var['scalar'][dependency]*unit.param['a_req'][1]

        namestr = 'a_req'
        unit.con[namestr] = pyo.Constraint(rule=con_rule)

    if 'v_req' in unit.param:
        def con_rule(m):
            return unit.var['scalar']['volume'] == unit.var['scalar']['i']*unit.param['v_req'][0] + unit.var['scalar'][dependency]*unit.param['v_req'][1]

        namestr = 'v_req'
        unit.con[namestr] = pyo.Constraint(rule=con_rule)


def add_logic_uvw(system, unit):
    if unit.param['u_active'] and unit.param['v_w_active']:
        def con_rule(m, s, t):
            return unit.var['seq']['u'][s, np.mod(t + 1, len(system.model.set_t))] - unit.var['seq']['u'][s, t] == \
                   unit.var['seq']['v'][s, np.mod(t + 1, len(system.model.set_t))] - unit.var['seq']['w'][
                       s, np.mod(t + 1, len(system.model.set_t))]

        namestr = 'logic'
        unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)
        add_min_utdt(system, unit)  # is needed if add_logic_uvw is needed


def add_simple_m_q(system, unit):
    def con_rule(m, s, t):
        return unit.var['seq']['q'][s, t] == unit.var['seq']['m'][s, t] * (
            unit.param['h_out'] - unit.param['h_in']) / 1e6

    namestr = 'm_q'
    unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


def add_cap_lim(unit, varname):
    if unit.param['i_active']:
        for n in varname:
            def con_rule(m):
                if 'i' in unit.var['scalar'].keys():
                    return unit.var['scalar']['cap'] <= unit.var['scalar']['i'] * unit.param['cap_' + n][1]
                else:
                    return unit.var['scalar']['cap'] <= unit.param['cap_' + n][1]

            namestr = 'cap_' + n + '_max'
            unit.con[namestr] = pyo.Constraint(rule=con_rule)

            def con_rule(m):
                if 'i' in unit.var['scalar'].keys():
                    return unit.var['scalar']['cap'] >= unit.var['scalar']['i'] * unit.param['cap_' + n][0]
                else:
                    return unit.var['scalar']['cap'] >= unit.param['cap_' + n][0]

            namestr = 'cap_' + n + '_min'
            unit.con[namestr] = pyo.Constraint(rule=con_rule)
    else: #for non i-active units --> inv_fix must not be alligned to a value
        for n in varname:
            def con_rule(m):
                return unit.var['scalar']['cap'] <= unit.param['cap_' + n][1]

            namestr = 'cap_' + n + '_max'
            unit.con[namestr] = pyo.Constraint(rule=con_rule)

            def con_rule(m):
                return unit.var['scalar']['cap'] >= unit.param['cap_' + n][0]

            namestr = 'cap_' + n + '_min'
            unit.con[namestr] = pyo.Constraint(rule=con_rule)


def add_op_lim(system, unit, varname):
    for n in varname:
        if unit.param['u_active'] and unit.param['v_w_active']:
            # q <= c * LIM_U
            def con_rule(m, s, t):
                return unit.var['seq'][n][s, t] <= unit.var['scalar']['cap'] * unit.param['lim_' + n][1]

            namestr = n + '_max1'
            unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

            # q <= u * C_MAX*LIM_U
            def con_rule(m, s, t):
                return unit.var['seq'][n][s, t] <= unit.var['seq']['u'][s, t] * unit.param['cap_' + n][1] * \
                       unit.param['lim_' + n][1]

            namestr = n + '_max2'
            unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

            # q <= c * MAX_SU + (1 - v) * C_MAX * (LIM_U - MAX_SU)
            def con_rule(m, s, t):
                return unit.var['seq'][n][s, t] <= unit.var['scalar']['cap'] * unit.param['max_susd'][0] + (
                    1 - unit.var['seq']['v'][s, t]) * unit.param['cap_' + n][1] * (
                           unit.param['lim_' + n][1] - unit.param['max_susd'][0])

            namestr = n + '_max3'
            unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

            # q <= c * MAX_SD + (1 - w) * C_MAX * (LIM_U - MAX_SD)
            def con_rule(m, s, t):
                return unit.var['seq'][n][s, t] <= unit.var['scalar']['cap'] * unit.param['max_susd'][1] + (
                    1 - unit.var['seq']['w'][s, np.mod(t + 1, len(system.model.set_t))]) * unit.param['cap_' + n][
                           1] * (unit.param['lim_' + n][1] - unit.param['max_susd'][1])

            namestr = n + '_max4'
            unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

            # q >= c * LIM_L - (1 - u) * C_MAX*LIM_L
            def con_rule(m, s, t):
                return unit.var['seq'][n][s, t] >= unit.var['scalar']['cap'] * unit.param['lim_' + n][0] - (
                    1 - unit.var['seq']['u'][s, t]) * unit.param['cap_' + n][1] * unit.param['lim_' + n][0]

            namestr = n + '_min1'
            unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

            # q >= 0
            def con_rule(m, s, t):
                return unit.var['seq'][n][s, t] >= 0

            namestr = n + '_min2'
            unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        elif unit.param['u_active']:
            def con_rule(m, s, t):
                return unit.var['scalar']['cap'] * unit.param['lim_' + n][0] - (1 - unit.var['seq']['u'][s, t]) * \
                       unit.param['lim_' + n][0] * unit.param['cap_' + n][1] <= unit.var['seq'][n][s, t]

            namestr = n + '_min1'
            unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

            def con_rule(m, s, t):
                return 0 <= unit.var['seq'][n][s, t]

            namestr = n + '_min2'
            unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

            def con_rule(m, s, t):
                return unit.var['seq'][n][s, t] <= unit.var['scalar']['cap']

            namestr = n + '_max1'
            unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

            def con_rule(m, s, t):
                return unit.var['seq'][n][s, t] <= unit.var['seq']['u'][s, t] * unit.param['lim_' + n][1] * \
                       unit.param['cap_' + n][1]

            namestr = n + '_max2'
            unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        else:
            def con_rule(m, s, t):
                return unit.var['seq'][n][s, t] >= 0

            namestr = n + '_min'
            unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

            def con_rule(m, s, t):
                return unit.var['scalar']['cap'] >= unit.var['seq'][n][s, t]

            namestr = n + '_max'
            unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


def add_ramp_con(system, unit, varname):
    for n in varname:
        if unit.param.get('ramp_' + n):
            if unit.param['v_w_active']:
                # q_t+1 - q_t <= R * TAU * c + (MAX_SU * C_MAX) * v
                def con_rule(m, s, t):
                    return unit.var['seq'][n][s, np.mod(t + 1, len(system.model.set_t))] - unit.var['seq'][n][s, t] <= \
                           unit.param['ramp_' + n][0] * system.param['tss'] * unit.var['scalar']['cap'] + (
                               unit.param['max_susd'][0] * unit.param['cap_' + n][1]) * unit.var['seq']['v'][s, t]

                namestr = 'ramp_up1_' + n
                unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

                # q_t+1 - q_t <= MAX_SU * c
                def con_rule(m, s, t):
                    return unit.var['seq'][n][s, np.mod(t + 1, len(system.model.set_t))] - unit.var['seq'][n][s, t] <= \
                           unit.param['max_susd'][0] * unit.var['scalar']['cap']

                namestr = 'ramp_up2_' + n
                unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

                # q_t - q_t+1 <= R * TAU * c + (MAX_SD * C_MAX) * w
                def con_rule(m, s, t):
                    return - unit.var['seq'][n][s, np.mod(t + 1, len(system.model.set_t))] + unit.var['seq'][n][s, t] <= \
                           unit.param['ramp_' + n][1] * system.param['tss'] * unit.var['scalar']['cap'] + (
                               unit.param['max_susd'][1] * unit.param['cap_' + n][1]) * unit.var['seq']['w'][
                               s, np.mod(t + 1, len(system.model.set_t))]

                namestr = 'ramp_down1_' + n
                unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

                # q_t - q_t+1 <= MAX_SD * c
                def con_rule(m, s, t):
                    return - unit.var['seq'][n][s, np.mod(t + 1, len(system.model.set_t))] + unit.var['seq'][n][s, t] <= \
                           unit.param['max_susd'][1] * unit.var['scalar']['cap']

                namestr = 'ramp_down2_' + n
                unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)
            else:
                # q_t+1 - q_t <= R * TAU * c
                def con_rule(m, s, t):
                    return unit.var['seq'][n][s, np.mod(t + 1, len(system.model.set_t))] - unit.var['seq'][n][s, t] <= \
                           unit.param['ramp_' + n][0] * system.param['tss'] * unit.var['scalar']['cap']

                namestr = 'ramp_up1_' + n
                unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

                # q_t+1 - q_t <= MAX_SU * c
                def con_rule(m, s, t):
                    return unit.var['seq'][n][s, np.mod(t + 1, len(system.model.set_t))] - unit.var['seq'][n][s, t] <= \
                           unit.param['max_susd'][0] * unit.var['scalar']['cap']

                namestr = 'ramp_up2_' + n
                unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

                # q_t - q_t+1 <= R * TAU * c + (MAX_SD * C_MAX) * w
                def con_rule(m, s, t):
                    return - unit.var['seq'][n][s, np.mod(t + 1, len(system.model.set_t))] + unit.var['seq'][n][s, t] <= \
                           unit.param['ramp_' + n][1] * system.param['tss'] * unit.var['scalar']['cap']

                namestr = 'ramp_down1_' + n
                unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

                # q_t - q_t+1 <= MAX_SD * c
                def con_rule(m, s, t):
                    return - unit.var['seq'][n][s, np.mod(t + 1, len(system.model.set_t))] + unit.var['seq'][n][s, t] <= \
                           unit.param['max_susd'][1] * unit.var['scalar']['cap']

                namestr = 'ramp_down2_' + n
                unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


def add_min_utdt(system, unit):  # is integrated in logic constraint (add_logic_uvw)
    if unit.param['v_w_active']:
        def con_rule(m, s, t):
            interval = []
            for i in range(unit.param['min_utdt_ts'][0]):
                interval += [np.mod(t - i, system.param['n_ts_sc'])]
            return sum(unit.var['seq']['v'][s, k] for k in interval) <= unit.var['seq']['u'][s, t]

        namestr = 'MIN_UT'
        unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            interval = []
            for i in range(unit.param['min_utdt_ts'][1]):
                interval += [np.mod(t - i, system.param['n_ts_sc'])]
            return sum(unit.var['seq']['w'][s, k] for k in interval) <= 1 - unit.var['seq']['u'][s, t]

        namestr = 'MIN_DT'
        unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


def add_lin_dep(system, unit, varname):
    def con_rule(m, s, t):
        if unit.param['u_active']:
            return unit.var['seq'][varname[1]][s, t] == c1 * unit.var['seq'][varname[0]][s, t] + c2 * \
                   unit.var['seq']['u'][
                       s, t]
        else:
            return unit.var['seq'][varname[1]][s, t] == c1 * unit.var['seq'][varname[0]][s, t]

    c1, c2 = np.round(np.polyfit(unit.param['lim_' + varname[0]], unit.param['lim_' + varname[1]], 1), 2)
    namestr = varname[1] + '(_)' + varname[0] + ')'
    unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


def add_es_balance(system, unit, varname):
    def con_rule(m, s, t):
        return (unit.var['seq'][varname[2]][s, np.mod(t + 1, len(system.model.set_t))] - (
            1 - system.param['tss'] * unit.param['loss_soc']) * unit.var['seq'][varname[2]][s, t]) == (
                   unit.param['eta_c/d'][0] * unit.var['seq'][varname[0]][s, t] - 1 / unit.param['eta_c/d'][1] *
                   unit.var['seq'][varname[1]][s, t]) * system.param['tss']

    namestr = 'con_' + unit.name + '_es_balance_' + varname[2]
    #system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))
    unit.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

def add_inv_param(system, unit, param, type=None):
    if type is None:
        suffix_list = ['fix', 'var']
    elif type == 'CETES':
        suffix_list = ['fix', 'var_cap', 'var_load']

    for suffix in suffix_list:
        namestr = 'param_' + unit.name + '_inv_{}'.format(suffix)
        par = param['inv_{}'.format(suffix)]
        system.model.add_component(namestr, pyo.Param(initialize=par, default=par, mutable=True))
        unit.param['inv_{}'.format(suffix)] = system.model.component(namestr)

def add_energy_param(system, unit, param):
    namestr = 'param_' + unit.name + '_energy'
    par = param['seq']
    def param_init(model, sc, t):
        return param['seq'][sc][t]
    system.model.add_component(namestr, pyo.Param(system.model.set_sc, system.model.set_t, initialize=param_init, default=param_init, mutable=True))
    unit.param['seq'] = system.model.component(namestr)

def add_flexbound_param(system, unit, param):
    namestr = 'param_' + unit.name + '_flexbound'
    par = param['flexbound']
    def param_init(model, sc, t):
        return param['flexbound'][sc][t]
    system.model.add_component(namestr, pyo.Param(system.model.set_sc, system.model.set_t, initialize=param_init, default=param_init, mutable=True))
    unit.param['flexbound'] = system.model.component(namestr)

def add_obj_inv(system, unit):
    i = unit.param['interest_rate']
    n = unit.param['depreciation_period']
    if i > 0:
        annuity_factor = ((1 + i) ** n * i) / ((1 + i) ** n - 1)
    else:
        annuity_factor = 1/n
    # investment costs
    if unit.param['i_active']:
        obj = (unit.param['inv_var'] * unit.var['scalar']['cap'] + unit.param['inv_fix'] * unit.var['scalar'][
            'i']) * annuity_factor
    else:
        obj = unit.param['inv_var'] * unit.var['scalar']['cap'] * annuity_factor
    
    if 'exists' in unit.param.keys():
        if unit.param['exists'] == 'True':
            obj=0
            

    namestr = 'obj_' + unit.name + '_inv'
    system.model.add_component(namestr, pyo.Objective(expr=obj))
    system.model.component(namestr).deactivate()
    unit.obj['inv'] = system.model.component(namestr)


def add_obj_u_v_w(system, unit):
    # Fix OPEX
    if 'opex_fix' in unit.param and unit.param.get('opex_fix') > 0:
        objective = sum(
            unit.param['opex_fix'] * unit.var['seq']['u'][s, t] * system.param['sc'][s][0] for s in system.model.set_sc
            for t in system.model.set_t) * system.param['tss'] / system.param['dur_sc'] * 8760
    else:
        objective = 0
    namestr = 'obj_' + unit.name + '_opex_fix'
    system.model.add_component(namestr, pyo.Objective(expr=objective))
    system.model.component(namestr).deactivate()
    unit.obj['opex_fix'] = system.model.component(namestr)

    # Startup costs
    if 'cost_susd' in unit.param:
        if unit.param['cost_susd'][0] > 0:
            objective = sum(unit.param['cost_susd'][0] * unit.var['seq']['v'][s, t] * system.param['sc'][s][0] for s in
                            system.model.set_sc for t in system.model.set_t) / system.param['dur_sc'] * 8760
        else:
            objective = 0
    else:
        objective = 0
    namestr = 'obj_' + unit.name + '_cost_SU'
    system.model.add_component(namestr, pyo.Objective(expr=objective))
    system.model.component(namestr).deactivate()
    unit.obj['cost_SU'] = system.model.component(namestr)

    # Shutdown costs
    if 'cost_susd' in unit.param:
        if unit.param['cost_susd'][1] > 0:
            objective = sum(unit.param['cost_susd'][1] * unit.var['seq']['w'][s, t] * system.param['sc'][s][0] for s in
                            system.model.set_sc for t in system.model.set_t) / system.param['dur_sc'] * 8760
        else:
            objective = 0
    else:
        objective = 0
    namestr = 'obj_' + unit.name + '_cost_SD'
    system.model.add_component(namestr, pyo.Objective(expr=objective))
    system.model.component(namestr).deactivate()
    unit.obj['cost_SD'] = system.model.component(namestr)


def solve_model(system, solver='cplex', threads=1, mipgap=0):
    opt = pyo.SolverFactory(solver)
    print('Starting optimization...')
    if solver == 'cplex':
        system.model.result = opt.solve(system.model,
                                        warmstart=False,
                                        tee=True,
                                        timelimit=system.param['opt']['timelimit'],
                                        options_string="mipgap={}".format(mipgap)
                                        )
    elif solver == 'glpk':
        system.model.result = opt.solve(system.model,
                                        # warmstart=False,
                                        tee=True,
                                        timelimit=system.param['opt']['timelimit'],
                                        options_string="mipgap={}".format(mipgap)
                                        )
    elif solver == 'cbc':
        options = {
            'ratio': system.param['opt']['optimality_gap'],
            'threads': threads
        }
        system.model.result = opt.solve(system.model,
                                        warmstart=False,
                                        tee=True,
                                        timelimit=system.param['opt']['timelimit'],
                                        options=options  # mipgap and threads cannot be passed to cbc via options_string
                                        )
    elif solver == 'gurobi': # todo: does not work yet -- activate license (--> Sophie?)
        system.model.result = opt.solve(system.model, tee=True,
                                        )
    return system


def save_object(doom_object, name):
    namestr = './' + name + '.pkl'
    with open(os.path.abspath(namestr), mode='wb') as file:
        cloudpickle.dump(doom_object, file)


def import_object(name):
    namestr = './' + name + '.pkl'
    with open(os.path.abspath(namestr), mode='rb') as file:
        model = cloudpickle.load(file)
    return model

def plot_unit_port(system):
    nfig = len(system.unit)
    ncols = np.ceil(np.sqrt(nfig)).astype(int)
    nrows = np.ceil(nfig / ncols).astype(int)
    fig = plt.figure(figsize=[18, 9])                   # maximization of plot on one screen, can be exchanged with next line
    # fig = plt.figure
    for i, name in enumerate(system.unit):
        min_value = 0
        max_value = 0
        ax = fig.add_subplot(nrows, ncols, 1 + i)
        ax.set_title(name)
        for n in system.unit[name].port:
            ax.plot([pyo.value(system.unit[name].port[n][s, t]) for s in system.model.set_sc for t in system.model.set_t],
                    label=n)
            min_value = min([min_value] + [pyo.value(system.unit[name].port[n][s, t]) for s in system.model.set_sc for t in
                                           system.model.set_t])
            max_value = max([max_value] + [pyo.value(system.unit[name].port[n][s, t]) for s in system.model.set_sc for t in
                                           system.model.set_t])
        ax.legend()
        for ids, s in enumerate(system.model.set_sc):
            if ids > 0:
                ax.plot(ids * np.array([system.param['n_ts_sc'], system.param['n_ts_sc']]) - 1, [min_value, max_value],
                        'k')

def plot_unit_port_from_list(system, unit):
    nfig = len(unit)
    ncols = np.ceil(np.sqrt(nfig)).astype(int)
    nrows = np.ceil(nfig / ncols).astype(int)
    fig = plt.figure(figsize=[18, 9])                   # maximization of plot on one screen, can be exchanged with next line
    # fig = plt.figure
    plt.subplots_adjust(hspace=0.25)

    for i, name in enumerate(unit):
        min_value = 0
        max_value = 0
        ax = fig.add_subplot(nrows, ncols, 1 + i)
        ax.set_title(name)
        for n in system.unit[name].port:
            ax.plot([pyo.value(system.unit[name].port[n][s, t]) for s in system.model.set_sc for t in system.model.set_t],
                    label=n)
            min_value = min([min_value] + [pyo.value(system.unit[name].port[n][s, t]) for s in system.model.set_sc for t in
                                           system.model.set_t])
            max_value = max([max_value] + [pyo.value(system.unit[name].port[n][s, t]) for s in system.model.set_sc for t in
                                           system.model.set_t])
        ax.legend()
        for ids, s in enumerate(system.model.set_sc):
            if ids > 0:
                ax.plot(ids * np.array([system.param['n_ts_sc'], system.param['n_ts_sc']]) - 1, [min_value, max_value],
                        'k')
    namestr = './plots/portlist_' + str(unit) + '.svg'
    plt.savefig(namestr, bbox_inches='tight', pad_inches=0)

def plot_node_slack(system):
    max_slack = max([pyo.value(system.node[nodename].var['seq'][n][s, t]) for nodename in system.node.keys() for n in
                     ['slack_lhs', 'slack_rhs'] for s in system.model.set_sc for t in system.model.set_t])
    sum_slack = sum([pyo.value(system.node[nodename].var['seq'][n][s, t]) for nodename in system.node.keys() for n in
                     ['slack_lhs', 'slack_rhs'] for s in system.model.set_sc for t in system.model.set_t])
    print('sum of slack is:  %20.2f' % sum_slack)

    if max_slack > 1e-10:
        nfig = len(system.node)
        ncols = np.ceil(np.sqrt(nfig)).astype(int)
        nrows = np.ceil(nfig / ncols).astype(int)
        fig = plt.figure(figsize=[18, 9])                   # maximization of plot on one screen, can be exchanged with next line
        #fig = plt.figure()
        for i, nodename in enumerate(system.node):
            min_value = 0
            max_value = 0
            ax = fig.add_subplot(nrows, ncols, 1 + i)
            ax.set_title(nodename)
            for n in ['slack_lhs', 'slack_rhs']:
                ax.plot([pyo.value(system.node[nodename].var['seq'][n][s, t]) for s in system.model.set_sc for t in
                         system.model.set_t], label=n)
                min_value = min(
                    [min_value] + [pyo.value(system.node[nodename].var['seq'][n][s, t]) for s in system.model.set_sc for t
                                   in system.model.set_t])
                max_value = max(
                    [max_value] + [pyo.value(system.node[nodename].var['seq'][n][s, t]) for s in system.model.set_sc for t
                                   in system.model.set_t])
            ax.legend()
            for ids, s in enumerate(system.model.set_sc):
                if ids > 0:
                    ax.plot(ids * np.array([system.param['n_ts_sc'] - 1, system.param['n_ts_sc'] - 1]),
                            [min_value, max_value], 'k')

        plt.savefig('./plots/slack.svg', bbox_inches='tight', pad_inches=0)
    else:
        print('Nothing to plot with "plot_node_slack" - Max. slack value: {:.6F}'.format(max_slack))

def plot_full_load_hours(system, unit_port):
    plt.figure(figsize=[18, 9])                   # maximization of plot on one screen, can be exchanged with next line
    #plt.figure()
    bar = []
    name = []
    for idxm, m in enumerate(unit_port.keys()):
        if system.unit[m].var['scalar']['cap'].value > 0:
            if system.unit[m].param['classname'] == 'SolarThermal' or system.unit[m].param['classname'] == 'Photovoltaic':
                bar += [sum(system.unit[m].port[unit_port[m]][s, t].value * system.param['sc'][s][1] for s in
                            system.model.set_sc for t in system.model.set_t) / sum(
                    system.unit[m].param['solar'][s][t] * system.param['sc'][s][1] * system.unit[m].param['eta'] *
                    system.unit[m].var['scalar']['cap'].value for s in system.model.set_sc for t in
                    system.model.set_t) * 8760]
            else:
                bar += [sum(system.unit[m].port[unit_port[m]][s, t].value * system.param['sc'][s][1] for s in
                            system.model.set_sc for t in system.model.set_t) * system.param['tss'] /
                        system.unit[m].var['scalar']['cap'].value]
        else:
            bar += [0]
        name += [m]
    plt.bar(name, bar)
    for index, value in enumerate(bar):
        plt.text(index, value + 5, str(int(np.around(value))), horizontalalignment='center')
    plt.plot(name, [8760] * len(bar), color='black')
    plt.xticks(name, rotation=15)
    plt.title('Full load hours of all units')
    plt.ylabel('Hours')
    plt.grid()
    plt.savefig('./plots/flh_q.svg', bbox_inches='tight', pad_inches=0)

def plot_unit_sizes(system, unit):
    figsize = (15, 5)
    fig = plt.figure(figsize=figsize)

    barnames_ecu = []
    y_plot_ecu = []
    for n in unit['MW']:
        barnames_ecu.append(n)
        y_plot_ecu.append(system.unit[n].var['scalar']['cap'].value)

    barnames_es = []
    y_plot_es = []
    for n in unit['MWh']:
        barnames_es.append(n)
        y_plot_es.append(system.unit[n].var['scalar']['cap'].value)

    barnames_strat = []
    y_plot_strat = []
    for n in unit['m³']:
        barnames_strat.append(n)
        y_plot_strat.append(system.unit[n].var['scalar']['cap'].value / 1000)

    barnames_solar = []
    y_plot_solar = []
    for n in unit['solar']:
        barnames_solar.append(n)
        y_plot_solar.append(system.unit[n].var['scalar']['cap'].value / 1000)

    gs = gridspec.GridSpec(1, 4,
                           width_ratios=[len(barnames_ecu), len(barnames_es), len(barnames_strat), len(barnames_solar)],
                           figure=fig)
    ax0 = plt.subplot(gs[0])
    ax1 = plt.subplot(gs[1])
    ax2 = plt.subplot(gs[2])
    ax3 = plt.subplot(gs[3])
    ax0.bar(barnames_ecu, y_plot_ecu)
    ax0.tick_params(labelrotation=30)
    ax0.set_title('a) ECU')
    ax0.set_ylabel('MW')
    ax1.bar(barnames_es, y_plot_es)
    ax1.tick_params(labelrotation=30)
    ax1.set_title('b) ES')
    ax1.set_ylabel('MWh')
    ax2.bar(barnames_strat, y_plot_strat)
    ax2.tick_params(labelrotation=30)
    ax2.set_title('c) STES')
    ax2.set_ylabel('m$^3$')
    ax3.bar(barnames_solar, y_plot_solar)
    ax3.tick_params(labelrotation=30)
    ax3.set_title('d) solar')
    ax3.set_ylabel('m$^2$ x 1000')
    # plt.savefig('./plots/unit_sizes', bbox_inches='tight', pad_inches=0)
    return fig

def plot_strat_soc(system, unit):
    # Plot stratified storage
    figsize = (15, 15)
    fig, _ax = plt.subplots(len(system.param['sc']), 1, figsize=figsize, squeeze=False)
    ax = _ax.flatten()
    plt.subplots_adjust(hspace=0.05)

    for idxs, s in enumerate(system.param['sc']):
        y_plot = [[system.unit[unit].var['seq']['soc'][s, t, n].value / 1000 for t in system.model.set_t] for n in
                  system.unit[unit].param['T']]
        # y_plot.reverse()
        ax[idxs].set_prop_cycle(color=[[0, 0, 1], [0.0, 0.4, 1], [1, 0.9, 0], [1, 0.4, 0], [1, 0, 0]])
        ax[idxs].stackplot(list(system.model.set_t), y_plot)
        ax[idxs].legend(['LT2', 'LT1', 'MT', 'HT2', 'HT1'])
        ax[idxs].set_ylabel(s)
        ax[0].set_title('SoC of STES')
        ax[-1].set_xlabel('Time in h')
    # plt.savefig('./plots/SoC_strat', bbox_inches='tight', pad_inches=0)

def plot_time_series(system):
    nfig = len(system.param['seq'])
    ncols = np.ceil(np.sqrt(nfig)).astype(int)
    nrows = np.ceil(nfig / ncols).astype(int)
    fig = plt.figure(figsize=[18, 9])                   # maximization of plot on one screen, can be exchanged with next line
    # fig = plt.figure
    for i, name in enumerate(system.param['seq']):
        min_value = 0
        max_value = 0
        ax = fig.add_subplot(nrows, ncols, 1 + i)
        fig.tight_layout(rect =(0.001, 0.001, 0.999, 0.999))
        fig.set_tight_layout(True)
        ax.set_title(name)
        ax.plot([pyo.value(system.param['seq'][name][s][t]) for s in system.model.set_sc for t in system.model.set_t])
        min_value = min(
            [min_value] + [system.param['seq'][name][s][t] for s in system.model.set_sc for t in system.model.set_t])
        max_value = max(
            [max_value] + [system.param['seq'][name][s][t] for s in system.model.set_sc for t in system.model.set_t])
        for ids, s in enumerate(system.model.set_sc):
            if ids > 0:
                ax.plot(ids * np.array([system.param['n_ts_sc'], system.param['n_ts_sc']]) - 1, [min_value, max_value],
                        'k')

    plt.savefig('./plots/timeseries.svg', bbox_inches='tight', pad_inches=0)

def plot_unit_inv_cost(system, unit):
    figsize = (15, 5)
    plt.figure(figsize=figsize)

    barnames = []
    y_plot = []
    for n in unit:
        barnames.append(n)
        try:
            y_plot.append(pyo.value(system.unit[n].obj['inv']))
        except:
            print('')

    ax = plt.subplot()
    ax.bar(barnames, y_plot)
    ax.tick_params(labelrotation=30)
    ax.set_title('Units; annual inv costs: ' + str(sum(pyo.value(system.unit[n].obj['inv']) for n in unit)))
    ax.set_ylabel('EUR')
    # plt.savefig('./plots/unit_sizes', bbox_inches='tight', pad_inches=0)

    inv_costs = {}
    for idx, n in enumerate(barnames):
        inv_costs[n] = y_plot[idx]

    #return inv_costs
    namestr = './plots/TAC_invest.svg'
    plt.savefig(namestr, bbox_inches='tight', pad_inches=0)

def plot_energy(system, unit):
    figsize = (15, 5)
    fig = plt.figure(figsize=figsize)

    names_heat = []
    y_plot_heat = []
    for n in unit['q']:
        for m in unit['q'][n]:
            names_heat.append(n + '_' + m)
            y_plot_heat.append(
                sum(system.unit[n].var['seq'][m][s, t].value * system.param['tss'] * system.param['sc'][s][1]
                    for s in system.model.set_sc for t in system.model.set_t))

    names_fuel = []
    y_plot_fuel = []
    for n in unit['f']:
        for m in unit['f'][n]:
            names_fuel.append(n + '_' + m)
            y_plot_fuel.append(
                sum(system.unit[n].var['seq'][m][s, t].value * system.param['tss'] * system.param['sc'][s][1]
                    for s in system.model.set_sc for t in system.model.set_t))

    names_power = []
    y_plot_power = []
    for n in unit['p']:
        for m in unit['p'][n]:
            names_power.append(n + '_' + m)
            y_plot_power.append(
                sum(system.unit[n].var['seq'][m][s, t].value * system.param['tss'] * system.param['sc'][s][1]
                    for s in system.model.set_sc for t in system.model.set_t))

    gs = gridspec.GridSpec(1, 3, width_ratios=[len(names_heat), len(names_power), len(names_fuel)],
                           figure=fig)
    ax0 = plt.subplot(gs[0])
    ax0.bar(names_heat, y_plot_heat)
    ax0.tick_params(labelrotation=30)
    ax0.set_title('Heat')
    ax0.set_ylabel('MWh')

    ax1 = plt.subplot(gs[1])
    ax1.bar(names_power, y_plot_power)
    ax1.tick_params(labelrotation=30)
    ax1.set_title('Power')
    ax1.set_ylabel('MWh')

    ax2 = plt.subplot(gs[2])
    ax2.bar(names_fuel, y_plot_fuel)
    ax2.tick_params(labelrotation=30)
    ax2.set_title('Fuel')
    ax2.set_ylabel('MWh')

    # plt.savefig('./plots/energy_provided', bbox_inches='tight', pad_inches=0)


def plot_es_soc(system):
    figsize = (15, 15)
    fig, ax = plt.subplots(1, len(system.model.set_sc), figsize=figsize)
    for idxs, s in enumerate(system.model.set_sc):
        # for i, n in enumerate(['tes_steam', 'tes_cooling']):
        for i, n in enumerate(['esu_esu2_ste']):
            y_plot = [system.unit[n].var['seq']['soc'][s, t].value for t in system.model.set_t]
            # ax[i, idxs].stackplot(system.model.set_t, y_plot, labels=['tes_steam', 'tes_cooling'])
            ax[i, idxs].stackplot(system.model.set_t, y_plot, labels=['esu_esu2_ste'])
            ax[i, 0].set_ylabel(n)
        # temp = np.array([50, 40, 30, 10, 0]) * 4200 * 1e-3 / 3600
        # y_plot = [sum(temp[j] * system.unit['ssml1'].var['seq']['soc'][s, t, m].value for j, m in
        #               enumerate(system.unit['ssml1'].param['T'])) for t in
        #           system.model.set_t]
        # ax[2, idxs].stackplot(system.model.set_t, y_plot, labels='strat')
        # ax[2, idxs].set_ylabel('strat')
        # y_plot = [system.unit['ees1'].var['seq']['soc'][s, t].value for t in system.model.set_t]
        # ax[3, idxs].stackplot(system.model.set_t, y_plot, labels='ees')
        # ax[3, idxs].set_ylabel('ees')
        ax[0, idxs].set_title('SOC of ES for ' + str(s))
        ax[-1, idxs].set_xlabel('Time in h')
    # plt.savefig('./plots/ES_SoC', bbox_inches='tight', pad_inches=0)


def plot_node(system):
    figopt = dict()
    figopt['dpi'] = 100
    figopt['min_to_show'] = 0 #0.00001

    n_node = len(system.node)
    # n_col = int(np.ceil(np.sqrt(n_node)))
    n_col = 2
    n_row = int(np.ceil(n_node / n_col))

    # figsize = (15, 15)
    # fig_nodes, ax = plt.subplots(n_row, n_col, figsize=figsize, dpi=figopt['dpi'])
    fig_nodes, ax = plt.subplots(n_row, n_col, dpi=figopt['dpi'])
    plt.subplots_adjust(hspace=0.05)

    for i_n, n in enumerate(system.node):
        i_row = int(np.mod(i_n, n_row))
        i_col = int(np.floor(i_n / n_row))
        y_plot = []
        cols = []
        max_value = 0
        min_value = 0
        for m in system.node[n].param['lhs']:
            c_plot = [pyo.value(system.unit[m[0]].port[m[1]][s, t]) * m[2] for s in system.model.set_sc for t in
                      system.model.set_t]
            if abs(max(c_plot, key=abs)) >= figopt['min_to_show']:
                y_plot.append(c_plot)
                cols.append(m[0])
            max_value = max(max_value, max(c_plot))

        y_plot_n = []
        cols_n = []
        for m in system.node[n].param['rhs']:
            c_plot = [-1 * pyo.value(system.unit[m[0]].port[m[1]][s, t]) * m[2] for s in system.model.set_sc for t in
                      system.model.set_t]
            if abs(max(c_plot, key=abs)) >= figopt['min_to_show']:
                y_plot_n.append(c_plot)
                cols_n.append(m[0])
            min_value = min(min_value, min(c_plot))

        if n_row > 1:
            axis = ax[i_row, i_col]
        else:
            axis = ax[i_col]

        axis.set_ylabel(n)
        axis.stackplot(range(len(system.model.set_t) * len(system.model.set_sc)), y_plot, labels=cols)
        axis.stackplot(range(len(system.model.set_t) * len(system.model.set_sc)), y_plot_n, labels=cols_n)
        axis.legend(ncol=1, prop={'size': 6})

        for idxs, s in enumerate(system.model.set_sc):
            if idxs > 0:
                axis.plot(idxs * np.array([system.param['n_ts_sc'], system.param['n_ts_sc']]) - 1,
                                      [min_value, max_value], 'k')

    # if n_row > 1:
    #     for j in range(int(np.mod(n_node, n_row)), n_row):
    #         ax[j, n_col - 1].axis('off')
    # else:
    #     ax[n_col - 1].axis('off')

def plot_nodes_from_list(system, node_list):
    figopt = dict()
    figopt['dpi'] = 100
    figopt['min_to_show'] = 0 #0.00001

    n_node = len(node_list)
    # n_col = int(np.ceil(np.sqrt(n_node)))
    n_col = 2
    n_row = int(np.ceil(n_node / n_col))


    figsize = (18, 9)
    fig_nodes, ax = plt.subplots(n_row, n_col, figsize=figsize, dpi=figopt['dpi'])
    #fig_nodes, ax = plt.subplots(n_row, n_col, dpi=figopt['dpi'])
    plt.subplots_adjust(hspace=0.25)

    for i_n, n in enumerate(node_list):
        i_row = int(np.mod(i_n, n_row))
        i_col = int(np.floor(i_n / n_row))
        y_plot = []
        cols = []
        max_value = 0
        min_value = 0
        for m in system.node[n].param['lhs']:
            c_plot = [pyo.value(system.unit[m[0]].port[m[1]][s, t]) * m[2] for s in system.model.set_sc for t in
                      system.model.set_t]
            if abs(max(c_plot, key=abs)) >= figopt['min_to_show']:
                y_plot.append(c_plot)
                cols.append(m[0])
            max_value = max(max_value, max(c_plot))

        y_plot_n = []
        cols_n = []
        for m in system.node[n].param['rhs']:
            c_plot = [-1 * pyo.value(system.unit[m[0]].port[m[1]][s, t]) * m[2] for s in system.model.set_sc for t in
                      system.model.set_t]
            if abs(max(c_plot, key=abs)) >= figopt['min_to_show']:
                y_plot_n.append(c_plot)
                cols_n.append(m[0])
            min_value = min(min_value, min(c_plot))

        if n_row > 1:
            axis = ax[i_row, i_col]
        else:
            axis = ax[i_col]

        axis.set_ylabel(n)
        axis.set_xlabel('timestep')
        axis.stackplot(range(len(system.model.set_t) * len(system.model.set_sc)), y_plot, labels=cols)
        axis.stackplot(range(len(system.model.set_t) * len(system.model.set_sc)), y_plot_n, labels=cols_n)
        axis.legend(ncol=1, prop={'size': 6})

        for idxs, s in enumerate(system.model.set_sc):
            if idxs > 0:
                axis.plot(idxs * np.array([system.param['n_ts_sc'], system.param['n_ts_sc']]) - 1,
                                      [min_value, max_value], 'k')
    #return fig_nodes

    namestr = './plots/nodelist_' + str(node_list) + '.svg'
    plt.savefig(namestr, bbox_inches='tight', pad_inches=0)

def plot_heat_demand(system):
    figopt = dict()
    figopt['dpi'] = 100
    figopt['min_to_show'] = 0.00001

    name = [system.unit[n].param['name'] for n in system.unit if system.unit[n].param['classname'] == 'HeatDemand']

    n_heat_demand = len(name)
    n_col = 2
    n_row = int(np.ceil(n_heat_demand / n_col))

    figsize = (15, 15)
    fig_nodes, ax = plt.subplots(n_row, n_col, figsize=figsize, dpi=figopt['dpi'])
    plt.subplots_adjust(hspace=0.05)

    for i_n, n in enumerate(name):
        i_row = int(np.mod(i_n, n_row))
        i_col = int(np.floor(i_n / n_row))
        y_plot = []
        cols = []
        max_value = 0
        min_value = 0
        for m in system.unit[n].param['T_in']:
            c_plot = [pyo.value(system.unit[n].var['seq']['m_in'][s, t, m]) for s in system.model.set_sc for t in
                      system.model.set_t]
            if abs(max(c_plot, key=abs)) > figopt['min_to_show']:
                y_plot.append(c_plot)
                cols.append(m)
            max_value = max(max_value, max(c_plot))

        y_plot_n = []
        cols_n = []
        for m in system.unit[n].param['T_out']:
            c_plot = [-1 * pyo.value(system.unit[n].var['seq']['m_out'][s, t, m]) for s in system.model.set_sc for t in
                      system.model.set_t]
            if abs(max(c_plot, key=abs)) > figopt['min_to_show']:
                y_plot_n.append(c_plot)
                cols_n.append(m)
            min_value = min(min_value, min(c_plot))

        ax[i_row, i_col].set_ylabel(n)
        ax[i_row, i_col].stackplot(range(len(system.model.set_t) * len(system.model.set_sc)), y_plot, labels=cols)
        ax[i_row, i_col].stackplot(range(len(system.model.set_t) * len(system.model.set_sc)), y_plot_n, labels=cols_n)
        ax[i_row, i_col].legend(ncol=1, prop={'size': 6})

        for idxs, s in enumerate(system.model.set_sc):
            if idxs > 0:
                ax[i_row, i_col].plot(idxs * np.array([system.param['n_ts_sc'], system.param['n_ts_sc']]) - 1,
                                      [min_value, max_value], 'k')

    if np.mod(n_heat_demand, n_row) != 0:
        for j in range(int(np.mod(n_heat_demand, n_row)), n_row):
            ax[j, n_col - 1].axis('off')

def write_results_summary(system, folder):      ## Author: Simon Dreymann
    import DOOM.classes
    demands = {}
    supplies = {}
    other_units = {}

    for key, val in system.unit.items():

        if val.param['classname'] ==  'Demand' or val.param['classname'] ==  'HeatDemand':
            demands.update({key: val})
        elif val.param['classname'] ==  'Supply':
            supplies.update({key: val})
        elif not val.param['classname'] ==  'Coupler':
            other_units.update({key: val})

    with open(folder+'/results_summary.txt', 'w') as f:
        f.write("Results:\n")
        f.write("========")

        f.write("\n\n\nDemands:")
        for name, dem in demands.items():
            f.write("\n\nName: " + name)
            f.write("\nType: " + dem.__class__.__name__)
            if dem.param['classname'] ==  'HeatDemand':
                f.write("\nMaximum: {:.3f} MW".format(max(dem.var['seq']['q'].get_values().values())))
            else:
                f.write("\nMaximum: {:.3f} MW".format(max(dem.var['seq']['d'].get_values().values())))

        f.write("\n\n\nSupplies:")
        for name, sup in supplies.items():
            f.write("\n\nName: " + name)
            f.write("\nType: " + sup.__class__.__name__)
            f.write("\nMaximum: {:.3f} MW".format(max(sup.var['seq']['s'].get_values().values())))
            f.write("\nCapacity: {:.3f} MW".format(sup.var['scalar']['cap'].value))
            f.write("\nCosts: ")
            for o in sup.obj.keys():
                f.write("\n    {}: {:.3f} MEUR".format(o, pyo.value(sup.obj[o])/1e6))

        f.write("\n\n\nUnits:")
        for name, unit in other_units.items():
            f.write("\n\nName: " + name)
            f.write("\nType: " + unit.__class__.__name__)

            if unit.__class__.__name__ == 'Photovoltaic' or unit.__class__.__name__ == 'SolarThermal':
                cap_unit = 'm^2'
            else:
                cap_unit = 'MW'

            f.write("\nCapacity: {:.3f} {}".format(unit.var['scalar']['cap'].value, cap_unit))

            if 'p' in unit.var['seq']:
                f.write("\nMaximum power: {:.3f} MW".format(max(unit.var['seq']['p'].get_values().values())))
            if 'q' in unit.var['seq'] or 'q_out' in unit.var['seq'] or 'q_sink' in unit.var['seq']:
                try:
                    f.write("\nMaximum heat: {:.3f} MW".format(max(unit.var['seq']['q'].get_values().values())))
                except KeyError:
                    pass
                try:
                    f.write("\nMaximum heat: {:.3f} MW".format(max(unit.var['seq']['q_out'].get_values().values())))
                except KeyError:
                    pass
                try:
                    f.write("\nMaximum heat: {:.3f} MW".format(max(unit.var['seq']['q_sink'].get_values().values())))
                except KeyError:
                    pass

            f.write("\nCosts: ")
            for o in unit.obj.keys():
                f.write("\n    {}: {:.3f} MEUR".format(o, pyo.value(unit.obj[o])/1e6))

        f.write("\n")
        f.close()

def write_full_results(system, folder):     ## Author: Simon Dreymann

    Path(Path.cwd() / folder / 'timeseries').mkdir(parents=True, exist_ok=True)

    with open(Path(Path.cwd() / folder / 'full_results.txt'), 'w') as f:
        f.write("Full Results:\n")
        f.write("=============\n")

        for name, unit in system.unit.items():
            f.write("\nName: " + name)
            f.write("\nType: " + unit.__class__.__name__)

            if 'scalar' in unit.var:
                try:
                    for sc in unit.var['scalar']:
                        f.write("\n" + sc + ": Value {}".format(unit.var['scalar'][sc].value))
                except:
                    print('Scalar Variables of Unit ' + name + ' could not be read/printed properly.')

            try:
                s = '\nObjectives:'
                for o in unit.obj.keys():
                    s += '\n' + str(unit.obj[o]) + ': {} EUR'.format(pyo.value(unit.obj[o]))
                f.write(s)
            except:
                print('Objectives of Unit ' + name + ' could not be read/printed properly.')

            for seq, var in unit.var['seq'].items():    # map of (string, pyomo.IndexedVar)

                try:
                    # make a pandas Series of all values
                    s = pd.Series(var.get_values(), index=var.get_values().keys())

                    f.write("\n" + seq + ": Maximum {}, Minimum {}".format(max(s), min(s)))

                    # This should always be true because all sequences have at least scenario and timestep as index
                    if type(s.index[0]) == tuple:
                        s = s.unstack(level=1).transpose()
                    else:
                        s = pd.DataFrame(s)           # force transition to DataFrame

                    # joins column names for multi-indexed timeseries (i.e. scenario and temperature as pyo index), does
                    # nothing for single-indexd timeseries (i.e. only scenario as pyo index)
                    s.columns = s.columns.to_flat_index()

                    s.index.name = 'Timestep'

                    # Write to uniquely named file
                    s.to_csv(Path.joinpath(Path.cwd(), folder, 'timeseries', name+"_"+seq+".csv"))
                except:
                    print('Sequences of Unit ' + name + ' could not be read/printed properly.')


            f.write('\n')
