import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def plot_HEN(HEN, return_df=False):


    stages = HEN.settings['HEN']['stages']
    streams_hot = np.array(list(HEN.data_input['indices']['hot streams'].keys()))
    streams_cold = np.array(list(HEN.data_input['indices']['cold streams'].keys()))
    streams = max(max(streams_hot), max(streams_cold))

    # PLOT basic grid
    ####################################################################################################################

    x_coord_streams = [-1.1, 1.1]
    y_coord_streams_hot = -streams_hot
    y_coord_streams_cold = -streams_cold


    x_coord_stages = np.linspace(-1, 1, stages + 1)
    y_coord_stages = [-min(streams_hot) + 0.3, - max(streams_cold) - 0.3]

    figure = plt.figure()
    for i in range(streams_hot.shape[0]):
        plt.plot(x_coord_streams, [y_coord_streams_hot[i], y_coord_streams_hot[i]], 'r')
        plt.plot(x_coord_streams[1], y_coord_streams_hot[i], 'r>')
        plt.text(x_coord_streams[0] - 0.1, y_coord_streams_hot[i], 'HS '+str(streams_hot[i]), horizontalalignment='right')
    for i in range(streams_cold.shape[0]):
        plt.plot(x_coord_streams, [y_coord_streams_cold[i], y_coord_streams_cold[i]], 'b')
        plt.plot(x_coord_streams[0], y_coord_streams_cold[i], 'b<')
        plt.text(x_coord_streams[0] - 0.1, y_coord_streams_cold[i], 'CS ' + str(streams_cold[i]), horizontalalignment='right')

    for i in range(stages + 1):
        plt.plot([x_coord_stages[i], x_coord_stages[i]], y_coord_stages, '--k')


    # calculate and PLOT stream splits
    ####################################################################################################################

    HEX_df = pd.DataFrame(columns=['type', 'string', 'SH', 'SC', 'U', 'old', 'reassigned', 'stage'])

    full_list = [values for values in HEN.coeffs['A_beta_x']['type'].unique()]

    for utility in full_list:
        var_z_max = getattr(HEN.model, 'var_' + utility + '_z_max')
        var_z_avail = getattr(HEN.model, 'var_' + utility + '_z_avail')
        var_z_reassign = getattr(HEN.model, 'var_' + utility + '_z_reassign')
        try:
            index_values = [HEN.retrofit['existing HEX'][utility][i]['location'][:2] for i in list(HEN.retrofit['existing HEX'][utility].keys())]
        except:
            index_values = []
        for row in range(len(var_z_max.get_values())):
            if np.round(list(var_z_max.get_values().values()))[row] == 1:
                H = list(var_z_max.get_values().keys())[row][0]
                C = list(var_z_max.get_values().keys())[row][1]

                if utility == 'Direct':
                    SH = H
                    SC = C
                    U = None
                    string = None
                elif utility in ['UH', 'UIH', 'CUH']:
                    SH = None
                    SC = C
                    U = H
                    string = utility + ' ' + str(list(var_z_max.get_values().keys())[row][0])
                elif utility in ['UC', 'UIC', 'CUC']:
                    SH = H
                    SC = None
                    U = C
                    string = utility + ' ' + str(list(var_z_max.get_values().keys())[row][1])



                stage = list(var_z_max.get_values().keys())[row][2]

                old = 0
                reassigned = 0

                if (H, C) in index_values:
                    old_hex_nr = list(HEN.retrofit['existing HEX'][utility].keys())[index_values.index((H, C))]
                    old = int(1 - var_z_avail[old_hex_nr].value)

                try:
                    if sum(var_z_reassign[H, C, stage, m].value for m in HEN.retrofit['existing HEX'][utility].keys()) > 0:
                        reassigned = 1
                except:
                    reassigned = 0


                HEX_df = HEX_df.append(pd.DataFrame({'type': utility, 'string': string, 'SH': [SH], 'SC': [SC], 'U': [U], 'old': [old], 'reassigned': [reassigned], 'stage': stage}), ignore_index=True)

    HEX_df = HEX_df.set_index('stage')

    if return_df:
        return HEX_df

    for k in np.unique(HEX_df.index):
        nr_all_HEX = np.sum(HEX_df.index == k)
        nr_indiv_HEX = np.zeros(streams)

        for i in range(streams):

            nr_indiv_HEX[i] = np.round(np.sum(HEX_df.loc[k]['SH'] == i+1) + np.sum(HEX_df.loc[k]['SC'] == i+1))

            if int(nr_indiv_HEX[i]) > 1:
                dx = x_coord_stages[k] - x_coord_stages[k-1]
                x = [x_coord_stages[k-1] + dx/10, x_coord_stages[k] - dx/10]
                y_coord_splits = np.linspace(- i - 1, - i - 2, int(nr_indiv_HEX[i]) + 1)[1:-1]

                if i + 1 in streams_hot:
                    color = 'r'
                else:
                    color = 'b'

                for j in range(len(y_coord_splits)):
                    plt.plot(x, [y_coord_splits[j], y_coord_splits[j]], color)

                plt.plot([x[0], x[0]], [y_coord_splits[j], - i - 1], color)
                plt.plot([x[1], x[1]], [y_coord_splits[j], - i - 1], color)

        x_coord_HEX = np.linspace(x_coord_stages[k-1], x_coord_stages[k], nr_all_HEX + 2)[1:-1]

        counter_indiv_HEX = np.zeros(streams)

        for i in range(nr_all_HEX):
            if nr_all_HEX > 1:
                hex_type = HEX_df.loc[k].iloc[i]['type']
                hex_string = HEX_df.loc[k].iloc[i]['string']
                SC = HEX_df.loc[k].iloc[i]['SC']
                SH = HEX_df.loc[k].iloc[i]['SH']
                old = HEX_df.loc[k].iloc[i]['old']
                reassigned = HEX_df.loc[k].iloc[i]['reassigned']
            else:
                hex_type = HEX_df.loc[k]['type']
                SC = HEX_df.loc[k]['SC']
                SH = HEX_df.loc[k]['SH']
                hex_string = HEX_df.loc[k]['string']
                old = HEX_df.loc[k]['old']
                reassigned = HEX_df.loc[k]['reassigned']


            if SC is not None:
                y_coord_SC_HEX = np.linspace(- SC, - SC - 1, int(nr_indiv_HEX[SC-1]) + 1)[int(counter_indiv_HEX[SC-1])]

                counter_indiv_HEX[SC-1] = counter_indiv_HEX[SC-1] + 1
            if SH is not None:
                try:
                    y_coord_SH_HEX = np.linspace(- SH, - SH - 1, int(nr_indiv_HEX[SH - 1]) + 1)[int(counter_indiv_HEX[SH - 1])]
                except:
                    print('error')

                counter_indiv_HEX[SH-1] = counter_indiv_HEX[SH-1] + 1

            linestyle = '-'
            linecolor = 'k'
            if old == 1:
                linecolor = (0.7, 0.7, 0.7)
            if reassigned == 1:
                linecolor = (0.4, 0.4, 0.4)
                linestyle = '--'

            if hex_type == 'Direct':
                plt.plot([x_coord_HEX[i], x_coord_HEX[i]], [y_coord_SC_HEX, y_coord_SH_HEX], color=linecolor, linestyle=linestyle, marker='o')

            else:
                if SC is not None:
                    plt.plot(x_coord_HEX[i], y_coord_SC_HEX, color=linecolor, linestyle=linestyle, marker='o')
                    plt.text(x_coord_HEX[i], y_coord_SC_HEX + 0.3, hex_string, horizontalalignment='center')
                if SH is not None:
                    plt.plot(x_coord_HEX[i], y_coord_SH_HEX, color=linecolor, linestyle=linestyle, marker='o')
                    plt.text(x_coord_HEX[i], y_coord_SH_HEX + 0.3, hex_string, horizontalalignment='center')

    plt.axis('off')
    # plt.show()
    #plt.close('all')
    return figure

