import pandas as pd
import numpy as np
import scipy.linalg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from pyomo.environ import *
#
Tmax = 130
Tmin = 40
dTmin = 20
dTmax = 70

print_output = 'off'

res_L = []
res_SL = []
res_NL = []

def run_optimization(stream_data_hot, stream_data_cold):
    number_hot_streams = np.shape(stream_data_hot)[0]
    number_cold_streams = np.shape(stream_data_cold)[0]

    q_req_hot_streams = abs(stream_data_hot[:, 0] - stream_data_hot[:, 1]) * stream_data_hot[:, 2]
    q_req_cold_streams = abs(stream_data_cold[:, 0] - stream_data_cold[:, 1]) * stream_data_cold[:, 2]

    q_max_hot_streams = abs(stream_data_hot[:, 0] - np.max([stream_data_hot[:, 1], np.ones(number_hot_streams)*Tmin], axis=0)) * stream_data_hot[:, 2]
    q_max_cold_streams = abs(stream_data_cold[:, 0] - np.min([stream_data_cold[:, 1], np.ones(number_cold_streams)*Tmax], axis=0)) * stream_data_cold[:, 2]


    #############################################################################
    # OPIMIZATION MODEL

    HP_test = ConcreteModel()
    # opt_type = 'NL'  # 'NL', 'SL'
    tee = False

    # Constraint names

    con_list_NL = []
    con_list_SL = []
    con_list_L = []

    # SETS
    # base model

    HP_test.set_PSH = Set(initialize=range(number_hot_streams), ordered=True)
    HP_test.set_PSC = Set(initialize=range(number_cold_streams), ordered=True)

    #############################################################################
    # VARIABLES
    # base model / NL

    HP_test.var_Qdot_e_i = Var(HP_test.set_PSH, within=NonNegativeReals)
    HP_test.var_Qdot_c_j = Var(HP_test.set_PSC, within=NonNegativeReals)

    HP_test.var_z_e_i = Var(HP_test.set_PSH, within=Binary)
    HP_test.var_z_c_j = Var(HP_test.set_PSC, within=Binary)

    HP_test.var_Pel = Var([0], within=NonNegativeReals)

    HP_test.var_dT = Var([0], bounds=(dTmin, dTmax))

    HP_test.var_T_h = Var([0], within=NonNegativeReals)
    HP_test.var_T_c = Var([0], within=NonNegativeReals)

    HP_test.var_UH = Var([0], within=NonNegativeReals)
    HP_test.var_UC = Var([0], within=NonNegativeReals)

    ##########################################
    # SL

    HP_test.var_Qdot_c_f_i = Var(HP_test.set_PSH, within=NonNegativeReals)
    HP_test.var_Qdot_e_f_j = Var(HP_test.set_PSC, within=NonNegativeReals)

    HP_test.var_slack_i = Var(HP_test.set_PSH, within=Reals)
    HP_test.var_slack_j = Var(HP_test.set_PSC, within=Reals)

    HP_test.var_Pel_f_i = Var([0], within=NonNegativeReals)
    HP_test.var_Pel_f_j = Var([0], within=NonNegativeReals)

    ##########################################
    # L

    HP_test.var_slack_i_j = Var(HP_test.set_PSH, HP_test.set_PSC, within=Reals)

    HP_test.var_Pel_i_j = Var([0], within=NonNegativeReals)

    HP_test.var_Qdot_e_i_j = Var(HP_test.set_PSH, HP_test.set_PSC, within=NonNegativeReals)
    HP_test.var_Qdot_c_i_j = Var(HP_test.set_PSH, HP_test.set_PSC, within=NonNegativeReals)


    #############################################################################
    # Constraints
    # base model

    # transferrable heat
    def con_fun(HP_test, i):
        return HP_test.var_Qdot_e_i[i] <= (stream_data_hot[i, 0] - HP_test.var_T_c[0])*stream_data_hot[i, 2]
    HP_test.con_Qdot_e_max = Constraint(HP_test.set_PSH, rule=con_fun)

    def con_fun(HP_test, i):
        return HP_test.var_Qdot_e_i[i] <= q_max_hot_streams[i] * HP_test.var_z_e_i[i]
    HP_test.con_Qdot_e_max_2 = Constraint(HP_test.set_PSH, rule=con_fun)

    def con_fun(HP_test, j):
        return HP_test.var_Qdot_c_j[j] <= (HP_test.var_T_h[0] - stream_data_cold[j, 0])*stream_data_cold[j, 2]
    HP_test.con_Qdot_c_max = Constraint(HP_test.set_PSC, rule=con_fun)

    def con_fun(HP_test, j):
        return HP_test.var_Qdot_c_j[j] <= q_max_cold_streams[j] * HP_test.var_z_c_j[j]
    HP_test.con_Qdot_c_max_2 = Constraint(HP_test.set_PSC, rule=con_fun)


    # Utility demand
    def con_fun(HP_test):
        return HP_test.var_UH[0] == sum(q_req_cold_streams) - sum(HP_test.var_Qdot_c_j[j] for j in HP_test.set_PSC)
    HP_test.con_UH = Constraint(rule=con_fun)

    def con_fun(HP_test):
        return HP_test.var_UC[0] == sum(q_req_hot_streams) - sum(HP_test.var_Qdot_e_i[i] for i in HP_test.set_PSH)
    HP_test.con_UC = Constraint(rule=con_fun)


    # Logical temperature constraint
    def con_fun(HP_test):
        return HP_test.var_T_h[0] >= HP_test.var_T_c[0]
    HP_test.con_T_dec = Constraint(rule=con_fun)

    # Temperature difference
    def con_fun(HP_test):
        return HP_test.var_dT[0] == HP_test.var_T_h[0]-HP_test.var_T_c[0]
    HP_test.con_dT_dec = Constraint(rule=con_fun)


    ##########################################
    # NL

    # NL Carnot
    con_name = 'con_NL_Q_e_c'
    def con_fun(HP_test):
        Q_e = sum(HP_test.var_Qdot_e_i[i] for i in HP_test.set_PSH)
        Q_c = sum(HP_test.var_Qdot_c_j[j] for j in HP_test.set_PSC)
        T_h = HP_test.var_T_h[0] + 273.15
        T_c = HP_test.var_T_c[0] + 273.15
        return Q_e == Q_c/(T_h*eta_c)*(T_h*eta_c-(T_h-T_c))
    HP_test.add_component(con_name, Constraint(rule=con_fun))
    con_list_NL.append(con_name)

    con_name = 'con_NL_Pel'
    def con_fun(HP_test):
        Q_e = sum(HP_test.var_Qdot_e_i[i] for i in HP_test.set_PSH)
        Q_c = sum(HP_test.var_Qdot_c_j[j] for j in HP_test.set_PSC)
        Pel = HP_test.var_Pel[0]
        return Q_e == Q_c - Pel
    HP_test.add_component(con_name, Constraint(rule=con_fun))
    con_list_NL.append(con_name)

    ##########################################
    # Function definition
    def linearization(q_max, cond_or_evap):
        res = 20
        dT = np.linspace(dTmin*1.1, dTmax*0.9, res)
        T_h = (Tmax + Tmin)/2 + 273.15

        if cond_or_evap == 'evap':
            q_e = np.linspace(q_max*0.6, q_max*0.8, res)

            DT, Q_E = np.meshgrid(dT, q_e, sparse=False)

            Q_C = T_h*eta_c*Q_E/(T_h*eta_c-DT)
        elif cond_or_evap == 'cond':
            q_c = np.linspace(q_max*0.6, q_max*0.8, res)

            DT, Q_C = np.meshgrid(dT, q_c, sparse=False)

            Q_E = Q_C/(T_h*eta_c)*(T_h*eta_c-DT)

        # fig = plt.figure()
        # ax = fig.gca(projection='3d')
        # ax.plot_surface(DT, Q_E, Q_C, linewidth=0, antialiased=False)


        # best-fit linear plane
        # M
        temp = np.c_[np.reshape(DT, (res**2, 1)), np.reshape(Q_E, (res**2, 1)), np.ones(res**2)]
        coeffs, _, _, _ = scipy.linalg.lstsq(temp, np.reshape(Q_C, (res**2, 1)))  # nonoptimal coefficients; Z = coeffs_nonopt[0]*X + coeffs_nonopt[1]*Y + coeffs_nonopt[2]
        # ax.plot_surface(DT, Q_E, coeffs[2] + coeffs[0] * DT + coeffs[1] * Q_E, linewidth=0, antialiased=False)
        # plt.show()
        return coeffs

    ##########################################
    # SL

    # fictive condenser heat loat as a function of dT and evaporator heat load
    con_name = 'con_SL_Qdot_c_f_i'
    def con_fun(HP_test, i):
        q_max = q_max_hot_streams[i]
        coeffs = linearization(q_max, 'evap')

        dT = HP_test.var_dT[0]
        Qe = HP_test.var_Qdot_e_i[i]
        slack = HP_test.var_slack_i[i]
        Qc = HP_test.var_Qdot_c_f_i[i]
        var_z = HP_test.var_z_e_i[i]

        # print(dTmax * coeffs[0, 0] + 0 * coeffs[1, 0] + coeffs[2, 0])
        # print(dTmin * coeffs[0, 0] + 0 * coeffs[1, 0] + coeffs[2, 0])
        return dT * coeffs[0, 0] + Qe * coeffs[1, 0] + var_z*coeffs[2, 0] + slack * (dTmax * coeffs[0, 0]) == Qc
    HP_test.add_component(con_name, Constraint(HP_test.set_PSH, rule=con_fun))
    con_list_SL.append(con_name)

    # fictive evaporator heat loat as a function of dT and condenser heat load
    con_name = 'con_SL_Qdot_e_f_j'
    def con_fun(HP_test, j):
        q_max = q_max_cold_streams[j]
        coeffs = linearization(q_max, 'cond')

        dT = HP_test.var_dT[0]
        Qe = HP_test.var_Qdot_e_f_j[j]
        slack = HP_test.var_slack_j[j]
        Qc = HP_test.var_Qdot_c_j[j]
        var_z = HP_test.var_z_c_j[j]

        # print(dTmax * coeffs[0, 0] + 0 * coeffs[1, 0] + coeffs[2, 0])
        # print(dTmin * coeffs[0, 0] + 0 * coeffs[1, 0] + coeffs[2, 0])
        return dT * coeffs[0, 0] + Qe * coeffs[1, 0] + var_z*coeffs[2, 0] + slack * (dTmax * coeffs[0, 0]) == Qc
    HP_test.add_component(con_name, Constraint(HP_test.set_PSC, rule=con_fun))
    con_list_SL.append(con_name)

    # fictive evaporator heat loat as a function of dT and condenser heat load
    con_name = 'con_SL_Qdot_c_j_bigger'
    def con_fun(HP_test):
        return sum(HP_test.var_Qdot_c_j[j] for j in HP_test.set_PSC) == sum(HP_test.var_Qdot_c_f_i[i] for i in HP_test.set_PSH)
    HP_test.add_component(con_name, Constraint(rule=con_fun))
    con_list_SL.append(con_name)

    con_name = 'con_SL_Pel_1'
    def con_fun(HP_test):
        return HP_test.var_Pel[0] >= sum(HP_test.var_Qdot_c_j[j] for j in HP_test.set_PSC) - sum(HP_test.var_Qdot_e_i[i] for i in HP_test.set_PSH)
    HP_test.add_component(con_name, Constraint(rule=con_fun))
    con_list_SL.append(con_name)

    con_name = 'con_SL_Pel_2'
    def con_fun(HP_test):
        return HP_test.var_Pel[0] >= sum(HP_test.var_Qdot_c_j[j] for j in HP_test.set_PSC) - sum(HP_test.var_Qdot_e_f_j[j] for j in HP_test.set_PSC)
    HP_test.add_component(con_name, Constraint(rule=con_fun))
    con_list_SL.append(con_name)

    # bounds for slack-variables
    con_name = 'con_SL_slack_limit_ub'
    def con_fun(HP_test, i):
        return HP_test.var_slack_i[i] <= 0
    HP_test.add_component(con_name, Constraint(HP_test.set_PSH, rule=con_fun))
    con_list_SL.append(con_name)

    con_name = 'con_SL_slack_limit_lb'
    def con_fun(HP_test, i):
        return HP_test.var_slack_i[i] >= -(1-HP_test.var_z_e_i[i])*1
    HP_test.add_component(con_name, Constraint(HP_test.set_PSH, rule=con_fun))
    con_list_SL.append(con_name)

    con_name = 'con_SL_slack_limit_ub2'
    def con_fun(HP_test, i):
        return HP_test.var_slack_j[i] <= 0
    HP_test.add_component(con_name, Constraint(HP_test.set_PSC, rule=con_fun))
    con_list_SL.append(con_name)

    con_name = 'con_SL_slack_limit_lb2'
    def con_fun(HP_test, i):
        return HP_test.var_slack_j[i] >= -(1-HP_test.var_z_c_j[i])*1
    HP_test.add_component(con_name, Constraint(HP_test.set_PSC, rule=con_fun))
    con_list_SL.append(con_name)

    ##########################################
    # L

    # condenser heat load as a function of dT and evaporator heat load
    con_name = 'con_L_Qdot_c_e'
    def con_fun(HP_test, i, j):
        q_max_evap = q_max_hot_streams[i]
        q_max_cond = q_max_cold_streams[j]

        if q_max_evap > q_max_cond:
            q_max = q_max_cond
            evap_or_cond = 'cond'
        else:
            q_max = q_max_evap
            evap_or_cond = 'evap'

        coeffs = linearization(q_max, evap_or_cond)

        dT = HP_test.var_dT[0]
        Qe = HP_test.var_Qdot_e_i_j[i, j]
        slack_i_j = HP_test.var_slack_i_j[i, j]
        Qc = HP_test.var_Qdot_c_i_j[i, j]

        # print(dTmax * coeffs[0, 0] + 0 * coeffs[1, 0] + coeffs[2, 0])
        # print(dTmin * coeffs[0, 0] + 0 * coeffs[1, 0] + coeffs[2, 0])
        return dT * coeffs[0, 0] + Qe * coeffs[1, 0] + coeffs[2, 0] + slack_i_j == Qc
    HP_test.add_component(con_name, Constraint(HP_test.set_PSH, HP_test.set_PSC, rule=con_fun))
    con_list_L.append(con_name)

    # Pel
    con_name = 'con_L_Pel'
    def con_fun(HP_test):
        return HP_test.var_Pel[0] == sum(HP_test.var_Qdot_c_i_j[i, j] for i in HP_test.set_PSH for j in HP_test.set_PSC) - sum(HP_test.var_Qdot_e_i_j[i, j] for i in HP_test.set_PSH for j in HP_test.set_PSC)
    HP_test.add_component(con_name, Constraint(rule=con_fun))
    con_list_L.append(con_name)

    # Q_c
    con_name = 'con_L_Q_c'
    def con_fun(HP_test, j):
        return sum(HP_test.var_Qdot_c_i_j[i, j] for i in HP_test.set_PSH) == HP_test.var_Qdot_c_j[j]
    HP_test.add_component(con_name, Constraint(HP_test.set_PSC, rule=con_fun))
    con_list_L.append(con_name)

    # Q_c_e
    con_name = 'con_L_Q_c_e_logical'
    def con_fun(HP_test, i, j):
        return HP_test.var_Qdot_c_i_j[i, j] >= HP_test.var_Qdot_e_i_j[i, j]
    HP_test.add_component(con_name, Constraint(HP_test.set_PSH, HP_test.set_PSC, rule=con_fun))
    con_list_L.append(con_name)

    # Q_c
    con_name = 'con_L_Q_c_logical_1'
    def con_fun(HP_test, i, j):
        return HP_test.var_Qdot_c_i_j[i, j] <= HP_test.var_z_c_j[j] * q_max_cold_streams[j]
    HP_test.add_component(con_name, Constraint(HP_test.set_PSH, HP_test.set_PSC, rule=con_fun))
    con_list_L.append(con_name)

    con_name = 'con_L_Q_c_logical_2'
    def con_fun(HP_test, i, j):
        return HP_test.var_Qdot_c_i_j[i, j] <= HP_test.var_z_e_i[i] * q_max_cold_streams[j]
    HP_test.add_component(con_name, Constraint(HP_test.set_PSH, HP_test.set_PSC, rule=con_fun))
    con_list_L.append(con_name)


    # Q_e
    con_name = 'con_L_Q_e'
    def con_fun(HP_test, i):
        return sum(HP_test.var_Qdot_e_i_j[i, j] for j in HP_test.set_PSC) == HP_test.var_Qdot_e_i[i]
    HP_test.add_component(con_name, Constraint(HP_test.set_PSH, rule=con_fun))
    con_list_L.append(con_name)

    # Q_e
    con_name = 'con_L_Q_e_logical_1'
    def con_fun(HP_test, i, j):
        return HP_test.var_Qdot_e_i_j[i, j] <= HP_test.var_z_c_j[j] * q_max_hot_streams[i]
    HP_test.add_component(con_name, Constraint(HP_test.set_PSH, HP_test.set_PSC, rule=con_fun))
    con_list_L.append(con_name)

    con_name = 'con_L_Q_e_logical_2'
    def con_fun(HP_test, i, j):
        return HP_test.var_Qdot_e_i_j[i, j] <= HP_test.var_z_e_i[i] * q_max_hot_streams[i]
    HP_test.add_component(con_name, Constraint(HP_test.set_PSH, HP_test.set_PSC, rule=con_fun))
    con_list_L.append(con_name)

    # bounds for slack-variables
    con_name = 'con_L_slack_limit_ub'
    def con_fun(HP_test, i, j):
        return HP_test.var_slack_i_j[i, j] <= (2-HP_test.var_z_e_i[i]-HP_test.var_z_c_j[j]) * 1000 # fixme: big M should be adjusted to be more tight
    HP_test.add_component(con_name, Constraint(HP_test.set_PSH, HP_test.set_PSC, rule=con_fun))
    con_list_L.append(con_name)

    con_name = 'con_L_slack_limit_lb'
    def con_fun(HP_test, i, j):
        return HP_test.var_slack_i_j[i, j] >= -(2-HP_test.var_z_e_i[i]-HP_test.var_z_c_j[j]) * 1000 # fixme: big M should be adjusted to be more tight
    HP_test.add_component(con_name, Constraint(HP_test.set_PSH, HP_test.set_PSC, rule=con_fun))
    con_list_L.append(con_name)

    #############################################################################

    HP_test.obj = Objective(expr=HP_test.var_UC[0] * 10 +
                                     HP_test.var_UH[0] * 100 +
                                     HP_test.var_Pel[0] * 30 +
                                     sum(HP_test.var_z_c_j[j] for j in HP_test.set_PSC) * 5 +
                                     sum(HP_test.var_z_e_i[i] for i in HP_test.set_PSH) * 5)

    for opt_type in ['L', 'SL', 'NL']:
        for i in con_list_L:
            constraint = getattr(HP_test, i)
            constraint.deactivate()

        for i in con_list_SL:
            constraint = getattr(HP_test, i)
            constraint.deactivate()

        for i in con_list_NL:
            constraint = getattr(HP_test, i)
            constraint.deactivate()

        if opt_type == 'L':
            for i in con_list_L:
                constraint = getattr(HP_test, i)
                constraint.activate()
        elif opt_type == 'SL':
            for i in con_list_SL:
                constraint = getattr(HP_test, i)
                constraint.activate()
        elif opt_type == 'NL':
            for i in con_list_NL:
                constraint = getattr(HP_test, i)
                constraint.activate()

        if opt_type == 'NL':
            opt = pyomo.environ.SolverFactory('couenne')
            if tee == True:
                result = opt.solve(HP_test, tee=True, timelimit=180)
            else:
                result = opt.solve(HP_test, timelimit=180)
        else:
            opt = pyomo.environ.SolverFactory('cplex')
            if tee == True:
                result = opt.solve(HP_test, tee=True, timelimit=180)
            else:
                result = opt.solve(HP_test, timelimit=180)

        Pel_real = sum(HP_test.var_Qdot_c_j.get_values().values()) - sum(HP_test.var_Qdot_e_i.get_values().values())
        COP_real = (HP_test.var_T_h[0].value+273.15)/HP_test.var_dT[0].value*eta_c
        if HP_test.var_Pel[0].value == 0:
            COP = 100
        else:
            COP = sum(HP_test.var_Qdot_c_j.get_values().values())/HP_test.var_Pel[0].value

        if print_output == 'on':
            print(' ')
            print('---------- ' + opt_type + ' ----------')
            print('dT: ' + str(HP_test.var_dT[0].value))
            print('UH: ' + str(HP_test.var_UH[0].value) + ' of ' + str(sum(q_req_cold_streams)))
            print('UC: ' + str(HP_test.var_UC[0].value) + ' of ' + str(sum(q_req_hot_streams)))

            print('Condenser: ' + str(sum(HP_test.var_Qdot_c_j.get_values().values())))
            print('Evaporator: ' + str(sum(HP_test.var_Qdot_e_i.get_values().values())))
            print('Pel: ' + str(HP_test.var_Pel[0].value))

            print('Pel_real: ' + str(Pel_real))

            print('COP_real: ' + str(COP_real))
            if HP_test.var_Pel[0].value == 0:
                print('COP: ' + 'inf')
            else:
                print('COP: ' + str(COP))
            print(' ')
            print('Error: ' + str(round((COP-COP_real)/COP_real*100, 3)) + '%')
            print(' ')
            print(' ')

        if opt_type == 'L':
            res_L.append(round((COP-COP_real)/COP_real*100, 3))
        elif opt_type == 'SL':
            res_SL.append(round((COP-COP_real)/COP_real*100, 3))
        elif opt_type == 'NL':
            res_NL.append(round((COP-COP_real)/COP_real*100, 3))


