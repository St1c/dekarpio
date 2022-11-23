import pandas as pd
import numpy as np
import scipy.linalg
import pi_framework.hens.PinchAnalysis.targets as targets
import pi_framework.hens.Calculations.estimate_storage_size as estimate_storage_size
import pi_framework.hens.Models.lin_funct as lin_funct
import matplotlib.pyplot as plt

from pyomo.environ import *
import time

# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D

class HENS:
    def __init__(self, settings, data_input, targ, conversion_units, retrofit, model=None):
        """
        :param datafile: url to file
        :param utility: specifies utilities
        """

        self.names_list = ['Direct'] + [i for i in conversion_units.keys() if not i == 'CU']
        if 'CU' in conversion_units.keys():
            self.names_list += ['CUH', 'CUC']

        for u in conversion_units.keys():
            data_input['indices'][u] = [tuple((i, 1)) for i in range(len(conversion_units[u]))]


        self.settings = settings

        if self.settings['SCHED']['active'] and not self.settings['SCHED']['testing']:
            try: #fixme try should be removed after implementing additional ['SCHED']-Settings ['intervals'] and ['duration']
                data_input['intervals']['index'] = [i for i in range(settings['SCHED']['intervals'])]
                data_input['intervals']['durations'] = [settings['SCHED']['duration'] for i in range(settings['SCHED']['intervals'])]
            except:
                data_input['intervals']['index'] = [i for i in range(24)]
                data_input['intervals']['durations'] = [1 for i in range(24)]

        self.data_input = data_input
        self.targets = targ
        self.conversion_units = conversion_units
        self.retrofit = retrofit

        # ################################################################################################################
        # #    set attributes for retrofit
        #
        # retrofit_HEX = {}
        # retrofit_HEX['Direct'] = pd.DataFrame(columns=['Hot Stream', 'Cold Stream', 'Stage', 'Value', 'Nr'])
        # retrofit_HEX['UH'] = pd.DataFrame(columns=['Hot Stream', 'Cold Stream', 'Stage', 'Value', 'Nr'])
        # retrofit_HEX['UC'] = pd.DataFrame(columns=['Hot Stream', 'Cold Stream', 'Stage', 'Value', 'Nr'])
        # retrofit_HEX['UIH'] = pd.DataFrame(columns=['Hot Stream', 'Cold Stream', 'Stage', 'Value', 'Nr'])
        # retrofit_HEX['UIC'] = pd.DataFrame(columns=['Hot Stream', 'Cold Stream', 'Stage', 'Value', 'Nr'])
        # retrofit_HEX['CUH'] = pd.DataFrame(columns=['Hot Stream', 'Cold Stream', 'Stage', 'Value', 'Nr'])
        # retrofit_HEX['CUC'] = pd.DataFrame(columns=['Hot Stream', 'Cold Stream', 'Stage', 'Value', 'Nr'])
        #
        # for i in self.names_list:
        #     retrofit_HEX[i].set_index(list(retrofit_HEX[i].columns[:3].values), inplace=True)
        #
        # self.retrofit = {
        #     'retrofit HEX': retrofit_HEX,
        #     'retrofit set': 0
        # }

        ################################################################################################################
        #    init model

        if model is None:
            model = ConcreteModel()

        ################################################################################################################
        #    init ports

        self.ports = {}
        for utility_name in conversion_units.keys():
            self.ports[utility_name] = [None]*self.conversion_units[utility_name].__len__()
        self.ports['HS'] = [None]*data_input['indices']['hot requirements'].__len__()
        self.ports['CS'] = [None]*data_input['indices']['cold requirements'].__len__()


        dTmin = settings['HEN']['dTmin']

        q_max = {}
        for utility_name in self.names_list:
            q_max[utility_name] = calc_q_max_spec(utility_name, data_input, conversion_units, dTmin)

        self.q_max = q_max

        coeffs = lin_funct.linearization(data_input, conversion_units, settings, self.names_list, q_max)
        self.coeffs = coeffs

        stages = settings['HEN']['stages']


        full_list = [values for values in coeffs['A_beta_x']['type'].unique()]

        full_list_cu = full_list.copy()
        if 'CUH' in full_list_cu:
            full_list_cu.remove('CUH')
            full_list_cu.remove('CUC')
            full_list_cu.append('CU')

        full_list_wo_direct = full_list.copy()
        full_list_wo_direct.remove('Direct')

        full_list_wo_direct_cu = full_list_wo_direct.copy()
        if 'CUH' in full_list_wo_direct_cu:
            full_list_wo_direct_cu.remove('CUH')
            full_list_wo_direct_cu.remove('CUC')
            full_list_wo_direct_cu.append('CU')

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # DEFINE SETS

        def addIndex(set_original):
            """
            Often an extended set is necessary to index variables
            :param set_original
            :return: set_new
            """
            set_new = Set(initialize=set_original | Set(initialize=[set_original.bounds()[-1] + 1], ordered=True))
            return set_new

        # additional components
        indices_heat_pump = []
        indices_storage = []
        if 'CU' in conversion_units.keys():
            for idx, key in enumerate(conversion_units['CU'].keys()):
                if 'Heat Pump' in key:
                    indices_heat_pump += [idx]
                if 'Storage' in key:
                    indices_storage += [idx]

        model.subset_heat_pump = Set(initialize=indices_heat_pump, ordered=True)
        model.subset_storage = Set(initialize=indices_storage, ordered=True)

        # auxiliary sets
        model.set_zero_one = Set(initialize=[0, 1], ordered=True)

        # Timesteps
        model.set_TS = Set(initialize=data_input['intervals']['index'], ordered=True)                          # Set with all timesteps
        model.set_TS_Plus = Set(initialize=np.append(data_input['intervals']['index'], max(data_input['intervals']['index'])+1), ordered=True)  # Set with all timesteps

        # Process streams
        model.set_PSH = Set(initialize=data_input['indices']['hot streams'].keys(), ordered=True)                # Set with all hot process streams
        model.set_PSC = Set(initialize=data_input['indices']['cold streams'].keys(), ordered=True)              # Set with all cold process streams


        model.set_PSH_r = Set(initialize=data_input['indices']['hot requirements'], ordered=True)  # Set with all hot process streams
        model.set_PSC_r = Set(initialize=data_input['indices']['cold requirements'], ordered=True)  # Set with all cold process streams

        # utilities and conversion units
        for u in full_list_wo_direct_cu:
            set_name = 'set_{}'
            init = [i[0] for i in data_input['indices'][u]]
            setattr(model, set_name.format(u), Set(initialize=init, ordered=True))  # Sets with all utilities

        # utilities and conversion units
        for u in full_list_wo_direct_cu:
            set_name = 'set_{}_r'
            init = data_input['indices'][u]
            setattr(model, set_name.format(u), Set(initialize=init, ordered=True))   # Sets with all utilities


        # stages
        model.set_Stages = Set(initialize=np.arange(stages)+1, ordered=True)                                  # Set with all temperature stages
        model.set_StagesDirect = Set(initialize=np.arange(1, stages-1)+1, ordered=True)                       # Set with all temperature stages for direct heat transfer
        if 'UH' in full_list:
            model.set_StagesUH = Set(initialize=[1],
                                     ordered=True)  # Set with all temperature stages for hot utilities
        if 'UC' in full_list:
            model.set_StagesUC = Set(initialize=[stages],
                                     ordered=True)  # Set with all temperature stages for cold utilities
        if 'UIH' in full_list:
            model.set_StagesUIH = Set(initialize=np.arange(1, stages-1)+1,
                                      ordered=True)  # Set with all temperature stages for internal hot utilities
        if 'UIC' in full_list:
            model.set_StagesUIC = Set(initialize=np.arange(1, stages-1)+1,
                                      ordered=True)  # Set with all temperature stages for internal cold utilities
        if 'CU' in full_list_cu:
            model.set_StagesCU = Set(initialize=np.arange(1, stages - 1) + 1,
                                     ordered=True)  # Set with all temperature stages for conversion units

        for u in [''] + full_list_cu:
            set_name = 'set_Stages{}_Plus'
            setattr(model, set_name.format(u), addIndex(getattr(model, 'set_Stages'+u)))

        # LMTD coefficients
        model.set_coeffs_LMTD = Set(initialize=np.arange(coeffs['LMTD'].shape[0]), ordered=True)

        # A coefficients
        for u in full_list:
            set_name = 'set_coeffs_A_{}'

            if u in [values for values in coeffs['A_beta_x']['type'].unique()]:
                init = coeffs['A_beta_x'].query('type == @u')['coeff nr'].values[0]
            else:
                init = [0]

            setattr(model, set_name.format(u), Set(initialize=init, ordered=True))

        for u in full_list:
            # A subsets
            set_name = 'subset_A_{}'
            if u in [values for values in coeffs['A_beta_x']['type'].unique()]:
                init = [tuple(value) for value in coeffs['A_beta_x'].query('type == @u')[['hot', 'cold']].values]
            else:
                init = []
            setattr(model, set_name.format(u), Set(initialize=init, ordered=True, dimen=None))

        for u in full_list:
            # A subsets with existing HEX
            set_name = 'subset_A_{}_ex_loc'
            if u in list(retrofit['existing HEX'].keys()):
                init = [tuple(retrofit['existing HEX'][u][i]['location']) for i in
                         retrofit['existing HEX'][u].keys()]
                print(u)
            else:
                init = []
            setattr(model, set_name.format(u), Set(initialize=init, ordered=True))

        for u in full_list:
            set_name = 'subset_A_{}_ex_iloc'
            if u in retrofit['existing HEX'].keys():
                init = [i for i in retrofit['existing HEX'][u].keys()]
            else:
                init = []
            setattr(model, set_name.format(u), Set(initialize=init, ordered=True))

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # INITIALIZE VARIABLES ##
        idx_con = {}
        if 'Direct' in full_list:
            idx_con['Direct'] = [model.set_PSH, model.set_PSC, model.set_PSH_r, model.set_PSC_r, model.set_StagesDirect, model.set_StagesDirect_Plus]
        if 'UH' in full_list:
            idx_con['UH'] = [model.set_UH, model.set_PSC, model.set_UH_r, model.set_PSC_r, model.set_StagesUH, model.set_StagesUH_Plus]
        if 'UC' in full_list:
            idx_con['UC'] = [model.set_PSH, model.set_UC, model.set_PSH_r, model.set_UC_r, model.set_StagesUC, model.set_StagesUC_Plus]
        if 'UIH' in full_list:
            idx_con['UIH'] = [model.set_UIH, model.set_PSC, model.set_UIH_r, model.set_PSC_r, model.set_StagesUIH, model.set_StagesUIH_Plus]
        if 'UIC' in full_list:
            idx_con['UIC'] = [model.set_PSH, model.set_UIC, model.set_PSH_r, model.set_UIC_r, model.set_StagesUIC, model.set_StagesUIC_Plus]
        if 'CUH' in full_list:
            idx_con['CUH'] = [model.set_CU, model.set_PSC, model.set_CU_r, model.set_PSC_r, model.set_StagesCU, model.set_StagesCU_Plus]
        if 'CUC' in full_list:
            idx_con['CUC'] = [model.set_PSH, model.set_CU, model.set_PSH_r, model.set_CU_r, model.set_StagesCU, model.set_StagesCU_Plus]

        for u in full_list:
            item_name = 'subset_A_{}_ex_iloc'
            item = getattr(model, item_name.format(u))
            idx_con[u].append(item)

            item_name = 'subset_A_{}_ex_loc'
            item = getattr(model, item_name.format(u))
            idx_con[u].append(item)

            item_name = 'subset_A_{}'
            item = getattr(model, item_name.format(u))
            idx_con[u].append(item)

            item_name = 'set_coeffs_A_{}'
            item = getattr(model, item_name.format(u))
            idx_con[u].append(item)

        idx_HS = 0
        idx_CS = 1
        idx_HS_r = 2
        idx_CS_r = 3
        idx_K = 4
        idx_K_Plus = 5
        idx_subset_A_ex_iloc = 6
        idx_subset_A_ex_loc = 7
        idx_subset_A = 8
        idx_coeffs_A = 9

        # temperature nodes of process streams
        model.var_PSH_T = Var(model.set_PSH, addIndex(model.set_Stages), model.set_TS)         # Temperature nodes on hot streams
        model.var_PSC_T = Var(model.set_PSC, addIndex(model.set_Stages), model.set_TS)         # Temperature nodes on cold streams

        # Binary variables to specify active requirement
        model.var_PSH_r_z = Var(model.set_PSH_r, model.set_TS, within=Binary)
        model.var_PSC_r_z = Var(model.set_PSC_r, model.set_TS, within=Binary)

        # Auxiliary variables for stage-wise energy balances
        model.var_PSH_r_Qdot_aux = Var(model.set_PSH_r, model.set_Stages, model.set_TS, within=NonNegativeReals)
        model.var_PSC_r_Qdot_aux = Var(model.set_PSC_r, model.set_Stages, model.set_TS, within=NonNegativeReals)

        # temperatures of conversion units
        if 'CU' in full_list_cu:
            model.var_CUH_T = Var(model.set_CU, model.set_TS)  # Temperature nodes on hot side of conversion unit
            model.var_CUC_T = Var(model.set_CU, model.set_TS)  # Temperature nodes on cold side of conversion unit

        # ports for interfaces
        ports_list = list(set(conversion_units.keys()).intersection(set(full_list_cu)))
        for u in ports_list:
            var_name = 'var_{}_Port'
            set_name = 'set_{}'.format(u)

            var = Var(getattr(model, set_name), model.set_TS, within=NonNegativeReals)

            setattr(model, var_name.format(u), var)
            set_u = getattr(model, set_name)
            for idx, i in enumerate(set_u):
                if u != 'CU' or ((u == 'CU') and ('Heat Pump' in list(conversion_units[u].keys())[idx])):
                    self.ports[u][idx] = Reference(var[i, :])

        for u in ['HS', 'CS']:
            var_name = 'var_{}_Port'
            if u == 'HS':
                set_name_r = 'set_PSH_r'
            else:
                set_name_r = 'set_PSC_r'

            var = Var(getattr(model, set_name_r), model.set_TS, within=NonNegativeReals)
            setattr(model, var_name.format(u), var)
            set_u = getattr(model, set_name_r)
            for idx, i in enumerate(set_u):
                self.ports[u][idx] = Reference(var[i, :])

        for u in full_list:
            set_HS = idx_con[u][idx_HS]  # set of Hot Streams
            set_CS = idx_con[u][idx_CS]  # set of Cold Streams
            set_HS_r = idx_con[u][idx_HS_r]  # set of Hot Streams
            set_CS_r = idx_con[u][idx_CS_r]  # set of Cold Streams
            set_K = idx_con[u][idx_K]  # set of Stages
            set_K_Plus = idx_con[u][idx_K_Plus]  # set of Stages + 1
            set_TS = model.set_TS  # set of time intervals
            subset_ex_iloc = idx_con[u][idx_subset_A_ex_iloc]
            subset_ex_loc = idx_con[u][idx_subset_A_ex_loc]

            # ----------------------------------------------------------------------------------------------------------
            # Basic variables

            # heat transfer direct or by means of Utilities (steam, cooling water, district heating,...)
            var_name = 'var_{}_Qdot'
            setattr(model, var_name.format(u),
                    Var(set_HS, set_CS, set_K, set_TS, within=NonNegativeReals))

            # Binary for existance of HEX (each time interval)
            var_name = 'var_{}_z'
            setattr(model, var_name.format(u),
                    Var(set_HS, set_CS, set_K, set_TS, within=Binary))

            # Binary for requirement selection (each time interval)
            var_name = 'var_{}_r_z'
            setattr(model, var_name.format(u),
                    Var(set_HS_r, set_CS_r, set_K, set_TS, within=Binary))

            # Binary for existance of HEX (overall)
            var_name = 'var_{}_z_max'
            setattr(model, var_name.format(u),
                    Var(set_HS, set_CS, set_K, within=Binary))


            # temperature differences
            var_name = 'var_{}_dT'
            setattr(model, var_name.format(u),
                    Var(set_HS, set_CS, set_K_Plus, set_TS, bounds=(dTmin, None)))

            # LMTD
            var_name = 'var_{}_LMTD'
            setattr(model, var_name.format(u),
                    Var(set_HS, set_CS, set_K, set_TS, bounds=(dTmin, None)))

            # Area
            var_name = 'var_{}_A_add_beta_x'
            setattr(model, var_name.format(u),
                    Var(set_HS, set_CS, set_K, within=NonNegativeReals))

            # ----------------------------------------------------------------------------------------------------------
            # Retrofit variables

            # Additional areas required
            var_name = 'var_{}_A_add_beta_1'
            setattr(model, var_name.format(u),
                    Var(set_HS, set_CS, set_K, within=NonNegativeReals))

            # areas reassigned
            var_name = 'var_{}_A_reassign'
            setattr(model, var_name.format(u),
                    Var(set_HS, set_CS, set_K, within=NonNegativeReals))

            # Binaries z_avail to depict availability of existing HEX area
            var_name = 'var_{}_z_avail'
            setattr(model, var_name.format(u),
                    Var(subset_ex_iloc, within=Binary))

            # Binary for assignment of HEX areas (can only be reassigned in the respective class; i.e. hot utilities, ..)
            var_name = 'var_{}_z_reassign'
            setattr(model, var_name.format(u),
                    Var(set_HS, set_CS, set_K, subset_ex_iloc, within=Binary))

        # ----------------------------------------------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------------------------
        ## SET EQUATIONS ##

        start = time.time()

        # ----------------------------------------------------------------------------------------------------------
        # Ports
        con_name = 'con_{}_Port'

        for u in ports_list:
            if u in ['UH', 'UIH', 'UC', 'UIC']:
                set_K = idx_con[u][idx_K]  # set of Stages
                set_TS = model.set_TS  # set of time intervals

                var_Port = getattr(model, 'var_{}_Port'.format(u))
                var_Qdot = getattr(model, 'var_{}_Qdot'.format(u))

                if u in ['UH', 'UIH']:
                    set_utility = idx_con[u][idx_HS]  # set of Hot Streams
                    set_stream = idx_con[u][idx_CS]  # set of Cold Streams

                    def con_fun(model, u, t):
                        return var_Port[u, t] == sum(var_Qdot[u, streams, k, t] for streams in set_stream for k in set_K)
                elif u in ['UC', 'UIC']:
                    set_stream = idx_con[u][idx_HS]  # set of Hot Streams
                    set_utility = idx_con[u][idx_CS]  # set of Cold Streams

                    def con_fun(model, u, t):
                        return var_Port[u, t] == sum(var_Qdot[streams, u, k, t] for streams in set_stream for k in set_K)

            # try:
                setattr(model, con_name.format(u), Constraint(set_utility, set_TS, rule=con_fun))
            # except:
            #     print()

        for u in ['HS', 'CS']:
            set_TS = model.set_TS  # set of time intervals

            var_Port = getattr(model, 'var_{}_Port'.format(u))

            if u in ['HS']:
                var_activity = getattr(model, 'var_PSH_r_z')
                set_stream = model.set_PSH  # set of Hot Streams
                set_stream_r = model.set_PSH_r  # set of Hot Streams requirements

            if u in ['CS']:
                var_activity = getattr(model, 'var_PSC_r_z')
                set_stream = model.set_PSC  # set of Hot Streams
                set_stream_r = model.set_PSC_r  # set of Hot Streams requirements

            def con_fun(model, u, u_r, t):
                return var_Port[u, u_r, t] == var_activity[u, u_r, t]

            setattr(model, con_name.format(u), Constraint(set_stream_r, set_TS, rule=con_fun))

        # ----------------------------------------------------------------------------------------------------------

        sd = data_input['streamdata']

        def read_sd(i, r, string):
            qry = '`stream nr` == @i & `requirement nr` == @r'
            return sd.query(qry)[string].values[0]

        def read_q_max(i, ir, j, jr, *args):
            if args.__len__() > 0:
                u = args[0]
            q_max_single = q_max[u].loc[(q_max[u]['hot'] == (i, ir)) & (q_max[u]['cold'] == (j, jr))]['q_max'].values[0]
            return q_max_single

        # ----------------------------------------------------------------------------------------------------------
        # Fix schedule

        if self.settings['SCHED']['testing']:

            def fix_sched_PSH(model, i, ir, t):
                return model.var_PSH_r_z[i, ir, t] == int(data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')['activity'].values[0][t])
            model.con_fix_sched_PSH = Constraint(model.set_PSH_r, model.set_TS, rule=fix_sched_PSH,
                                                 doc='Fix schedule for hot streams')

            def fix_sched_PSC(model, j, jr, t):
                return model.var_PSC_r_z[j, jr, t] == int(data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')['activity'].values[0][t])
            model.con_fix_sched_PSC = Constraint(model.set_PSC_r, model.set_TS, rule=fix_sched_PSC,
                                                 doc='Fix schedule for cold streams')

        # ----------------------------------------------------------------------------------------------------------
        # Set in- and outlet temperatures
        if self.settings['SCHED']['active']:
            def assign_T_in_PSH(model, i, t):
                idx_0 = data_input['indices']['hot streams'][i][0]

                shift = sum((read_sd(i, r, 'T in') - read_sd(i, idx_0, 'T in')) * model.var_PSH_r_z[(i, r, t)] for r in data_input['indices']['hot streams'][i][1:])
                return model.var_PSH_T[i, 1, t] == read_sd(i, idx_0, 'T in') + shift
            model.con_assign_T_in_PSH = Constraint(model.set_PSH, model.set_TS, rule=assign_T_in_PSH,
                                                   doc='Set hot inlet temperature')

            # def assign_T_out_PSH(model, i, t):
            #     idx_0 = data_input['indices']['hot streams'][i][0]
            #
            #     shift = sum((read_sd(i, r, 'T out') - read_sd(i, idx_0, 'T out')) * model.var_PSH_r_z[(i, r, t)] for r in data_input['indices']['hot streams'][i][1:])
            #     return model.var_PSH_T[i, stages + 1, t] == read_sd(i, idx_0, 'T out') + shift
            # model.con_assign_T_out_PSH = Constraint(model.set_PSH, model.set_TS, rule=assign_T_out_PSH,
            #                                         doc='Set hot outlet temperature')

            def assign_T_in_PSC(model, j, t):
                idx_0 = data_input['indices']['cold streams'][j][0]

                shift = sum((read_sd(j, r, 'T in') - read_sd(j, idx_0, 'T in')) * model.var_PSC_r_z[(j, r, t)] for r in data_input['indices']['cold streams'][j][1:])
                return model.var_PSC_T[j, stages + 1, t] == read_sd(j, idx_0, 'T in') + shift
            model.con_assign_T_in_PSC = Constraint(model.set_PSC, model.set_TS, rule=assign_T_in_PSC,
                                                   doc='Set cold inlet temperature')

            # def assign_T_out_PSC(model, j, t):
            #     idx_0 = data_input['indices']['cold streams'][j][0]
            #
            #     shift = sum((read_sd(j, r, 'T out') - read_sd(j, idx_0, 'T out')) * model.var_PSC_r_z[(j, r, t)] for r in data_input['indices']['cold streams'][j][1:])
            #     return model.var_PSC_T[j, 1, t] == read_sd(j, idx_0, 'T out') + shift
            # model.con_assign_T_out_PSC = Constraint(model.set_PSC, model.set_TS, rule=assign_T_out_PSC,
            #                                         doc='Set cold outlet temperature')

        else:
            def assign_T_in_PSH(model, i, t):
                IR = data_input['indices']['hot streams'][i]
                return model.var_PSH_T[i, 1, t] == sum([read_sd(i, ir, 'T in')*data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')['activity'].values[0][t] for ir in IR])
            model.con_assign_T_in_PSH = Constraint(model.set_PSH, model.set_TS, rule=assign_T_in_PSH,
                                                   doc='Set hot inlet temperature')

            # def assign_T_out_PSH(model, i, t):
            #     IR = data_input['indices']['hot streams'][i]
            #     return model.var_PSH_T[i, stages + 1, t] == sum([read_sd(i, ir, 'T out')*data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')['activity'].values[0][t] for ir in IR])
            # model.con_assign_T_out_PSH = Constraint(model.set_PSH, model.set_TS, rule=assign_T_out_PSH,
            #                                         doc='Set hot outlet temperature')

            def assign_T_in_PSC(model, j, t):
                JR = data_input['indices']['cold streams'][j]
                return model.var_PSC_T[j, stages + 1, t] == sum([read_sd(j, jr, 'T in')*data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')['activity'].values[0][t] for jr in JR])
            model.con_assign_T_in_PSC = Constraint(model.set_PSC, model.set_TS, rule=assign_T_in_PSC,
                                                   doc='Set cold inlet temperature')

            # def assign_T_out_PSC(model, j, t):
            #     JR = data_input['indices']['cold streams'][j]
            #     return model.var_PSC_T[j, 1, t] == sum([read_sd(j, jr, 'T out')*data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')['activity'].values[0][t] for jr in JR])
            #
            # model.con_assign_T_out_PSC = Constraint(model.set_PSC, model.set_TS, rule=assign_T_out_PSC,
            #                                         doc='Set cold outlet temperature')

        # ----------------------------------------------------------------------------------------------------------
        # Logical Constraints - req. selection
        if self.settings['SCHED']['active']:
            con_name = 'con_req_select_01_{}'

            def con_fun(model, i, t):
                IR = data_input['indices']['hot streams'][i]
                return sum(model.var_PSH_r_z[(i, ir, t)] for ir in IR) <= 1

            setattr(model, con_name.format(u), Constraint(model.set_PSH, model.set_TS, rule=con_fun))

            con_name = 'con_req_select_02_{}'

            def con_fun(model, j, t):
                JR = data_input['indices']['cold streams'][j]
                return sum(model.var_PSC_r_z[(j, jr, t)] for jr in JR) <= 1

            setattr(model, con_name.format(u), Constraint(model.set_PSC, model.set_TS, rule=con_fun))

        # ----------------------------------------------------------------------------------------------------------
        # Monotonic decrease in temperature

        def T_decrease_PSH(model, i, k, t):
            return model.var_PSH_T[i, k, t] >= model.var_PSH_T[i, k + 1, t]
        model.con_T_decrease_PSH = Constraint(model.set_PSH, model.set_Stages, model.set_TS, rule=T_decrease_PSH, doc='ensure monotonic decrease')

        def T_decrease_PSC(model, i, k, t):
            return model.var_PSC_T[i, k, t] >= model.var_PSC_T[i, k + 1, t]
        model.con_T_decrease_PSC = Constraint(model.set_PSC, model.set_Stages, model.set_TS, rule=T_decrease_PSC, doc='ensure monotonic decrease')


        for u in full_list:
            set_K = idx_con[u][idx_K]  # set of Stages
            set_TS = model.set_TS  # set of time intervals
            set_HS = idx_con[u][idx_HS]  # set of Hot Streams
            set_CS = idx_con[u][idx_CS]  # set of Cold Streams
            set_HS_r = idx_con[u][idx_HS_r]  # set of Hot Streams
            set_CS_r = idx_con[u][idx_CS_r]  # set of Cold Streams
            set_01 = model.set_zero_one

            var_z = getattr(model, 'var_{}_z'.format(u))
            var_r_z = getattr(model, 'var_{}_r_z'.format(u))
            var_dT = getattr(model, 'var_{}_dT'.format(u))

            subset_A = idx_con[u][idx_subset_A]
            set_coeffs_A = idx_con[u][idx_coeffs_A]
            subset_ex_iloc = idx_con[u][idx_subset_A_ex_iloc]

            var_A_add_beta_x = getattr(model, 'var_{}_A_add_beta_x'.format(u))
            var_A_add_beta_1 = getattr(model, 'var_{}_A_add_beta_1'.format(u))
            var_A_reassign = getattr(model, 'var_{}_A_reassign'.format(u))
            var_Qdot = getattr(model, 'var_{}_Qdot'.format(u))
            var_LMTD = getattr(model, 'var_{}_LMTD'.format(u))
            var_z = getattr(model, 'var_{}_z'.format(u))
            var_z_reassign = getattr(model, 'var_{}_z_reassign'.format(u))
            var_z_avail = getattr(model, 'var_{}_z_avail'.format(u))
            var_z_max = getattr(model, 'var_{}_z_max'.format(u))

            coeffs_beta_x = coeffs['A_beta_x'].query('type == @u')
            coeffs_beta_1 = coeffs['A_beta_1'].query('type == @u')

            # ----------------------------------------------------------------------------------------------------------
            # Temperature approach
            con_name = 'con_dT_{}'

            if self.settings['SIMP']['max_pair_hex'] == 0:
                z_add = settings['TIGHT']['z_add']
            else:
                z_add = settings['TIGHT']['z_add']

            # fixme: calculation of z needs to be adjusted for the introduction of requirements!
            def con_fun(model, i, j, k, t, zo):
                if u in ['UH', 'UIH']:

                    T_hot_max = list(conversion_units[u].values())[i]['Tin']
                    T_hot_min = list(conversion_units[u].values())[i]['Tout']
                    T_cold_max = max(data_input['streamdata'].query('`stream nr` == @j')['T out'])

                    T_hot = T_hot_max if zo == 0 else T_hot_min
                    T_cold = model.var_PSC_T[j, k + zo, t]


                elif u in ['UC', 'UIC']:
                    T_hot_min = min(data_input['streamdata'].query('`stream nr` == @i')['T out'])
                    T_cold_max = list(conversion_units[u].values())[j]['Tout']
                    T_cold_min = list(conversion_units[u].values())[j]['Tin']

                    T_hot = model.var_PSH_T[i, k + zo, t]
                    T_cold = T_cold_max if zo == 0 else T_cold_min

                elif u in ['CUH']:
                    T_hot_min = list(conversion_units['CU'].values())[i]['Tmin']
                    T_cold_max = max(data_input['streamdata'].query('`stream nr` == @j')['T out'])

                    if (i in model.subset_heat_pump):
                        T_hot = model.var_CUH_T[i, t]
                    elif (i in model.subset_storage):
                        T_hot = model.var_CUH_T[i, t] if zo == 0 else model.var_CUC_T[i, t]
                    T_cold = model.var_PSC_T[j, k + zo, t]

                elif u in ['CUC']:
                    T_hot_min = min(data_input['streamdata'].query('`stream nr` == @i')['T out'])
                    T_cold_max = list(conversion_units['CU'].values())[j]['Tmax']

                    T_hot = model.var_PSH_T[i, k + zo, t]
                    if (j in model.subset_heat_pump):
                        T_cold = model.var_CUC_T[j, t]
                    elif (j in model.subset_storage):
                        T_cold = model.var_CUH_T[j, t] if zo == 0 else model.var_CUC_T[j, t]

                else:
                    T_hot_min = min(data_input['streamdata'].query('`stream nr` == @i')['T out'])
                    T_cold_max = max(data_input['streamdata'].query('`stream nr` == @j')['T out'])

                    T_hot = model.var_PSH_T[i, k + zo, t]
                    T_cold = model.var_PSC_T[j, k + zo, t]

                z = T_cold_max - T_hot_min + dTmin + z_add  # !!!!!!! Wird noch angepasst
                try:
                    dT = T_hot - T_cold
                except:
                    print()

                # if self.settings['SCHED']['active']:
                #     z = 0
                # else:
                if z < 0:
                    z = 0

                if self.settings['SIMP']['max_pair_hex'] == 0:
                    return var_dT[i, j, k + zo, t] <= dT + (1 - var_z[i, j, k, t]) * (z+z_add)
                else:
                    return var_dT[i, j, min(set_K) + zo, t] <= dT + (1 - var_z[i, j, k, t]) * (z+z_add)

            setattr(model, con_name.format(u), Constraint(set_HS, set_CS, set_K, set_TS, set_01, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # Logarithmic mean temperature difference (LMTD)
            con_name = 'con_LMTD_{}'

            if self.settings['SIMP']['max_pair_hex'] == 0:

                def con_fun(model, t, i, j, k, p):
                    expr = (var_LMTD[i, j, k, t] <= var_dT[i, j, k, t] * coeffs['LMTD'][p, 0] + var_dT[
                        i, j, k + 1, t] * coeffs['LMTD'][p, 1])
                    return expr

                setattr(model, con_name.format(u), Constraint(set_TS, set_HS, set_CS, set_K, model.set_coeffs_LMTD, rule=con_fun))
            else:

                def con_fun(model, t, i, j, p):
                    return var_LMTD[i, j, min(set_K), t] <= var_dT[i, j, min(set_K), t] * coeffs['LMTD'][p, 0] + var_dT[
                        i, j, min(set_K)+1, t] * coeffs['LMTD'][p, 1]

                setattr(model, con_name.format(u), Constraint(set_TS, set_HS, set_CS, model.set_coeffs_LMTD, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------

            def check_retro(ij, u):
                """
                This function checks whether a HEX is already placed between steams i and j for type u (e.g. Direct,
                or UH, UC, etc.)

                :param ij: tuple for location (i, j, k)
                :param u: type e.g. Direct, or UH, UC, etc.)
                :return: True/False + Location index if True
                """

                if u in retrofit['existing HEX'].keys():
                    retro = retrofit['existing HEX'][u]  # dict of all hex for type u
                    retro_loc = [values['location'][:len(ij)] for values in list(retro.values())]  # location of hex
                    retro_keys = list(retro.keys())  # list of keys for dict with all hex for type u
                    if ij in retro_loc:  # check if stream pairing ij already has a hex (return True / False, if True also return index of location)
                        return True, retro_keys[retro_loc.index(ij)]
                    else:
                        return False, None
                else:
                    return False, None

            def simp_coeff(coeffs, i, ir, j, jr):
                if type(ir) != str:
                    coeffs_aux = coeffs.loc[(coeffs['hot'] == (i, ir)) & (coeffs['cold'] == (j, jr))]
                else:
                    coeffs_aux = coeffs.loc[
                            ((np.array([val[0] for val in coeffs['hot'].values]) == i) & (
                                    np.array([val[0] for val in coeffs['cold'].values]) == j))]

                coeffs_s = {
                    'C1': coeffs_aux['C1'].values[0],
                    'C2': coeffs_aux['C2'].values[0],
                    'C3': coeffs_aux['C3'].values[0],
                    'A_max': coeffs_aux['A_max'].values[0],
                    'LMTD max': coeffs_aux['LMTD max'].values[0],
                }

                return coeffs_s

            # ----------------------------------------------------------------------------------------------------------
            # Heat exchanger areas (beta = x)
            con_name = 'con_A_beta_x_{}'

            if self.settings['SIMP']['max_pair_hex'] == 0:
                def con_fun(model, t, i, ir, j, jr, k, p):
                    if self.settings['SCHED']['active'] == 0:
                        if u == 'Direct':
                            ir_active = data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')[
                                'activity'].values[0][t]
                            jr_active = data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')[
                                'activity'].values[0][t]
                        elif u in ['UH', 'UIH', 'CUH']:
                            ir_active = True
                            jr_active = data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')[
                                'activity'].values[0][t]
                        elif u in ['UC', 'UIC', 'CUC']:
                            ir_active = data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')[
                                'activity'].values[0][t]
                            jr_active = True
                        if int(jr_active) + int(ir_active) < 2:
                            return Constraint.Skip

                    try:
                        coeffs_aux = simp_coeff(coeffs_beta_x, i, ir, j, jr)
                    except:
                        return Constraint.Skip

                    lhs = var_A_add_beta_x[i, j, k] + var_A_reassign[i, j, k]

                    if type(coeffs_aux['C3']) == np.ndarray:

                        rhs = var_Qdot[i, j, k, t] * coeffs_aux['C2'][p] + \
                                   var_LMTD[i, j, k, t] * coeffs_aux['C1'][p] + \
                                   (var_z[i, j, k, t] - sum(var_z_reassign[i, j, k, M] for M in subset_ex_iloc)) * \
                                   (coeffs_aux['C3'][p] + dTmin * coeffs_aux['C1'][p]) - \
                                   dTmin * coeffs_aux['C1'][p]

                        check, m = check_retro((i, j, k), u)
                        if check:
                            return lhs >= rhs - (1 - var_z_avail[m]) * (coeffs_aux['C3'][p] + dTmin * coeffs_aux['C1'][p])
                        else:
                            return lhs >= rhs

                    else:

                        rhs = var_Qdot[i, j, k, t] * coeffs_aux['C1'] + \
                              (var_z[i, j, k, t] - sum(var_z_reassign[i, j, k, M] for M in subset_ex_iloc)) * \
                              coeffs_aux['C2']

                        check, m = check_retro((i, j, k), u)
                        if check:
                            return lhs >= rhs - (1 - var_z_avail[m]) * coeffs_aux['C2']
                        else:
                            return lhs >= rhs

                setattr(model, con_name.format(u), Constraint(set_TS, set_HS_r, set_CS_r, set_K, set_coeffs_A, rule=con_fun))
            else:
                def con_fun(model, t, i, ir, j, jr, p):
                    if self.settings['SCHED']['active'] == 0:
                        if u == 'Direct':
                            ir_active = data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')['activity'].values[0][t]
                            jr_active = data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')['activity'].values[0][t]
                        elif u in ['UH', 'UIH', 'CUH']:
                            ir_active = True
                            jr_active = data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')['activity'].values[0][t]
                        elif u in ['UC', 'UIC', 'CUC']:
                            ir_active = data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')['activity'].values[0][t]
                            jr_active = True

                        if int(jr_active) + int(ir_active) < 2:
                            return Constraint.Skip
                    try:
                        coeffs_aux = simp_coeff(coeffs_beta_x, i, ir, j, jr)
                    except:
                        return Constraint.Skip

                    k = min(set_K)

                    lhs = var_A_add_beta_x[i, j, k] + var_A_reassign[i, j, k]

                    if type(coeffs_aux['C3']) == np.ndarray:


                        rhs = sum(var_Qdot[i, j, K, t] for K in set_K) * coeffs_aux['C2'][p] + \
                              var_LMTD[i, j, k, t] * coeffs_aux['C1'][p] + \
                              (sum(var_z[i, j, K, t] for K in set_K) - sum(var_z_reassign[i, j, K, M] for K in set_K for M in subset_ex_iloc)) * \
                              (coeffs_aux['C3'][p] + dTmin * coeffs_aux['C1'][p]) - \
                              dTmin * coeffs_aux['C1'][p]


                        check, m = check_retro((i, j), u)
                        if check:
                            return lhs >= rhs - (1 - var_z_avail[m]) * (
                                        coeffs_aux['C3'][p] + dTmin * coeffs_aux['C1'][p])
                        else:
                            return lhs >= rhs


                    else:

                        rhs = sum(var_Qdot[i, j, K, t] for K in set_K) * coeffs_aux['C1'] + \
                              (sum(var_z[i, j, K, t] for K in set_K) - sum(var_z_reassign[i, j, K, M] for K in set_K for M in subset_ex_iloc)) * \
                              coeffs_aux['C2']

                        check, m = check_retro((i, j), u)
                        if check:
                            return lhs >= rhs - (1 - var_z_avail[m]) * coeffs_aux['C2']
                        else:
                            return lhs >= rhs

                setattr(model, con_name.format(u), Constraint(set_TS, set_HS_r, set_CS_r, set_coeffs_A, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # Heat exchanger areas (beta = 1)
            con_name = 'con_A_beta_1_{}'

            if self.settings['SIMP']['max_pair_hex'] == 0:
                def con_fun(model, t, i, ir, j, jr, k, p):
                    if self.settings['SCHED']['active'] == 0:
                        if u == 'Direct':
                            ir_active = data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')[
                                'activity'].values[0][t]
                            jr_active = data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')[
                                'activity'].values[0][t]
                        elif u in ['UH', 'UIH', 'CUH']:
                            ir_active = True
                            jr_active = data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')[
                                'activity'].values[0][t]
                        elif u in ['UC', 'UIC', 'CUC']:
                            ir_active = data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')[
                                'activity'].values[0][t]
                            jr_active = True
                        if jr_active + ir_active < 2:
                            return Constraint.Skip
                        
                    try:
                        coeffs_aux = simp_coeff(coeffs_beta_1, i, ir, j, jr)
                    except:
                        return Constraint.Skip

                    lhs = var_A_add_beta_1[i, j, k] + var_A_reassign[i, j, k]

                    if type(coeffs_aux['C3']) == np.ndarray:

                        rhs = var_Qdot[i, j, k, t] * coeffs_aux['C2'][p] + \
                              var_LMTD[i, j, k, t] * coeffs_aux['C1'][p] + \
                              coeffs_aux['C3'][p] - \
                              (1 - sum(var_z_reassign[i, j, k, M] for M in subset_ex_iloc)) * coeffs_aux['A_max']

                    else:

                        rhs = var_Qdot[i, j, k, t] * coeffs_aux['C1'] + coeffs_aux['C2'] - \
                              (1 - sum(var_z_reassign[i, j, k, M] for M in subset_ex_iloc)) * coeffs_beta_1['A_max'][
                                  t, i, j]

                    check, m = check_retro((i, j, k), u)
                    if check:
                        return lhs >= rhs + (1 - var_z_avail[m]) * coeffs_aux['A_max']
                    else:
                        return lhs >= rhs

                setattr(model, con_name.format(u), Constraint(set_TS, set_HS_r, set_CS_r, set_K, set_coeffs_A, rule=con_fun))
            else:
                def con_fun(model, t, i, ir, j, jr, p):
                    if self.settings['SCHED']['active'] == 0:
                        if u == 'Direct':
                            ir_active = data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')[
                                'activity'].values[0][t]
                            jr_active = data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')[
                                'activity'].values[0][t]
                        elif u in ['UH', 'UIH', 'CUH']:
                            ir_active = True
                            jr_active = data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')[
                                'activity'].values[0][t]
                        elif u in ['UC', 'UIC', 'CUC']:
                            ir_active = data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')[
                                'activity'].values[0][t]
                            jr_active = True
                        if jr_active + ir_active < 2:
                            return Constraint.Skip
                        
                    try:
                        coeffs_aux = simp_coeff(coeffs_beta_1, i, ir, j, jr)
                    except:
                        return Constraint.Skip

                    k = min(set_K)

                    lhs = var_A_add_beta_1[i, j, k] + var_A_reassign[i, j, k]

                    if type(coeffs_aux['C3']) == np.ndarray:

                        rhs = sum(var_Qdot[i, j, K, t] for K in set_K) * coeffs_aux['C2'][p] + \
                              var_LMTD[i, j, k, t] * coeffs_aux['C1'][p] + \
                              coeffs_aux['C3'][p] - \
                              (1 - sum(var_z_reassign[i, j, K, M] for K in set_K for M in subset_ex_iloc)) * \
                              coeffs_aux['A_max']

                    else:
                        rhs = sum(var_Qdot[i, j, K, t] for K in set_K) * coeffs_aux['C1'] + coeffs_aux['C2'] - \
                              (1 - sum(var_z_reassign[i, j, K, M] for K in set_K for M in subset_ex_iloc)) * coeffs_aux[
                                  'A_max']

                    check, m = check_retro((i, j), u)
                    if check:
                        return lhs >= rhs + (1 - var_z_avail[m]) * coeffs_aux['A_max']
                    else:
                        return lhs >= rhs

                setattr(model, con_name.format(u), Constraint(set_TS, set_HS_r, set_CS_r, set_coeffs_A, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # Linearization of additional HEX area for retrofit example cases

            con_name = 'con_A_add_lin_{}'

            if self.settings['SIMP']['max_pair_hex'] == 0:
                def con_fun(model, i, j, k, m):
                    try:
                        coeffs_aux = simp_coeff(coeffs_beta_1, i, 'all', j, 'all')
                    except:
                        return Constraint.Skip

                    x = np.linspace(0, retrofit['existing HEX'][u][m]['area']*settings['RETROFIT']['add_hex'], settings['LIN']['res_add_HEX'])
                    # x = np.linspace(0, retrofit['existing HEX'][u][m]['area'], settings['LIN']['res_add_HEX'])
                    y = x ** settings['COSTS']['beta']
                    C = np.mean(x * y) / np.mean(x ** 2)

                    lhs = var_A_add_beta_x[i, j, k]
                    rhs = var_A_add_beta_1[i, j, k] * C - C * coeffs_aux['A_max'] * \
                               (1 - var_z_reassign[i, j, k, m])

                    check, M = check_retro((i, j, k), u)
                    if check:
                        return lhs >= rhs + C * coeffs_aux['A_max'] * (1 - var_z_avail[M])
                    else:
                        return lhs >= rhs

                setattr(model, con_name.format(u), Constraint(set_HS, set_CS, set_K, subset_ex_iloc, rule=con_fun))
            else:
                def con_fun(model, i, j, m):
                    try:
                        coeffs_aux = simp_coeff(coeffs_beta_1, i, 'all', j, 'all')
                    except:
                        return Constraint.Skip

                    k = min(set_K)

                    x = np.linspace(0, retrofit['existing HEX'][u][m]['area']*settings['RETROFIT']['add_hex'], settings['LIN']['res_add_HEX'])
                    # x = np.linspace(0, retrofit['existing HEX'][u][m]['area'], settings['LIN']['res_add_HEX'])
                    y = x ** self.settings['COSTS']['beta']
                    C = np.mean(x * y) / np.mean(x ** 2)

                    apen_plots = 0
                    if apen_plots:
                        fig = plt.figure()
                        plt.plot(x, y, 'k')
                        plt.plot(x, x*C, 'r')

                        plt.xlabel('Additional area (m²)')
                        plt.ylabel('Discounted area (m²)')

                        plt.show()



                    lhs = var_A_add_beta_x[i, j, k]
                    rhs = var_A_add_beta_1[i, j, k] * C - C * coeffs_aux['A_max'] * \
                          (1 - sum(var_z_reassign[i, j, K, m] for K in set_K))

                    check, M = check_retro((i, j), u)
                    if check:
                        return lhs >= rhs + C * coeffs_aux['A_max'] * (1 - var_z_avail[M])
                    else:
                        return lhs >= rhs

                setattr(model, con_name.format(u), Constraint(set_HS, set_CS, subset_ex_iloc, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # Restrict additional HEX area for retrofit example cases
            #
            # HEX area of an already existing HEX can only be extended to extent

            con_name = 'con_A_add_restrict_{}'

            if self.settings['SIMP']['max_pair_hex'] == 0:
                def con_fun(model, i, j, k, m):
                    try:
                        coeffs_aux = simp_coeff(coeffs_beta_1, i, 'all', j, 'all')
                    except:
                        return Constraint.Skip

                    lhs = var_A_add_beta_1[i, j, k]
                    rhs = retrofit['existing HEX'][u][m]['area'] * self.settings['RETROFIT']['add_hex'] + coeffs_aux['A_max'] * \
                               (1 - var_z_reassign[i, j, k, m])

                    check, M = check_retro((i, j, k), u)
                    if check:
                        return lhs <= rhs - coeffs_aux['A_max'] * (1 - var_z_avail[M])
                    else:
                        return lhs <= rhs
                setattr(model, con_name.format(u), Constraint(set_HS, set_CS, set_K, subset_ex_iloc, rule=con_fun))
            else:
                def con_fun(model, i, j, m):
                    try:
                        coeffs_aux = simp_coeff(coeffs_beta_1, i, 'all', j, 'all')
                    except:
                        return Constraint.Skip

                    k = min(set_K)

                    lhs = var_A_add_beta_1[i, j, k]
                    rhs = retrofit['existing HEX'][u][m]['area'] * self.settings['RETROFIT']['add_hex'] + \
                          coeffs_aux['A_max'] * (1 - sum(var_z_reassign[i, j, K, m] for K in set_K))

                    check, M = check_retro((i, j), u)
                    if check:
                        return lhs <= rhs - coeffs_aux['A_max'] * (1 - var_z_avail[M])
                    else:
                        return lhs <= rhs
                setattr(model, con_name.format(u), Constraint(set_HS, set_CS, subset_ex_iloc, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # HEX area reassignment

            con_name = 'con_A_reassign_{}'

            if self.settings['SIMP']['max_pair_hex'] == 0:
                def con_fun(model, i, j, k):
                    lhs = var_A_reassign[i, j, k]
                    rhs = sum([retrofit['existing HEX'][u][M]['area'] * var_z_reassign[i, j, k, M] for M in subset_ex_iloc])

                    check, m = check_retro((i, j, k), u)
                    if check:
                        return lhs == rhs + retrofit['existing HEX'][u][m]['area'] * (1 - var_z_avail[m])
                    else:
                        return lhs == rhs
                setattr(model, con_name.format(u), Constraint(set_HS, set_CS, set_K, rule=con_fun))
            else:
                def con_fun(model, i, j):
                    k = min(set_K)

                    lhs = var_A_reassign[i, j, k]
                    rhs = sum([retrofit['existing HEX'][u][M]['area'] * var_z_reassign[i, j, K, M] for K in set_K for M in
                               subset_ex_iloc])

                    check, m = check_retro((i, j), u)
                    if check:
                        return lhs == rhs + retrofit['existing HEX'][u][m]['area'] * (1 - var_z_avail[m])
                    else:
                        return lhs == rhs
                setattr(model, con_name.format(u), Constraint(set_HS, set_CS, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # HEX reuse

            con_name = 'con_z_reuse_{}'

            if not self.settings['RETROFIT']['reuse']:
                def con_fun(model):
                    # expr = sum(var_z_reassign[i, j, k, m] for i in set_HS for j in set_CS for k in set_K for m in subset_ex_iloc)
                    expr = summation(var_z_reassign)
                    # if expr == 0:
                    #     return Constraint.Skip
                    # else:
                    return expr == 0
                setattr(model, con_name.format(u), Constraint(rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # Logical Constraints - Q_dot max

            con_name = 'con_Q_dot_max_{}'
            
            if self.settings['SCHED']['active']:
                def con_fun(model, i, j, k, t):
                    if u == 'Direct':
                        IR = data_input['indices']['hot streams'][i]
                        JR = data_input['indices']['cold streams'][j]
                    elif u in ['UH', 'UIH', 'CUH']:
                        if u == 'CUH':
                            IR = [idx[1] for idx in data_input['indices']['CU'] if idx[0] == i]
                        else:
                            IR = [idx[1] for idx in data_input['indices'][u] if idx[0] == i]
                        JR = data_input['indices']['cold streams'][j]
                    elif u in ['UC', 'UIC', 'CUC']:
                        if u == 'CUC':
                            JR = [idx[1] for idx in data_input['indices']['CU'] if idx[0] == j]
                        else:
                            JR = [idx[1] for idx in data_input['indices'][u] if idx[0] == j]
                        IR = data_input['indices']['hot streams'][i]
                    return var_Qdot[i, j, k, t] <= sum(read_q_max(i, ir, j, jr, u) * var_r_z[i, ir, j, jr, k, t] for ir in IR for jr in JR)
                
            else:
                def con_fun(model, i, j, k, t):
                    if u == 'Direct':
                        IR = data_input['indices']['hot streams'][i]
                        JR = data_input['indices']['cold streams'][j]
                    elif u in ['UH', 'UIH', 'CUH']:
                        if u == 'CUH':
                            IR = [idx[1] for idx in data_input['indices']['CU'] if idx[0] == i]
                        else:
                            IR = [idx[1] for idx in data_input['indices'][u] if idx[0] == i]
                        JR = data_input['indices']['cold streams'][j]
                    elif u in ['UC', 'UIC', 'CUC']:
                        if u == 'CUC':
                            JR = [idx[1] for idx in data_input['indices']['CU'] if idx[0] == j]
                        else:
                            JR = [idx[1] for idx in data_input['indices'][u] if idx[0] == j]
                        IR = data_input['indices']['hot streams'][i]
                    if u == 'Direct':
                        return var_Qdot[i, j, k, t] <= var_z[i, j, k, t] * sum([read_q_max(i, ir, j, jr, u) *
                                                                                data_input['activity'].query(
                                                                                    '`stream nr` == @i & `requirement nr` == @ir')[
                                                                                    'activity'].values[0][t] *
                                                                                data_input['activity'].query(
                                                                                    '`stream nr` == @j & `requirement nr` == @jr')[
                                                                                    'activity'].values[0][t] for ir in
                                                                                IR for jr in JR])

                    elif u in ['UH', 'UIH', 'CUH']:
                        return var_Qdot[i, j, k, t] <= var_z[i, j, k, t] * sum([read_q_max(i, ir, j, jr, u) *
                                                                                data_input['activity'].query(
                                                                                    '`stream nr` == @j & `requirement nr` == @jr')[
                                                                                    'activity'].values[0][t] for ir in
                                                                                IR for jr in JR])

                    elif u in ['UC', 'UIC', 'CUC']:
                        return var_Qdot[i, j, k, t] <= var_z[i, j, k, t] * sum([read_q_max(i, ir, j, jr, u) *
                                                                                data_input['activity'].query(
                                                                                    '`stream nr` == @i & `requirement nr` == @ir')[
                                                                                    'activity'].values[0][t] for ir in
                                                                                IR for jr in JR])

            setattr(model, con_name.format(u), Constraint(set_HS, set_CS, set_K, set_TS, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # Logical Constraints - req. selection

            if self.settings['SCHED']['active']:
                con_name = 'con_req_select_{}'
    
                def con_fun(model, i, j, k, t):
                    if u == 'Direct':
                        IR = data_input['indices']['hot streams'][i]
                        JR = data_input['indices']['cold streams'][j]
                    elif u in ['UH', 'UIH', 'CUH']:
                        if u == 'CUH':
                            IR = [idx[1] for idx in data_input['indices']['CU'] if idx[0] == i]
                        else:
                            IR = [idx[1] for idx in data_input['indices'][u] if idx[0] == i]
                        JR = data_input['indices']['cold streams'][j]
                    elif u in ['UC', 'UIC', 'CUC']:
                        if u == 'CUC':
                            JR = [idx[1] for idx in data_input['indices']['CU'] if idx[0] == j]
                        else:
                            JR = [idx[1] for idx in data_input['indices'][u] if idx[0] == j]
                        IR = data_input['indices']['hot streams'][i]
    
                    return var_z[i, j, k, t] >= sum(var_r_z[i, ir, j, jr, k, t] for ir in IR for jr in JR)
    
                setattr(model, con_name.format(u), Constraint(set_HS, set_CS, set_K, set_TS, rule=con_fun))

                # ----------------------------------------------------------------------------------------------------------
                # Logical Constraints - req. selection
    
                con_name = 'con_req_select_2_{}'
    
                def con_fun(model, i, ir, j, jr, k, t):
                    if u == ['Direct', 'UC', 'UIC', 'CUC']:
                        stream_z_r = model.var_PSH_r_z[i, ir, t]
                        return var_r_z[i, ir, j, jr, k, t] <= stream_z_r
                    else:
                        return Constraint.Skip
    
                setattr(model, con_name.format(u), Constraint(set_HS_r, set_CS_r, set_K, set_TS, rule=con_fun))

                # ----------------------------------------------------------------------------------------------------------
                # Logical Constraints - req. selection
    
                con_name = 'con_req_select_3_{}'
    
                def con_fun(model, i, ir, j, jr, k, t):
                    if u == ['Direct', 'UH', 'UIH', 'CUH']:
                        stream_z_r = model.var_PSC_r_z[j, jr, t]
                        return var_r_z[i, ir, j, jr, k, t] <= stream_z_r
                    else:
                        return Constraint.Skip
    
                setattr(model, con_name.format(u), Constraint(set_HS_r, set_CS_r, set_K, set_TS, rule=con_fun))



            # ----------------------------------------------------------------------------------------------------------
            # Logical Constraints - single HEX per pair

            con_name = 'con_single_HEX_{}'

            if self.settings['SIMP']['max_pair_hex'] == 1:
                def con_fun(model, i, j):
                    return sum(var_z_max[i, j, k] for k in set_K) <= 1
                setattr(model, con_name.format(u), Constraint(set_HS, set_CS, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # Logical Constraints - z max

            con_name = 'con_z_max_{}'

            def con_fun(model, i, j, k, t):
                return var_z[i, j, k, t] <= var_z_max[i, j, k]
            setattr(model, con_name.format(u), Constraint(set_HS, set_CS, set_K, set_TS, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # Logical Constraints - equal z for every period

            con_name = 'con_z_equal_{}'

            if self.settings['SIMP']['equal z'] is True:
                def con_fun(model, i, j, k, t):
                    return var_z[i, j, k, t] >= var_z_max[i, j, k]
                setattr(model, con_name.format(u), Constraint(set_HS, set_CS, set_K, set_TS, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # Logical Constraints - z max upper bound

            # con_name = 'con_z_max_ub_{}'
            #
            # def con_fun(model, i, j, k):
            #     if (i, j) in [value[1:] for value in coeffs_beta_x['A_max'].index]:
            #         z = 1
            #     else:
            #         z = 0
            #
            #     return var_z_max[i, j, k] <= z
            # setattr(model, con_name.format(u), Constraint(set_HS, set_CS, set_K, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # Logical Constraints - z max reassign

            con_name = 'con_z_max_reassign_{}'

            def con_fun(model, i, j, k):
                return sum([var_z_reassign[i, j, k, M] for M in subset_ex_iloc]) <= var_z_max[i, j, k]
            setattr(model, con_name.format(u), Constraint(set_HS, set_CS, set_K, rule=con_fun))

            # ----------------------------------------------------------------------------------------------------------
            # Logical Constraints - z reassign / z avail

            con_name = 'con_z_reassign_avail_{}'

            def con_fun(model, m):
                return sum([var_z_reassign[i, j, k, m] for i in set_HS for j in set_CS for k in set_K]) <= var_z_avail[m]
            setattr(model, con_name.format(u), Constraint(subset_ex_iloc, rule=con_fun))

        # ----------------------------------------------------------------------------------------------------------
        # Energy Balances
        # ---------------------------------------------------------------------------------------------------------
        set_TS = model.set_TS  # set of time intervals

        var_Qdot_Direct = getattr(model, 'var_{}_Qdot'.format('Direct'))

        # ---------------------------------------------------------------------------------------------------------
        # Hot Process Streams balance

        con_name = 'con_e_balance_hot_stream'

        if self.settings['SCHED']['active']:
            def con_fun(model, i, t):
                Qdot_stream = sum((read_sd(i, r, 'T in') - read_sd(i, r, 'T out')) * \
                                  read_sd(i, r, 'm') * read_sd(i, r, 'cp') * model.var_PSH_r_z[(i, r, t)] for r in
                                  data_input['indices']['hot streams'][i])
                
                lhs = sum(
                    var_Qdot_Direct[i, j, k, t] for j in idx_con['Direct'][idx_CS] for k in idx_con['Direct'][idx_K])
                for u in [x for x in full_list_wo_direct if x[-1] == 'C']:
                    var_Qdot = getattr(model, 'var_{}_Qdot'.format(u))
                    lhs = lhs + sum(var_Qdot[i, j, k, t] for j in idx_con[u][idx_CS] for k in idx_con[u][idx_K])
    
                if np.max([read_sd(i, r, 'soft') for r in data_input['indices']['hot streams'][i]]) == 0:
                    return lhs == Qdot_stream
                else:
                    return lhs <= Qdot_stream
        else:
            
            def con_fun(model, i, t):
                
                Qdot_stream = sum([(read_sd(i, ir, 'T in') - read_sd(i, ir, 'T out')) * \
                                   read_sd(i, ir, 'm') * read_sd(i, ir, 'cp') *
                                   data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')[
                                       'activity'].values[0][t] for ir in data_input['indices']['hot streams'][i]])

                lhs = sum(
                    var_Qdot_Direct[i, j, k, t] for j in idx_con['Direct'][idx_CS] for k in idx_con['Direct'][idx_K])
                for u in [x for x in full_list_wo_direct if x[-1] == 'C']:
                    var_Qdot = getattr(model, 'var_{}_Qdot'.format(u))
                    lhs = lhs + sum(var_Qdot[i, j, k, t] for j in idx_con[u][idx_CS] for k in idx_con[u][idx_K])

                if np.max([read_sd(i, r, 'soft') for r in data_input['indices']['hot streams'][i]]) == 0:
                    return lhs == Qdot_stream
                else:
                    return lhs <= Qdot_stream
        setattr(model, con_name, Constraint(idx_con['Direct'][idx_HS], set_TS, rule=con_fun))

        # ---------------------------------------------------------------------------------------------------------
        # Cold Process Streams balance

        con_name = 'con_e_balance_cold_stream'

        if self.settings['SCHED']['active']:
            def con_fun(model, j, t):
                Qdot_stream = sum((read_sd(j, r, 'T out') - read_sd(j, r, 'T in')) * \
                              read_sd(j, r, 'm') * read_sd(j, r, 'cp') * model.var_PSC_r_z[(j, r, t)] for r in data_input['indices']['cold streams'][j])
    
                lhs = sum(var_Qdot_Direct[i, j, k, t] for i in idx_con['Direct'][idx_HS] for k in idx_con['Direct'][idx_K])
                for u in [x for x in full_list_wo_direct if x[-1] == 'H']:
                    var_Qdot = getattr(model, 'var_{}_Qdot'.format(u))
                    lhs = lhs + sum(var_Qdot[i, j, k, t] for i in idx_con[u][idx_HS] for k in idx_con[u][idx_K])
    
                if np.max([read_sd(j, r, 'soft') for r in data_input['indices']['cold streams'][j]]) == 0:
                    return lhs == Qdot_stream
                else:
                    return lhs <= Qdot_stream
        else:

            def con_fun(model, j, t):
                Qdot_stream = sum([(read_sd(j, jr, 'T out') - read_sd(j, jr, 'T in')) * \
                     read_sd(j, jr, 'm') * read_sd(j, jr, 'cp') *
                     data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')[
                         'activity'].values[0][t] for jr in data_input['indices']['cold streams'][j]])

                lhs = sum(
                    var_Qdot_Direct[i, j, k, t] for i in idx_con['Direct'][idx_HS] for k in idx_con['Direct'][idx_K])
                for u in [x for x in full_list_wo_direct if x[-1] == 'H']:
                    var_Qdot = getattr(model, 'var_{}_Qdot'.format(u))
                    lhs = lhs + sum(var_Qdot[i, j, k, t] for i in idx_con[u][idx_HS] for k in idx_con[u][idx_K])

                if np.max([read_sd(j, r, 'soft') for r in data_input['indices']['cold streams'][j]]) == 0:
                    return lhs == Qdot_stream
                else:
                    return lhs <= Qdot_stream
        setattr(model, con_name, Constraint(idx_con['Direct'][idx_CS], set_TS, rule=con_fun))

        # ---------------------------------------------------------------------------------------------------------
        # Hot Process Streams balance stage-wise
        con_name = 'con_e_balance_hot_stream_stages'

        if self.settings['SCHED']['active']:
            def con_fun(model, i, k, t):
                IR = data_input['indices']['hot streams'][i]

                k_set = set({k})
                lhs = sum(var_Qdot_Direct[i, j, k, t] for j in idx_con['Direct'][idx_CS] if
                          k_set.issubset(model.set_StagesDirect.data()))
                for u in [x for x in full_list_wo_direct if x[-1] == 'C']:
                    var_Qdot = getattr(model, 'var_{}_Qdot'.format(u))
                    lhs = lhs + sum(
                        var_Qdot[i, j, k, t] for j in idx_con[u][idx_CS] if k_set.issubset(idx_con[u][idx_K].data()))

                rhs = sum(model.var_PSH_r_Qdot_aux[i, ir, k, t] for ir in IR)
                con = (lhs == rhs)

                if con is True:
                    return Constraint.Skip
                else:
                    return con
        else:

            def con_fun(model, i, k, t):
                IR = data_input['indices']['hot streams'][i]

                k_set = set({k})
                lhs = sum(var_Qdot_Direct[i, j, k, t] for j in idx_con['Direct'][idx_CS] if
                          k_set.issubset(model.set_StagesDirect.data()))
                for u in [x for x in full_list_wo_direct if x[-1] == 'C']:
                    var_Qdot = getattr(model, 'var_{}_Qdot'.format(u))
                    lhs = lhs + sum(
                        var_Qdot[i, j, k, t] for j in idx_con[u][idx_CS] if k_set.issubset(idx_con[u][idx_K].data()))

                mcp = sum([read_sd(i, ir, 'm') * read_sd(i, ir, 'cp') *
                                   data_input['activity'].query('`stream nr` == @i & `requirement nr` == @ir')[
                                       'activity'].values[0][t] for ir in IR])

                rhs = mcp * (model.var_PSH_T[i, k, t] - model.var_PSH_T[i, k + 1, t])

                con = (lhs == rhs)

                if con is True:
                    return Constraint.Skip
                else:
                    return con

        setattr(model, con_name, Constraint(idx_con['Direct'][idx_HS], model.set_Stages, set_TS, rule=con_fun))

        if self.settings['SCHED']['active']:
            con_name = 'con_e_balance_hot_stream_stages_aux_1'

            def con_fun(model, i, ir, k, t):
                mcp = read_sd(i, ir, 'm') * read_sd(i, ir, 'cp')
                dTmax = read_sd(i, ir, 'T in') - read_sd(i, ir, 'T out')

                dT = model.var_PSH_T[i, k, t] - model.var_PSH_T[i, k + 1, t]
                r_z = model.var_PSH_r_z[i, ir, t]
                q_aux = model.var_PSH_r_Qdot_aux[i, ir, k, t]

                return dT * mcp - (1 - r_z) * dTmax * mcp <= q_aux


            setattr(model, con_name, Constraint(idx_con['Direct'][idx_HS_r], model.set_Stages, set_TS, rule=con_fun))

            con_name = 'con_e_balance_hot_stream_stages_aux_2'

            def con_fun(model, i, ir, k, t):
                mcp = read_sd(i, ir, 'm') * read_sd(i, ir, 'cp')

                dT = model.var_PSH_T[i, k, t] - model.var_PSH_T[i, k + 1, t]
                q_aux = model.var_PSH_r_Qdot_aux[i, ir, k, t]

                return dT * mcp >= q_aux

            setattr(model, con_name, Constraint(idx_con['Direct'][idx_HS_r], model.set_Stages, set_TS, rule=con_fun))

            con_name = 'con_e_balance_hot_stream_stages_aux_3'

            def con_fun(model, i, ir, k, t):
                mcp = read_sd(i, ir, 'm') * read_sd(i, ir, 'cp')
                dTmax = read_sd(i, ir, 'T in') - read_sd(i, ir, 'T out')

                r_z = model.var_PSH_r_z[i, ir, t]
                q_aux = model.var_PSH_r_Qdot_aux[i, ir, k, t]

                return r_z * dTmax * mcp >= q_aux

            setattr(model, con_name, Constraint(idx_con['Direct'][idx_HS_r], model.set_Stages, set_TS, rule=con_fun))


        # ---------------------------------------------------------------------------------------------------------
        # Cold Process Streams balance stage-wise

        con_name = 'con_e_balance_cold_stream_stages'

        if self.settings['SCHED']['active']:
            def con_fun(model, j, k, t):
                JR = data_input['indices']['cold streams'][j]

                k_set = set({k})
                lhs = sum(var_Qdot_Direct[i, j, k, t] for i in idx_con['Direct'][idx_HS] if k_set.issubset(model.set_StagesDirect.data()))
                for u in [x for x in full_list_wo_direct if x[-1] == 'H']:
                    var_Qdot = getattr(model, 'var_{}_Qdot'.format(u))
                    lhs = lhs + sum(var_Qdot[i, j, k, t] for i in idx_con[u][idx_HS] if k_set.issubset(idx_con[u][idx_K].data()))

                rhs = sum(model.var_PSC_r_Qdot_aux[j, jr, k, t] for jr in JR)
                con = (lhs == rhs)

                if con is True:
                    return Constraint.Skip
                else:
                    return con

        else:
            def con_fun(model, j, k, t):
                JR = data_input['indices']['cold streams'][j]

                k_set = set({k})
                lhs = sum(var_Qdot_Direct[i, j, k, t] for i in idx_con['Direct'][idx_HS] if
                          k_set.issubset(model.set_StagesDirect.data()))
                for u in [x for x in full_list_wo_direct if x[-1] == 'H']:
                    var_Qdot = getattr(model, 'var_{}_Qdot'.format(u))
                    lhs = lhs + sum(
                        var_Qdot[i, j, k, t] for i in idx_con[u][idx_HS] if k_set.issubset(idx_con[u][idx_K].data()))

                mcp = sum([read_sd(j, jr, 'm') * read_sd(j, jr, 'cp') *
                           data_input['activity'].query('`stream nr` == @j & `requirement nr` == @jr')[
                               'activity'].values[0][t] for jr in JR])

                rhs = mcp * (model.var_PSC_T[j, k, t] - model.var_PSC_T[j, k + 1, t])
                con = (lhs == rhs)

                if con is True:
                    return Constraint.Skip
                else:
                    return con
        setattr(model, con_name, Constraint(idx_con['Direct'][idx_CS], model.set_Stages, set_TS, rule=con_fun))

        if self.settings['SCHED']['active']:
            con_name = 'con_e_balance_cold_stream_stages_aux_1'

            def con_fun(model, j, jr, k, t):
                mcp = read_sd(j, jr, 'm') * read_sd(j, jr, 'cp')
                dTmax = read_sd(j, jr, 'T out') - read_sd(j, jr, 'T in')

                dT = model.var_PSC_T[j, k, t] - model.var_PSC_T[j, k + 1, t]
                r_z = model.var_PSC_r_z[j, jr, t]
                q_aux = model.var_PSC_r_Qdot_aux[j, jr, k, t]

                return dT * mcp - (1 - r_z) * dTmax * mcp <= q_aux

            setattr(model, con_name, Constraint(idx_con['Direct'][idx_CS_r], model.set_Stages, set_TS, rule=con_fun))

            con_name = 'con_e_balance_cold_stream_stages_aux_2'

            def con_fun(model, j, jr, k, t):
                mcp = read_sd(j, jr, 'm') * read_sd(j, jr, 'cp')

                dT = model.var_PSC_T[j, k, t] - model.var_PSC_T[j, k + 1, t]
                q_aux = model.var_PSC_r_Qdot_aux[j, jr, k, t]

                return dT * mcp >= q_aux

            setattr(model, con_name, Constraint(idx_con['Direct'][idx_CS_r], model.set_Stages, set_TS, rule=con_fun))

            con_name = 'con_e_balance_cold_stream_stages_aux_3'

            def con_fun(model, j, jr, k, t):
                mcp = read_sd(j, jr, 'm') * read_sd(j, jr, 'cp')
                dTmax = read_sd(j, jr, 'T out') - read_sd(j, jr, 'T in')

                r_z = model.var_PSC_r_z[j, jr, t]
                q_aux = model.var_PSC_r_Qdot_aux[j, jr, k, t]

                return r_z * dTmax * mcp >= q_aux

            setattr(model, con_name, Constraint(idx_con['Direct'][idx_CS_r], model.set_Stages, set_TS, rule=con_fun))

        # ----------------------------------------------------------------------------------------------------------
        # Conversion Units
        # ---------------------------------------------------------------------------------------------------------

        # def CU_heat_pump(model):
        #     eta_c = 0.5
        #     COPmax = 6
        #
        #     model.var_CU_heat_pump_Qdot_e_PSH = Var(model.subset_heat_pump, model.set_PSH, model.set_TS, within=NonNegativeReals)
        #     model.var_CU_heat_pump_Qdot_c_linearized = Var(model.subset_heat_pump, model.set_PSH, model.set_TS, within=NonNegativeReals)
        #     model.var_CU_heat_pump_slack = Var(model.subset_heat_pump, model.set_PSH, model.set_TS, within=Reals)
        #
        #     model.var_CU_heat_pump_Qdot_e = Var(model.subset_heat_pump, model.set_TS, within=NonNegativeReals)
        #     model.var_CU_heat_pump_Qdot_c = Var(model.subset_heat_pump, model.set_TS, within=NonNegativeReals)
        #     model.var_CU_heat_pump_Pel = Var(model.subset_heat_pump, model.set_TS, within=NonNegativeReals)
        #
        #     model.var_CU_heat_pump_z = Var(model.subset_heat_pump, model.set_TS, domain=Binary)
        #     model.var_CU_heat_pump_z_max = Var(model.subset_heat_pump, domain=Binary)
        #
        #     # def HP_port(model, u, t):
        #     #     return model.var_CU_Port[u, t] == model.var_CU_heat_pump_Pel[u, t]
        #     # model.con_CU_HP_port = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_port)
        #
        #     def COP_limit(model, u, t):
        #         return model.var_CU_heat_pump_Qdot_c[u, t] <= model.var_CU_heat_pump_Pel[u, t] * COPmax
        #     model.con_CU_HP_COP_limit = Constraint(model.subset_heat_pump, model.set_TS, rule=COP_limit)
        #
        #     def Qdot_e_PSH(model, u, i, t):
        #         return sum(model.var_CUC_Qdot[i, u, K, t] for K in model.set_StagesCU) == model.var_CU_heat_pump_Qdot_e_PSH[u, i, t]
        #     model.con_CU_HP_Qdot_e_PSH = Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=Qdot_e_PSH)
        #
        #     def Qdot_c_linearized_max(model, u, i, t):
        #         IR = data_input['indices']['cold streams'][i]
        #         return sum(model.var_CUC_z[i, u, K, t] for K in model.set_StagesCU) * np.max(read_q_max(u, 1, i, ir) for ir in IR)*2 >= model.var_CU_heat_pump_Qdot_c_linearized[u, i, t]
        #     model.con_CU_HP_Qdot_c_linearized_max = Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=Qdot_c_linearized_max)
        #
        #     def Qdot_linearization(model, u, i, t):
        #         Tmax = self.conversion_units['CU']['Tmax'].values[u]
        #         Tmin = self.conversion_units['CU']['Tmin'].values[u]
        #         dTliftmax = self.conversion_units['CU']['dT lift max'].values[u]
        #         dTliftmin = self.conversion_units['CU']['dT lift min'].values[u]
        #
        #         IR = data_input['indices']['cold streams'][i]
        #
        #         if np.max(read_q_max(u, 1, i, ir) for ir in IR) == 0:
        #             return 0 == model.var_CU_heat_pump_Qdot_c_linearized[u, i, t]
        #         else:
        #             q_max = self.q_max['CUC'].loc[t, i, u].values[0]
        #             res = 20
        #             dT = np.linspace(dTliftmin, dTliftmax, res)
        #             T_h = Tmax + 273.15
        #             q_e = np.linspace(q_max*0.1, q_max*0.6, res)
        #
        #             DT, Q_E = np.meshgrid(dT, q_e, sparse=False)
        #
        #             Q_C = T_h*eta_c*Q_E/(T_h*eta_c-DT)
        #
        #             # fig = plt.figure()
        #             # ax = fig.gca(projection='3d')
        #             # ax.plot_surface(DT, Q_E, Q_C, linewidth=0, antialiased=Fals
        #
        #             # best-fit linear plane
        #             # M
        #             temp = np.c_[np.reshape(DT, (res**2, 1)), np.reshape(Q_E, (res**2, 1)), np.ones(res**2)]
        #             coeffs, _, _, _ = scipy.linalg.lstsq(temp, np.reshape(Q_C, (res**2, 1)))  # nonoptimal coefficients; Z = coeffs_nonopt[0]*X + coeffs_nonopt[1]*Y + coeffs_nonopt[2]
        #
        #             dT = model.var_CUH_T[u, t] - model.var_CUC_T[u, t]
        #             Qe = model.var_CU_heat_pump_Qdot_e_PSH[u, i, t]
        #             slack = model.var_CU_heat_pump_slack[u, i, t]
        #             Qc = model.var_CU_heat_pump_Qdot_c_linearized[u, i, t]
        #             var_z = sum(model.var_CUC_z[i, u, K, t] for K in model.set_StagesCU)
        #             print(dTliftmax * coeffs[0, 0] + 0 * coeffs[1, 0] + coeffs[2, 0])
        #             print(dTliftmin * coeffs[0, 0] + 0 * coeffs[1, 0] + coeffs[2, 0])
        #             return dT * coeffs[0, 0] + Qe * coeffs[1, 0] + var_z*coeffs[2, 0] + slack * (dTliftmax * coeffs[0, 0]) == Qc
        #     model.con_CU_HP_Qdot_linearization = Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=Qdot_linearization)
        #
        #     def slack_limit_ub(model, u, i, t):
        #         return model.var_CU_heat_pump_slack[u, i, t] <= (1-sum(model.var_CUC_z[i, u, K, t] for K in model.set_StagesCU))*0
        #     model.con_CU_HP_slack_limit_ub = Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=slack_limit_ub)
        #
        #     def slack_limit_lb(model, u, i, t):
        #         return model.var_CU_heat_pump_slack[u, i, t] >= -(1-sum(model.var_CUC_z[i, u, K, t] for K in model.set_StagesCU))*1
        #     model.con_CU_HP_slack_limit_lb = Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=slack_limit_lb)
        #
        #     def z_sum_C(model, u, i, t):
        #         return sum(model.var_CUC_z[i, u, K, t] for K in model.set_StagesCU) <= 1
        #     model.con_CU_HP_z_sum_C = Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=z_sum_C)
        #
        #     def z_sum_H(model, u, j, t):
        #         return sum(model.var_CUH_z[u, j, K, t] for K in model.set_StagesCU) <= 1
        #     model.con_CU_HP_z_sum_H = Constraint(model.subset_heat_pump, model.set_PSC, model.set_TS, rule=z_sum_H)
        #
        #     def HP_z_H(model, u, j, t):
        #         return sum(model.var_CUH_z[u, j, K, t] for K in model.set_StagesCU) <= model.var_CU_heat_pump_z[u, t]
        #     model.con_CU_HP_z_H = Constraint(model.subset_heat_pump, model.set_PSC, model.set_TS, rule=HP_z_H)
        #
        #     def HP_z_H_lb(model, u, t):
        #         return sum(model.var_CUH_z[u, J, K, t] for K in model.set_StagesCU for J in model.set_PSC) >= model.var_CU_heat_pump_z[u, t]
        #     model.con_CU_HP_z_H_lb = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_z_H_lb)
        #
        #     def HP_z_C(model, u, i, t):
        #         return sum(model.var_CUC_z[i, u, K, t] for K in model.set_StagesCU) <= model.var_CU_heat_pump_z[u, t]
        #     model.con_CU_HP_z_C = Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=HP_z_C)
        #
        #     def HP_z_C_lb(model, u, t):
        #         return sum(model.var_CUC_z[I, u, K, t] for K in model.set_StagesCU for I in model.set_PSH) >= model.var_CU_heat_pump_z[u, t]
        #     model.con_CU_HP_z_C_lb = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_z_C_lb)
        #
        #     def HP_z_max(model, u, t):
        #         return model.var_CU_heat_pump_z_max[u] >= model.var_CU_heat_pump_z[u, t]
        #     model.con_CU_HP_z_max = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_z_max)
        #
        #     # FIXME: TEST CONSTRAINT!!!
        #     def model(model, u):
        #         return sum(model.var_CU_heat_pump_Qdot_e[u, T] for T in model.set_TS) >= 50
        #     # model.con_CU_model = Constraint(model.subset_heat_pump, rule=model)
        #
        #
        #     def HP_dT(model, u, t):
        #         dTliftmax = self.conversion_units['CU']['dT lift max'].values[0]
        #         dTliftmin = self.conversion_units['CU']['dT lift min'].values[0]
        #         return inequality(dTliftmin, model.var_CUH_T[u, t] - model.var_CUC_T[u, t], dTliftmax)
        #     model.con_HP_dT = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_dT)
        #
        #     def HP_dT_monotonics(model, u, t):
        #         return model.var_CUH_T[u, t] >= model.var_CUC_T[u, t]
        #     model.con_HP_dT_monotonics = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_dT_monotonics)
        #
        #     def HP_dT_ub(model, u, t):
        #         Tmax = self.conversion_units['CU']['Tmax'].values[0]
        #         return model.var_CUH_T[u, t] <= Tmax
        #     model.con_HP_dT_ub = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_dT_ub)
        #
        #     def HP_dT_lb(model, u, t):
        #         Tmin = self.conversion_units['CU']['Tmin'].values[0]
        #         return model.var_CUC_T[u, t] >= Tmin
        #     model.con_HP_dT_lb = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_dT_lb)
        #
        #     def Qdot_c_PSC(model, u, t):
        #         return sum(model.var_CUH_Qdot[u, J, K, t] for J in model.set_PSC for K in model.set_StagesCU) == sum(model.var_CU_heat_pump_Qdot_c_linearized[u, I, t] for I in model.set_PSH)
        #     model.con_CU_HP_Qdot_e_PSC = Constraint(model.subset_heat_pump, model.set_TS, rule=Qdot_c_PSC)
        #
        #     def Qdot_e(model, u, t):
        #         return sum(model.var_CU_heat_pump_Qdot_e_PSH[u, I, t] for I in model.set_PSH) == model.var_CU_heat_pump_Qdot_e[u, t]
        #     model.con_CU_HP_Qdot_e = Constraint(model.subset_heat_pump, model.set_TS, rule=Qdot_e)
        #
        #     def Qdot_c(model, u, t):
        #         return sum(model.var_CU_heat_pump_Qdot_c_linearized[u, I, t] for I in model.set_PSH) == model.var_CU_heat_pump_Qdot_c[u, t]
        #     model.con_CU_HP_Qdot_c = Constraint(model.subset_heat_pump, model.set_TS, rule=Qdot_c)
        #
        #     def Qdot_c_e_equal(model, u, t):
        #         return model.var_CU_heat_pump_Qdot_e[u, t] + model.var_CU_heat_pump_Pel[u, t] == model.var_CU_heat_pump_Qdot_c[u, t]
        #     model.con_CU_HP_Qdot_c_e_equal = Constraint(model.subset_heat_pump, model.set_TS, rule=Qdot_c_e_equal)
        #
        #     # def test_Qdot_e(model, u):
        #     #     Tmax = self.conversion_units['CU']['Tmax']
        #     #     Tmin = self.conversion_units['CU']['Tmin']
        #     #     dTmax = self.conversion_units['CU']['dTmax']
        #     #     dTmin = self.conversion_units['CU']['dTmin']
        #     #
        #     #     # t_in = self.streamdata['Tin'][t, u]
        #     #     # t_out = self.streamdata['Tout'][t, u]
        #     #
        #     #     # mcp_hot = self.streamdata['m'][t, u] * self.streamdata['cp'][t, u]
        #     #
        #     #    # qmax_e = max(0, (self.streamdata[]))
        #     #     return sum(model.var_CUH_Qdot[u, J, K, 2] for J in model.set_PSC for K in model.set_StagesCU) >= 40
        #     #
        #     # model.con_CU_HP_Qdot_e_test = Constraint(model.set_CU, rule=test_Qdot_e)
        #
        #     return model

        def CU_heat_pump_SL(model):
            # eta_c = [val['eta_c'] for val in list(conversion_units['CU'].values())][0]
            #
            # dTliftmax = self.conversion_units['CU']['dT lift max'].values[0]
            # dTliftmin = self.conversion_units['CU']['dT lift min'].values[0]
            #
            # Tmax = self.conversion_units['CU']['Tmax'].values[0]
            # Tmin = self.conversion_units['CU']['Tmin'].values[0]
            #
            # COPmax = (Tmax + 273.15) / dTliftmin * eta_c
            # COPmin = (Tmin + dTliftmin + 273.15) / dTliftmax * eta_c

            def read_val(i, string):
                value = list(conversion_units['CU'].values())[i][string]
                return value

            # SL Model

            model.var_CU_heat_pump_Qdot_e_i = Var(model.subset_heat_pump, model.set_PSH, model.set_TS, within=NonNegativeReals)
            model.var_CU_heat_pump_Qdot_c_j = Var(model.subset_heat_pump, model.set_PSC, model.set_TS, within=NonNegativeReals)

            model.var_CU_heat_pump_Qdot_e = Var(model.subset_heat_pump, model.set_TS, within=NonNegativeReals)
            model.var_CU_heat_pump_Qdot_c_max = Var(model.subset_heat_pump, within=NonNegativeReals)
            model.var_CU_heat_pump_Qdot_c = Var(model.subset_heat_pump, model.set_TS, within=NonNegativeReals)

            model.var_CU_heat_pump_z_e_i = Var(model.subset_heat_pump, model.set_PSH, model.set_TS, within=Binary)
            model.var_CU_heat_pump_z_c_j = Var(model.subset_heat_pump, model.set_PSC, model.set_TS, within=Binary)

            model.var_CU_heat_pump_Pel = Var(model.subset_heat_pump, model.set_TS, within=NonNegativeReals)
            model.var_CU_heat_pump_Pel_max = Var(model.subset_heat_pump, within=NonNegativeReals)

            model.var_CU_heat_pump_Qdot_c_f_i = Var(model.subset_heat_pump, model.set_PSH, model.set_TS, within=NonNegativeReals)
            model.var_CU_heat_pump_Qdot_e_f_j = Var(model.subset_heat_pump, model.set_PSC, model.set_TS, within=NonNegativeReals)

            model.var_CU_heat_pump_slack_i = Var(model.subset_heat_pump, model.set_PSH, model.set_TS, within=Reals)
            model.var_CU_heat_pump_slack_j = Var(model.subset_heat_pump, model.set_PSC, model.set_TS, within=Reals)

            model.var_CU_heat_pump_z = Var(model.subset_heat_pump, model.set_TS, domain=Binary)
            model.var_CU_heat_pump_z_max = Var(model.subset_heat_pump, domain=Binary)

            #############################################################################
            # Constraints

            # transferrable heat
            def con_fun(model, j, i, t):
                return sum(model.var_CUC_Qdot[i, j, K, t] for K in model.set_StagesCU) == model.var_CU_heat_pump_Qdot_e_i[j, i, t]
            model.con_CU_HP_Qdot_e_PSH = Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=con_fun)

            def con_fun(model, i, j, t):
                return sum(model.var_CUH_Qdot[i, j, K, t] for K in model.set_StagesCU) <= model.var_CU_heat_pump_Qdot_c_max[i]
            model.con_CU_HP_Qdot_c_max = Constraint(model.subset_heat_pump, model.set_PSC, model.set_TS, rule=con_fun)

            def con_fun(model, i, j, t):
                return sum(model.var_CUH_Qdot[i, j, K, t] for K in model.set_StagesCU) == model.var_CU_heat_pump_Qdot_c_j[i, j, t]
            model.con_CU_HP_Qdot_c_PSC = Constraint(model.subset_heat_pump, model.set_PSC, model.set_TS, rule=con_fun)

            def con_fun(model, j, t):
                return model.var_CU_heat_pump_Qdot_e[j, t] == sum(model.var_CU_heat_pump_Qdot_e_i[j, i, t] for i in model.set_PSH)
            model.con_CU_HP_Qdot_e_PSH_sum = Constraint(model.subset_heat_pump, model.set_TS, rule=con_fun)

            def con_fun(model, i, t):
                return model.var_CU_heat_pump_Qdot_c[i, t] == sum(model.var_CU_heat_pump_Qdot_c_j[i, j, t] for j in model.set_PSC)
            model.con_CU_HP_Qdot_c_PSC_sum = Constraint(model.subset_heat_pump, model.set_TS, rule=con_fun)

            # Logical temperature constraint
            def HP_dT(model, i, t):
                dTliftmax = read_val(i, 'dT lift max')
                dTliftmin = read_val(i, 'dT lift min')
                return inequality(dTliftmin, model.var_CUH_T[i, t] - model.var_CUC_T[i, t], dTliftmax)
            model.con_HP_dT = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_dT)

            def HP_dT_monotonics(model, i, t):
                return model.var_CUH_T[i, t] >= model.var_CUC_T[i, t]
            model.con_HP_dT_monotonics = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_dT_monotonics)

            def HP_dT_ub(model, i, t):
                Tmax = read_val(i, 'Tmax')
                return model.var_CUH_T[i, t] <= Tmax
            model.con_HP_dT_ub = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_dT_ub)

            def HP_dT_lb(model, i, t):
                Tmin = read_val(i, 'Tmin')
                return model.var_CUC_T[i, t] >= Tmin
            model.con_HP_dT_lb = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_dT_lb)

            ##########################################
            # Function definition
            def linearization(q_max, cond_or_evap, u):
                eta_c = read_val(u, 'eta_c')

                dTliftmax = read_val(u, 'dT lift max')
                dTliftmin = read_val(u, 'dT lift min')
                Tmax = read_val(u, 'Tmax')
                Tmin = read_val(u, 'Tmin')

                res = settings['Heat Pumps']['LIN']['res']
                dT = np.linspace(dTliftmin * 1, dTliftmax * 1, res)
                T_h = (Tmax + Tmin) / 2 + 273.15
                T_h = (Tmin + dTliftmin) + 273.15

                if cond_or_evap == 'evap':
                    q_e = np.linspace(q_max * 0, q_max * settings['Heat Pumps']['LIN']['dom_fact'], res)

                    DT, Q_E = np.meshgrid(dT, q_e, sparse=False)

                    Q_C = T_h * eta_c * Q_E / (T_h * eta_c - DT)
                elif cond_or_evap == 'cond':
                    q_c = np.linspace(q_max * 0, q_max * settings['Heat Pumps']['LIN']['dom_fact'], res)

                    DT, Q_C = np.meshgrid(dT, q_c, sparse=False)

                    Q_E = Q_C / (T_h * eta_c) * (T_h * eta_c - DT)

                # fig = plt.figure()
                # ax = fig.gca(projection='3d')
                # ax.plot_surface(DT, Q_E, Q_C, linewidth=0, antialiased=False)

                # best-fit linear plane
                # M
                temp = np.c_[np.reshape(DT, (res ** 2, 1)), np.reshape(Q_E, (res ** 2, 1)), np.ones(res ** 2)]
                coeffs, _, _, _ = scipy.linalg.lstsq(temp, np.reshape(Q_C, (res ** 2,
                                                                            1)))  # nonoptimal coefficients; Z = coeffs_nonopt[0]*X + coeffs_nonopt[1]*Y + coeffs_nonopt[2]
                # ax.plot_surface(DT, Q_E, coeffs[2] + coeffs[0] * DT + coeffs[1] * Q_E, linewidth=0, antialiased=False)
                # plt.show()
                return coeffs


            # fictive condenser heat load as a function of dT and evaporator heat load
            con_name = 'con_SL_Qdot_c_f_i'

            def con_fun(model, j, i, t):
                dTliftmax = read_val(j, 'dT lift max')

                u = 'CUC'
                IR = data_input['indices']['hot streams'][i]
                q_max = np.max([read_q_max(i, ir, j, 1, u) for ir in IR])
                if q_max == 0:
                    return Constraint.Skip
                else:
                    coeffs = linearization(q_max, 'evap', j)

                    dT = model.var_CUH_T[j, t] - model.var_CUC_T[j, t]
                    Qe = model.var_CU_heat_pump_Qdot_e_i[j, i, t]
                    slack = model.var_CU_heat_pump_slack_i[j, i, t]
                    Qc = model.var_CU_heat_pump_Qdot_c_f_i[j, i, t]
                    var_z = sum(model.var_CUC_z[i, j, K, t] for K in model.set_StagesCU)

                    # print(dTmax * coeffs[0, 0] + 0 * coeffs[1, 0] + coeffs[2, 0])
                    # print(dTmin * coeffs[0, 0] + 0 * coeffs[1, 0] + coeffs[2, 0])
                    return dT * coeffs[0, 0] + Qe * coeffs[1, 0] + var_z * coeffs[2, 0] + slack * (
                                dTliftmax * coeffs[0, 0]) <= Qc

            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=con_fun))

            con_name = 'con_SL_Qdot_c_f_i_2'
            def con_fun(model, j, i, t):
                Qe = model.var_CU_heat_pump_Qdot_e_i[j, i, t]
                Qc = model.var_CU_heat_pump_Qdot_c_f_i[j, i, t]
                return Qc <= settings['Heat Pumps']['LIN']['Qc_Qe']*Qe
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=con_fun))

            con_name = 'con_SL_Qdot_c_f_i_3'

            def con_fun(model, j, i, t):
                Qe = model.var_CU_heat_pump_Qdot_e_i[j, i, t]
                Qc = model.var_CU_heat_pump_Qdot_c_f_i[j, i, t]
                return Qc >= Qe

            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=con_fun))

            # fictive evaporator heat load as a function of dT and condenser heat load
            con_name = 'con_SL_Qdot_e_f_j'
            def con_fun(model, i, j, t):
                dTliftmax = read_val(i, 'dT lift max')

                u = 'CUH'
                JR = data_input['indices']['cold streams'][j]
                q_max = np.max([read_q_max(i, 1, j, jr, u) for jr in JR])
                if q_max == 0:
                    return Constraint.Skip
                else:
                    coeffs = linearization(q_max, 'cond', i)

                    dT = model.var_CUH_T[i, t] - model.var_CUC_T[i, t]
                    Qe = model.var_CU_heat_pump_Qdot_e_f_j[i, j, t]
                    slack = model.var_CU_heat_pump_slack_j[i, j, t]
                    Qc = model.var_CU_heat_pump_Qdot_c_j[i, j, t]
                    var_z = sum(model.var_CUH_z[i, j, K, t] for K in model.set_StagesCU)

                    # print(dTmax * coeffs[0, 0] + 0 * coeffs[1, 0] + coeffs[2, 0])
                    # print(dTmin * coeffs[0, 0] + 0 * coeffs[1, 0] + coeffs[2, 0])
                    return dT * coeffs[0, 0] + Qe * coeffs[1, 0] + var_z * coeffs[2, 0] + slack * (
                                dTliftmax * coeffs[0, 0]) <= Qc
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_PSC, model.set_TS, rule=con_fun))

            con_name = 'con_SL_Qdot_e_f_j_2'
            def con_fun(model, i, j, t):
                Qe = model.var_CU_heat_pump_Qdot_e_f_j[i, j, t]
                Qc = model.var_CU_heat_pump_Qdot_c_j[i, j, t]

                return Qe <= Qc
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_PSC, model.set_TS, rule=con_fun))


            # real and fictive condenser heat load needs to be equal
            con_name = 'con_SL_Qdot_c_j_bigger'
            def con_fun(model, I, t):
                return sum(model.var_CU_heat_pump_Qdot_c_j[I, j, t] for j in model.set_PSC) == sum(
                    model.var_CU_heat_pump_Qdot_c_f_i[I, i, t] for i in model.set_PSH)
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_TS, rule=con_fun))

            # Pel from condenser hl and evaporator hl (real values)
            con_name = 'con_SL_Pel_1'
            def con_fun(model, I, t):
                return model.var_CU_heat_pump_Pel[I, t] >= sum(model.var_CU_heat_pump_Qdot_c_j[I, j, t] for j in model.set_PSC) - sum(
                    model.var_CU_heat_pump_Qdot_e_i[I, i, t] for i in model.set_PSH)
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_TS, rule=con_fun))

            con_name = 'con_SL_Pel_2'
            def con_fun(model, I, t):
                return model.var_CU_heat_pump_Pel[I, t] >= sum(model.var_CU_heat_pump_Qdot_c_j[I, j, t] for j in model.set_PSC) - sum(
                    model.var_CU_heat_pump_Qdot_e_f_j[I, j, t] for j in model.set_PSC)
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_TS, rule=con_fun))

            con_name = 'con_SL_Pel_max'
            def con_fun(model, I, t):
                return model.var_CU_heat_pump_Pel_max[I] >= model.var_CU_heat_pump_Pel[I, t]
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_TS, rule=con_fun))


        # Bounds for COP
            con_name = 'con_COP_1'
            def con_fun(model, I, t):
                COPmin = (read_val(I, 'Tmin') + read_val(I, 'dT lift min') + 273.15) / read_val(I, 'dT lift max') * read_val(I, 'eta_c')
                return sum(model.var_CU_heat_pump_Qdot_c_j[I, j, t] for j in model.set_PSC) >= model.var_CU_heat_pump_Pel[I, t] * COPmin
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_TS, rule=con_fun))

            con_name = 'con_COP_2'
            def con_fun(model, I, t):
                COPmax = (read_val(I, 'Tmax') + 273.15) / read_val(I, 'dT lift min') * read_val(I, 'eta_c')
                return sum(model.var_CU_heat_pump_Qdot_c_j[I, j, t] for j in model.set_PSC) <= \
                       model.var_CU_heat_pump_Pel[I, t] * COPmax
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_TS, rule=con_fun))


            # bounds for slack-variables
            con_name = 'con_SL_slack_limit_ub'
            def con_fun(model, j, i, t):
                return model.var_CU_heat_pump_slack_i[j, i, t] <= 0
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=con_fun))

            con_name = 'con_SL_slack_limit_lb'
            def con_fun(model, j, i, t):
                return model.var_CU_heat_pump_slack_i[j, i, t] >= -(1 - sum(model.var_CUC_z[i, j, K, t] for K in model.set_StagesCU)) * 1
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=con_fun))


            con_name = 'con_SL_slack_limit_ub2'
            def con_fun(model, i, j, t):
                return model.var_CU_heat_pump_slack_j[i, j, t] <= 0
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_PSC, model.set_TS, rule=con_fun))

            con_name = 'con_SL_slack_limit_lb2'
            def con_fun(model, i, j, t):
                return model.var_CU_heat_pump_slack_j[i, j, t] >= -(1 - sum(model.var_CUH_z[i, j, K, t] for K in model.set_StagesCU)) * 1
            model.add_component(con_name, Constraint(model.subset_heat_pump, model.set_PSC, model.set_TS, rule=con_fun))


            def z_sum_C(model, j, i, t):
                return sum(model.var_CUC_z[i, j, K, t] for K in model.set_StagesCU) <= 1
            model.con_CU_HP_z_sum_C = Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=z_sum_C)

            def z_sum_H(model, i, j, t):
                return sum(model.var_CUH_z[i, j, K, t] for K in model.set_StagesCU) <= 1
            model.con_CU_HP_z_sum_H = Constraint(model.subset_heat_pump, model.set_PSC, model.set_TS, rule=z_sum_H)

            def HP_z_H(model, i, j, t):
                return sum(model.var_CUH_z[i, j, K, t] for K in model.set_StagesCU) <= model.var_CU_heat_pump_z[i, t]
            model.con_CU_HP_z_H = Constraint(model.subset_heat_pump, model.set_PSC, model.set_TS, rule=HP_z_H)

            def HP_z_H_lb(model, I, t):
                return sum(model.var_CUH_z[I, J, K, t] for K in model.set_StagesCU for J in model.set_PSC) >= model.var_CU_heat_pump_z[I, t]
            model.con_CU_HP_z_H_lb = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_z_H_lb)

            def HP_z_C(model, j, i, t):
                return sum(model.var_CUC_z[i, j, K, t] for K in model.set_StagesCU) <= model.var_CU_heat_pump_z[j, t]
            model.con_CU_HP_z_C = Constraint(model.subset_heat_pump, model.set_PSH, model.set_TS, rule=HP_z_C)

            def HP_z_C_lb(model, J, t):
                return sum(model.var_CUC_z[I, J, K, t] for K in model.set_StagesCU for I in model.set_PSH) >= model.var_CU_heat_pump_z[J, t]
            model.con_CU_HP_z_C_lb = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_z_C_lb)

            def HP_z_max(model, J, t):
                return model.var_CU_heat_pump_z_max[J] >= model.var_CU_heat_pump_z[J, t]
            model.con_CU_HP_z_max = Constraint(model.subset_heat_pump, model.set_TS, rule=HP_z_max)

            # FIXME: TEST CONSTRAINT!!!
            def con_fun(model, I):
                return sum(model.var_CU_heat_pump_Qdot_e[I, T] for T in model.set_TS) >= 50
            # model.con_CU_model = Constraint(model.subset_heat_pump, rule=con_fun)

            return model

        def CU_storage(model):
            cp = settings['Storages']['cp']   # kJ/kgK

            model.var_CU_storage_Qdot_charge = Var(model.subset_storage, model.set_TS, within=NonNegativeReals)
            model.var_CU_storage_Qdot_discharge = Var(model.subset_storage, model.set_TS, within=NonNegativeReals)

            model.var_CU_storage_Q_stored = Var(model.subset_storage, model.set_TS, within=Reals)

            model.var_CU_storage_Q_stored_ub = Var(model.subset_storage, within=NonNegativeReals)
            model.var_CU_storage_Q_stored_lb = Var(model.subset_storage, within=NegativeReals)

            model.var_CU_storage_Q_stored_cap = Var(model.subset_storage, within=NonNegativeReals)

            model.var_CU_storage_mass = Var(model.subset_storage, within=NonNegativeReals)

            model.var_CU_storage_z = Var(model.subset_storage, model.set_TS, domain=Binary)
            model.var_CU_storage_z_max = Var(model.subset_storage, domain=Binary)

            def Qdot_charge(model, u, t):
                return sum(model.var_CUC_Qdot[I, u, K, t] for I in model.set_PSH for K in model.set_StagesCU) == model.var_CU_storage_Qdot_charge[u, t]
            model.con_CU_storage_Qdot_charge = Constraint(model.subset_storage, model.set_TS, rule=Qdot_charge)


            def Qdot_discharge(model, u, t):
                return sum(model.var_CUH_Qdot[u, I, K, t] for I in model.set_PSC for K in model.set_StagesCU) == model.var_CU_storage_Qdot_discharge[u, t]
            model.con_CU_storage_Qdot_discharge = Constraint(model.subset_storage, model.set_TS, rule=Qdot_discharge)

            def Q_stored(model, u, t):
                if t == min(model.set_TS):
                    return model.var_CU_storage_Q_stored[u, max(model.set_TS)] + (model.var_CU_storage_Qdot_charge[u, t] - model.var_CU_storage_Qdot_discharge[u, t])*self.data_input['intervals']['durations'][t] == model.var_CU_storage_Q_stored[u, t]
                else:
                    return model.var_CU_storage_Q_stored[u, t-1] + (model.var_CU_storage_Qdot_charge[u, t] - model.var_CU_storage_Qdot_discharge[u, t])*self.data_input['intervals']['durations'][t] == model.var_CU_storage_Q_stored[u, t]
            model.con_CU_storage_Q_stored = Constraint(model.subset_storage, model.set_TS, rule=Q_stored)

            def Q_stored_ub(model, u, t):
                return model.var_CU_storage_Q_stored_ub[u] >= model.var_CU_storage_Q_stored[u, t]
            model.con_CU_storage_Q_stored_ub = Constraint(model.subset_storage, model.set_TS, rule=Q_stored_ub)

            def Q_stored_lb(model, u, t):
                return model.var_CU_storage_Q_stored_lb[u] <= model.var_CU_storage_Q_stored[u, t]
            model.con_CU_storage_Q_stored_lb = Constraint(model.subset_storage, model.set_TS, rule=Q_stored_lb)

            def Q_stored_cap(model, u):
                return model.var_CU_storage_Q_stored_cap[u] == model.var_CU_storage_Q_stored_ub[u] - model.var_CU_storage_Q_stored_lb[u]
            model.con_CU_storage_Q_stored_cap = Constraint(model.subset_storage, rule=Q_stored_cap)

            def Q_stored_cycle(model, u):
                return model.var_CU_storage_Q_stored[u, min(model.set_TS)] == model.var_CU_storage_Q_stored[u, max(model.set_TS)]
            model.con_CU_storage_Q_stored_cycle = Constraint(model.subset_storage, rule=Q_stored_cycle)

            def T_equal_h(model, u, t):
                if t > min(model.set_TS):
                    return model.var_CUH_T[u, t-1] == model.var_CUH_T[u, t]
                else:
                    return Constraint.Skip
            model.con_CU_storage_T_equal_h = Constraint(model.subset_storage, model.set_TS, rule=T_equal_h)

            def T_equal_c(model, u, t):
                if t > min(model.set_TS):
                    return model.var_CUC_T[u, t-1] == model.var_CUC_T[u, t]
                else:
                    return Constraint.Skip
            model.con_CU_storage_T_equal_c = Constraint(model.subset_storage, model.set_TS, rule=T_equal_c)

            def mass_linearization(model, u):
                Tmax = self.conversion_units['CU'][list(self.conversion_units['CU'].keys())[u]]['Tmax']
                Tmin = self.conversion_units['CU'][list(self.conversion_units['CU'].keys())[u]]['Tmin']
                dTliftmin = self.conversion_units['CU'][list(self.conversion_units['CU'].keys())[u]]['dT lift min']
                dQmax = estimate_storage_size.estimate_storage_size(self, self.settings['HEN']['dTmin'], Tmax, Tmin)

                # FIXME: Hier muss eine sinnvolle linearisierung her!

                res = settings['Storages']['LIN']['res']

                dQ = np.linspace(settings['Storages']['LIN']['dom_fact']*dQmax, dQmax, res)
                dT = np.linspace(dTliftmin, Tmax-Tmin, res)

                DQ, DT = np.meshgrid(dQ, dT, sparse=False)

                MASS = (DQ/DT/(cp/3600))

                # fig = plt.figure()
                # ax = fig.gca(projection='3d')
                # ax.plot_surface(DQ, DT, MASS, linewidth=0, antialiased=False)

                # best-fit linear plane
                temp = np.c_[np.reshape(DQ, (res**2, 1)), np.reshape(DT, (res**2, 1)), np.ones(res**2)]
                coeffs, _, _, _ = scipy.linalg.lstsq(temp, np.reshape(MASS, (res**2, 1)))  # nonoptimal coefficients; Z = coeffs_nonopt[0]*X + coeffs_nonopt[1]*Y + coeffs_nonopt[2]

                dT_var = model.var_CUH_T[u, 0] - model.var_CUC_T[u, 0]
                dQ_var = model.var_CU_storage_Q_stored_cap[u]
                return dQ_var * coeffs[0, 0] + dT_var * coeffs[1, 0] + coeffs[2, 0] * model.var_CU_storage_z_max[u] <= model.var_CU_storage_mass[u]
            model.con_CU_storage_mass_linearization = Constraint(model.subset_storage, rule=mass_linearization)


            def z_sum_C(model, u, i, t):
                return sum(model.var_CUC_z[i, u, K, t] for K in model.set_StagesCU) <= 1
            model.con_CU_storage_z_sum_C = Constraint(model.subset_storage, model.set_PSH, model.set_TS, rule=z_sum_C)

            def z_sum_H(model, u, j, t):
                return sum(model.var_CUH_z[u, j, K, t] for K in model.set_StagesCU) <= 1
            model.con_CU_storage_z_sum_H = Constraint(model.subset_storage, model.set_PSC, model.set_TS, rule=z_sum_H)

            def storage_z_H(model, u, j, t):
                return sum(model.var_CUH_z[u, j, K, t] for K in model.set_StagesCU) <= model.var_CU_storage_z[u, t]
            model.con_CU_storage_z_H = Constraint(model.subset_storage, model.set_PSC, model.set_TS, rule=storage_z_H)

            def storage_z_C(model, u, i, t):
                return sum(model.var_CUC_z[i, u, K, t] for K in model.set_StagesCU) <= model.var_CU_storage_z[u, t]
            model.con_CU_storage_z_C = Constraint(model.subset_storage, model.set_PSH, model.set_TS, rule=storage_z_C)

            def storage_z_max(model, u, t):
                return model.var_CU_storage_z_max[u] >= model.var_CU_storage_z[u, t]
            model.con_CU_storage_z_max = Constraint(model.subset_storage, model.set_TS, rule=storage_z_max)

            # FIXME: TEST CONSTRAINT!!!
            # def storage_test(model, u):
            #     return sum(model.var_CU_storage_Qdot_charge[u, T] for T in model.set_TS) >= 1
            # model.con_CU_storage_test = Constraint(model.subset_storage, rule=storage_test)


            def storage_dT(model, u, t):
                dTliftmin = self.conversion_units['CU'][list(self.conversion_units['CU'].keys())[u]]['dT lift min']
                return model.var_CUH_T[u, t] - model.var_CUC_T[u, t] >= dTliftmin
            model.con_storage_dT = Constraint(model.subset_storage, model.set_TS, rule=storage_dT)

            def storage_dT_monotonics(model, u, t):
                return model.var_CUH_T[u, t] >= model.var_CUC_T[u, t]
            model.con_storage_dT_monotonics = Constraint(model.subset_storage, model.set_TS, rule=storage_dT_monotonics)

            def storage_dT_ub(model, u, t):
                Tmax = self.conversion_units['CU'][list(self.conversion_units['CU'].keys())[u]]['Tmax']
                return model.var_CUH_T[u, t] <= Tmax
            model.con_storage_dT_ub = Constraint(model.subset_storage, model.set_TS, rule=storage_dT_ub)

            def storage_dT_lb(model, u, t):
                Tmin = self.conversion_units['CU'][list(self.conversion_units['CU'].keys())[u]]['Tmin']
                return model.var_CUC_T[u, t] >= Tmin
            model.con_storage_dT_lb = Constraint(model.subset_storage, model.set_TS, rule=storage_dT_lb)

            return model

        if len(model.subset_heat_pump) > 0:
            model = CU_heat_pump_SL(model)

            var_Port = getattr(model, 'var_CU_Port'.format(u))
            def con_fun(model, u, t):
                return var_Port[u, t] == model.var_CU_heat_pump_Pel[u, t]

            setattr(model, 'con_CU_heat_pump_port', Constraint(model.subset_heat_pump, set_TS, rule=con_fun))

        if len(model.subset_storage) > 0:
            model = CU_storage(model)

        # ----------------------------------------------------------------------------------------------------------
        # Tightening Constraints
        # ---------------------------------------------------------------------------------------------------------

        # ---------------------------------------------------------------------------------------------------------
        # minimum number of HEX

        def tight_z_min_PSH(model, i):
            if np.max([read_sd(i, r, 'soft') for r in data_input['indices']['hot streams'][i]]) == 0:
                lhs = sum(model.var_Direct_z_max[i, j, k] for j in model.set_PSC for k in model.set_StagesDirect)
                for u in [x for x in full_list_wo_direct if x[-1] == 'C']:
                    var_z_max = getattr(model, 'var_{}_z_max'.format(u))

                    lhs = lhs + sum(var_z_max[i, j, k] for j in idx_con[u][idx_CS] for k in idx_con[u][idx_K])
                return lhs >= 1
            else:
                return Constraint.Skip
        model.con_tight_z_min_PSH = Constraint(model.set_PSH, rule=tight_z_min_PSH, doc='tightening constraint z_min')

        def tight_z_min_PSC(model, j):
            if np.max([read_sd(j, r, 'soft') for r in data_input['indices']['cold streams'][j]]) == 0:
                lhs = sum(model.var_Direct_z_max[i, j, k] for i in model.set_PSH for k in model.set_StagesDirect)
                for u in [x for x in full_list_wo_direct if x[-1] == 'H']:
                    var_z_max = getattr(model, 'var_{}_z_max'.format(u))

                    lhs = lhs + sum(var_z_max[i, j, k] for i in idx_con[u][idx_HS] for k in idx_con[u][idx_K])
                return lhs >= 1
            else:
                return Constraint.Skip
        model.con_tight_z_min_PSC = Constraint(model.set_PSC, rule=tight_z_min_PSC, doc='tightening constraint z_min')

        # ---------------------------------------------------------------------------------------------------------
        # eliminate redundant HENs
        list_wo_UH_UC = [elem for elem in full_list if elem not in ['UH', 'UC']]


        for u in list_wo_UH_UC:
            # if u == 'Direct':
                con_name = 'con_tight_redundant_HENs_{}'.format(u)

                var_z_max = getattr(model, 'var_{}_z_max'.format(u))
                set_HS = idx_con[u][idx_HS]  # set of Hot Streams
                set_CS = idx_con[u][idx_CS]  # set of Cold Streams
                set_K = idx_con[u][idx_K]  # set of Stages

                def con_fun(model, i, j, k):
                    k_set = set({k})
                    k_set_1 = set({k+1})
                    if k_set_1.issubset(set_K.data()):
                        if u == 'Direct':
                            rhs = sum(model.var_Direct_z_max[i, J, k] for J in model.set_PSC if
                                      k_set.issubset(model.set_StagesDirect.data())) \
                                  + sum(model.var_Direct_z_max[I, j, k] for I in model.set_PSH if
                                        k_set.issubset(model.set_StagesDirect.data()))

                            for u_ in list_wo_UH_UC:
                                if u_ == 'UIH':
                                    rhs = rhs + sum(model.var_UIH_z_max[I, j, k] for I in model.set_UIH if k_set.issubset(model.set_StagesUIH.data()))
                                if u_ == 'UIC':
                                    rhs = rhs + sum(model.var_UIC_z_max[i, J, k] for J in model.set_UIC if k_set.issubset(model.set_StagesUIC.data()))
                                if u_ == 'CUH':
                                    rhs = rhs + sum(model.var_CUH_z_max[I, j, k] for I in model.set_CU if k_set.issubset(model.set_StagesCU.data()))
                                if u_ == 'CUC':
                                    rhs = rhs + sum(model.var_CUC_z_max[i, J, k] for J in model.set_CU if k_set.issubset(model.set_StagesCU.data()))

                            return var_z_max[i, j, k + 1] <= rhs
                        else:
                            return Constraint.Skip

                        # fixme: needs to be implemented for u = UIH, CUH, UIC, CUC
                        # elif (u == 'UIH') or (u == 'CUH'):
                        #     return var_z_max[i, j, k + 1] <= sum(model.var_Direct_z_max[I, j, k] for I in model.set_PSH if k_set.issubset(model.set_StagesDirect.data())) \
                        #            + sum(model.var_UIH_z_max[I, j, k] for I in model.set_UIH if k_set.issubset(model.set_StagesUIH.data())) \
                        #            + sum(model.var_CUH_z_max[I, j, k] for I in model.set_CU if k_set.issubset(model.set_StagesCU.data()))
                        # else:
                        #     return var_z_max[i, j, k+1] <= sum(model.var_Direct_z_max[j, J, k] for J in model.set_PSC if k_set.issubset(model.set_StagesDirect.data())) \
                        #            + sum(model.var_UIC_z_max[i, J, k] for J in model.set_UIC if k_set.issubset(model.set_StagesUIC.data()))\
                        #            + sum(model.var_CUC_z_max[i, J, k] for J in model.set_CU if k_set.issubset(model.set_StagesCU.data()))

                    else:
                        return Constraint.Skip

                setattr(model, con_name, Constraint(set_HS, set_CS, set_K, rule=con_fun))

        # ---------------------------------------------------------------------------------------------------------
        # Light LMTD formulation

        # fixme!!
        if self.settings['SIMP']['max_pair_hex'] == 0:
            def tight_LMTD_Direct(model, t, i, j, k):
                var_LMTD = getattr(model, 'var_' + 'Direct' + '_LMTD')
                var_Qdot = getattr(model, 'var_' + 'Direct' + '_Qdot')
                var_z = getattr(model, 'var_' + 'Direct' + '_z')

                IR = data_input['indices']['hot streams'][i]
                JR = data_input['indices']['cold streams'][j]

                try:
                    coeffs_aux = np.max(
                        np.array([simp_coeff(coeffs['A_beta_x'], i, ir, j, jr)['LMTD max'] for ir in IR for jr in JR]),
                        axis=0)
                except:
                    return Constraint.Skip
                q_max_aux = np.max(np.array([read_q_max(i, ir, j, jr, 'Direct') for ir in IR for jr in JR]))

                slope = (coeffs_aux[1] - coeffs_aux[0]) / q_max_aux

                return var_LMTD[i, j, k, t] <= var_Qdot[i, j, k, t] * slope + dTmin + (coeffs_aux[0] - dTmin) * var_z[i, j, k, t]
            model.con_tight_LMTD_Direct = Constraint(model.subset_A_Direct, model.set_StagesDirect, rule=tight_LMTD_Direct, doc='tight LMTD in HEX')

        if self.settings['SIMP']['max_pair_hex'] == 1:
            def tight_LMTD_Direct_single(model, t, i, j):
                var_LMTD = getattr(model, 'var_' + 'Direct' + '_LMTD')
                var_Qdot = getattr(model, 'var_' + 'Direct' + '_Qdot')
                var_z = getattr(model, 'var_' + 'Direct' + '_z')

                IR = data_input['indices']['hot streams'][i]
                JR = data_input['indices']['cold streams'][j]

                try:
                    coeffs_aux = np.max(np.array([simp_coeff(coeffs['A_beta_x'], i, ir, j, jr)['LMTD max'] for ir in IR for jr in JR]), axis=0)
                except:
                    return Constraint.Skip
                q_max_aux = np.max(np.array([read_q_max(i, ir, j, jr, 'Direct') for ir in IR for jr in JR]))

                k = min(model.set_StagesDirect.data())

                slope = (coeffs_aux[1] - coeffs_aux[0]) / q_max_aux

                return var_LMTD[i, j, k, t] <= sum(var_Qdot[i, j, K, t] for K in model.set_StagesDirect) * slope + dTmin + (coeffs_aux[0] - dTmin) * sum(var_z[i, j, K, t] for K in model.set_StagesDirect)
            model.con_tight_LMTD_Direct_single = Constraint(model.set_TS, model.set_PSH, model.set_PSC, rule=tight_LMTD_Direct_single, doc='tight LMTD in HEX')

        # ---------------------------------------------------------------------------------------------------------
        # set minimal heat recovery

        if (self.settings['SIMP']['min HR'] > 0) and (self.settings['SCHED']['active'] == 0):

            def min_HR(model):
                max_recovery = sum(
                    [self.targets['Heat Recovery'][:, t - 1] * self.durations[t - 1] for t in self.intervals])
                recovery_direct = sum(
                    [model.var_Direct_Qdot[i, j, k, t] * self.durations[t - 1] for i in model.set_PSH for j
                     in model.set_PSC for k in model.set_StagesDirect for t in self.intervals])
                recovery_CU = sum([model.var_CUH_Qdot[i, j, k, t] * self.durations[t - 1] for i in model.set_CU for j in
                                   model.set_PSC for k in model.set_StagesCU for t in self.intervals])
                recovery_actual = recovery_direct + recovery_CU
                return recovery_actual >= self.settings['SIMP']['min HR'] * max_recovery[0]
            model.con_min_HR = Constraint(rule=min_HR)

        # ---------------------------------------------------------------------------------------------------------
        # set minimal heat recovery including storage

        if (self.settings['SIMP']['min HR TAM'] > 0) and (self.settings['SCHED']['active'] == 0):
            targets.calc_targets(self, 5, 1, 0, 0, 0)  # fixme Check!
            max_recovery_TAM = self.targets_TAM['Heat Recovery']
            def min_HR_TAM(model):
                recovery_direct = sum(
                    [model.var_Direct_Qdot[i, j, k, t] * self.durations[t - 1] for i in model.set_PSH for j
                     in model.set_PSC for k in model.set_StagesDirect for t in self.intervals])
                recovery_CU = sum([model.var_CUH_Qdot[i, j, k, t] * self.durations[t - 1] for i in model.set_CU for j in
                                   model.set_PSC for k in model.set_StagesCU for t in self.intervals])
                recovery_actual = recovery_direct + recovery_CU
                return recovery_actual >= self.settings['SIMP']['min HR TAM'] * max_recovery_TAM[0][0]
            model.con_min_HR = Constraint(rule=min_HR_TAM)

        end = time.time()
        print('Model set-up took')
        print(end-start)
        print('seconds')

        def read_val(i, unit, string):
            value = list(conversion_units[unit].values())[i][string]
            return value

        def ObjRule(model):
            obj_dict = {}

            if settings['UC']['active'] == 0:
                obj_dict['HP'] = {}
                obj_dict['HP']['HP OPEX'] = 0
                obj_dict['HP']['HP OPEX'] += sum(model.var_CU_heat_pump_Pel[u, t] * data_input['intervals']['durations'][t] * read_val(u, 'CU', 'costs') for u in model.subset_heat_pump for t in model.set_TS)

                obj_dict['HP']['HP residual'] = 0
                obj_dict['HP']['HP residual'] += sum(model.var_CU_heat_pump_Pel_max[u] * settings['Heat Pumps']['COSTS']['P_el specific'] / settings['Heat Pumps']['COSTS']['annualization'] for u in model.subset_heat_pump)
                obj_dict['HP']['HP residual'] += sum(model.var_CU_heat_pump_Qdot_c_max[u] * settings['Heat Pumps']['COSTS']['Q_max specific'] / settings['Heat Pumps']['COSTS']['annualization'] for u in model.subset_heat_pump)
                obj_dict['HP']['HP residual'] += sum(model.var_CU_heat_pump_z_max[u] * settings['Heat Pumps']['COSTS']['P_el fix'] / settings['Heat Pumps']['COSTS']['annualization'] for u in model.subset_heat_pump)

                obj_dict['HP']['HP HEX'] = 0
                obj_dict['HP']['HP HEX'] += sum(getattr(model, 'var_{}_A_add_beta_x'.format('CUC'))[i,u,k] * settings['COSTS']['HEX var'] / settings['COSTS']['annualization'] for u in model.subset_heat_pump for i in model.set_PSH for k in model.set_StagesCU) * settings['Heat Pumps']['COSTS']['HEX-cost related']
                obj_dict['HP']['HP HEX'] += sum(getattr(model, 'var_{}_A_add_beta_x'.format('CUH'))[u,j,k] * settings['COSTS']['HEX var'] / settings['COSTS']['annualization'] for u in model.subset_heat_pump for j in model.set_PSC for k in model.set_StagesCU) * settings['Heat Pumps']['COSTS']['HEX-cost related']
                obj_dict['HP']['HP HEX'] += sum(getattr(model, 'var_{}_z_max'.format('CUC'))[i,u,k] * settings['COSTS']['HEX fix'] / settings['COSTS']['annualization'] for u in model.subset_heat_pump for i in model.set_PSH for k in model.set_StagesCU) * settings['Heat Pumps']['COSTS']['HEX-cost related']
                obj_dict['HP']['HP HEX'] += sum(getattr(model, 'var_{}_z_max'.format('CUH'))[u,j,k] * settings['COSTS']['HEX fix'] / settings['COSTS']['annualization'] for u in model.subset_heat_pump for j in model.set_PSC for k in model.set_StagesCU) * settings['Heat Pumps']['COSTS']['HEX-cost related']

            obj_dict['STO']={}
            obj_dict['STO']['STO residual'] = 0
            obj_dict['STO']['STO residual'] += sum(model.var_CU_storage_mass[u] * read_val(u, 'CU', 'costs var') / read_val(u, 'CU', 'annualization') for u in model.subset_storage)
            obj_dict['STO']['STO residual'] += sum(model.var_CU_storage_z_max[u] * read_val(u, 'CU', 'costs fix') / read_val(u, 'CU', 'annualization') for u in model.subset_storage)
            # fixme: costs for heat pump compressors need to be included in the cost function - right now only HEX costs are considered

            for u in full_list:
                var_A_add_beta_x = getattr(model, 'var_{}_A_add_beta_x'.format(u))
                var_z_max = getattr(model, 'var_{}_z_max'.format(u))
                var_z_avail = getattr(model, 'var_{}_z_avail'.format(u))
                subset_ex_loc = idx_con[u][idx_subset_A_ex_loc]
                subset_ex_iloc = idx_con[u][idx_subset_A_ex_iloc]
                var_Qdot = getattr(model, 'var_{}_Qdot'.format(u))
                set_K = idx_con[u][idx_K]  # set of Stages
                set_TS = model.set_TS  # set of time intervals
                set_HS = idx_con[u][idx_HS]  # set of Hot Streams
                set_CS = idx_con[u][idx_CS]  # set of Cold Streams

                obj_dict[u] = {}

                if u not in ['UC', 'UH']:
                    if 'Hex_spec' in settings.keys():
                        def get_medium(idx, hc, u):
                            if (u == 'Direct') or ((hc == 'h') and (u in ['UC', 'UIC', 'CUC'])) or ((hc == 'c') and (u in ['UH', 'UIH', 'CUH'])):
                                return list(data_input['streamdata'][data_input['streamdata']['stream nr'] == idx]['Medium'])[0]

                            else:
                                if u in ['CUH', 'CUC']:
                                    u = 'CU'
                                key = list(conversion_units[u].keys())[idx]
                                return conversion_units[u][key]['Medium']

                        def get_var_costs(med1, med2):
                            key = [i for i in settings['Hex_spec'].keys() if set([med1, med2]) == set(i)][0]
                            c_var = settings['Hex_spec'][key]['c_var']
                            return c_var

                        def get_fix_costs(med1, med2):
                            key = [i for i in settings['Hex_spec'].keys() if set([med1, med2]) == set(i)][0]
                            c_fix = settings['Hex_spec'][key]['c_fix']
                            return c_fix

                    obj_dict[u]['HEX'] = 0
                    if 'Hex_spec' in settings.keys():
                        obj_dict[u]['HEX'] += sum([var_A_add_beta_x[i,j,k]*get_var_costs(get_medium(i,'h',u), get_medium(j,'c',u))/ settings['COSTS']['annualization'] for i in set_HS for j in set_CS for k in set_K])
                        obj_dict[u]['HEX'] += sum([var_z_max[i,j,k]*get_fix_costs(get_medium(i,'h',u), get_medium(j,'c',u))/ settings['COSTS']['annualization'] for i in set_HS for j in set_CS for k in set_K])
                        try:
                            obj_dict[u]['HEX'] += - sum([(1 - var_z_avail[subset_ex_iloc[list(subset_ex_iloc)[m]]])*get_fix_costs(get_medium(i, 'h', u), get_medium(j, 'c', u)) for m, (i, j, _) in enumerate(subset_ex_loc)]) / settings['COSTS']['annualization']
                        except:
                            print('error in objective creation -> retrofit problem')
                        # obj1 += summation(var_z_avail) * settings['COSTS']['HEX fix'] / settings['COSTS']['annualization']

                    else:
                        obj_dict[u]['HEX'] += summation(var_A_add_beta_x) * settings['COSTS']['HEX var'] / settings['COSTS']['annualization']
                        obj_dict[u]['HEX'] += summation(var_z_max) * settings['COSTS']['HEX fix'] / settings['COSTS']['annualization']
                        obj_dict[u]['HEX'] += - var_z_avail.get_values().values().__len__() * settings['COSTS']['HEX fix'] / settings['COSTS']['annualization']
                        obj_dict[u]['HEX'] += summation(var_z_avail) * settings['COSTS']['HEX fix'] / settings['COSTS']['annualization']


                if settings['UC']['active'] == 0:
                    if u in ['UH', 'UIH']:
                        obj_dict[u]['OPEX'] = 0
                        obj_dict[u]['OPEX'] += sum([var_Qdot[i, j, k, t] * data_input['intervals']['durations'][t-1] * read_val(i, u, 'costs') for i in set_HS for j in set_CS for k in set_K for t in model.set_TS])

                    if u in ['UC', 'UIC']:
                        obj_dict[u]['OPEX'] = 0
                        obj_dict[u]['OPEX'] += sum([var_Qdot[i, j, k, t] * data_input['intervals']['durations'][t-1] * read_val(j, u, 'costs') for i in set_HS for j in set_CS for k in set_K for t in model.set_TS])

            obj1 = 0
            for i in obj_dict.keys():
                for j in obj_dict[i].keys():
                    obj1 += obj_dict[i][j]

            return obj1, obj_dict

        model.g = Objective(expr= ObjRule(model)[0])
        model.g.deactivate()

        self.model = model
        self.costs = ObjRule(model)[1]

    def solve(self, timelimit):
        opt = pyomo.environ.SolverFactory('cplex')


        result = opt.solve(self.model, warmstart=False, tee=True, timelimit=timelimit)

        print(result.Solver._list)

        return result

        # self.opt_model = model

    # def add_HEX(self, utility_name, indices, value):
    #     df = self.retrofit['retrofit HEX'][utility_name]
    #
    #     if utility_name in ['UH', 'UIH', 'CUH']:
    #         if indices[1] in self.streams_cold and indices[0] in self.conversion_units[utility_name].index:
    #             if df.index.isin([indices]).any() == False:
    #                 if df['Nr'].values.shape[0] == 0:
    #                     df.loc[indices, ['Nr']] = 0
    #                 else:
    #                     df.loc[indices, ['Nr']] = max(df['Nr'].values) + 1
    #                 df.loc[indices, ['Value']] = value
    #
    #             else:
    #                 print('Index error / Index already exists!')
    #         else:
    #             print('Index error!')
    #
    #     if utility_name in ['UC', 'UIC', 'CUC']:
    #         if indices[0] in self.streams_hot and indices[1] in self.conversion_units[utility_name].index:
    #             if df.index.isin([indices]).any() == False:
    #                 if df['Nr'].values.shape[0] == 0:
    #                     df.loc[indices, ['Nr']] = 0
    #                 else:
    #                     df.loc[indices, ['Nr']] = max(df['Nr'].values) + 1
    #                 df.loc[indices, ['Value']] = value
    #             else:
    #                 print('Index error / Index already exists!')
    #         else:
    #             print('Index error!')
    #
    #     if utility_name == 'Direct':
    #         if indices[0] in self.streams_hot and indices[1] in self.streams_cold and indices[2] in np.arange(1, self.settings['HEN']['stages']):
    #             if df.index.isin([indices]).any() == False:
    #                 if df['Nr'].values.shape[0] == 0:
    #                     df.loc[indices, ['Nr']] = 0
    #                 else:
    #                     df.loc[indices, ['Nr']] = max(df['Nr'].values) + 1
    #                 df.loc[indices, ['Value']] = value
    #             else:
    #                 print('Index error / Index already exists!')
    #         else:
    #             print('Index error!')
    #
    #     if len(df.index) > 0:
    #         self.retrofit['retrofit set'] = 1
    #     else:
    #         self.retrofit['retrofit set'] = 0