def plot_CCs(targets, CCs, TAM, show, interval):
    if TAM == 1:
        targets = targets['targets TAM']
        intervals = np.array([1])
    else:
        targets = targets['targets']
        intervals = np.array([interval])

    if CCs == 'CCs':
        for t in intervals-1:
            hot_CC = targets['CCs'][0][t]
            cold_CC = targets['CCs'][1][t]

            figure = plt.figure()
            if hot_CC is not None:
                plt.plot(hot_CC[:,0], hot_CC[:,1], 'r')
            if cold_CC is not None:
                plt.plot(cold_CC[:, 0], cold_CC[:, 1], 'b')
            plt.xlabel('heat load (kW)')
            plt.ylabel('temperature (°C)')
            if show == 1:
                plt.show()
            else:
                plt.close('all')


    if CCs == 'GCCs':
        for t in intervals-1:
            GCC = targets['GCCs'][0][t]

            figure = plt.figure()
            if GCC is not None:
                plt.plot(GCC[:,0], GCC[:,1], 'k')
            plt.xlabel('heat load (kW)')
            plt.ylabel('temperature (°C)')
            if show == 1:
                plt.show()
            else:
                plt.close('all')

    if CCs == 'mGCCs':
        for t in intervals - 1:
            hot_CC = targets['mGCCs'][0][t]
            cold_CC = targets['mGCCs'][1][t]

            figure = plt.figure()
            if hot_CC is not None:
                plt.plot(hot_CC[:, 0], hot_CC[:, 1], 'r')
            if cold_CC is not None:
                plt.plot(cold_CC[:, 0], cold_CC[:, 1], 'b')
            plt.xlabel('heat load (kW)')
            plt.ylabel('temperature (°C)')
            if show == 1:
                plt.show()
            else:
                plt.close('all')
    return figure

