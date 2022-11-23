import pandas as pd
import numpy as np
import scipy.linalg

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def check_COP(HEN):
    model = HEN.model
    for u in model.subset_heat_pump:
        for t in model.set_TS:
            print('===== HP ' + str(u) + ' TS: ' +str(t)+ ' =======')

            print('Qdot_c:')
            print(str(model.var_CU_heat_pump_Qdot_c[u, t].value) + ' kW')

            print('COP calculated (Qdot_c/Pel):')
            print(str(round(model.var_CU_heat_pump_Qdot_c[u, t].value/(model.var_CU_heat_pump_Pel[u, t].value + 0.001), 2)))
            print('COP calculated (Qdot_c/(Qdot_c-Qdot_e)):')
            try:
                print(str(
                    round(model.var_CU_heat_pump_Qdot_c[u, t].value, 2) / (round(model.var_CU_heat_pump_Qdot_c[u, t].value, 2)-round(model.var_CU_heat_pump_Qdot_e[u, t].value, 2))))
            except:
                print(0)
            print('COP real:')
            COP = (model.var_CUH_T[u, t].value + 273.15) / (model.var_CUH_T[u, t].value - model.var_CUC_T[u, t].value) * HEN.conversion_units['CU'][list(HEN.conversion_units['CU'].keys())[u]]['eta_c']
            print(str(round(COP, 2)))

            print('Pel calculated:')
            print(str(round(model.var_CU_heat_pump_Pel[u, t].value, 2)) + ' kW')
            print('Pel real:')
            print(str(round(model.var_CU_heat_pump_Qdot_c[u, t].value/COP, 2)) + ' kW')

            # print('Lift: ' + str(round(model.var_CUC_T[u, t].value, 2)) + ' --> ' + str(round(model.var_CUH_T[u, t].value,2)) + ' (dT:' + str(round(model.var_CUH_T[u, t].value - model.var_CUC_T[u, t].value,2)) + ') °C')
            print('Lift: {}°C ({}°C --> {}°C)'.format(round(model.var_CUH_T[u, t].value - model.var_CUC_T[u, t].value,2), round(model.var_CUC_T[u, t].value, 2), round(model.var_CUH_T[u, t].value, 2)))

            print('==================')
            print('')


def check_lin(HEN):
    model = HEN.opt_model
    eta_c = 0.5

    def linearization(q_max, cond_or_evap):
        dTliftmax = HEN.conversion_units['CU']['dT lift max'].values[0]
        dTliftmin = HEN.conversion_units['CU']['dT lift min'].values[0]
        Tmax = HEN.conversion_units['CU']['Tmax'].values[0]
        Tmin = HEN.conversion_units['CU']['Tmin'].values[0]

        res = 20
        dT = np.linspace(dTliftmin, dTliftmax, res)
        T_h = (Tmax + Tmin) / 2 + 273.15

        if cond_or_evap == 'evap':
            q_e = np.linspace(q_max*0, q_max, res)

            DT, Q_E = np.meshgrid(dT, q_e, sparse=False)

            Q_C = T_h * eta_c * Q_E / (T_h * eta_c - DT)
        elif cond_or_evap == 'cond':
            q_c = np.linspace(q_max*0, q_max, res)

            DT, Q_C = np.meshgrid(dT, q_c, sparse=False)

            Q_E = Q_C / (T_h * eta_c) * (T_h * eta_c - DT)

        fig = plt.figure()
        ax = fig.gca(projection='3d')
        ax.plot_surface(DT, Q_E, Q_C, linewidth=0, antialiased=False)

        # best-fit linear plane
        # M
        temp = np.c_[np.reshape(DT, (res ** 2, 1)), np.reshape(Q_E, (res ** 2, 1)), np.ones(res ** 2)]
        coeffs, _, _, _ = scipy.linalg.lstsq(temp, np.reshape(Q_C, (res ** 2,
                                                                    1)))  # nonoptimal coefficients; Z = coeffs_nonopt[0]*X + coeffs_nonopt[1]*Y + coeffs_nonopt[2]
        ax.plot_surface(DT, Q_E, coeffs[2] + coeffs[0] * DT + coeffs[1] * Q_E, linewidth=0, antialiased=False)
        return ax

    for u in model.subset_heat_pump:
        for i in model.set_PSH:
            for t in model.set_TS:
                q_max = HEN.q_max['CUC'].loc[t, i, u].values[0]
                if q_max > 0:
                    if model.var_CU_heat_pump_Qdot_e_i[u, i, t].value + model.var_CU_heat_pump_Qdot_c_f_i[u, i, t].value > 0:
                        ax = linearization(q_max, 'evap')
                        ax.scatter(model.var_CUH_T[u, t].value - model.var_CUC_T[u, t].value, model.var_CU_heat_pump_Qdot_e_i[u, i, t].value, model.var_CU_heat_pump_Qdot_c_f_i[u, i, t].value)
        for i in model.set_PSC:
            for t in model.set_TS:
                q_max = HEN.q_max['CUH'].loc[t, u, i].values[0]
                if q_max > 0:
                    if model.var_CU_heat_pump_Qdot_e_f_j[u, i, t].value + model.var_CU_heat_pump_Qdot_c_j[
                        u, i, t].value > 0:
                        ax = linearization(q_max, 'cond')
                        ax.scatter(model.var_CUH_T[u, t].value - model.var_CUC_T[u, t].value, model.var_CU_heat_pump_Qdot_e_f_j[u, i, t].value, model.var_CU_heat_pump_Qdot_c_j[u, i, t].value)


        