for runs in range(0, 30):
    hot_streams = round(np.random.rand()*10+1)
    cold_streams = round(np.random.rand()*10+1)

    stream_data_hot = np.ndarray((hot_streams, 3))
    for i in range(hot_streams):
        stream_data_hot[i, :] = [80-np.random.rand()*10, 50-np.random.rand()*10, np.random.rand()*2]

    stream_data_cold = np.ndarray((cold_streams, 3))
    for j in range(cold_streams):
        stream_data_cold[j, :] = [80-np.random.rand()*10, 100-np.random.rand()*10, np.random.rand()*2]

    eta_c = 0.5

    run_optimization(stream_data_hot, stream_data_cold)

for i in range(len(res_L)):
    print('L: ' + str(res_L[i]) + '%; SL: ' + str(res_SL[i]) + '%; NL: ' + str(res_NL[i]) + '%')
print('')
print('')
print('---------- mean error (apprixmated COP / real COP) / real COP ---------')
def Average(lst):
    return sum(lst) / len(lst)

print('L: ' + str(Average([abs(number) for number in res_L])) + '%; SL: ' + str(Average([abs(number) for number in res_SL])) + '%; NL: ' + str(Average([abs(number) for number in res_NL])) + '%')
print('L: ' + str(Average(res_L)) + '%; SL: ' + str(Average(res_SL)) + '%; NL: ' + str(Average(res_NL)) + '%')

plt.figure()
plot_L = plt.plot(res_L, marker='o', label='Model L')
plot_SL = plt.plot(res_SL, marker='x', label='Model SL')
plot_NL = plt.plot(res_NL, marker='.', label='Model NL')
plt.ylim((-100, 100))
plt.xlabel('runs')
plt.ylabel('relative error (%)')
plt.legend()
plt.show()




