import pyomo.environ as pyo
import CoolProp.CoolProp as CP    # CoolProp Units: SI -- J, kg, K, Pa, ...
import auxiliary as da
import numpy as np


class System:
    def __init__(self, param, model=None):
        self.param = param
        self.unit = dict()  # dictionary with all units
        self.node = dict()
        self.var = dict()
        self.port = dict()
        self.con = dict()
        self.obj = dict()

        if model is None:
            self.model = pyo.ConcreteModel()
        else:
            self.model = model
            self.model = model

        self.model.set_t = pyo.Set(initialize=range(self.param['n_ts_sc']))
        self.model.set_te = pyo.Set(initialize=range(self.param['n_ts_sc']+1))
        self.model.set_sc = pyo.Set(initialize=self.param['sc'].keys())
        self.param['n_sc'] = len(self.param['sc'])  # number of scenarios
        self.param['dur_sc'] = self.param['n_ts_sc'] * self.param['tss']  # duration of one scenario in hours
        self.param['dur_total'] = self.param['n_sc'] * self.param['dur_sc']  # total duration in hours
        self.param['n_ts_total'] = self.param['n_sc'] * self.param['n_ts_sc']  # total number of time steps

    def add_unit(self, param):
        self.unit[param['name']] = globals()[param['classname']](param, self)

    def add_node(self, param):
        self.node[param['name']] = Node(param, self)

    # def add_con(self, param):
    #     self.con[param['name']] = Node(param, self)

    def build_model(self):
        # Build system constraints
        for u in self.unit:
            for c in self.unit[u].con:
                namestr = 'con_' + u + '_' + c
                try:
                    self.model.add_component(namestr, self.unit[u].con[c])
                except:
                    print('error')

        for n in self.node:
            for c in self.node[n].con:
                namestr = 'con_' + n + '_' + c
                self.model.add_component(namestr, self.node[n].con[c])

        # Build system objective
        obj = 0
        obj_real = 0
        if self.param['free_certificate_fossil'] > 0:
            obj -= self.param['free_certificate_fossil'] * self.param['cost_co2_fossil']
            obj_real -= self.param['free_certificate_fossil'] * self.param['cost_co2_fossil']

        if self.param['free_certificate_bio'] > 0:
            obj -= self.param['free_certificate_bio'] * self.param['cost_co2_biogen']
            obj_real -= self.param['free_certificate_bio'] * self.param['cost_co2_biogen']

        for u in self.unit:
            if 'total' in self.unit[u].obj.keys():
                obj += self.unit[u].obj['total'].expr
                obj_real += self.unit[u].obj['total'].expr
                # small costs for variables in order to reduce equivalent solutions
                # for v in self.unit[u].var['seq'].keys():
                #     obj += 1 * 1e-7 * sum(self.unit[u].var['seq'][v][i] for i in self.unit[u].var['seq'][v].keys())
        for n in self.node:
            if 'total' in self.node[n].obj.keys():
                obj += self.node[n].obj['total'].expr
        namestr = 'obj_system_total'
        self.model.add_component(namestr, pyo.Objective(expr=obj))
        self.obj['total'] = self.model.component('obj_system_total')
        namestr = 'obj_system_total_real'
        self.model.add_component(namestr, pyo.Objective(expr=obj_real))
        self.model.component(namestr).deactivate()
        self.obj['total_real'] = self.model.component('obj_system_total_real')


class Unit:
    def __init__(self, param, system):
        # Initialization
        self.name = param['name']
        self.var = dict()
        self.port = dict()
        self.con = dict()
        self.obj = dict()
        self.param = param

        da.set_general_param(system, self)

#-----------#
### Units ###
#-----------#