def calc_LMTD_chen(dt1, dt2):
    """
    use chen approximation to calculate LMTD
    :param dt1: temperature difference
    :param dt2: temperature difference
    :return LMTD: LMTD (chen approximation)
    """
    LMTD = (dt1 * dt2 * (dt1 + dt2) / 2) ** (1 / 3)
    return LMTD


def calc_A(settings, LMTD, q, k, beta):
    """
    calculates and return A^beta where beta is the cost exponent (0<beta<=1)
    to consider decreasing specific costs for HEX area

    :param settings:
    :param k:
    :param q:
    :param LMTD:
    :return:
    """

    A = (q / (k * LMTD)) ** beta
    return A


# def cut_values(LMTD_grid, q_grid, A_grid, LMTD_min, LMTD_max):
#     from numpy import max, zeros, nonzero, append, logical_and
#     """
#     Cut infeasible values from domain for HEX area
#
#     :param LMTD_min:
#     :param LMTD_max:
#     :param q:
#     :return:
#     """
#
#     q_max = max(q_grid)
#     q_min = 0.2 * q_max
#
#     LMTD_cut = zeros((0, 1))
#     q_cut = zeros((0, 1))
#     A_cut = zeros((0, 1))
#
#     for i in range(LMTD_min.shape[0]):
#         if q_grid[i, 0] >= q_min:
#             LMTD_slice = LMTD_grid[i, :]
#             LMTD_min_slice = LMTD_min[i]
#             LMTD_max_slice = LMTD_max[i]
#
#             indices = nonzero(logical_and(LMTD_slice <= LMTD_max_slice, LMTD_slice >= LMTD_min_slice))
#
#             LMTD_cut = append(LMTD_cut, LMTD_slice[indices])
#             q_cut = append(q_cut, q_grid[i, indices])
#             A_cut = append(A_cut, A_grid[i, indices])
#
#     return LMTD_cut, q_cut, A_cut