def plot_Costs(demand, model):
    costs = {}

    full_list = [values for values in demand.coeffs['A_beta_x']['type'].unique()]

    def read_conversion_unit(ut, string, idx):
        cu = demand.conversion_units[ut]
        keys = list(cu.keys())
        return cu[keys[idx]][string]

    heat_pump = {}
    heat_pump['electricity'] = sum(model.var_CU_heat_pump_Pel.get_values()[u, t] * demand.data_input['intervals']['durations'][t] * read_conversion_unit('CU', 'costs', u) for u in model.subset_heat_pump for t in model.set_TS)
    heat_pump['HEX var'] = (sum(model.var_CUH_A_add_beta_x.get_values()[u, i, k] for u in model.subset_heat_pump for i in model.set_PSC for k in model.set_StagesCU) +
                            sum(model.var_CUC_A_add_beta_x.get_values()[i, u, k] for u in model.subset_heat_pump for i in model.set_PSH for k in model.set_StagesCU)) * \
                            demand.settings['COSTS']['HEX var'] / demand.settings['COSTS']['annualization']
    heat_pump['HEX fix'] = (sum(model.var_CUH_z_max.get_values()[u, i, k] for u in model.subset_heat_pump for i in model.set_PSC for k in model.set_StagesCU) +
                            sum(model.var_CUC_z_max.get_values()[i, u, k] for u in model.subset_heat_pump for i in model.set_PSH for k in model.set_StagesCU)) * \
                           demand.settings['COSTS']['HEX fix'] / demand.settings['COSTS']['annualization']
    costs['heat pump'] = heat_pump

    storage = {}
    storage['HEX var'] = (sum(model.var_CUH_A_add_beta_x.get_values()[u, i, k] for u in model.subset_storage for i in model.set_PSC for k in model.set_StagesCU) +
                            sum(model.var_CUC_A_add_beta_x.get_values()[i, u, k] for u in model.subset_storage for i in model.set_PSH for k in model.set_StagesCU)) * \
                           demand.settings['COSTS']['HEX var'] / demand.settings['COSTS']['annualization']
    storage['HEX fix'] = (sum(model.var_CUH_z_max.get_values()[u, i, k] for u in model.subset_storage for i in model.set_PSC for k in model.set_StagesCU) +
                            sum(model.var_CUC_z_max.get_values()[i, u, k] for u in model.subset_storage for i in model.set_PSH for k in model.set_StagesCU)) * \
                           demand.settings['COSTS']['HEX fix'] / demand.settings['COSTS']['annualization']
    storage['Vessel'] = sum(model.var_CU_storage_mass.get_values()[u] * read_conversion_unit('CU', 'costs var', u) / read_conversion_unit('CU', 'annualization', u) for u in model.subset_storage) + \
                        sum(model.var_CU_storage_z_max.get_values()[u] * read_conversion_unit('CU', 'costs fix', u) / read_conversion_unit('CU', 'annualization', u) for u in model.subset_storage)
    costs['storage'] = storage

    direct = {}
    direct['HEX var'] = sum(model.var_Direct_A_add_beta_x.get_values()[u, i, k] for u in model.set_PSH for i in model.set_PSC for k in model.set_StagesDirect) * \
                         demand.settings['COSTS']['HEX var'] / demand.settings['COSTS']['annualization']
    direct['HEX fix'] = (sum(model.var_Direct_z_max.get_values()[u, i, k] for u in model.set_PSH for i in model.set_PSC for k in model.set_StagesDirect) -
                         sum(1 - np.array(list(model.var_Direct_z_avail.get_values().values())))) * \
                         demand.settings['COSTS']['HEX fix'] / demand.settings['COSTS']['annualization']
    costs['direct'] = direct

    utility = {}
    aux_var = 0
    aux_fix = 0
    if 'UH' in full_list:
        aux_var = aux_var + sum(model.var_UH_A_add_beta_x.get_values()[u, i, k] for u in model.set_UH for i in model.set_PSC for k in model.set_StagesUH)
        aux_fix = aux_fix + sum(model.var_UH_z_max.get_values()[u, i, k] for u in model.set_UH for i in model.set_PSC for k in model.set_StagesUH) - sum(1 - np.array(list(model.var_UH_z_avail.get_values().values())))
    if 'UC' in full_list:
        aux_var = aux_var + sum(model.var_UC_A_add_beta_x.get_values()[i, u, k] for u in model.set_UC for i in model.set_PSH for k in model.set_StagesUC)
        aux_fix = aux_fix + sum(model.var_UC_z_max.get_values()[i, u, k] for u in model.set_UC for i in model.set_PSH for k in model.set_StagesUC) - sum(1 - np.array(list(model.var_UC_z_avail.get_values().values())))
    if 'UIH' in full_list:
        aux_var = aux_var + sum(model.var_UIH_A_add_beta_x.get_values()[u, i, k] for u in model.set_UIH for i in model.set_PSC for k in model.set_StagesUIH)
        aux_fix = aux_fix + sum(model.var_UIH_z_max.get_values()[u, i, k] for u in model.set_UIH for i in model.set_PSC for k in model.set_StagesUIH) - sum(1 - np.array(list(model.var_UIH_z_avail.get_values().values())))
    if 'UIC' in full_list:
        aux_var = aux_var + sum(model.var_UIC_A_add_beta_x.get_values()[i, u, k] for u in model.set_UIC for i in model.set_PSH for k in model.set_StagesUIC)
        aux_fix = aux_fix + sum(model.var_UIC_z_max.get_values()[i, u, k] for u in model.set_UIC for i in model.set_PSH for k in model.set_StagesUIC) - sum(1 - np.array(list(model.var_UIC_z_avail.get_values().values())))
    utility['HEX var'] = aux_var * demand.settings['COSTS']['HEX var'] / demand.settings['COSTS']['annualization']
    utility['HEX fix'] = aux_fix * demand.settings['COSTS']['HEX fix'] / demand.settings['COSTS']['annualization']

    if 'UH' in full_list:
        utility['Hot Utility costs'] = sum([model.var_UH_Qdot.get_values()[u, j, k, t] * demand.data_input['intervals']['durations'][t - 1] * read_conversion_unit('UH', 'costs', u) for
                    u in model.set_UH for j in model.set_PSC for k in model.set_StagesUH for t in model.set_TS])
    if 'UIH' in full_list:
        utility['Hot Utility costs'] = sum([model.var_UIH_Qdot.get_values()[u, j, k, t] * demand.data_input['intervals']['durations'][t - 1] * read_conversion_unit('UIH', 'costs', u) for
                    u in model.set_UIH for j in model.set_PSC for k in model.set_StagesUIH for t in model.set_TS])
    if 'UC' in full_list:
        utility['Cold Utility costs'] = sum([model.var_UC_Qdot.get_values()[i, u, k, t] * demand.data_input['intervals']['durations'][t - 1] * read_conversion_unit('UC', 'costs', u) for
                    u in model.set_UC for i in model.set_PSH for k in model.set_StagesUC for t in model.set_TS])
    if 'UIC' in full_list:
        utility['Cold Utility costs'] = sum([model.var_UIC_Qdot.get_values()[i, u, k, t] * demand.data_input['intervals']['durations'][t - 1] * read_conversion_unit('UIC', 'costs', u) for
                    u in model.set_UIC for i in model.set_PSH for k in model.set_StagesUIC for t in model.set_TS])
    costs['utility'] = utility

    matrix = np.zeros((12, 5))
    count = 0
    matrix[count:count+len(heat_pump), 0] = [heat_pump['electricity'], heat_pump['HEX var'], heat_pump['HEX fix']]
    count = count + len(heat_pump)
    matrix[count:count + len(storage), 1] = [storage['HEX var'], storage['HEX fix'], storage['Vessel']]
    count = count + len(storage)
    matrix[count:count + len(direct), 2] = [direct['HEX var'], direct['HEX fix']]
    count = count + len(direct)
    matrix[count:count + len(utility), 3] = [utility['HEX var'], utility['HEX fix'], utility['Hot Utility costs'], utility['Cold Utility costs']]

    matrix[:, -1] = np.sum(matrix, axis=1)

    figure = plt.figure()
    plt.bar(np.arange(5), matrix[0, :])
    for i in range(1, 12):
        plt.bar(np.arange(5), matrix[i, :], bottom=np.sum(matrix[:i, :],axis=0))

    plt.ylabel('Annual costs (€)')
    xticks = list(costs.keys())
    xticks.extend(['total'])
    plt.xticks(np.arange(5), xticks)
    legendentries = []
    legendentries.extend(['heat pump: ' + s for s in list(heat_pump.keys())])
    legendentries.extend(['storage: ' + s for s in list(storage.keys())])
    legendentries.extend(['direct: ' + s for s in list(direct.keys())])
    legendentries.extend(['utility: ' + s for s in list(utility.keys())])
    plt.legend(legendentries)
    #plt.show()
    #plt.close('all')
    return figure, costs


