import pandas as pd
import numpy as np

def A_actual(model, set_val):

    full_list = list(model.coeffs['A_beta_x']['type'].unique())

    A_add_beta = {}

    sd = model.data_input['streamdata']

    def read_sd(i, r, string):
        qry = '`stream nr` == @i & `requirement nr` == @r'
        return sd.query(qry)[string].values[0]

    def read_val(u, i, string):
        value = [val[string] for val in list(model.conversion_units[u].values())][i]
        return value



    def A_actual_general(set_U, set_J, set_K, utility_name, docstring):
        var_A_add_beta_x = getattr(model.model, 'var_{}_A_add_beta_x'.format(utility_name))
        var_dT = getattr(model.model, 'var_{}_dT'.format(utility_name))
        var_A_reassign = getattr(model.model, 'var_{}_A_reassign'.format(utility_name))
        var_Qdot = getattr(model.model, 'var_{}_Qdot'.format(utility_name))
        var_z_avail = getattr(model.model, 'var_{}_z_avail'.format(utility_name))
        var_z = getattr(model.model, 'var_{}_z'.format(utility_name))
        var_PSH_r_z = getattr(model.model, 'var_PSH_r_z')
        var_PSC_r_z = getattr(model.model, 'var_PSC_r_z')

        my_index_t = pd.MultiIndex(levels=[[], [], [], []],
                                 codes=[[], [], [], []],
                                 names=['HS', 'CS', 'K', 'T'])

        my_index = pd.MultiIndex(levels=[[], [], []],
                                   codes=[[], [], []],
                                   names=['HS', 'CS', 'K'])

        my_columns = [u'Area', u'Area_beta', u'Area_beta_calc', u'Activity']

        A_add_beta_t = pd.DataFrame(index=my_index_t, columns=my_columns)
        A_add_beta = pd.DataFrame(index=my_index, columns=my_columns)

        for u in set_U:
            for j in set_J:
                if model.settings['SIMP']['max_pair_hex'] == False:
                    k_set = set_K.value
                else:
                    k_set = [min(set_K.data())]

                for k in k_set:
                    for t in model.model.set_TS:
                            if model.settings['SIMP']['max_pair_hex'] == False:
                                q = round(var_Qdot.get_values()[u, j, k, t],3)
                                z = var_z.get_values()[u, j, k, t]
                            else:
                                q = round(sum(var_Qdot.get_values()[u, j, K, t] for K in set_K),3)
                                z = sum(var_z.get_values()[u, j, K, t] for K in set_K)

                            dT1 = var_dT.get_values()[u, j, k, t]
                            dT2 = var_dT.get_values()[u, j, k+1, t]
                            LMTD = (dT1*dT2*(dT1+dT2)/2)**(1/3)



                            if utility_name == 'Direct':
                                h1 = np.max([read_sd(u, r, 'h') * var_PSH_r_z.get_values()[u, r, t] for r in model.data_input['indices']['hot streams'][u]])
                                h2 = np.max([read_sd(j, r, 'h') * var_PSC_r_z.get_values()[j, r, t] for r in model.data_input['indices']['cold streams'][j]])
                                
                            elif (utility_name == 'CUH'):
                                h1 = read_val('CU', u, 'h')
                                h2 = np.max([read_sd(j, r, 'h') * var_PSC_r_z.get_values()[j, r, t] for r in
                                             model.data_input['indices']['cold streams'][j]])

                            elif (utility_name == 'CUC'):
                                h1 = np.max([read_sd(u, r, 'h') * var_PSH_r_z.get_values()[u, r, t] for r in
                                             model.data_input['indices']['hot streams'][u]])
                                h2 = read_val('CU', j, 'h')
                            elif utility_name in ['UH', 'UIH']:
                                h1 = read_val(utility_name, u, 'h')
                                h2 = np.max([read_sd(j, r, 'h') * var_PSC_r_z.get_values()[j, r, t] for r in
                                             model.data_input['indices']['cold streams'][j]])
                            elif utility_name in ['UC', 'UIC']:
                                h1 = np.max([read_sd(u, r, 'h') * var_PSH_r_z.get_values()[u, r, t] for r in
                                             model.data_input['indices']['hot streams'][u]])
                                h2 = read_val(utility_name, j, 'h')

                            U = 1 / (1 / h1 + 1 / h2)
                            A = q/(LMTD*U) - var_A_reassign.get_values()[u, j, k]

                            if A < 0:
                                A = 0

                            
                            if 'Hex_spec' in model.settings.keys():   
                                def get_medium(idx, hc, u):
                                    if (u == 'Direct') or ((hc == 'h') and (u in ['UC', 'UIC', 'CUC'])) or ((hc == 'c') and (u in ['UH', 'UIH', 'CUH'])):
                                        return list(model.data_input['streamdata'][model.data_input['streamdata']['stream nr'] == idx]['Medium'])[0]
                                    else:
                                        if u in ['CUH', 'CUC']:
                                            u = 'CU'
                                        key = list(model.conversion_units[u].keys())[idx]
                                        return model.conversion_units[u][key]['Medium']

                                def get_beta(med1, med2):
                                    key = [i for i in model.settings['Hex_spec'].keys() if set([med1, med2]) == set(i)][0]
                                    beta = model.settings['Hex_spec'][key]['beta']
                                    return beta

                                A_add_beta_t.loc[(u, j, k, t),:] = [A, A**get_beta(get_medium(u,'h',utility_name), get_medium(j, 'c', utility_name)), var_A_add_beta_x.get_values()[u, j, k], z]

                            else:
                                A_add_beta_t.loc[(u, j, k, t),:] = [A, A**model.settings['COSTS']['beta'], var_A_add_beta_x.get_values()[u, j, k], z]

                    if np.max(A_add_beta_t.loc[(u, j, k), my_columns[-1]]) > 0:
                        A_add_beta.loc[(u, j, k), :] = np.max(A_add_beta_t.loc[(u, j, k),:])
                        if set_val:
                            var_A_add_beta_x[u, j, k].value = np.max(A_add_beta_t.loc[(u, j, k),:])['Area_beta']

        return A_add_beta

    if 'Direct' in full_list:
        A_add_beta['Direct'] = A_actual_general(model.model.set_PSH, model.model.set_PSC, model.model.set_StagesDirect, 'Direct', 'A in HEX UH')
    if 'UH' in full_list:
        A_add_beta['UH'] = A_actual_general(model.model.set_UH, model.model.set_PSC, model.model.set_StagesUH, 'UH', 'A in HEX UH')
    if 'UC' in full_list:
        A_add_beta['UC'] = A_actual_general(model.model.set_PSH, model.model.set_UC, model.model.set_StagesUC, 'UC', 'A in HEX UC')
    if 'UIH' in full_list:
        A_add_beta['UIH'] = A_actual_general(model.model.set_UIH, model.model.set_PSC, model.model.set_StagesUIH, 'UIH', 'A in HEX UIH')
    if 'UIC' in full_list:
        A_add_beta['UIC'] = A_actual_general(model.model.set_PSH, model.model.set_UIC, model.model.set_StagesUIC, 'UIC', 'A in HEX UIC')
    if 'CUH' in full_list:
        A_add_beta['CUH'] = A_actual_general(model.model.set_CU, model.model.set_PSC, model.model.set_StagesCU, 'CUH', 'A in HEX CUH')
    if 'CUC' in full_list:
        A_add_beta['CUC'] = A_actual_general(model.model.set_PSH, model.model.set_CU, model.model.set_StagesCU, 'CUC', 'A in HEX CUC')

    return A_add_beta