def calc_qmax_aux(i, j, utility_name, sd, dTmin, data_input, conversion_units):
    if utility_name == 'Direct':
        q_max_temp = targets.calc_qmax(data_input, dTmin, np.array([i]), np.array([j]))

    elif utility_name in ['UH', 'UIH']:
        idx = (sd['stream nr'] == j[0]) & (sd['requirement nr'] == j[1])
        key = list(conversion_units[utility_name].keys())[i[0]]
        if conversion_units[utility_name][key]['Tout'] - dTmin < sd.loc[idx, 'T in'].values[0]:
            q_max_temp = 0
        else:
            dT = min([conversion_units[utility_name][key]['Tin'] - dTmin,
                      sd.loc[idx, 'T out'].values[0]]) - sd.loc[idx, 'T in'].values[0]
            q_max_temp = dT * sd.loc[idx, 'm'].values[0] * sd.loc[idx, 'cp'].values[0]

    elif utility_name in ['CUH']:
        idx = (sd['stream nr'] == j[0]) & (sd['requirement nr'] == j[1])
        key = list(conversion_units['CU'].keys())[i[0]]
        if conversion_units['CU'][key]['Tmax'] - dTmin < sd.loc[idx, 'T in'].values[0]:
            q_max_temp = 0
        else:
            dT = min([conversion_units['CU'][key]['Tmax'] - dTmin,
                      sd.loc[idx, 'T out'].values[0]]) - sd.loc[idx, 'T in'].values[0]
            q_max_temp = dT * sd.loc[idx, 'm'].values[0] * sd.loc[idx, 'cp'].values[0]

    elif utility_name in ['UC', 'UIC']:
        idx = (sd['stream nr'] == i[0]) & (sd['requirement nr'] == i[1])
        key = list(conversion_units[utility_name].keys())[j[0]]
        if conversion_units[utility_name][key]['Tout'] + dTmin > sd.loc[idx, 'T in'].values[0]:
            q_max_temp = 0
        else:
            dT = - max([conversion_units[utility_name][key]['Tin'] + dTmin,
                        sd.loc[idx, 'T out'].values[0]]) + sd.loc[idx, 'T in'].values[0]
            q_max_temp = dT * sd.loc[idx, 'm'].values[0] * sd.loc[idx, 'cp'].values[0]

    elif utility_name in ['CUC']:
        idx = (sd['stream nr'] == i[0]) & (sd['requirement nr'] == i[1])
        key = list(conversion_units['CU'].keys())[j[0]]
        if conversion_units['CU'][key]['Tmin'] + dTmin > sd.loc[idx, 'T in'].values[0]:
            q_max_temp = 0
        else:
            dT = - max([conversion_units['CU'][key]['Tmin'] + dTmin,
                        sd.loc[idx, 'T out'].values[0]]) + sd.loc[idx, 'T in'].values[0]
            q_max_temp = dT * sd.loc[idx, 'm'].values[0] * sd.loc[idx, 'cp'].values[0]

    return q_max_temp