def plot_HR(demand, model):
    full_list = [values for values in demand.coeffs['A_beta_x']['type'].unique()]

    max_recovery = sum([demand.targets['targets']['Heat Recovery'][:, t] * demand.data_input['intervals']['durations'][t] for t in demand.data_input['intervals']['index']])
    max_recovery_TAM  = demand.targets['targets TAM']['Heat Recovery']

    recovery_direct = sum([model.var_Direct_Qdot.get_values()[i, j, k, t] * demand.data_input['intervals']['durations'][t] for i in model.set_PSH for j in model.set_PSC for k in model.set_StagesDirect for t in demand.data_input['intervals']['index']])
    if ('CUH' in full_list):
        recovery_CU = sum([model.var_CUH_Qdot.get_values()[i, j, k, t] * demand.data_input['intervals']['durations'][t] for i in model.set_CU for j in model.set_PSC for k in model.set_StagesCU for t in demand.data_input['intervals']['index']])
    else:
        recovery_CU = 0
    recovery_actual = recovery_direct + recovery_CU

    y_pos = np.arange(1, 6)
    figure = plt.figure()
    plt.bar(y_pos, [max_recovery, max_recovery_TAM, recovery_actual, recovery_direct, recovery_CU])
    bars = ('max', 'TAM', 'actual', 'direct', 'CU')
    plt.xticks(y_pos, bars)
    plt.title('Heat recovery')
    plt.ylabel('Heat recovery (kWh)')
    # plt.show()
    #plt.close('all')
    print(f'Max. heat recovery: {max_recovery}, actual heat recovery: {recovery_actual}')
    return figure, recovery_direct, recovery_CU