class MultifuelBoiler(Unit):                            ## WARNING: currently only usable with list in, share in, list out and share out!
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['lim_q'][0] > 0 or self.param['lim_f'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q'][0], self.param['lim_q'][0])
            else:
                self.param['max_susd'] = (1, 1)

        self.param['h_in'] = CP.PropsSI('H', 'T', self.param['T_in'] + 273.15, 'P', self.param['p_in'],
                                        self.param['medium'])*1e3    # mJ/kg.K
        self.param['h_levels'] = CP.PropsSI('H', 'T', self.param['T_levels'] + 273.15*np.ones(len(self.param['T_levels'])), 'P', self.param['p_levels'],
                                         self.param['medium'])*1e3   # # mJ/kg.K
        # todo h_levels currently not used, still: prepared for missing mass constraint

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q_sep'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['list_out'], domain=pyo.NonNegativeReals)
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['list_out'], domain=pyo.NonNegativeReals)
        self.var['seq']['f'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['f_sep'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['list_in'], domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        self.var['seq']['q_corr'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)

        # if 'port_ele' in self.param:      # todo
        #     self.var['seq']['q_el'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        #     self.var['seq']['f_el'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)


        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['f'] = self.var['seq']['f']

        for n, element in enumerate(self.param['list_out']):            # with this formulation the naming of ports in the form q_sl0 is enabled
            if len(self.param['share_out']) == 1:
                namestr = 'q'                                           #todo checken ob das sinn macht oder weg kann
                namestr2 = 'm'
            else:
                namestr = 'q_' + str(element)
                namestr2 = 'm_' + str(element)
            self.port[namestr] = pyo.Reference(self.var['seq']['q_sep'][:, :, element])
            self.port[namestr2] = pyo.Reference(self.var['seq']['m'][:, :, element])

        for n, element in enumerate(self.param['list_in']):
            if len(self.param['share_in']) == 1:
                namestr = 'f'
            else:
                namestr = 'f_' + str(element)
            self.port[namestr] = pyo.Reference(self.var['seq']['f_sep'][:, :, element])

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q'])
        da.add_cap_lim(self, ['q'])
        da.add_ramp_con(system, self, ['q'])
        da.add_lin_dep(system, self, ['q', 'f'])
        #da.add_simple_m_q(system, self)
        da.add_inv_param(system, self, param)
        da.add_con_a_v(self)

        # if 'port_ele' in self.param:      # todo
        #     da.add_lin_dep(system, self, ['q_el', 'f_el'])
        #
        #     def con_rule(m, s, t):
        #         return self.var['seq']['q_corr'][s, t] == 0
        #     namestr = 'q_corr_case2'
        #     self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)
        #
        # else:
        #     def con_rule(m, s, t):
        #         return self.var['seq']['q_corr'][s, t] == 0
        #     namestr = 'q_corr_case2'
        #     self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


        # todo add  mass-constraint (vgl chp)
        # todo check mit simon

        # def con_rule(m, s, t):        #todo
        #     return self.var['seq']['q'][s, t] == self.var['q_corr'][s, t] +
        # namestr = 'summarize_q'
        # self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


        def con_rule(m, s, t, n):
            return self.var['seq']['q'][s, t] * (self.param['share_out'][self.param['list_out'].index(n)]) == \
                   self.var['seq']['q_sep'][s, t, n]

        namestr = 'relation_q_sep_'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, self.param['list_out'], rule=con_rule)  #

        def con_rule(m, s, t):
            return sum(self.var['seq']['q_sep'][s, t, n] for n in self.param['list_out']) == self.var['seq']['q'][s, t]

        namestr = 'summarize_q_sep_to_q'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


        def con_rule(m, s, t, k):
            return self.var['seq']['f_sep'][s, t, k] <= self.var['seq']['f'][s, t] * (self.param['share_in'][self.param['list_in'].index(k)])
        namestr = 'relation_f_sep_'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, self.param['list_in'], rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['f'][s, t] == sum(self.var['seq']['f_sep'][s, t, z] for z in self.param['list_in'])
        namestr = 'summarize_f_sep_to_f'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class GasBoiler(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['lim_q'][0] > 0 or self.param['lim_f'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q'][0], self.param['lim_q'][0])
            else:
                self.param['max_susd'] = (1, 1)

        self.param['h_in'] = CP.PropsSI('H', 'T', self.param['T_in'] + 273.15, 'P', self.param['pressure'],
                                        self.param['medium'])*1e3    # mJ/kg.K
        self.param['h_out'] = CP.PropsSI('H', 'T', self.param['T_out'] + 273.15, 'P', self.param['pressure'],
                                         self.param['medium'])*1e3   # # mJ/kg.K

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['f'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['m'] = self.var['seq']['m']
        self.port['f'] = self.var['seq']['f']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q'])
        da.add_cap_lim(self, ['q'])
        da.add_ramp_con(system, self, ['q'])
        da.add_lin_dep(system, self, ['q', 'f'])
        da.add_simple_m_q(system, self)
        da.add_inv_param(system, self, param)
        da.add_con_a_v(self)

        # Objective
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class InternalCombustionEngine(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if 'lim_p' in self.param:
            if self.param['lim_p'][0] > 0:
                self.param['u_active'] = True

        if 'lim_f' in self.param:
            if self.param['lim_f'][0] > 0:
                self.param['u_active'] = True

        if self.param['cap_p'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_p'][0], self.param['lim_p'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['f'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['p'] = self.var['seq']['p']
        self.port['f'] = self.var['seq']['f']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['p'])
        da.add_cap_lim(self, ['p'])
        da.add_ramp_con(system, self, ['p'])
        if 'lim_f' in self.param:
            da.add_lin_dep(system, self, ['p', 'f'])
        if 'lim_q' in self.param:
            da.add_lin_dep(system, self, ['q', 'f'])
        da.add_inv_param(system, self, param)
        da.add_con_a_v(self)

        # Objective
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class GasTurbine(Unit): #to do: in steam turbine convert
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if 'lim_p' in self.param:
            if self.param['lim_p'][0] > 0:
                self.param['u_active'] = True

        if 'lim_f' in self.param:
            if self.param['lim_f'][0] > 0:
                self.param['u_active'] = True

        if self.param['cap_p'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_p'][0], self.param['lim_p'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['f'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self) # not necessary, only added (area and volume) if param defined in example

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['p'] = self.var['seq']['p']
        self.port['f'] = self.var['seq']['f']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['p'])
        da.add_cap_lim(self, ['p'])
        da.add_ramp_con(system, self, ['p'])
        if 'lim_f' in self.param:
            da.add_lin_dep(system, self, ['p', 'f'])
        da.add_inv_param(system, self, param)
        da.add_con_a_v(self)    # to do: check what this is

        def con_rule(m, s, t):
            #return self.var['seq']['q'][s, t] == 0.5 * self.var['seq']['f'][s, t]                           # comment(7_12_22 SK) new constraint added - todo calculate factor 0.5 with thermodynamic params
            return self.var['seq']['q'][s, t] == 0.95 * (self.var['seq']['f'][s, t] - self.var['seq']['p'][s, t])   # comment (7_12_22 SK): previous - adapted from thermodynamic considerations - todo add to manual
        namestr = 'energy_balance'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class BackPressureSteamTurbine(Unit): #to do: in steam turbine convert
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if 'lim_p' in self.param:
            if self.param['lim_p'][0] > 0:
                self.param['u_active'] = True

        if 'lim_f' in self.param:
            if self.param['lim_q_in'][0] > 0:
                self.param['u_active'] = True

        if self.param['cap_p'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_p'][0], self.param['lim_p'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q_out'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q_in'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self) # not necessary, only added (area and volume) if param defined in example

        da.add_var_to_model(system, self)

        # Ports
        self.port['q_out'] = self.var['seq']['q_out']
        self.port['p'] = self.var['seq']['p']
        self.port['q_in'] = self.var['seq']['q_in']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['p'])
        da.add_cap_lim(self, ['p'])
        da.add_ramp_con(system, self, ['p'])
        da.add_lin_dep(system, self, ['p', 'q_in'])
        da.add_inv_param(system, self, param)
        da.add_con_a_v(self)    # to do: check what this is

        def con_rule(m, s, t):
            return self.var['seq']['q_out'][s, t] == (self.var['seq']['q_in'][s, t] - self.var['seq']['p'][s, t])*self.param['eta_th']
        namestr = 'energy_balance'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

        # to do - integrate isentropic eff and extraction level

class BackPressureSteamTurbine_new(Unit): #todo final check
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if 'lim_p' in self.param:
            if self.param['lim_p'][0] > 0:
                self.param['u_active'] = True

        if 'lim_f' in self.param:
            if self.param['lim_q_in'][0] > 0:
                self.param['u_active'] = True

        if self.param['cap_p'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_p'][0], self.param['lim_p'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Enthalpies (h_0 = feedwater, h_in = livesteam, h_out = of levels
        self.param['h_0'] = CP.PropsSI('H', 'T', self.param['T_0'] + 273.15,
                                       'P', self.param['p_0'], self.param['medium'])/1e6        # MJ/kg
        self.param['h_in'] = CP.PropsSI('H', 'T', self.param['T_in'] + 273.15,
                                        'P', self.param['p_in'], self.param['medium'])/1e6      # MJ/kg

        self.param['h_out'] = dict()                                                            # calculate specific enthalpy of different (extraction levels)
        for i, n in enumerate(self.param['share_out']):
            self.param['h_out'][n] = CP.PropsSI('H', 'T', self.param['T_levels'][i], 'P', self.param['p_levels'][i],
                                                      self.param['medium'])/1e6

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q_out'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q_out_sep'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['share_out'], domain=pyo.NonNegativeReals)
        self.var['seq']['m_out'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['share_out'], domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q_in'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m_in'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)

        da.add_var_uvwi(system, self)
        da.add_var_a_v(self) # not necessary, only added (area and volume) if param defined in example
        da.add_var_to_model(system, self)

        # Ports
        self.port['q_out'] = self.var['seq']['q_out']
        self.port['p'] = self.var['seq']['p']
        self.port['q_in'] = self.var['seq']['q_in']
        self.port['m_in'] = self.var['seq']['m_in']

        for n, element in enumerate(self.param['list_out']):
            if len(self.param['share_out']) == 1:
                namestr = 'q_out'
                namestr2 = 'm_out'
            else:
                namestr = 'q_out_' + str(element)
                namestr2 = 'm_out_' + str(element)
            self.port[namestr] = pyo.Reference(self.var['seq']['q_out_sep'][:, :, n])
            self.port[namestr2] = pyo.Reference(self.var['seq']['m_out_sep'][:, :, n])

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['p'])
        da.add_cap_lim(self, ['p'])
        da.add_ramp_con(system, self, ['p'])
        #da.add_lin_dep(system, self, ['p', 'q_in'])
        da.add_inv_param(system, self, param)
        da.add_con_a_v(self)    # to do: check what this is

        def con_rule(m, s, t):
            return self.var['seq']['m_in'][s, t] == self.var['seq']['q_in'][s, t] * (self.param['h_in'] - self.param['h_0'])
        namestr = 'livesteam_m_q_balance'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        for i, j in enumerate(self.param['share_out']):
            def con_rule(m, s, t, n):
                return self.var['seq']['m_out'][s, t, n] <= self.var['seq']['m_in'][s, t] * self.param['share_out'][i]
            namestr = 'mass distribution'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


        def con_rule(m, s, t, n):
            return self.var['seq']['q_out_sep'][s, t, n] == self.var['seq']['m_out'][s, t, n] * (self.param['h_out'][n]-self.param['h_0'])
        namestr = 'heat distribution'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['p'][s, t] == self.param['eta'] * (self.var['seq']['m_in'] * (self.param['h_in']-self.param['h_out'][0]) -
                    sum(self.var['seq']['m_out'][s, t, n] * (self.param['h_out'][n] - self.param['h_out'][0])
                        for n in range(1, len(self.param['h_out']))))
        namestr = 'electric production'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

        # to do - integrate isentropic eff and extraction level

class CondensingSteamTurbine_new(Unit): #todo final check
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if 'lim_p' in self.param:
            if self.param['lim_p'][0] > 0:
                self.param['u_active'] = True

        if 'lim_f' in self.param:
            if self.param['lim_q_in'][0] > 0:
                self.param['u_active'] = True

        if self.param['cap_p'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_p'][0], self.param['lim_p'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Enthalpies (h_0 = feedwater and condensate, h_in = livesteam, h_out = of levels, here only extraction

        # self.param['T_cond'] = param['T_cond']
        # self.param['h_out'] = CP.PropsSI('H', 'T', param['T_cond'] + 273.15, 'Q', 0, 'Water')/1e6
        # self.param['T_in'] = param['T_in']
        # self.param['P_in'] = param['P_in']
        # self.param['h_in']  = CP.PropsSI('H', 'T', param['T_in'] + 273.15, 'P',param['P_in'], 'Water')/1e6

        self.param['h_0'] = CP.PropsSI('H', 'T', self.param['T_0'] + 273.15,
                                       'P', self.param['p_0'], self.param['medium'])/1e6        # MJ/kg
        self.param['h_in'] = CP.PropsSI('H', 'T', self.param['T_in'] + 273.15,
                                        'P', self.param['p_in'], self.param['medium'])/1e6      # MJ/kg

        self.param['h_out'] = dict()                                                            # MJ/kg,  specific enthalpy of different (extraction) levels
        for i, n in enumerate(self.param['share_out']):
            self.param['h_out'][n] = CP.PropsSI('H', 'T', self.param['T_levels'][i], 'P', self.param['p_levels'][i],
                                                      self.param['medium'])/1e6

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q_out'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q_out_sep'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['share_out'], domain=pyo.NonNegativeReals)
        self.var['seq']['m_out'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['share_out'], domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q_in'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m_in'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)

        da.add_var_uvwi(system, self)
        da.add_var_a_v(self) # not necessary, only added (area and volume) if param defined in example
        da.add_var_to_model(system, self)

        # Ports
        self.port['q_out'] = self.var['seq']['q_out']
        self.port['p'] = self.var['seq']['p']
        self.port['q_in'] = self.var['seq']['q_in']
        self.port['m_in'] = self.var['seq']['m_in']

        for n, element in enumerate(self.param['list_out']):
            if len(self.param['share_out']) == 1:
                namestr = 'q_out'
                namestr2 = 'm_out'
            else:
                namestr = 'q_out_' + str(element)
                namestr2 = 'm_out_' + str(element)
            self.port[namestr] = pyo.Reference(self.var['seq']['q_out_sep'][:, :, n])
            self.port[namestr2] = pyo.Reference(self.var['seq']['m_out_sep'][:, :, n])

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['p'])
        da.add_cap_lim(self, ['p'])
        da.add_ramp_con(system, self, ['p'])
        #da.add_lin_dep(system, self, ['p', 'q_in'])
        da.add_inv_param(system, self, param)
        da.add_con_a_v(self)    # to do: check what this is

        def con_rule(m, s, t):
            return self.var['seq']['m_in'][s, t] == self.var['seq']['q_in'][s, t] * (self.param['h_in'] - self.param['h_0'])
        namestr = 'livesteam_m_q_balance'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        for i, j in enumerate(self.param['share_out']):
            def con_rule(m, s, t, n):
                return self.var['seq']['m_out'][s, t, n] <= self.var['seq']['m_in'][s, t] * self.param['share_out'][i]
            namestr = 'mass distribution'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


        def con_rule(m, s, t, n):
            return self.var['seq']['q_out_sep'][s, t, n] == self.var['seq']['m_out'][s, t, n] * (self.param['h_out'][n]-self.param['h_0'])
        namestr = 'heat distribution'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['p'][s, t] == self.param['eta'] * (self.var['seq']['m_in'] * (self.param['h_in']-self.param['h_0']) -
                    sum(self.var['seq']['m_out'][s, t, n] * (self.param['h_out'][n] - self.param['h_0']) for n in range(0, len(self.param['h_out']))))
        namestr = 'electric production'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

        # to do - integrate isentropic eff and extraction level

class CondensingSteamTurbine(Unit): #to do: in steam turbine convert
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)
        self.param['T_cond'] = param['T_cond']
        self.param['h_out'] = CP.PropsSI('H', 'T', param['T_cond'] + 273.15, 'Q', 0, 'Water')/1e6
        self.param['T_in'] = param['T_in']
        self.param['P_in'] = param['P_in']
        self.param['h_in']  = CP.PropsSI('H', 'T', param['T_in'] + 273.15, 'P',param['P_in'], 'Water')/1e6

        if 'lim_p' in self.param:
            if self.param['lim_p'][0] > 0:
                self.param['u_active'] = True

        if 'lim_f' in self.param:
            if self.param['lim_q_in'][0] > 0:
                self.param['u_active'] = True

        if self.param['cap_p'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_p'][0], self.param['lim_p'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q_out'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q_in'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self) # not necessary, only added (area and volume) if param defined in example

        da.add_var_to_model(system, self)

        # Ports
        self.port['q_out'] = self.var['seq']['q_out']
        self.port['p'] = self.var['seq']['p']
        self.port['q_in'] = self.var['seq']['q_in']
        self.port['m'] = self.var['seq']['m']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['p'])
        da.add_cap_lim(self, ['p'])
        da.add_ramp_con(system, self, ['p'])
        da.add_lin_dep(system, self, ['p', 'q_in'])
        da.add_inv_param(system, self, param)
        da.add_con_a_v(self)    # to do: check what this is

        def con_rule(m, s, t):
            return self.var['seq']['p'][s, t] == (self.var['seq']['q_in'][s, t]) * self.param['eta_el']
        namestr = 'el_production'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q_in'][s, t] / self.param['h_in'] == (self.var['seq']['m'][s, t])
        namestr = 'mass_q_in'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q_out'][s, t] == (self.var['seq']['m'][s, t]) * self.param['h_out']
        namestr = 'mass_q_out'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class HeatRecoveryBoiler(Unit):
    # Abhitzekessel
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['lim_q_out'][0] > 0 or self.param['lim_f'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q_out'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q'][0], self.param['lim_q'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q_in'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q_out'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['f'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        # self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q_in'] = self.var['seq']['q_in']
        self.port['q_out'] = self.var['seq']['q_out']
        # self.port['m'] = self.var['seq']['m']
        self.port['f'] = self.var['seq']['f']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q_out'])
        da.add_cap_lim(self, ['q_out'])
        da.add_ramp_con(system, self, ['q_out'])
        # da.add_lin_dep(system, self, ['q', 'f'])
        # da.add_simple_m_q(system, self)
        da.add_inv_param(system, self, param)
        da.add_con_a_v(self)

        def con_rule(m, s, t):
            return self.var['seq']['q_out'][s, t] == (self.var['seq']['q_in'][s, t] +
                                                      self.var['seq']['f'][s, t]) * self.param['eta']
        namestr = 'conversion_efficiency'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class Electrolyser(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if 'lim_h2' in self.param:
            if self.param['lim_h2'][0] > 0:
                self.param['u_active'] = True

        if 'lim_p' in self.param:
            if self.param['lim_p'][0] > 0:
                self.param['u_active'] = True

        if self.param['cap_p'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_h2'][0], self.param['lim_h2'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['h2'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['h2'] = self.var['seq']['h2']
        self.port['p'] = self.var['seq']['p']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['p'])
        da.add_cap_lim(self, ['p'])
        da.add_ramp_con(system, self, ['p'])
        # da.add_lin_dep(system, self, ['h2', 'p'])
        da.add_inv_param(system, self, param)
        da.add_con_a_v(self)


        def con_rule(m, s, t):
            return self.var['seq']['p'][s, t]*param['eta'] == self.var['seq']['h2'][s, t]
        namestr = 'conversion_efficiency'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['p'][s, t]*param['loss'] == self.var['seq']['q'][s, t]
        namestr = 'heat_loss'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class Compressor(Unit):
    """
    Compressor model with pressure lift as parameter
    fixme: not realy usable yet!!
    """
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)
        if 'lim_m' in self.param:
            if self.param['lim_m'][0] > 0 or self.param['lim_p'][0] > 0:
                self.param['u_active'] = True

        if 'lim_p' in self.param:
            if self.param['lim_p'][0] > 0:
                self.param['u_active'] = True

        if self.param['cap_p'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_p'][0], self.param['lim_p'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['m'] = self.var['seq']['m']
        self.port['p'] = self.var['seq']['p']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['p'])
        da.add_cap_lim(self, ['p'])
        da.add_ramp_con(system, self, ['p'])
        if 'lim_m' in self.param and 'lim_p' in self.param:
            da.add_lin_dep(system, self, ['m', 'p'])
        da.add_inv_param(system, self, param)
        da.add_con_a_v(self)




        def con_rule(m, s, t):
            return self.var['seq']['p'][s, t]*param['eta'] == self.var['seq']['m'][s, t]
        namestr = 'conversion_efficiency'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['p'][s, t]*param['loss'] == self.var['seq']['q'][s, t]
        namestr = 'heat_loss'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class Burner(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['lim_q'][0] > 0 or self.param['lim_f'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q'][0], self.param['lim_q'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['f'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['f'] = self.var['seq']['f']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q'])
        da.add_cap_lim(self, ['q'])
        da.add_ramp_con(system, self, ['q'])
        da.add_lin_dep(system, self, ['q', 'f'])
        da.add_inv_param(system, self, param)
        da.add_con_a_v(self)

        # Objective
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class ElectrodeBoiler(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['lim_q'][0] > 0 or self.param['lim_p'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q'][0], self.param['lim_q'][0])
            else:
                self.param['max_susd'] = (1, 1)

        self.param['h_in'] = CP.PropsSI('H', 'T', self.param['T_in'] + 273.15, 'P', self.param['pressure'],
                                        self.param['medium']) #*1e3 #Todo check, correction by sk 231122
        # self.param['h_out'] = CP.PropsSI('H', 'T', self.param['T_out'] + 273.15, 'P', self.param['pressure'],
        #                                  self.param['medium'])
        if round(CP.PropsSI('T', 'Q',  1, 'P', self.param['pressure'], 'WATER')-273.15,4) == round(self.param['T_out'],4):
            self.param['h_out'] = CP.PropsSI('H', 'Q',  1, 'P', self.param['pressure'], 'WATER')#*1e3 #Todo check, correction by sk 231122
        else:
            self.param['h_out'] = CP.PropsSI('H', 'T',  self.param['T_out']+273.15, 'P', self.param['pressure'], 'WATER') #*1e3 #Todo check, correction by sk 231122

        da.add_inv_param(system, self, param)

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['m'] = self.var['seq']['m']
        self.port['p'] = self.var['seq']['p']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q'])
        da.add_cap_lim(self, ['q'])
        da.add_ramp_con(system, self, ['q'])
        da.add_lin_dep(system, self, ['q', 'p'])
        da.add_simple_m_q(system, self)
        da.add_con_a_v(self)

        # Objectives
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class Cooler(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['lim_q'][0] > 0 or self.param['lim_p'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q'][0], self.param['lim_q'][0])
            else:
                self.param['max_susd'] = (1, 1)

        self.param['h_in'] = CP.PropsSI('H', 'T', self.param['T_in'] + 273.15, 'P', self.param['pressure'],
                                        self.param['medium'])
        self.param['h_out'] = CP.PropsSI('H', 'T', self.param['T_out'] + 273.15, 'P', self.param['pressure'],
                                         self.param['medium'])

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['m'] = self.var['seq']['m']
        self.port['p'] = self.var['seq']['p']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q'])
        da.add_cap_lim(self, ['q'])
        da.add_ramp_con(system, self, ['q'])
        da.add_lin_dep(system, self, ['q', 'p'])
        da.add_con_a_v(self)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t] == self.var['seq']['m'][s, t] * (
                self.param['h_in'] - self.param['h_out']) / 1e6

        namestr = 'm_q'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objectives
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['inv'].expr
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class CHP(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['lim_q'][0] > 0 or self.param['lim_p'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q'][0], self.param['lim_q'][0])
            else:
                self.param['max_susd'] = (1, 1)

        self.param['h_in'] = dict()
        for i, n in enumerate(self.param['T_in']):
            self.param['h_in'][n] = CP.PropsSI('H', 'T', n + 273.15, 'P', self.param['pressure'][i],
                                                    self.param['medium'][i])

        self.param['h_out'] = dict()
        for i, n in enumerate(self.param['T_in']):
            self.param['h_out'][n] = CP.PropsSI('H', 'T', self.param['T_out'][self.param['T_in'].index(n)] + 273.15, 'P', self.param['pressure'][i],
                                                      self.param['medium'][i])

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q_sep'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['T_in'], domain=pyo.NonNegativeReals)
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['T_in'], domain=pyo.NonNegativeReals)
        self.var['seq']['f'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['p'] = self.var['seq']['p']
        self.port['f'] = self.var['seq']['f']

        for n in self.param['T_in']:
            if len(self.param['T_in']) == 1:
                namestr = 'q'
                namestr2 = 'm'
            else:
                namestr = 'q_' + str(n)
                namestr2 = 'm_' + str(n)
            self.port[namestr] = pyo.Reference(self.var['seq']['q_sep'][:, :, n])
            self.port[namestr2] = pyo.Reference(self.var['seq']['m'][:, :, n])

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q'])
        da.add_cap_lim(self, ['q'])
        da.add_ramp_con(system, self, ['q'])
        da.add_lin_dep(system, self, ['q', 'f'])
        da.add_lin_dep(system, self, ['q', 'p'])
        da.add_con_a_v(self)
        # da.add_simple_m_q(system, self)

        for i, n in enumerate(self.param['T_in']):
            def con_rule(m, s, t, n):
                return self.var['seq']['q_sep'][s, t, n] == self.var['seq']['m'][s, t, n] * (self.param['h_out'][n] - self.param['h_in'][n]) / 1e6
            namestr = 'm_q_sep_' + str(n)
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, self.param['T_in'], rule=con_rule)

        def con_rule(m, s, t, n):
            return self.var['seq']['q_sep'][s, t, n] == self.var['seq']['q'][s, t] * self.param['dist'][self.param['T_in'].index(n)]
        namestr = 'm_q_q_sep'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, self.param['T_in'], rule=con_rule)

        # Objectives
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv'].expr
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class HeatPump_new(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters

        da.init_uvwi_param(self)

        # comb = [(side, inout) for side in ['sink', 'source'] for inout in ['in', 'out']]

        # for c in comb:
        #     side = c[0]
        #     inout = c[1]
        #
        #     self.param['h_{}_{}'.format(side, inout)] = dict()
        #     for i, n in enumerate(self.param['T_{}_{}'.format(side, inout)]):
        #         self.param['h_{}_{}'.format(side, inout)][n] = CP.PropsSI('H', 'T', n + 273.15, 'P', self.param['pressure_{}'.format(side)][i],
        #                                                 self.param['medium_{}'.format(side)])

        # self.param['lim_p'] = tuple(self.param['lim_q_sink'][k] / self.param['COP'][k] for k in range(2))

        if self.param['lim_q_sink'][0] > 0:  # or self.param['lim_p'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q_sink'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q_sink'][0], self.param['lim_q_sink'][0])
            else:
                self.param['max_susd'] = (1, 1)


        # Sets
        sources = np.arange(0, self.param['T_source_out'].__len__())
        sinks = np.arange(0, self.param['T_sink_out'].__len__())
        combinations = [(m, n) for m in sources for n in sinks]
        self.set_source = pyo.Set(initialize=sources)
        self.set_sink = pyo.Set(initialize=sinks)
        self.set_combinations = pyo.Set(initialize=combinations)
        # Variables

        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q_sink_ind'] = pyo.Var(system.model.set_sc, system.model.set_t, self.set_combinations, domain=pyo.NonNegativeReals)
        self.var['seq']['q_sink'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q_source_ind'] = pyo.Var(system.model.set_sc, system.model.set_t, self.set_combinations, domain=pyo.NonNegativeReals)
        self.var['seq']['q_source'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        # self.var['seq']['m_sink_in'] = pyo.Var(system.model.set_sc, system.model.set_t, self.set_combinations,
        #                                        domain=pyo.NonNegativeReals)
        # self.var['seq']['m_source_in'] = pyo.Var(system.model.set_sc, system.model.set_t, self.set_combinations,
        #                                          domain=pyo.NonNegativeReals)
        self.var['seq']['p_ind'] = pyo.Var(system.model.set_sc, system.model.set_t, self.set_combinations, domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports

        for n in self.set_combinations:
            if len(sinks) == 1:
                namestr = 'q_sink'
            else:
                namestr = 'q_sink_' + str(n)
            self.port[namestr] = pyo.Reference(self.var['seq']['q_sink_ind'][:, :, n])

        if len(self.set_combinations) > 1:
            def expr_rule(m, s, t):
                return sum(self.var['seq']['q_sink_ind'][s, t, k] for k in self.set_combinations)

            namestr = 'port_' + self.name + '_q_sink'
            system.model.add_component(namestr, pyo.Expression(system.model.set_sc, system.model.set_t, rule=expr_rule))
            self.port['q_sink'] = system.model.component(namestr)


        for n in self.set_combinations:
            if len(sources) == 1:
                namestr = 'q_source'
            else:
                namestr = 'q_source_' + str(n)
            self.port[namestr] = pyo.Reference(self.var['seq']['q_source_ind'][:, :, n])

        if len(self.set_combinations) > 1:
            def expr_rule(m, s, t):
                return sum(self.var['seq']['q_source_ind'][s, t, k] for k in self.set_combinations)

            namestr = 'port_' + self.name + '_q_source'
            system.model.add_component(namestr, pyo.Expression(system.model.set_sc, system.model.set_t, rule=expr_rule))
            self.port['q_source'] = system.model.component(namestr)

        def expr_rule(m, s, t):
            return sum(self.var['seq']['p_ind'][s, t, k] for k in self.set_combinations)

        namestr = 'port_' + self.name + '_p'
        system.model.add_component(namestr, pyo.Expression(system.model.set_sc, system.model.set_t, rule=expr_rule))
        self.port['p'] = system.model.component(namestr)

        # for n in self.param['T_sink_in']:
        #     if len(self.param['T_sink_in']) == 1:
        #         namestr = 'm_sink_in'
        #     else:
        #         namestr = 'm_sink_in_' + str(n)
        #     self.port[namestr] = pyo.Reference(self.var['seq']['m_sink_in'][:, :, n])
        #
        # for n in self.param['T_source_in']:
        #     if len(self.param['T_source_in']) == 1:
        #         namestr = 'm_source_in'
        #     else:
        #         namestr = 'm_source_in_' + str(n)
        #     self.port[namestr] = pyo.Reference(self.var['seq']['m_source_in'][:, :, n])

        # def expr_rule(m, s, t):
        #     return sum(self.var['seq']['m_source_in'][s, t, k] for k in self.param['T_source_in'])
        #
        # namestr = 'port_' + self.name + '_m_source_out'
        # system.model.add_component(namestr, pyo.Expression(system.model.set_sc, system.model.set_t, rule=expr_rule))
        # self.port['m_source_out'] = system.model.component(namestr)

        # def expr_rule(m, s, t):
        #     return sum(self.var['seq']['m_sink_in'][s, t, k] for k in self.param['T_sink_in'])
        #
        # namestr = 'port_' + self.name + '_m_sink_out'
        # system.model.add_component(namestr, pyo.Expression(system.model.set_sc, system.model.set_t, rule=expr_rule))
        # self.port['m_sink_out'] = system.model.component(namestr)

        da.add_inv_param(system, self, param)

        # Constraints

        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q_sink'])
        da.add_cap_lim(self, ['q_sink'])
        da.add_ramp_con(system, self, ['q_sink'])
        da.add_con_a_v(self)
        # da.add_lin_dep(system, self, ['q_sink', 'p'])

        def con_rule(m, s, t):
            return self.var['seq']['q_sink'][s, t] == self.var['seq']['q_source'][s, t] + self.var['seq']['p'][s, t]

        namestr = 'energy_balance'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t, c1, c2):
            return self.var['seq']['q_sink_ind'][s, t, c1, c2] == self.var['seq']['q_source_ind'][s, t, c1, c2] + self.var['seq']['p_ind'][s, t, c1, c2]

        namestr = 'energy_balance_ind'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, self.set_combinations, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q_sink'][s, t] == sum(self.var['seq']['q_sink_ind'][s, t, c] for c in self.set_combinations)

        namestr = 'energy_balance_sink'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q_source'][s, t] == sum(self.var['seq']['q_source_ind'][s, t, c] for c in self.set_combinations)

        namestr = 'energy_balance_source'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['p'][s, t] == sum(self.var['seq']['p_ind'][s, t, c] for c in self.set_combinations)

        namestr = 'energy_balance_p'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)



        self.param['COP'] = {}

        for m in sources:
            for n in sinks:
                self.param['COP'][(m, n)] = self.param['eta_comp'][combinations.index((m, n))] * (self.param['T_sink_out'][n] + self.param['delta_T_sink'][n] + 273.15) / \
                                            (self.param['T_sink_out'][n] + self.param['delta_T_sink'][n] - self.param['T_source_out'][m] + self.param['delta_T_source'][m])

        def con_rule(m, s, t, c1, c2):
            return self.var['seq']['q_sink_ind'][s, t, c1, c2] == self.param['COP'][(c1, c2)] * self.var['seq']['p_ind'][s, t, c1, c2]

        namestr = 'cop'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, self.set_combinations, rule=con_rule)

        # def con_rule(m, s, t):
        #     return self.var['seq']['q_sink'][s, t] == sum(
        #         self.var['seq']['m_sink_in'][s, t, n] * (self.param['h_sink_out'] - self.param['h_sink_in'][n]) / 1e6
        #         for n in self.param['T_sink_in'])
        #
        # namestr = 'm_sink(q_sink)'
        # self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # def con_rule(m, s, t):
        #     return self.var['seq']['q_source'][s, t] == sum(self.var['seq']['m_source_in'][s, t, n] * (
        #             self.param['h_source_in'][n] - self.param['h_source_out']) / 1e6 for n in self.param['T_source_in'])
        #
        # namestr = 'm_source(q_source)'
        # self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objectives

        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)
        # self.obj['inv'] = (self.param['inv_var'] * self.var['scalar']['cap'] + self.param['inv_fix'] * self.var['scalar'][
        #     'i']) / param['depreciation_period']

        # # Total objective, which is assigned directly to unit
        # obj = 0
        # obj += self.obj['inv']

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class HeatPump(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters

        da.init_uvwi_param(self)

        self.param['h_sink_in'] = dict()
        for n in self.param['T_sink_in']:
            self.param['h_sink_in'][n] = CP.PropsSI('H', 'T', n + 273.15, 'P', self.param['pressure_sink'],
                                                    self.param['medium_sink']) / 1e6                                    # MJ/kg
        self.param['h_source_in'] = dict()
        for n in self.param['T_source_in']:
            self.param['h_source_in'][n] = CP.PropsSI('H', 'T', n + 273.15, 'P', self.param['pressure_source'],
                                                      self.param['medium_source']) / 1e6                                # MJ/kg
        self.param['h_sink_out'] = CP.PropsSI('H', 'T', self.param['T_sink_out'] + 273.15, 'P',
                                              self.param['pressure_sink'], self.param['medium_sink']) / 1e6             # MJ/kg
        self.param['h_source_out'] = CP.PropsSI('H', 'T', self.param['T_source_out'] + 273.15, 'P',
                                                self.param['pressure_source'], self.param['medium_source']) / 1e6       # MJ/kg
        self.param['COP'] = tuple(
            self.param['eta_comp'][k] * (self.param['T_sink_out'] + self.param['delta_T_sink'][k] + 273.15) /
            (self.param['T_sink_out'] + self.param['delta_T_sink'][k] - self.param['T_source_out'] +
             self.param['delta_T_source'][k])
            for k in range(2)
        )
        self.param['lim_p'] = tuple(self.param['lim_q_sink'][k] / self.param['COP'][k] for k in range(2))               # MW

        if self.param['lim_q_sink'][0] > 0 or self.param['lim_p'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q_sink'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q_qink'][0], self.param['lim_q_qink'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables

        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q_sink'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q_source'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m_sink_in'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['T_sink_in'],
                                               domain=pyo.NonNegativeReals)
        self.var['seq']['m_source_in'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['T_source_in'],
                                                 domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports

        self.port['q_sink'] = self.var['seq']['q_sink']
        self.port['q_source'] = self.var['seq']['q_source']
        self.port['p'] = self.var['seq']['p']

        for n in self.param['T_sink_in']:
            if len(self.param['T_sink_in']) == 1:
                namestr = 'm_sink_in'
            else:
                namestr = 'm_sink_in_' + str(n)
            self.port[namestr] = pyo.Reference(self.var['seq']['m_sink_in'][:, :, n])

        for n in self.param['T_source_in']:
            if len(self.param['T_source_in']) == 1:
                namestr = 'm_source_in'
            else:
                namestr = 'm_source_in_' + str(n)
            self.port[namestr] = pyo.Reference(self.var['seq']['m_source_in'][:, :, n])

        def expr_rule(m, s, t):
            return sum(self.var['seq']['m_source_in'][s, t, k] for k in self.param['T_source_in'])

        namestr = 'port_' + self.name + '_m_source_out'
        system.model.add_component(namestr, pyo.Expression(system.model.set_sc, system.model.set_t, rule=expr_rule))
        self.port['m_source_out'] = system.model.component(namestr)

        def expr_rule(m, s, t):
            return sum(self.var['seq']['m_sink_in'][s, t, k] for k in self.param['T_sink_in'])

        namestr = 'port_' + self.name + '_m_sink_out'
        system.model.add_component(namestr, pyo.Expression(system.model.set_sc, system.model.set_t, rule=expr_rule))
        self.port['m_sink_out'] = system.model.component(namestr)

        da.add_inv_param(system, self, param)

        # Constraints

        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q_sink'])
        da.add_cap_lim(self, ['q_sink'])
        da.add_ramp_con(system, self, ['q_sink'])
        da.add_lin_dep(system, self, ['q_sink', 'p'])
        da.add_con_a_v(self)

        def con_rule(m, s, t):
            return self.var['seq']['q_sink'][s, t] == self.var['seq']['q_source'][s, t] + self.var['seq']['p'][s, t]    # MW

        namestr = 'energy_balance'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q_sink'][s, t] == sum(
                self.var['seq']['m_sink_in'][s, t, n] * (self.param['h_sink_out'] - self.param['h_sink_in'][n])         # MW
                for n in self.param['T_sink_in'])

        namestr = 'm_sink(q_sink)'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q_source'][s, t] == sum(self.var['seq']['m_source_in'][s, t, n] * (
                self.param['h_source_in'][n] - self.param['h_source_out']) for n in self.param['T_source_in'])          # MW

        namestr = 'm_source(q_source)'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objectives

        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)
        # self.obj['inv'] = (self.param['inv_var'] * self.var['scalar']['cap'] + self.param['inv_fix'] * self.var['scalar'][
        #     'i']) / param['depreciation_period']

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class HeatPumpSimple(Unit):
    # deprecated?
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters

        da.init_uvwi_param(self)

        self.param['COP'] = (self.param['eta_comp'] * (self.param['T_cond'] + 273.15) /
            (self.param['T_cond'] - self.param['T_evap'] ))

        self.param['lim_p'] = [self.param['lim_q_sink'][k] / self.param['COP'] for k in self.param['lim_q_sink']]

        if self.param['lim_q_sink'][0] > 0 or self.param['lim_p'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q_sink'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q_qink'][0], self.param['lim_q_qink'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables

        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q_sink'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q_source'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports

        self.port['q_sink'] = self.var['seq']['q_sink']
        self.port['q_source'] = self.var['seq']['q_source']
        self.port['p'] = self.var['seq']['p']

        da.add_inv_param(system, self, param)

        # Constraints

        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q_sink'])
        da.add_cap_lim(self, ['q_sink'])
        da.add_ramp_con(system, self, ['q_sink'])
        da.add_lin_dep(system, self, ['q_sink', 'p'])
        da.add_con_a_v(self)

        def con_rule(m, s, t):
            return self.var['seq']['q_sink'][s, t] == self.var['seq']['q_source'][s, t] + self.var['seq']['p'][s, t]

        namestr = 'energy_balance'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objectives

        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class VapourCompression(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters

        da.init_uvwi_param(self)
        self.param['T_in'] = param['T_in']  # °C
        self.param['T_out'] = param['T_out']  # °C
        self.param['P_in'] = param['P_in']  # Pa
        self.param['P_out'] = param['P_out']  # Pa
        # self.param['saturated'] = param['saturated']  # bool
        self.param['FW T_in'] = param['FW T_in']  # °C
        self.param['FW P_in'] = param['FW P_in']  # Pa
        self.param['eta'] = param['eta']  # -

        self.param['T_isentrop'] = CP.PropsSI('T', 'S', CP.PropsSI('S', 'P', param['P_in'], 'Q', 1, 'Water'), 'P', param['P_out'], 'Water')-273.15    # °C
        self.param['h_in'] = CP.PropsSI('H', 'T', self.param['T_in']+273.15, 'P', param['P_in'], 'WATER') / 1e6                                       # MJ/kg
        self.param['h_isentrop'] = CP.PropsSI('H', 'T', self.param['T_isentrop']+273.15, 'P', param['P_out'], 'WATER') / 1e6                          # MJ/kg
        self.param['h_corrected'] = (self.param['h_isentrop'] - CP.PropsSI('H','P', param['P_in'], 'Q', 1, 'Water') / 1e6)/param['eta'] + CP.PropsSI('H', 'P', param['P_in'], 'Q', 1, 'Water') / 1e6 # MJ/kg

        self.param['dh'] = self.param['h_corrected'] - self.param['h_in']                                                                             # MJ/kg

        self.param['h_FW'] = CP.PropsSI('H', 'T',  param['FW T_in']+273.15, 'P', param['FW P_in'], 'WATER') / 1e6                                     # MJ/kg

        if round(CP.PropsSI('T', 'Q',  1, 'P', param['P_out'], 'WATER')-273.15,4) == round(param['T_out'],4):           # enthalpy at saturation curve after freshwater addition
            self.param['h_target'] = CP.PropsSI('H', 'Q',  1, 'P', param['P_out'], 'WATER') / 1e6                                                     # MJ/kg
        else:
            self.param['h_target'] = CP.PropsSI('H', 'T', param['T_out']+273.15, 'P', param['P_out'], 'WATER') / 1e6                                 # MJ/kg

        # from h_target * (m_in + m_FW) = h_corrected * m_in + h_FW * m_FW
        self.param['FW fraction'] = (self.param['h_target'] - self.param['h_corrected']) / (self.param['h_FW'] - self.param['h_target'])              # [-]

        self.param['dh_out'] = self.param['dh'] + self.param['h_FW'] * self.param['FW fraction']





        if self.param['lim_q'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q'][0], self.param['lim_q'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables

        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q_in'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m_in'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m_out'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)

        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports

        self.port['q'] = self.var['seq']['q']
        self.port['q_in'] = self.var['seq']['q_in']
        self.port['p'] = self.var['seq']['p']
        self.port['m_in'] = self.var['seq']['m_in']
        self.port['m_out'] = self.var['seq']['m_out']

        da.add_inv_param(system, self, param)

        # Constraints

        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q'])
        da.add_cap_lim(self, ['q'])
        da.add_ramp_con(system, self, ['q'])
        da.add_con_a_v(self)
        # da.add_lin_dep(system, self, ['q', 'p'])

        # # from q = H_target - H_in = (m_in * h_corrected + m_FW * h_FW) - m_in * h_in = m_in * (h_corrected + m_FW / m_in * h_FW) - h_in = m_in * dh_out
        # def con_rule(m, s, t):
        #     return self.var['seq']['q'][s, t] == self.var['seq']['m_in'][s, t] * self.param['dh_out']
        #
        # namestr = 'efficiency'
        # self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['m_out'][s,t] * self.param['h_target'] == self.var['seq']['q'][s,t]

        namestr= 'useful_heat'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['m_in'][s,t] * self.param['h_in'] == self.var['seq']['q_in'][s,t]

        namestr= 'relation_mass_heat_inlet'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['p'][s, t] == self.var['seq']['m_in'][s, t] * self.param['dh']

        namestr = 'p'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # def con_rule(m, s, t):
        #     return self.var['seq']['p'][s, t] <= self.var['scalar']['cap']      #nicht notwendig todo check
        #
        # namestr = 'cap_p'
        # self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)
        # # Objectives

        def con_rule(m, s, t):
            return self.var['seq']['m_out'][s, t] == self.var['seq']['m_in'][s, t] * (1 + self.param['FW fraction'])    # kg/s
        namestr = 'm_out'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)
        # self.obj['inv'] = (self.param['inv_var'] * self.var['scalar']['cap'] + self.param['inv_fix'] * self.var['scalar'][
        #     'i']) / param['depreciation_period']

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class VapourCompressionEnhanced(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters

        da.init_uvwi_param(self)
        self.param['T_in'] = param['T_in']  # °C    ideal value
        self.param['T_lift'] = param['T_lift']  # °C      ideal value
        self.param['T_drop'] = param['T_drop']  # °C      ideal value
        self.param['P_in'] = param['P_in']  # Pa
        self.param['P_out'] = param['P_out']  # Pa
        # self.param['saturated'] = param['saturated']  # bool
        self.param['FW T_in'] = param['FW T_in']  # °C
        self.param['FW P_in'] = param['FW P_in']  # Pa
        self.param['eta'] = param['eta']  # -

        self.param['stage'] = param['stage'] # currently not used

        self.param['T_isentrop'] = CP.PropsSI('T', 'S', CP.PropsSI('S', 'P', param['P_in'], 'Q', 1, 'Water'), 'P', param['P_out'], 'Water')-273.15    # °C
        self.param['h_in'] = CP.PropsSI('H', 'T', self.param['T_in'] + 273.15, 'P', param['P_in'], 'WATER') / 1e6                                       # MJ/kg

        self.param['h_isentrop'] = CP.PropsSI('H', 'T', self.param['T_isentrop']+273.15, 'P', param['P_out'], 'WATER') / 1e6                          # MJ/kg
        self.param['h_corrected_FL'] = (self.param['h_isentrop'] - CP.PropsSI('H','P', param['P_in'], 'Q', 1, 'Water') / 1e6)/param['eta'][1] + CP.PropsSI('H', 'P', param['P_in'], 'Q', 1, 'Water') / 1e6 # MJ/kg
        self.param['h_corrected_PL'] = (self.param['h_isentrop'] - CP.PropsSI('H','P', param['P_in'], 'Q', 1, 'Water') / 1e6)/param['eta'][0] + CP.PropsSI('H', 'P', param['P_in'], 'Q', 1, 'Water') / 1e6 # MJ/kg

        self.param['dh_FL'] = self.param['h_corrected_FL'] - self.param['h_in']                                                                       # MJ/kg
        self.param['dh_PL'] = self.param['h_corrected_PL'] - self.param['h_in']                                                                       # MJ/kg

        self.param['h_FW'] = CP.PropsSI('H', 'T',  param['FW T_in']+273.15, 'P', param['FW P_in'], 'WATER') / 1e6                                     # MJ/kg

        if round(CP.PropsSI('T', 'Q',  1, 'P', param['P_out'], 'WATER')-273.15,4) == round(param['T_in']+param['T_lift'],4):           # enthalpy at saturation curve after freshwater addition
            self.param['h_target_FL'] = CP.PropsSI('H', 'Q',  1, 'P', param['P_out'], 'WATER') / 1e6                                                     # MJ/kg
        else:
            self.param['h_target_FL'] = CP.PropsSI('H', 'T',  param['T_in']+param['T_lift']+273.15, 'P', param['P_out'], 'WATER') / 1e6                                 # MJ/kg

        if round(CP.PropsSI('T', 'Q',  1, 'P', param['P_out'], 'WATER')-273.15,4) == round(param['T_in']+param['T_lift']-param['T_drop'],4):           # enthalpy at saturation curve after freshwater addition
            self.param['h_target_PL'] = CP.PropsSI('H', 'Q',  1, 'P', param['P_out'], 'WATER') / 1e6                                                     # MJ/kg
        else:
            self.param['h_target_PL'] = CP.PropsSI('H', 'T',  param['T_in']+param['T_lift']-param['T_drop']+273.15, 'P', param['P_out'], 'WATER') / 1e6                                 # MJ/kg

        # from h_target * (m_in + m_FW) = h_corrected * m_in + h_FW * m_FW
        self.param['FW fraction_FL'] = (self.param['h_target_FL'] - self.param['h_corrected_FL']) / (self.param['h_FW'] - self.param['h_target_FL'])              # [-]
        self.param['FW fraction_PL'] = (self.param['h_target_PL'] - self.param['h_corrected_PL']) / (self.param['h_FW'] - self.param['h_target_PL'])              # [-]

        self.param['dh_out_FL'] = self.param['dh_FL'] + self.param['h_FW']*self.param['FW fraction_FL']                                                        # MJ/kg
        self.param['dh_out_PL'] = self.param['dh_PL'] + self.param['h_FW']*self.param['FW fraction_PL']                                                        # MJ/kg

        if self.param['lim_q'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q'][0], self.param['lim_q'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables

        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q_in'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m_in'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m_out_low'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m_out_high'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m_out'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)

        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)

        self.var['seq']['delta_on'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['delta_off'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['b_low'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeIntegers, bounds=(0, 1))
        self.var['seq']['b_high'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeIntegers, bounds=(0, 1))

        self.var['seq']['q_low'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['q_high'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)

        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['delta_on'] = self.var['seq']['delta_on']
        self.port['b_low'] = self.var['seq']['b_low']
        self.port['b_high'] = self.var['seq']['b_high']
        self.port['q'] = self.var['seq']['q']
        self.port['q_low'] = self.var['seq']['q_low']
        self.port['q_high'] = self.var['seq']['q_high']
        self.port['q_in'] = self.var['seq']['q_in']
        self.port['p'] = self.var['seq']['p']
        self.port['m_in'] = self.var['seq']['m_in']
        self.port['m_out_low'] = self.var['seq']['m_out_low']
        self.port['m_out_high'] = self.var['seq']['m_out_high']
        self.port['m_out'] = self.var['seq']['m_out']




        da.add_inv_param(system, self, param)

        # Constraints

        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q'])
        da.add_cap_lim(self, ['q'])
        da.add_ramp_con(system, self, ['q'])
        da.add_con_a_v(self)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s,t] + self.var['seq']['delta_on'][s,t] + self.var['seq']['delta_off'][s,t] == self.var['scalar']['cap']

        namestr= 'close delta balance'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['delta_on'][s,t] <= self.var['scalar']['cap'] * (self.param['lim_q'][1]-self.param['lim_q'][0])

        namestr= 'limit delta_on_1'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['delta_on'][s,t] <= self.var['seq']['u'][s,t] * self.param['cap_q'][1]

        namestr= 'limit delta_on_2'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['delta_off'][s,t] <= (1-self.var['seq']['u'][s,t]) * self.param['cap_q'][1]

        namestr= 'limit delta_off'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['delta_on'][s,t] + 1000 * self.var['seq']['b_low'][s,t] >= self.var['scalar']['cap'] * 0.5 * (self.param['lim_q'][1]-self.param['lim_q'][0])

        namestr= 'big_m_delta_on1'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['delta_on'][s,t] - 1000 * self.var['seq']['b_high'][s,t] <= self.var['scalar']['cap'] * 0.5 * (self.param['lim_q'][1]-self.param['lim_q'][0])

        namestr= 'big_m_delta_on2'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['b_low'][s,t] + self.var['seq']['b_high'][s,t] == self.var['seq']['u'][s,t]

        namestr= 'SOS1_for_b_low+high'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)



        ## thermodynamic relations

        def con_rule(m, s, t):
            return self.var['seq']['m_in'][s,t] * self.param['h_in'] == self.var['seq']['q_in'][s,t]

        namestr= 'relation_mass_heat_inlet'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['m_out_low'][s, t] <= self.var['seq']['m_in'][s, t] * (1 + self.param['FW fraction_FL'])    # kg/s
        namestr = 'm_out_lowT_FL'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['m_out_low'][s, t] <= self.var['seq']['b_low'][s, t] * 1000    # kg/s
        namestr = 'm_out_lowT_limit'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['m_out_high'][s, t] <= self.var['seq']['m_in'][s, t] * (1 + self.param['FW fraction_PL'])    # kg/s
        namestr = 'm_out_highT_PL'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['m_out_high'][s, t] <= self.var['seq']['b_high'][s, t] * 1000    # kg/s
        namestr = 'm_out_highT_limit'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['m_out_high'][s, t] + self.var['seq']['m_out_low'][s, t] == self.var['seq']['m_out'][s, t]    # kg/s
        namestr = 'sum_mass'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['m_out'][s, t] >= self.var['seq']['m_in'][s, t]*(1 + self.param['FW fraction_FL'])   # kg/s
        namestr = 'minimum_mass'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['m_out_low'][s, t] * self.param['h_target_FL'] == self.var['seq']['q_low'][s,t]

        namestr= 'useful_heat_FL'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['m_out_high'][s, t] * self.param['h_target_PL'] == self.var['seq']['q_high'][s,t]

        namestr= 'useful_heat_PL'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t] == self.var['seq']['q_high'][s,t] + self.var['seq']['q_low'][s,t]

        namestr= 'sum_heat'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


        def con_rule(m, s, t):
            return self.var['seq']['p'][s, t] >= self.var['seq']['m_out_low'][s,t] / (1 + self.param['FW fraction_FL']) * self.param['dh_FL'] + self.var['seq']['m_out_high'][s,t] / (1 +self.param['FW fraction_PL']) * self.param['dh_PL']

        namestr = 'p'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)



        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)
        # self.obj['inv'] = (self.param['inv_var'] * self.var['scalar']['cap'] + self.param['inv_fix'] * self.var['scalar'][
        #     'i']) / param['depreciation_period']

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['cost_SU'].expr
        obj += self.obj['cost_SD'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class Photovoltaic(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['cap_area'][0] > 0:
            self.param['i_active'] = True

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['p'] = self.var['seq']['p']

        da.add_inv_param(system, self, param)

        # Constraints
        da.add_cap_lim(self, ['area'])

        # note: param['seq']['solar'] muss Global Horizontal Irradiance in W/m^2 sein
        # (GHI = Direkte Normalstrahlung * cos(z) + Diffuse Strahlung ...)
        # Fläche in cap == Fläche in m^2
        self.param['solar'] = self.param['seq']

        def con_rule(m, s, t):
            if 'ppa_mode' in self.param.keys():
                if self.param['ppa_mode'] == 1:
                    return self.var['seq']['p'][s, t] == float(self.param['eta'] * self.param['solar'][s][t]/1e6) * \
                   self.var['scalar']['cap']
                else:
                    return self.var['seq']['p'][s, t] <= float(self.param['eta'] * self.param['solar'][s][t]/1e6) * \
                   self.var['scalar']['cap']
            else:
                return self.var['seq']['p'][s, t] <= float(self.param['eta'] * self.param['solar'][s][t]/1e6) * \
                   self.var['scalar']['cap']

        namestr = 'max_p'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objectives
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class WindTurbinePark(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['cap_max_power'][0] > 0:
            self.param['i_active'] = True

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['p'] = self.var['seq']['p']

        da.add_inv_param(system, self, param)

        # Constraints
        da.add_cap_lim(self, ['max_power'])


        def con_rule(m, s, t):
            # todo: ppa mode needs to be implemented
            # if 'ppa_mode' in self.param.keys():
            #     if self.param['ppa_mode'] == 1:
            #         return self.var['seq']['p'][s, t] == float(self.param['eta'] * self.param['solar'][s][t]) * \
            #        self.var['scalar']['cap']
            #     else:
            #         return self.var['seq']['p'][s, t] <= float(self.param['eta'] * self.param['solar'][s][t]) * \
            #        self.var['scalar']['cap']
            # else:
            return self.var['seq']['p'][s, t] <= float(self.var['scalar']['rotor_radius'] * self.param['solar'][s][t]) * \
                   self.var['scalar']['cap']
        namestr = 'max_p'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # note: param['seq']['wind_speed'] muss Windgeschwindigkeit im m/s sein
        # Objectives
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class SolarThermal(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        def q_max_calc(param):
            if param['unit'] == 'kW':
                cf = 1000


            q_max = {}

            c0 = param['coefficients'][0]
            c1 = param['coefficients'][1]
            c2 = param['coefficients'][2]
            for s in system.model.set_sc:
                q_max.setdefault(s, {})
                q_max_aux = np.ndarray(system.model.set_t.__len__())
                for t in system.model.set_t:
                    T_col = (param['T_out'][0]+param['T_in'][0])/2
                    q_max_aux[t] = c0 * param['solar'][s][t]*cf - c1*(T_col-param['T_amb'][s][t]) - c2*(T_col-param['T_amb'][s][t])**2
                q_max_aux[q_max_aux<0] = 0
                q_max[s] = q_max_aux/cf
            return q_max

        # Parameters
        da.init_uvwi_param(self)

        if self.param['cap_area'][0] > 0:
            self.param['i_active'] = True

        self.param['h_in'] = dict()
        for n in self.param['T_in']:
            self.param['h_in'][n] = CP.PropsSI('H', 'T', n + 273.15, 'P', self.param['pressure'], self.param['medium'])
        self.param['h_out'] = dict()
        for n in self.param['T_out']:
            self.param['h_out'][n] = CP.PropsSI('H', 'T', n + 273.15, 'P', self.param['pressure'], self.param['medium'])

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m_in'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['T_in'],
                                          domain=pyo.NonNegativeReals)  # negative values are admissible, since demand may be negative too.
        self.var['seq']['m_out'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['T_out'],
                                           domain=pyo.NonNegativeReals)  # negative values are admissible, since demand may be negative too.
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']

        for n in self.param['T_in']:
            if len(self.param['T_in']) == 1:
                namestr = 'm_in'
            else:
                namestr = 'm_in_' + str(n)
            self.port[namestr] = pyo.Reference(self.var['seq']['m_in'][:, :, n])

        for n in self.param['T_out']:
            if len(self.param['T_out']) == 1:
                namestr = 'm_out'
            else:
                namestr = 'm_out_' + str(n)
            self.port[namestr] = pyo.Reference(self.var['seq']['m_out'][:, :, n])

        # cost param
        da.add_inv_param(system, self, param)

        # Constraints
        da.add_cap_lim(self, ['area'])

        def con_rule(m, s, t):
            return sum(self.var['seq']['m_in'][s, t, n] for n in self.param['T_in']) == sum(
                self.var['seq']['m_out'][s, t, n] for n in self.param['T_out'])

        namestr = 'm_in_is_m_out'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        if 'm_out_dist' in self.param.keys():
            def con_rule(m, s, t, n):
                return self.param['m_out_dist'][s][n][t] * sum(
                    self.var['seq']['m_out'][s, t, k] for k in self.param['T_out']) == self.var['seq']['m_out'][s, t, n]

            namestr = 'm_out_dist'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, self.param['T_out'],
                                               rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t] == (
                sum(self.var['seq']['m_out'][s, t, n] * self.param['h_out'][n] for n in self.param['T_out']) - sum(
                    self.var['seq']['m_in'][s, t, n] * self.param['h_in'][n] for n in self.param['T_in'])) / 1e3

        namestr = 'q(m_in,m_out)'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        if 'coefficients' in param.keys():
            q_max = q_max_calc(param)
            def con_rule(m, s, t):
                return self.var['seq']['q'][s, t] <= self.var['scalar']['cap'] * q_max[s][t]

        else:
            def con_rule(m, s, t):
                return self.var['seq']['q'][s, t] <= float(self.param['eta']*self.param['seq']['solar'][s,t]) * \
                           self.var['scalar']['cap']

        namestr = 'max_q'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objectives
        self.obj['inv'] = (self.param['inv_var'] * self.var['scalar']['cap'] + self.param['inv_fix'] * self.var['scalar'][
            'i']) / param['depreciation_period']

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class HeatRecovery(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['cap_q'][0] > 0:
            self.param['i_active'] = True

        self.param['h_in'] = CP.PropsSI('H', 'T', self.param['T_in'] + 273.15, 'P', self.param['pressure'],
                                        self.param['medium'])
        self.param['h_out'] = CP.PropsSI('H', 'T', self.param['T_out'] + 273.15, 'P', self.param['pressure'],
                                         self.param['medium'])

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['m'] = self.var['seq']['m']

        da.add_inv_param(system, self, param)

        # Constraints
        da.add_con_a_v(self)
        da.add_cap_lim(self, ['q'])

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t] == self.var['seq']['m'][s, t] * (
                self.param['h_out'] - self.param['h_in']) / 1e6

        namestr = 'm_q'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t] <= float(self.param['max_recovery'] * self.param['source'][s][t])

        namestr = 'max_q'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t] <= self.var['scalar']['cap']

        namestr = 'max_cap'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objectives
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class Storage(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['cap_soc'][0] > 0:
            self.param['i_active'] = True
        # if self.param['eta_c/d'][0] < 1 or self.param['eta_c/d'][1] < 1:
        #     self.param['u_active'] = True

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['c'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['d'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        if self.param['u_active']:
            self.var['seq']['u'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.Binary)
        self.var['seq']['soc'] = pyo.Var(system.model.set_sc, system.model.set_te, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)



        da.add_var_to_model(system, self)

        # Ports
        self.port['c'] = self.var['seq']['c']
        self.port['d'] = self.var['seq']['d']
        self.port['soc'] = self.var['seq']['soc']

        da.add_inv_param(system, self, param)

        # Constraints
        da.add_op_lim(system, self, ['soc'])
        da.add_cap_lim(self, ['soc'])
        da.add_es_balance(system, self, ['c', 'd', 'soc'])
        da.add_con_a_v(self)

        def con_rule(m, s, t):
            if self.param['u_active']:
                return self.var['seq']['c'][s, t] <= self.param['lim_c/d'][0] * self.var['seq']['u'][s, t]
            else:
                return self.var['seq']['c'][s, t] <= self.param['lim_c/d'][0]

        namestr = 'con_' + self.name + '_c_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # max discharging power
        def con_rule(m, s, t):
            if self.param['u_active']:
                return self.var['seq']['d'][s, t] <= self.param['lim_c/d'][1] * (1 - self.var['seq']['u'][s, t])
            else:
                return self.var['seq']['d'][s, t] <= self.param['lim_c/d'][1]

        namestr = 'con_' + self.name + '_d_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # Objectives
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class PeriodStorage(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        self.param['set_n_period'] = range(len(self.param['set_period']))

        if self.param['cap_soc'][0] > 0:
            self.param['i_active'] = True
        if self.param['eta_c/d'][0] < 1 or self.param['eta_c/d'][1] < 1:
            self.param['u_active'] = True

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['c'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['d'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        if self.param['u_active']:
            self.var['seq']['u'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.Binary)
        self.var['seq']['soc'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['soc_p'] = pyo.Var(self.param['set_n_period'], domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['c'] = self.var['seq']['c']
        self.port['d'] = self.var['seq']['d']
        self.port['soc'] = self.var['seq']['soc']

        da.add_inv_param(system, self, param)

        # Constraints
        da.add_cap_lim(self, ['soc'])
        da.add_con_a_v(self)

        # Intraperiod energy balance
        def con_rule(m, s, t):
            return (self.var['seq']['soc'][s, t + 1] - self.var['seq']['soc'][s, t]) == (
                       self.param['eta_c/d'][0] * self.var['seq']['c'][s, t] - 1 / self.param['eta_c/d'][1] *
                       self.var['seq']['d'][s, t]) * system.param['tss']
        namestr = 'con_' + self.name + '_es_balance_' + 'soc'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, list(system.model.set_t)[:-1], rule=con_rule))

        # max charging power
        def con_rule(m, s, t):
            if self.param['u_active']:
                return self.var['seq']['c'][s, t] <= self.param['lim_c/d'][0] * self.var['seq']['u'][s, t]
            else:
                return self.var['seq']['c'][s, t] <= self.param['lim_c/d'][0]
        namestr = 'con_' + self.name + '_c_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # max discharging power
        def con_rule(m, s, t):
            if self.param['u_active']:
                return self.var['seq']['d'][s, t] <= self.param['lim_c/d'][1] * (1 - self.var['seq']['u'][s, t])
            else:
                return self.var['seq']['d'][s, t] <= self.param['lim_c/d'][1]
        namestr = 'con_' + self.name + '_d_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # Period energy balance
        def con_rule(m, t_p):
            return (self.var['seq']['soc_p'][np.mod(t_p + 1, len(self.param['set_n_period']))] - (1 - system.param['tss'] * self.param['loss_soc'])**system.param['n_ts_sc'] * self.var['seq']['soc_p'][t_p]) <= sum(self.param['eta_c/d'][0] * self.var['seq']['c'][self.param['set_period'][t_p], t] - 1 / self.param['eta_c/d'][1] * self.var['seq']['d'][self.param['set_period'][t_p], t] for t in system.model.set_t) * system.param['tss']
        namestr = 'con_' + self.name + '_es_balance_' + 'soc_p'
        system.model.add_component(namestr, pyo.Constraint(self.param['set_n_period'], rule=con_rule))

        # op_lim
        def con_rule(m, t_p, t2):
            # return (1 - system.param['tss'] * self.param['loss_soc'])**(t2) * self.var['seq']['soc_p'][t_p] + sum((1 - system.param['tss'] * self.param['loss_soc'])**(t2) * (self.param['eta_c/d'][0] * self.var['seq']['c'][self.param['set_period'][t_p], t] - 1 / self.param['eta_c/d'][1] * self.var['seq']['d'][self.param['set_period'][t_p], t]) for t in range(t2)) * system.param['tss'] <= self.var['scalar']['cap']
            return (1 - system.param['tss'] * self.param['loss_soc'])**t2 * self.var['seq']['soc_p'][t_p] + sum((1 - system.param['tss'] * self.param['loss_soc'])**t * (self.param['eta_c/d'][0] * self.var['seq']['c'][self.param['set_period'][t_p], t] - 1 / self.param['eta_c/d'][1] * self.var['seq']['d'][self.param['set_period'][t_p], t]) for t in range(t2)) * system.param['tss'] <= self.var['scalar']['cap']
        namestr = 'con_' + self.name + '_' + 'soc_p_max'
        system.model.add_component(namestr, pyo.Constraint(self.param['set_n_period'], system.model.set_t, rule=con_rule))

        # op_lim1
        def con_rule(m, t_p, t2):
            # return (1 - system.param['tss'] * self.param['loss_soc'])**(t2) * self.var['seq']['soc_p'][t_p] + sum((1 - system.param['tss'] * self.param['loss_soc'])**(t2) * (self.param['eta_c/d'][0] * self.var['seq']['c'][self.param['set_period'][t_p], t] - 1 / self.param['eta_c/d'][1] * self.var['seq']['d'][self.param['set_period'][t_p], t]) for t in range(t2)) * system.param['tss'] <= self.var['scalar']['cap']
            return (1 - system.param['tss'] * self.param['loss_soc'])**t2 * self.var['seq']['soc_p'][t_p] + sum((1 - system.param['tss'] * self.param['loss_soc'])**t * (self.param['eta_c/d'][0] * self.var['seq']['c'][self.param['set_period'][t_p], t] - 1 / self.param['eta_c/d'][1] * self.var['seq']['d'][self.param['set_period'][t_p], t]) for t in range(t2)) * system.param['tss'] >= 0
        namestr = 'con_' + self.name + '_' + 'soc_p_max2'
        system.model.add_component(namestr, pyo.Constraint(self.param['set_n_period'], system.model.set_t, rule=con_rule))

        # op_lim2
        def con_rule(m, s, t):
            return self.var['seq']['soc'][s, t] <= self.var['scalar']['cap']
        namestr = 'con_' + self.name + '_' + 'soc_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # Objectives
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class PeriodStorageSimple(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        self.param['set_n_period'] = range(len(self.param['set_period']))

        if self.param['cap_soc'][0] > 0:
            self.param['i_active'] = True
        if self.param['eta_c/d'][0] < 1 or self.param['eta_c/d'][1] < 1:
            self.param['u_active'] = True

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['c'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['d'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        if self.param['u_active']:
            self.var['seq']['u'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.Binary)
        self.var['seq']['soc'] = pyo.Var(system.model.set_sc, system.model.set_te, domain=pyo.NonNegativeReals)
        self.var['seq']['ave soc'] = pyo.Var(system.model.set_sc, domain=pyo.NonNegativeReals)
        self.var['seq']['soc_max'] = pyo.Var(system.model.set_sc, domain=pyo.NonNegativeReals)
        self.var['seq']['delta_soc_p'] = pyo.Var(self.param['set_n_period'], domain=pyo.NonNegativeReals)
        self.var['seq']['soc_slack'] = pyo.Var(self.param['set_n_period'], domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['c'] = self.var['seq']['c']
        self.port['d'] = self.var['seq']['d']
        self.port['soc'] = self.var['seq']['soc']

        # param
        da.add_inv_param(system, self, param)


        # Constraints
        da.add_cap_lim(self, ['soc'])
        da.add_con_a_v(self)

        # Intraperiod energy balance
        def con_rule(m, s, t):
            return (self.var['seq']['soc'][s, t + 1] - self.var['seq']['soc'][s, t]) == (
                    self.param['eta_c/d'][0] * self.var['seq']['c'][s, t] - 1 / self.param['eta_c/d'][1] *
                    self.var['seq']['d'][s, t]) * system.param['tss']
        namestr = 'con_' + self.name + '_es_balance_' + 'soc'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # max charging power
        def con_rule(m, s, t):
            if self.param['u_active']:
                return self.var['seq']['c'][s, t] <= self.param['lim_c/d'][0] * self.var['seq']['u'][s, t]
            else:
                return self.var['seq']['c'][s, t] <= self.param['lim_c/d'][0]
        namestr = 'con_' + self.name + '_c_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # max discharging power
        def con_rule(m, s, t):
            if self.param['u_active']:
                return self.var['seq']['d'][s, t] <= self.param['lim_c/d'][1] * (1 - self.var['seq']['u'][s, t])
            else:
                return self.var['seq']['d'][s, t] <= self.param['lim_c/d'][1]
        namestr = 'con_' + self.name + '_d_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # ave soc calculations
        def con_rule(m, sc):
            ave_soc = sum([self.var['seq']['soc'][sc, t] for t in system.model.set_te])/system.model.set_te.__len__()
            return self.var['seq']['ave soc'][sc] == ave_soc
        namestr = 'con_' + self.name + '_es_balance_' + 'ave_soc'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, rule=con_rule))

        # Period energy balance
        def con_rule(m):
            losses = (self.var['seq']['ave soc'][self.param['set_period'][0]] + self.var['seq']['delta_soc_p'][0])*param['loss_soc']*system.model.set_te.__len__()
            return self.var['seq']['soc'][self.param['set_period'][0], list(system.model.set_te)[0]] + self.var['seq']['delta_soc_p'][0] == self.var['seq']['soc'][self.param['set_period'][-1], list(system.model.set_te)[-1]] + self.var['seq']['delta_soc_p'][self.param['set_n_period'][-1]] + losses
        namestr = 'con_' + self.name + '_es_balance_' + 'soc_p'
        system.model.add_component(namestr, pyo.Constraint(rule=con_rule))

        def con_rule(m, t_p):
            losses = (self.var['seq']['ave soc'][self.param['set_period'][t_p]] + self.var['seq']['delta_soc_p'][t_p])*param['loss_soc']*system.model.set_te.__len__()
            return self.var['seq']['soc'][self.param['set_period'][t_p], list(system.model.set_te)[-1]] + self.var['seq']['delta_soc_p'][t_p] == self.var['seq']['soc'][self.param['set_period'][t_p+1], list(system.model.set_te)[0]] + self.var['seq']['delta_soc_p'][t_p+1] + self.var['seq']['soc_slack'][t_p+1] + losses
        namestr = 'con_' + self.name + '_es_balance_2_' + 'soc_p'
        system.model.add_component(namestr, pyo.Constraint(self.param['set_n_period'][:-1], rule=con_rule))

        def con_rule(m):
            return sum(self.var['seq']['c'][self.param['set_period'][t_p], t] for t_p in range(self.param['set_period'].__len__()) for t in system.model.set_t) >= sum(self.var['seq']['d'][self.param['set_period'][t_p], t] for t_p in range(self.param['set_period'].__len__()) for t in system.model.set_t)
        namestr = 'con_' + self.name + '_es_balance_3_' + 'soc_p'
        system.model.add_component(namestr, pyo.Constraint(rule=con_rule))


    # maximal soc for each period
        def con_rule(m, s, t):
            return self.var['seq']['soc'][s, t] <= self.var['seq']['soc_max'][s]
        namestr = 'con_' + self.name + '_' + 'soc_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # maximal soc for each period
        def con_rule(m, t_p):
            return self.var['seq']['soc_max'][self.param['set_period'][t_p]] + self.var['seq']['delta_soc_p'][t_p] <= self.var['scalar']['cap']
        namestr = 'con_' + self.name + '_' + 'cap'
        system.model.add_component(namestr, pyo.Constraint(self.param['set_n_period'], rule=con_rule))

        # Objectives
        da.add_obj_inv(system, self)
        # self.obj['inv'] = (self.param['inv_var'] * self.var['scalar']['cap'] + self.param['inv_fix'] * self.var['scalar'][
        #     'i']) / param['depreciation_period']

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['inv']
        obj += (pyo.summation(self.var['seq']['d']) + pyo.summation(self.var['seq']['c'])) * 1e-5
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class PeriodStorageSimple_CETES(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        self.param['set_n_period'] = range(len(self.param['set_period']))

        if self.param['cap_soc'][0] > 0:
            self.param['i_active'] = True
        if self.param['eta_c/d'][0] < 1 or self.param['eta_c/d'][1] < 1:
            self.param['u_active'] = True

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['c'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['d'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        if self.param['u_active']:
            self.var['seq']['u'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.Binary)
        self.var['seq']['soc'] = pyo.Var(system.model.set_sc, system.model.set_te, domain=pyo.NonNegativeReals)
        self.var['seq']['ave soc'] = pyo.Var(system.model.set_sc, domain=pyo.NonNegativeReals)
        self.var['seq']['soc_max'] = pyo.Var(system.model.set_sc, domain=pyo.NonNegativeReals)
        self.var['seq']['delta_soc_p'] = pyo.Var(self.param['set_n_period'], domain=pyo.NonNegativeReals)
        self.var['seq']['soc_slack'] = pyo.Var(self.param['set_n_period'], domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)

        self.var['scalar']['c_max'] = pyo.Var(domain=pyo.NonNegativeReals)
        self.var['scalar']['d_max'] = pyo.Var(domain=pyo.NonNegativeReals)
        self.var['scalar']['c_d_max'] = pyo.Var(bounds=(0, param['cap_soc'][1]*max(param['lim_c/d'])))

        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['c'] = self.var['seq']['c']
        self.port['d'] = self.var['seq']['d']
        self.port['soc'] = self.var['seq']['soc']

        # param
        da.add_inv_param(system, self, param, type='CETES')


        # Constraints
        da.add_cap_lim(self, ['soc'])
        da.add_con_a_v(self)

        # Intraperiod energy balance
        def con_rule(m, s, t):
            return (self.var['seq']['soc'][s, t + 1] - self.var['seq']['soc'][s, t]) == (
                    self.param['eta_c/d'][0] * self.var['seq']['c'][s, t] - 1 / self.param['eta_c/d'][1] *
                    self.var['seq']['d'][s, t]) * system.param['tss']
        namestr = 'con_' + self.name + '_es_balance_' + 'soc'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # max charging power
        def con_rule(m, s, t):
            return self.var['seq']['c'][s, t] - self.var['seq']['d'][s, t] <= self.param['lim_c/d'][0] * self.var['scalar']['cap']
        namestr = 'con_' + self.name + '_c_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        def con_rule(m, s, t):
            return self.var['scalar']['c_max'] >= self.var['seq']['c'][s, t] - self.var['seq']['d'][s, t]
        namestr = 'con_' + self.name + '_c_max_2'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))


        # max discharging power
        def con_rule(m, s, t):
            return self.var['seq']['d'][s, t] - self.var['seq']['c'][s, t] <= self.param['lim_c/d'][1] * self.var['scalar']['cap']
        namestr = 'con_' + self.name + '_d_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        def con_rule(m, s, t):
            return self.var['scalar']['d_max'] >= self.var['seq']['d'][s, t] - self.var['seq']['c'][s, t]
        namestr = 'con_' + self.name + '_d_max_2'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # max overall power
        def con_rule(m):
            return self.var['scalar']['d_max'] <= self.var['scalar']['c_d_max']
        namestr = 'con_' + self.name + '_c_d_max'
        system.model.add_component(namestr, pyo.Constraint(rule=con_rule))

        def con_rule(m):
            return self.var['scalar']['c_max'] <= self.var['scalar']['c_d_max']
        namestr = 'con_' + self.name + '_c_d_max_2'
        system.model.add_component(namestr, pyo.Constraint(rule=con_rule))


    # ave soc calculations
        def con_rule(m, sc):
            ave_soc = sum([self.var['seq']['soc'][sc, t] for t in system.model.set_te])/system.model.set_te.__len__()
            return self.var['seq']['ave soc'][sc] == ave_soc
        namestr = 'con_' + self.name + '_es_balance_' + 'ave_soc'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, rule=con_rule))

        # Period energy balance
        def con_rule(m):
            losses = (self.var['seq']['ave soc'][self.param['set_period'][0]] + self.var['seq']['delta_soc_p'][0])*param['loss_soc']*system.model.set_te.__len__()
            return self.var['seq']['soc'][self.param['set_period'][0], list(system.model.set_te)[0]] + self.var['seq']['delta_soc_p'][0] == self.var['seq']['soc'][self.param['set_period'][-1], list(system.model.set_te)[-1]] + self.var['seq']['delta_soc_p'][self.param['set_n_period'][-1]] + losses
        namestr = 'con_' + self.name + '_es_balance_' + 'soc_p'
        system.model.add_component(namestr, pyo.Constraint(rule=con_rule))

        def con_rule(m, t_p):
            losses = (self.var['seq']['ave soc'][self.param['set_period'][t_p]] + self.var['seq']['delta_soc_p'][t_p])*param['loss_soc']*system.model.set_te.__len__()
            return self.var['seq']['soc'][self.param['set_period'][t_p], list(system.model.set_te)[-1]] + self.var['seq']['delta_soc_p'][t_p] == self.var['seq']['soc'][self.param['set_period'][t_p+1], list(system.model.set_te)[0]] + self.var['seq']['delta_soc_p'][t_p+1] + self.var['seq']['soc_slack'][t_p+1] + losses
        namestr = 'con_' + self.name + '_es_balance_2_' + 'soc_p'
        system.model.add_component(namestr, pyo.Constraint(self.param['set_n_period'][:-1], rule=con_rule))

        def con_rule(m):
            return sum(self.var['seq']['c'][self.param['set_period'][t_p], t] for t_p in range(self.param['set_period'].__len__()) for t in system.model.set_t) >= sum(self.var['seq']['d'][self.param['set_period'][t_p], t] for t_p in range(self.param['set_period'].__len__()) for t in system.model.set_t)
        namestr = 'con_' + self.name + '_es_balance_3_' + 'soc_p'
        system.model.add_component(namestr, pyo.Constraint(rule=con_rule))


        # maximal soc for each period
        def con_rule(m, s, t):
            return self.var['seq']['soc'][s, t] <= self.var['seq']['soc_max'][s]
        namestr = 'con_' + self.name + '_' + 'soc_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # maximal soc for each period
        def con_rule(m, t_p):
            return self.var['seq']['soc_max'][self.param['set_period'][t_p]] + self.var['seq']['delta_soc_p'][t_p] <= self.var['scalar']['cap']
        namestr = 'con_' + self.name + '_' + 'cap'
        system.model.add_component(namestr, pyo.Constraint(self.param['set_n_period'], rule=con_rule))

        # Objectives
        # da.add_obj_inv(system, self)
        self.obj['inv'] = (self.param['inv_var_cap'] * self.var['scalar']['cap'] + self.param['inv_var_load'] * self.var['scalar']['c_d_max'] + self.param['inv_fix'] * self.var['scalar'][
            'i']) / param['depreciation_period']

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['inv']
        obj += (pyo.summation(self.var['seq']['d']) + pyo.summation(self.var['seq']['c'])) * 1e-5
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class StratifiedMultiLayer(Unit):
    # Multi layer stratified storage
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['cap_soc'][0] > 0:
            self.param['i_active'] = True

        self.param['H'] = dict()
        for i in self.param['T']:
            self.param['H'][i] = CP.PropsSI('H', 'T', i + 273.15, 'P', self.param['pressure'], self.param['medium'])

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['m_c'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['T'],
                                         domain=pyo.NonNegativeReals)
        self.var['seq']['m_d'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['T'],
                                         domain=pyo.NonNegativeReals)
        self.var['seq']['soc'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['T'],
                                         domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)
        da.add_var_a_v(self)

        da.add_var_to_model(system, self)

        # Ports
        for n in self.param['T']:
            self.port['m_c_' + str(n)] = pyo.Reference(self.var['seq']['m_c'][:, :, n])
            self.port['m_d_' + str(n)] = pyo.Reference(self.var['seq']['m_d'][:, :, n])
            self.port['soc_' + str(n)] = pyo.Reference(self.var['seq']['soc'][:, :, n])

        da.add_inv_param(system, self, param)

        # Constraints
        da.add_cap_lim(self, ['soc'])
        da.add_con_a_v(self)

        # Energy balance
        def con_rule(m, s, t, n):
            return (self.var['seq']['soc'][s, np.mod(t + 1, len(system.model.set_t)), n] - self.var['seq']['soc'][
                s, t, n]) == (
                       self.var['seq']['m_c'][s, t, n] - self.var['seq']['m_d'][s, t, n]) * system.param['tss'] * 3600

        namestr = 'con_' + self.name + '_es_balance'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, self.param['T'],
                                                           rule=con_rule))

        # max charging power
        def con_rule(m, s, t, n):
            return self.var['seq']['m_c'][s, t, n] <= self.param['lim_c/d'][0]

        namestr = 'con_' + self.name + '_c_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, self.param['T'],
                                                           rule=con_rule))

        # max discharging power
        def con_rule(m, s, t, n):
            return self.var['seq']['m_c'][s, t, n] <= self.param['lim_c/d'][1]

        namestr = 'con_' + self.name + '_d_max'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, self.param['T'],
                                                           rule=con_rule))

        # total mass balance
        def con_rule(m, s, t):
            return sum(self.var['seq']['soc'][s, t, n] for n in self.param['T']) == self.var['scalar']['cap']

        namestr = 'con_' + self.name + '_total_mass_balance'
        system.model.add_component(namestr, pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule))

        # Objectives
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['inv']
        # obj += self.obj['opex_var'].expr
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class Demand(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters

        # Variables
        self.var['seq'] = dict()
        self.var['seq']['d'] = pyo.Var(system.model.set_sc,
                                       system.model.set_t)  # negative values are admissible, since demand may be negative too.

        da.add_var_to_model(system, self)

        # Ports
        self.port['d'] = self.var['seq']['d']

        if 'seq' in self.param.keys():
            # Constraints
            def con_rule(m, s, t):
                return self.var['seq']['d'][s, t] == self.param['seq'][s][t]

            namestr = '_fix_var'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objectives
        obj = 0
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class HeatDemand(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        self.param['h_in'] = dict()
        for n in self.param['T_in']:
            self.param['h_in'][n] = CP.PropsSI('H', 'T', n + 273.15, 'P', self.param['pressure'], self.param['medium'])
        self.param['h_out'] = dict()
        for n in self.param['T_out']:
            self.param['h_out'][n] = CP.PropsSI('H', 'T', n + 273.15, 'P', self.param['pressure'], self.param['medium'])

        # Variables
        self.var['seq'] = dict()
        self.var['seq']['m_in'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['T_in'],
                                          domain=pyo.NonNegativeReals)  # negative values are admissible, since demand may be negative too.
        self.var['seq']['m_out'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['T_out'],
                                           domain=pyo.NonNegativeReals)  # negative values are admissible, since demand may be negative too.
        self.var['seq']['q'] = pyo.Var(system.model.set_sc,
                                       system.model.set_t)  # negative values are admissible, since demand may be negative too.

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']

        for n in self.param['T_in']:
            if len(self.param['T_in']) == 1:
                namestr = 'm_in'
                namestr = 'm_in'
            else:
                namestr = 'm_in_' + str(n)
            self.port[namestr] = pyo.Reference(self.var['seq']['m_in'][:, :, n])

        for n in self.param['T_out']:
            if len(self.param['T_out']) == 1:
                namestr = 'm_out'
            else:
                namestr = 'm_out_' + str(n)
            self.port[namestr] = pyo.Reference(self.var['seq']['m_out'][:, :, n])

        # Constraints
        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t] == self.param['seq'][s][t]

        namestr = '_fix_var'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t] == (
                sum(self.var['seq']['m_in'][s, t, n] * self.param['h_in'][n] for n in self.param['T_in']) - sum(
                    self.var['seq']['m_out'][s, t, n] * self.param['h_out'][n] for n in self.param['T_out'])) / 1e6

        namestr = 'q(m_in,m_out)'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return sum(self.var['seq']['m_in'][s, t, n] for n in self.param['T_in']) == sum(
                self.var['seq']['m_out'][s, t, n] for n in self.param['T_out'])

        namestr = 'm_in_is_m_out'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        if 'm_out_dist' in self.param.keys():
            def con_rule(m, s, t, n):
                return self.param['m_out_dist'][s][n][t] * sum(
                    self.var['seq']['m_out'][s, t, k] for k in self.param['T_out']) == self.var['seq']['m_out'][s, t, n]

            namestr = 'm_out_dist'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, self.param['T_out'],
                                               rule=con_rule)

        # Objectives
        obj = 0
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class Supply(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        # todo: cap_s[0] hat aktuell keine Bedeutung, d.h. Mindestabnahmeleistung gibt es nicht
        if 'cap_s' not in self.param:
            self.param['cap_s'] = (0, np.inf)

        self.param['u_active'] = False
        self.param['v_w_active'] = False
        if 'cap_s' in self.param:
            if self.param['cap_s'][0] > 0:
                self.param['i_active'] = True
            else:
                self.param['i_active'] = False
        else:
            self.param['i_active'] = False

        da.add_energy_param(system, self, param)

        if 'flexbound' in self.param.keys():
            da.add_flexbound_param(system, self, param)

         # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['s'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)

        if 'cap_existing' in self.param.keys():
            self.var['scalar']['cap_expansion'] = pyo.Var(domain=pyo.NonNegativeReals)
            self.var['scalar']['dec_cap_expansion'] = pyo.Var(domain=pyo.Binary)

        if 'co2_biogen' in self.param.keys():
            self.var['seq']['m_co2_biogen'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)

        if 'co2_fossil' in self.param.keys():
            self.var['seq']['m_co2_fossil'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)

        da.add_var_to_model(system, self)

        # Ports
        self.port['s'] = self.var['seq']['s']

        if 'co2_fossil' in self.param.keys():
            self.port['m_co2_fossil'] = self.var['seq']['m_co2_fossil']

        if 'co2_biogen' in self.param.keys():
            self.port['m_co2_biogen'] = self.var['seq']['m_co2_biogen']

        # Constraints
        da.add_op_lim(system, self, ['s'])
        da.add_cap_lim(self, ['s'])                 #

        if 'flexbound' in self.param.keys():
            #da.add_flexbound_param(system, self, param)
            def con_rule(m, s, t):
                return self.var['seq']['s'][s, t] <= self.param['flexbound'][s, t] * self.var['scalar']['cap']

            namestr = '_flexbound_UB'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

            def con_rule(m, s, t):
                return self.var['seq']['s'][s, t] >= 0.99 * self.param['flexbound'][s, t] * self.var['scalar']['cap']

            namestr = '_flexbound_LB'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        if 'cap_existing' in self.param.keys():
            def con_rule(m):
                return self.var['scalar']['cap_expansion'] >= self.var['scalar']['cap'] - self.param['cap_existing']

            namestr = '_cap_expansion'
            self.con[namestr] = pyo.Constraint(rule=con_rule)

        if 'cap_existing' in self.param.keys():
            def con_rule(m):
                return self.var['scalar']['cap_expansion'] <= self.var['scalar']['dec_cap_expansion'] * 1000

            namestr = '_dec_expansion'
            self.con[namestr] = pyo.Constraint(rule=con_rule)

        if 'co2_biogen' in self.param.keys():
            def con_rule(m, s, t):
                return self.var['seq']['m_co2_biogen'][s, t] == self.param['co2_biogen'] * self.var['seq']['s'][s, t]

            namestr = '_calc_co2_biogen'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        if 'co2_fossil' in self.param.keys():
            def con_rule(m, s, t):
                return self.var['seq']['m_co2_fossil'][s, t] == self.param['co2_fossil'] * self.var['seq']['s'][s, t]

            namestr = '_calc_co2_fossil'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


        # Objectives
        obj = sum(
            self.var['seq']['s'][s, t] * self.param['seq'][s, t] * system.param['sc'][s][0] for s in system.model.set_sc
            for t in system.model.set_t) / system.param['dur_sc'] * 8760
        namestr = 'obj_' + self.name + '_energy'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['energy'] = system.model.component(namestr)

        # add costs for additional features, max power investment co2 factors
        if 'cap_existing' in self.param.keys():
            obj = (self.var['scalar']['dec_cap_expansion'] * self.param['cost_fix_ex'] +
                   self.var['scalar']['cap_expansion'] * self.param['cost_max_ex']) / system.param['depreciation_period']
            namestr = 'obj_' + self.name + '_inv'
            system.model.add_component(namestr, pyo.Objective(expr=obj))
            system.model.component(namestr).deactivate()
            self.obj['inv'] = system.model.component(namestr)

        if 'co2_biogen' in self.param.keys():
            obj = sum(
                self.var['seq']['m_co2_biogen'][s, t] * system.param['sc'][s][0] for s in system.model.set_sc
                for t in system.model.set_t) * system.param['cost_co2_biogen'] / system.param['dur_sc'] * 8760
            namestr = 'obj_' + self.name + '_co2_biogen'
            system.model.add_component(namestr, pyo.Objective(expr=obj))
            system.model.component(namestr).deactivate()
            self.obj['co2_biogen'] = system.model.component(namestr)

            obj_mass = sum(
                self.var['seq']['m_co2_biogen'][s, t] * system.param['sc'][s][0] for s in system.model.set_sc
                for t in system.model.set_t) / system.param['dur_sc'] * 8760
            namestr = 'obj_mass_' + self.name + '_co2_biogen'
            system.model.add_component(namestr, pyo.Objective(expr=obj_mass))
            system.model.component(namestr).deactivate()
            self.obj['mass_biogen'] = system.model.component(namestr)

        if 'co2_fossil' in self.param.keys():
            obj = sum(
                self.var['seq']['m_co2_fossil'][s, t] * system.param['sc'][s][0] for s in system.model.set_sc
                for t in system.model.set_t) * system.param['cost_co2_fossil'] / system.param['dur_sc'] * 8760
            namestr = 'obj_' + self.name + '_co2_fossil'
            system.model.add_component(namestr, pyo.Objective(expr=obj))
            system.model.component(namestr).deactivate()
            self.obj['co2_fossil'] = system.model.component(namestr)

            obj_mass =sum(
                self.var['seq']['m_co2_fossil'][s, t] * system.param['sc'][s][0] for s in system.model.set_sc
                for t in system.model.set_t) / system.param['dur_sc'] * 8760
            namestr = 'obj_mass_' + self.name + '_co2_fossil'
            system.model.add_component(namestr, pyo.Objective(expr=obj_mass))
            system.model.component(namestr).deactivate()
            self.obj['mass_fossil'] = system.model.component(namestr)

        # add costs for peak load (annual costs)

        if 'cost_max_load' in self.param:
            obj = self.var['scalar']['cap'] * self.param['cost_max_load']
            namestr = 'obj_' + self.name + '_max_s'
            system.model.add_component(namestr, pyo.Objective(expr=obj))
            system.model.component(namestr).deactivate()
            self.obj['max_s'] = system.model.component(namestr)

        obj = 0
        obj += self.obj['energy'].expr
        if 'cost_max_load' in self.param:
            obj += self.obj['max_s'].expr
        if 'cap_existing' in self.param:
            obj += self.obj['inv'].expr
        if 'co2_biogen' in self.param:
            obj += self.obj['co2_biogen'].expr
        if 'co2_fossil' in self.param:
            obj += self.obj['co2_fossil'].expr

        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

        obj_co2 = 0
        if 'co2_biogen' in self.param:
            obj_co2 += self.obj['mass_biogen'].expr

        namestr = 'obj_co2' + self.name + '_co2_total_bio'
        system.model.add_component(namestr, pyo.Objective(expr=obj_co2))
        system.model.component(namestr).deactivate()
        self.obj['co2_total_bio'] = system.model.component(namestr)

        obj_co2 = 0
        if 'co2_fossil' in self.param:
            obj_co2 += self.obj['mass_fossil'].expr

        namestr = 'obj_co2' + self.name + '_co2_total_fossil'
        system.model.add_component(namestr, pyo.Objective(expr=obj_co2))
        system.model.component(namestr).deactivate()
        self.obj['co2_total_fossil'] = system.model.component(namestr)

    def get_supply(self, system):
        return sum(
            pyo.value(self.var['seq']['s'][s, t]) * system.param['sc'][s][0] for s in system.model.set_sc
            for t in system.model.set_t) / system.param['dur_sc'] * 8760

class DistrictHeating(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        self.param['h_in'] = CP.PropsSI('H', 'T', self.param['T_in'] + 273.15, 'P', self.param['pressure'],
                                        self.param['medium'])
        self.param['h_out'] = CP.PropsSI('H', 'T', self.param['T_out'] + 273.15, 'P', self.param['pressure'],
                                         self.param['medium'])

        if 'cap_q' not in self.param:
            self.param['cap_q'] = (0, np.inf)
        self.param['u_active'] = False
        self.param['v_w_active'] = False
        if 'cap_q' in self.param:
            if self.param['cap_q'][0] > 0:
                self.param['i_active'] = True
            else:
                self.param['i_active'] = False
        else:
            self.param['i_active'] = False

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']

        def expr_rule(m, s, t):
            return self.var['seq']['q'][s, t] / ((self.param['h_out'] - self.param['h_in']) / 1e6)

        namestr = 'port_' + self.name + '_m'
        system.model.add_component(namestr, pyo.Expression(system.model.set_sc, system.model.set_t, rule=expr_rule))
        self.port['m'] = system.model.component(namestr)

        # Constraints
        da.add_op_lim(system, self, ['q'])
        da.add_cap_lim(self, ['q'])

        # Objectives
        obj = sum(
            self.var['seq']['q'][s, t] * self.param['seq'][s][t] * system.param['sc'][s][0] for s in system.model.set_sc
            for t in system.model.set_t) / system.param['dur_sc'] * 8760
        namestr = 'obj_' + self.name + '_energy'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['energy'] = system.model.component(namestr)

        if 'cost_max_q' in self.param:
            obj = self.var['scalar']['cap'] * self.param['cost_max_q']
            namestr = 'obj_' + self.name + '_max_q'
            system.model.add_component(namestr, pyo.Objective(expr=obj))
            system.model.component(namestr).deactivate()
            self.obj['max_q'] = system.model.component(namestr)

        obj = 0
        obj += self.obj['energy'].expr
        if 'cost_max_q' in self.param:
            obj += self.obj['max_q'].expr
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class GeothermalPlant(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        # correct?
        if self.param['d_boundaries'][0] > 0:
            self.param['i_active'] = True

        self.param['c_p'] = CP.PropsSI('C', 'T', param['T_amb'] + 273.15,
                                       'P', 101325, 'Water')                           # J/kg.K

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        #self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        self.var['scalar']['d'] = pyo.Var(domain=pyo.NonNegativeReals)
        self.var['scalar']['T_extraction'] = pyo.Var(domain=pyo.NonNegativeReals)
        self.var['scalar']['T_reinjection'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        # self.port['p'] = self.var['seq']['p']    # p-q relation needs to be added

        da.add_inv_param(system, self, param)

        # Constraints

        # Extraction temperature
        def con_rule(m, s, t):
            return (self.var['scalar']['T_extraction'] == (
                    self.param['T_amb'] + self.param['gradT'] * self.var['scalar']['d']) )
        namestr = 'T_extraction'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Re-inection temperature
        def con_rule(m, s, t):
            return self.var['scalar']['T_reinjection'] == self.param['T_reinjection']
        namestr = 'T_reinjection'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # linear m relation between m, d and q
        def con_rule(m, s, t):
            return (self.var['seq']['q'][s, t] == self.param['m'] * self.param['c_p'] * (
                    self.var['scalar']['T_extraction'] - self.var['scalar']['T_reinjection']) / 1e6)
        namestr = 'm_q'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        min_q = self.param['m'] * self.param['c_p'] * (
                self.param['T_amb'] + self.param['gradT'] * self.param['d_boundaries'][0]
                - self.param['T_reinjection']) / 1e6
        max_q = self.param['m'] * self.param['c_p'] * (
                self.param['T_amb'] + self.param['gradT'] * self.param['d_boundaries'][1]
                - self.param['T_reinjection']) / 1e6
        self.param['cap_q'] = [min_q, max_q]           # q values depending on min and max drilling depth

        da.add_cap_lim(self, ['q'])         # self.var['seq']['q'] < self.var['scalar']['cap']
        da.add_op_lim(system, self, ['q'])  # param['cap_q'][0] < var['scalar']['cap'] < param['cap_q'][1]

        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here

        # Objectives
        da.add_obj_u_v_w(system, self)
        da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['opex_fix'].expr
        obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class CascadicHeatExchanger(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)
        # no objective, only used for functionality
        # Parameters
        # --- none

        # Variables
        self.var['scalar'] = dict()
        self.var['scalar']['T_supply_high'] =pyo.Var(domain=pyo.NonNegativeReals)
        self.var['scalar']['T_supply_low'] = pyo.Var(domain=pyo.NonNegativeReals)
        self.var['seq'] = dict()
        self.var['seq']['q'] = pyo.Var(
            system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']

        # Constraints
        # Extraction temperature
        def con_rule(m, s, t):
            return (self.var['seq']['q'][s, t] == self.param['m'] * self.param['c_p'] * (
                    self.var['scalar']['T_supply_high'] - self.var['scalar']['T_supply_low'] ) / 1e6)
        namestr = 'mcp_q'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        obj = 0
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class Coupler(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters

        # Variables
        self.var['seq'] = dict()
        self.var['seq']['in'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['in'],
                                        domain=pyo.NonNegativeReals)
        self.var['seq']['out'] = pyo.Var(system.model.set_sc, system.model.set_t, self.param['out'],
                                         domain=pyo.NonNegativeReals)

        da.add_var_to_model(system, self)

        # Ports
        for n in self.param['in']:
            self.port['in_' + str(n)] = pyo.Reference(self.var['seq']['in'][:, :, n])
        for n in self.param['out']:
            self.port['out_' + str(n)] = pyo.Reference(self.var['seq']['out'][:, :, n])

        # Constraints
        def con_rule(m, s, t):
            return sum(self.var['seq']['in'][s, t, :]) == sum(self.var['seq']['out'][s, t, :])

        namestr = '_balance'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        obj = 0
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class Node(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)
        # Parameters

        # Variables
        self.var['seq'] = dict()
        self.var['seq']['slack_lhs'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['slack_rhs'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)

        da.add_var_to_model(system, self)

        # Ports

        # Constraints
        def con_rule(m, s, t):
            lhs = self.var['seq']['slack_lhs'][s, t]
            rhs = self.var['seq']['slack_rhs'][s, t]
            for n in self.param['lhs']:
                if len(n) < 3:
                    n.append(1)
                lhs += system.unit[n[0]].port[n[1]][s, t] * n[2]
            for n in self.param['rhs']:
                if len(n) < 3:
                    n.append(1)
                rhs += system.unit[n[0]].port[n[1]][s, t] * n[2]
            if self.param['type'] == '==':
                return lhs == rhs
            elif self.param['type'] == '>=':
                return lhs >= rhs
            elif self.param['type'] == '>':
                return lhs > rhs
            elif self.param['type'] == '<=':
                return lhs <= rhs
            elif self.param['type'] == '<':
                return lhs < rhs

        namestr = '_node'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objectives
        big_m = 1e8
        obj = big_m * sum(self.var['seq'][n][s, t] for n in ['slack_lhs', 'slack_rhs'] for s in system.model.set_sc
                          for t in system.model.set_t)
        namestr = 'obj_' + self.name + '_slack'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['slack'] = system.model.component(namestr)

        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['slack'].expr
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class GridService(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        power_price = param['power_price']
        energy_price = param['energy_price']

        max_power_limit = param['max power']
        energy_limit = param['max energy']

        gs_timesteps = param['gs_timesteps']
        gs_duration = param['gs_duration']

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()

        self.var['seq']['p_pos'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p_neg'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p_res'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p_res_pos'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p_res_neg'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p_res_min'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)

        self.var['seq']['gs_active'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.Binary)

        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)

        da.add_var_to_model(system, self)

        # Ports
        self.port['p_pos'] = self.var['seq']['p_pos']
        self.port['p_neg'] = self.var['seq']['p_neg']
        self.port['p_res_pos'] = self.var['seq']['p_res_pos']
        self.port['p_res_neg'] = self.var['seq']['p_res_neg']

        # Constraints
        def con_fun(model, s, t):
            if (t % gs_duration == 0):
                return pyo.Constraint.Skip
            else:
                return self.var['seq']['gs_active'][s, t-1] == self.var['seq']['gs_active'][s, t]
        namestr = 'gs_activity_1'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_fun)

        def con_fun(model, s, t):
            if (t % gs_duration == 0):
                return pyo.Constraint.Skip
            else:
                return self.var['seq']['p_res'][s, t-1] == self.var['seq']['p_res'][s, t]
        namestr = 'gs_activity_2'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_fun)


        if param['type'] in ['PRL', 'SRL pos']:
            def con_fun(model, s, t):
                return self.var['seq']['p_res_pos'][s, t] + self.var['seq']['p_pos'][s, t] >= self.var['seq']['p_res'][s, t]
            namestr = 'p_res_1'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_fun)

            def con_fun(model, s, t):
                return self.var['seq']['p_res'][s, t] <= param['max power']*self.var['seq']['gs_active'][s, t]
            namestr = 'p_res_2'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_fun)

            def con_fun(model, s, t):
                return self.var['seq']['p_pos'][s, t] == self.var['seq']['p_res'][s, t] * param['realized positive'][s][t]
            namestr = 'p_res_9'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_fun)



        if param['type'] in ['PRL', 'SRL neg']:
            def con_fun(model, s, t):
                return self.var['seq']['p_res_neg'][s, t] + self.var['seq']['p_neg'][s, t] >= self.var['seq']['p_res'][s, t]
            namestr = 'p_res_3'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_fun)

            def con_fun(model, s, t):
                return self.var['seq']['p_res'][s, t] <= param['max power']*self.var['seq']['gs_active'][s, t]
            namestr = 'p_res_4'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_fun)

            def con_fun(model, s, t):
                return self.var['seq']['p_neg'][s, t] == self.var['seq']['p_res'][s, t] * param['realized negative'][s][t]
            namestr = 'p_res_10'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_fun)


        if param['type'] in ['SRL pos']:
            def con_fun(model, s, t):
                return self.var['seq']['p_neg'][s, t] <= 0
            namestr = 'p_res_5'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_fun)

        if param['type'] in ['SRL neg']:
            def con_fun(model, s, t):
                return self.var['seq']['p_pos'][s, t] <= 0
            namestr = 'p_res_6'
            self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_fun)


        def con_fun(model, s, t):
            return self.var['seq']['p_res'][s, t] >= param['min power']*self.var['seq']['gs_active'][s, t]
        namestr = 'p_res_8'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_fun)







        # ==============================================================================================================
        # Linear cost function
        power_costs = 0
        energy_spec_costs = 0
        try:
            power_costs = sum(power_price[s][t] * self.var['seq']['p_res'][s, t] for s in system.model.set_sc for t in system.model.set_t) * system.param['tss'] / gs_duration
        except:
            print('power price is scalar')
            power_costs = sum(power_price * self.var['seq']['p_res'][s, t] for s in system.model.set_sc for t in system.model.set_t) * system.param['tss'] / gs_duration

        if param['type'] in ['SRL neg', 'SRL pos']:
            try:
                energy_spec_costs = sum(energy_price[s][t] * self.var['seq']['p_pos'][s, t] for s in system.model.set_sc for t in system.model.set_t) * system.param['tss'] \
                                    + sum(energy_price[s][t] * self.var['seq']['p_neg'][s, t] for s in system.model.set_sc for t in system.model.set_t) * system.param['tss']
            except:
                print('energy price is scalar')
                energy_spec_costs = sum(energy_price * self.var['seq']['p_pos'][s, t] for s in system.model.set_sc for t in system.model.set_t) * system.param['tss'] \
                                    + sum(energy_price * self.var['seq']['p_neg'][s, t] for s in system.model.set_sc for t in system.model.set_t) * system.param['tss']

        energy_costs = power_costs + energy_spec_costs



        # energy_costs = energy_costs * 365*24 / ((model.set_timesteps[-1]+1)*settings['stepsize'])

        #work_costs = np.multiply(energy_price, power)
        #energy_costs = (power_price*max_power) + (summation(work_costs) * settings['stepsize'])

        self.energy_costs = energy_costs

        obj = self.energy_costs
        namestr = 'obj_' + self.name + '_energy'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['energy'] = system.model.component(namestr)

#-----------------------#
### ADDITIONS FOR UPM ###
#-----------------------#

class PaperMachine(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['lim_q'][0] > 0:
            self.param['u_active'] = True

        if self.param['cap_q'][0] > 0:
            self.param['i_active'] = True

        if 'max_susd' not in self.param:
            if self.param['v_w_active']:
                self.param['max_susd'] = (self.param['lim_q'][0], self.param['lim_q'][0])
            else:
                self.param['max_susd'] = (1, 1)

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['e'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['s'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['g'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['d'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['e'] = self.var['seq']['e']
        self.port['s'] = self.var['seq']['s']
        self.port['g'] = self.var['seq']['g']
        self.port['p'] = self.var['seq']['p']
        self.port['d'] = self.var['seq']['d']
        self.port['u'] = self.var['seq']['u']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q'])
        da.add_cap_lim(self, ['q'])
        #da.add_ramp_con(system, self, ['q'])

        # def con_rule(m, s, t):
        #     return self.var['seq']['q'][s, t] <= self.var['scalar']['cap']*param['lim_q'][1]
        # namestr = 'upperbound'
        # self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)
        #
        # def con_rule(m, s, t):
        #     return self.var['seq']['q'][s, t] >= self.var['scalar']['cap']*param['lim_q'][0]
        # namestr = 'lowerbound'
        # self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t] * param['spec_el'] / system.param['tss'] == self.var['seq']['e'][s, t]
        namestr = 'electric_power_demand_paper'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t]*param['spec_steam'] / system.param['tss'] == self.var['seq']['s'][s, t]
        namestr = 'steam_power_demand_paper'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t]*param['spec_gw'] == self.var['seq']['g'][s, t]
        namestr = 'gw_demand_paper'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t]*param['spec_pgw'] == self.var['seq']['p'][s, t]
        namestr = 'pgw_demand_paper'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t]*param['spec_dip'] == self.var['seq']['d'][s, t]
        namestr = 'dip_demand_paper'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        #da.add_obj_u_v_w(system, self)
        #da.add_obj_inv(system, self)

        ## fixme define costs constraints, etc.!

        # Total objective, which is assigned directly to unit
        obj = 0
        #obj += self.obj['opex_fix'].expr
        #obj += self.obj['cost_SU'].expr
        #obj += self.obj['cost_SD'].expr
        #obj += self.obj['inv']
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class GroundWood(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['t'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeIntegers, bounds=(0, param['lim_grinders'])) #number of active units
        self.var['seq']['c'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)            # production above min output of operating units
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['w'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['e'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)

        da.add_var_to_model(system, self)

        # Ports
        self.port['t'] = self.var['seq']['t']
        self.port['c'] = self.var['seq']['c']
        self.port['m'] = self.var['seq']['m']
        self.port['w'] = self.var['seq']['w']
        self.port['e'] = self.var['seq']['e']

        # Constraints
        def con_rule(m, s, t):
            return self.var['seq']['w'][s, t] * param['eta'] == self.var['seq']['m'][s, t]
        namestr = 'production_gw_from_wood'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['c'][s, t] <= self.var['seq']['t'][s,t]*(param['lim_gw'][1]-param['lim_gw'][0])
        namestr = 'production_point_gw'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


        def con_rule(m, s, t):
            return (self.var['seq']['c'][s, t] + self.var['seq']['t'][s, t] * param['lim_gw'][0]) * param['spec_el'] == self.var['seq']['e'][s, t]
        namestr = 'elec_power_demand_gw'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return (self.var['seq']['c'][s, t] + self.var['seq']['t'][s, t] * param['lim_gw'][0]) * param['max_prod'] == self.var['seq']['m'][s, t]

        namestr = 'production_mass_gw'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)


        # Objective
        # da.add_obj_u_v_w(system, self)
        # da.add_obj_inv(system, self)


        # Total objective, which is assigned directly to unit
        # here probably none (9.8.2022)

class PressurizedGroundWood(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['t'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeIntegers, bounds=(0, self.param['lim_grinders']))
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['w'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['e'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)

        if self.param['type_gc3'] == 0:
            self.var['seq']['a'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals, bounds=(0, 0))
            self.var['seq']['e_a'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals, bounds=(0, 0))
        else:
            self.var['seq']['a'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeIntegers, bounds=(0, 4))
            self.var['seq']['e_a'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)


        da.add_var_to_model(system, self)

        # Ports
        self.port['t'] = self.var['seq']['t']
        self.port['a'] = self.var['seq']['a']
        self.port['m'] = self.var['seq']['m']
        self.port['w'] = self.var['seq']['w']
        self.port['e'] = self.var['seq']['e']
        self.port['e_a'] = self.var['seq']['e_a']

        # Constraints
        def con_rule(m, s, t):
            return self.var['seq']['w'][s, t] * param['eta'] == self.var['seq']['m'][s, t]
        namestr = 'production_pgw_from_wood'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['t'][s, t] * param['max_prod'] == self.var['seq']['m'][s, t]
        namestr = 'production_mass_pgw'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['t'][s, t] * param['spec_el'] == self.var['seq']['e'][s, t]
        namestr = 'electric power_demand_pgw'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['a'][s, t] * param['spec_el']  == self.var['seq']['e_a'][s, t]
        namestr = 'electricity_demand_pgw_AGU'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['a'][s, t] <= self.var['seq']['t'][s, t]
        namestr = 'restrict_grid_con3'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        # da.add_obj_u_v_w(system, self)
        # da.add_obj_inv(system, self)


        # Total objective, which is assigned directly to unit
        # here probably none (9.8.2022)

class DeInkedPulp(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        #da.init_uvwi_param(self)

        #if self.param['lim_q'][0] > 0 or self.param['lim_f'][0] > 0:
        #    self.param['u_active'] = True

       #if self.param['cap_q'][0] > 0:
       #    self.param['i_active'] = True

       # if 'max_susd' not in self.param:
       #     if self.param['v_w_active']:
       #         self.param['max_susd'] = (self.param['lim_q'][0], self.param['lim_q'][0])
       #     else:
       #         self.param['max_susd'] = (1, 1)

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['e'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['s'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)

        da.add_var_to_model(system, self)

        # Ports
        self.port['m'] = self.var['seq']['m']
        self.port['e'] = self.var['seq']['e']
        self.port['s'] = self.var['seq']['s']

        # Constraints
        def con_rule(m, s, t):
            return self.var['seq']['m'][s, t] * param['spec_el'] / system.param['tss'] == self.var['seq']['e'][s, t]
        namestr = 'electric_power_demand_dip'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['m'][s, t]*param['spec_steam'] / system.param['tss'] == self.var['seq']['s'][s, t]
        namestr = 'steam_power_demand_dip'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        # Objective
        #da.add_obj_u_v_w(system, self)
        #da.add_obj_inv(system, self)

        # Total objective, which is assigned directly to unit
        #obj = 0
        #obj += self.obj['opex_fix'].expr
        #obj += self.obj['cost_SU'].expr
        #obj += self.obj['cost_SD'].expr
        #obj += self.obj['inv']
        #namestr = 'obj_' + self.name + '_total'
        #system.model.add_component(namestr, pyo.Objective(expr=obj))
        #system.model.component(namestr).deactivate()
        #self.obj['total'] = system.model.component(namestr)

class HoursRegime(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        if 'cap_s' not in self.param:
            self.param['cap_s'] = (0, np.inf)

        self.param['u_active'] = False
        self.param['v_w_active'] = False
        if 'cap_s' in self.param:
            if self.param['cap_s'][0] > 0:
                self.param['i_active'] = True
            else:
                self.param['i_active'] = False
        else:
            self.param['i_active'] = False

        #da.add_energy_param(system, self, param)


        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['s'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        self.var['scalar']['penalty'] = pyo.Var(domain=pyo.Binary)

        da.add_var_to_model(system, self)

        # Ports
        self.port['s'] = self.var['seq']['s']

        # Constraints
        da.add_op_lim(system, self, ['s'])
        da.add_cap_lim(self, ['s'])

        def con_rule(m):
            return sum(self.var['seq']['s'][s, t] for s in system.model.set_sc
                       for t in system.model.set_t) + (50000 * self.var['scalar']['penalty'])>= \
                   self.param['duration']/system.param['tss'] * self.var['scalar']['cap']

        namestr = '_7000_hour'
        self.con[namestr] = pyo.Constraint(rule=con_rule)


        # Objectives
        ## add costs for 7000 hours regime violation penalty
        obj = (self.var['scalar']['penalty'] * self.param['cost_violation'])
        namestr = 'obj_' + self.name + '_penalty'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['penalty'] = system.model.component(namestr)


        obj = 0
        obj += self.obj['penalty'].expr
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)

class PersonelCost(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        da.add_energy_param(system, self, param)

        # Variables
        self.var['seq'] = dict()
        self.var['seq']['o'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.Binary)
        da.add_var_to_model(system, self)

        # Ports
        self.port['o'] = self.var['seq']['o']

        # Constraints
        set_days = range(1, self.param['days']+1, 1)

        for i, n in enumerate(set_days):
            # start = (n-1) * self.param['steps_per_day']
            # end = n * self.param['steps_per_day'] - 1
            def con_rule(m, s, n):
                return self.var['seq']['o'][s, (n-1) * self.param['steps_per_day']] + self.var['seq']['o'][s, (n-1) * self.param['steps_per_day'] + 1] + self.var['seq']['o'][s, (n-1) * self.param['steps_per_day'] + 2] + self.var['seq']['o'][s, (n-1) * self.param['steps_per_day'] + 3] == self.param['steps_per_day'] * self.var['seq']['o'][s, (n-1) * self.param['steps_per_day']]

            namestr = 'const_holiday_operation' + str(n)
            self.con[namestr] = pyo.Constraint(system.model.set_sc, set_days, rule=con_rule)

        # Objective
        obj = sum(self.var['seq']['o'][s, t] * self.param['seq'][s, t] for s in system.model.set_sc for t in system.model.set_t)
        namestr = 'obj_' + self.name + '_holiday'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['holiday'] = system.model.component(namestr)


        # Total objective, which is assigned directly to unit
        obj = 0
        obj += self.obj['holiday'].expr
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)