def calc_q_max_spec(utility_name, data_input, conversion_units, dTmin):
    """
    Calculates pairwise transferable heat
    :return: q_max (dataframe)
    """

    q_max = pd.DataFrame(columns=['hot', 'cold', 'q_max'])

    hot = data_input['indices']['hot requirements']
    cold = data_input['indices']['cold requirements']

    sd = data_input['streamdata']

    if utility_name in ['Direct', 'UH', 'UIH', 'CUH']:
        cold_side = cold
    if utility_name in ['Direct', 'UC', 'UIC', 'CUC']:
        hot_side = hot
    if utility_name in ['UH', 'UIH']:
        hot_side = [tuple((i, 1)) for i in range(len(conversion_units[utility_name]))]
    if utility_name in ['UC', 'UIC']:
        cold_side = [tuple((i, 1)) for i in range(len(conversion_units[utility_name]))]
    if utility_name in ['CUH']:
        hot_side = [tuple((i, 1)) for i in range(len(conversion_units['CU']))]
    if utility_name in ['CUC']:
        cold_side = [tuple((i, 1)) for i in range(len(conversion_units['CU']))]

    for i in hot_side:
        for j in cold_side:
            q_max = q_max.append({'hot': i, 'cold': j, 'q_max': calc_qmax_aux(i, j, utility_name, sd, dTmin, data_input, conversion_units)},
                                 ignore_index=True)
    return q_max