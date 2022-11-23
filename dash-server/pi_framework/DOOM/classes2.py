import pyomo.environ as pyo
import CoolProp.CoolProp as CP
import auxiliary as da
import numpy as np


class System:
    def __init__(self, param):
        self.param = param
        self.unit = dict()  # dictionary with all units
        self.node = dict()
        self.model = []
        self.var = dict()
        self.port = dict()
        self.con = dict()
        self.obj = dict()
        self.derive_param()
        self.create_concrete_model()

    def derive_param(self):
        self.param['n_sc'] = len(self.param['sc'])  # number of scenarios
        self.param['dur_sc'] = self.param['n_ts_sc'] * self.param['tss']  # duration of one scenario in hours
        self.param['dur_total'] = self.param['n_sc'] * self.param['dur_sc']  # total duration in hours
        self.param['n_ts_total'] = self.param['n_sc'] * self.param['n_ts_sc']  # total number of time steps

    def create_concrete_model(self):
        self.model = pyo.ConcreteModel()
        self.model.set_t = pyo.Set(initialize=range(self.param['n_ts_sc']))
        self.model.set_sc = pyo.Set(initialize=self.param['sc'].keys())

    def add_unit(self, param):
        self.unit[param['name']] = globals()[param['classname']](param, self)

    def add_node(self, param):
        self.node[param['name']] = Node(param, self)

    def build_model(self):
        # Build system constraints
        for u in self.unit:
            for c in self.unit[u].con:
                namestr = 'con_' + u + '_' + c
                self.model.add_component(namestr, self.unit[u].con[c])

        for n in self.node:
            for c in self.node[n].con:
                namestr = 'con_' + n + '_' + c
                self.model.add_component(namestr, self.node[n].con[c])

        # Build system objective
        obj = 0
        obj_real = 0
        for u in self.unit:
            if 'total' in self.unit[u].obj.keys():
                obj += self.unit[u].obj['total'].expr
                obj_real += self.unit[u].obj['total'].expr
                # small costs for variables in order to reduce equivalent solutions
                for v in self.unit[u].var['seq'].keys():
                    obj += 0 * 1e-6 * sum(self.unit[u].var['seq'][v][i] for i in self.unit[u].var['seq'][v].keys())
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
                                        self.param['medium'])
        self.param['h_out'] = CP.PropsSI('H', 'T', self.param['T_out'] + 273.15, 'P', self.param['pressure'],
                                         self.param['medium'])

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['q'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['f'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)

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

        # Objective
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
    # todo: add multiple mass inlet and outlets and multiple heat flows with fixed ratio
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
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['m'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['seq']['f'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['p'] = self.var['seq']['p']
        self.port['m'] = self.var['seq']['m']
        self.port['f'] = self.var['seq']['f']

        # Constraints
        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q'])
        da.add_cap_lim(self, ['q'])
        da.add_ramp_con(system, self, ['q'])
        da.add_lin_dep(system, self, ['q', 'f'])
        da.add_lin_dep(system, self, ['q', 'p'])
        da.add_simple_m_q(system, self)

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


class HeatPump(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters

        da.init_uvwi_param(self)

        self.param['h_sink_in'] = dict()
        for n in self.param['T_sink_in']:
            self.param['h_sink_in'][n] = CP.PropsSI('H', 'T', n + 273.15, 'P', self.param['pressure_sink'],
                                                    self.param['medium_sink'])
        self.param['h_source_in'] = dict()
        for n in self.param['T_source_in']:
            self.param['h_source_in'][n] = CP.PropsSI('H', 'T', n + 273.15, 'P', self.param['pressure_source'],
                                                      self.param['medium_source'])
        self.param['h_sink_out'] = CP.PropsSI('H', 'T', self.param['T_sink_out'] + 273.15, 'P',
                                              self.param['pressure_sink'], self.param['medium_sink'])
        self.param['h_source_out'] = CP.PropsSI('H', 'T', self.param['T_source_out'] + 273.15, 'P',
                                                self.param['pressure_source'], self.param['medium_source'])
        self.param['COP'] = tuple(
            self.param['eta_comp'][k] * (self.param['T_sink_out'] + self.param['delta_T_sink'][k] + 273.15) /
            (self.param['T_sink_out'] + self.param['delta_T_sink'][k] - self.param['T_source_out'] +
             self.param['delta_T_source'][k])
            for k in range(2)
        )
        self.param['lim_p'] = tuple(self.param['lim_q_sink'][k] / self.param['COP'][k] for k in range(2))

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

        # Constraints

        da.add_logic_uvw(system, self)  # min uptime and downtime constraint is integrated here
        da.add_op_lim(system, self, ['q_sink'])
        da.add_cap_lim(self, ['q_sink'])
        da.add_ramp_con(system, self, ['q_sink'])
        da.add_lin_dep(system, self, ['q_sink', 'p'])

        def con_rule(m, s, t):
            return self.var['seq']['q_sink'][s, t] == self.var['seq']['q_source'][s, t] + self.var['seq']['p'][s, t]

        namestr = 'energy_balance'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q_sink'][s, t] == sum(
                self.var['seq']['m_sink_in'][s, t, n] * (self.param['h_sink_out'] - self.param['h_sink_in'][n]) / 1e6
                for n in self.param['T_sink_in'])

        namestr = 'm_sink(q_sink)'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q_source'][s, t] == sum(self.var['seq']['m_source_in'][s, t, n] * (
                self.param['h_source_in'][n] - self.param['h_source_out']) / 1e6 for n in self.param['T_source_in'])

        namestr = 'm_source(q_source)'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

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


class Photovoltaic(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

        # Parameters
        da.init_uvwi_param(self)

        if self.param['cap_area'][0] > 0:
            self.param['i_active'] = True

        self.param['solar'] = system.param['seq']['solar']

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['p'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['p'] = self.var['seq']['p']

        # Constraints
        da.add_cap_lim(self, ['area'])

        def con_rule(m, s, t):
            return self.var['seq']['p'][s, t] <= float(self.param['eta'] * self.param['solar'][s][t]) * \
                   self.var['scalar']['cap']

        namestr = 'max_p'
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


class SolarThermal(Unit):
    def __init__(self, param, system):
        Unit.__init__(self, param, system)

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
                    self.var['seq']['m_in'][s, t, n] * self.param['h_in'][n] for n in self.param['T_in'])) / 1e6

        namestr = 'q(m_in,m_out)'
        self.con[namestr] = pyo.Constraint(system.model.set_sc, system.model.set_t, rule=con_rule)

        def con_rule(m, s, t):
            return self.var['seq']['q'][s, t] <= float(self.param['eta'] * self.param['solar'][s][t]) * \
                   self.var['scalar']['cap']

        namestr = 'max_q'
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

        da.add_var_to_model(system, self)

        # Ports
        self.port['q'] = self.var['seq']['q']
        self.port['m'] = self.var['seq']['m']

        # Constraints
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
        obj += self.obj['inv'].expr
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
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)
        da.add_var_uvwi(system, self)

        da.add_var_to_model(system, self)

        # Ports
        self.port['c'] = self.var['seq']['c']
        self.port['d'] = self.var['seq']['d']
        self.port['soc'] = self.var['seq']['soc']

        # Constraints
        da.add_op_lim(system, self, ['soc'])
        da.add_cap_lim(self, ['soc'])
        da.add_es_balance(system, self, ['c', 'd', 'soc'])

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
        obj += self.obj['inv'].expr
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

        if self.param['cap_soc_p'][0] > 0:
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

        da.add_var_to_model(system, self)

        # Ports
        self.port['c'] = self.var['seq']['c']
        self.port['d'] = self.var['seq']['d']
        self.port['soc'] = self.var['seq']['soc']

        # Constraints
        da.add_cap_lim(self, ['soc_p'])

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
            return (self.var['seq']['soc_p'][np.mod(t_p + 1, len(self.param['set_n_period']))] - (1 - system.param['tss'] * self.param['loss_soc'])**system.param['n_ts_sc'] * self.var['seq']['soc_p'][t_p]) == sum(self.var['seq']['c'][self.param['set_period'][t_p], t] - self.var['seq']['d'][self.param['set_period'][t_p], t] for t in system.model.set_t) * system.param['tss']
        namestr = 'con_' + self.name + '_es_balance_' + 'soc_p'
        system.model.add_component(namestr, pyo.Constraint(self.param['set_n_period'], rule=con_rule))

        # op_lim
        def con_rule(m, t_p, t2):
            return self.var['seq']['soc_p'][t_p] + sum(self.var['seq']['c'][self.param['set_period'][t_p], t] - self.var['seq']['d'][self.param['set_period'][t_p], t] for t in range(t2)) * system.param['tss'] <= self.var['scalar']['cap']
        namestr = 'con_' + self.name + '_' + 'soc_p_max'
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
        obj += self.obj['inv'].expr
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

        da.add_var_to_model(system, self)

        # Ports
        for n in self.param['T']:
            self.port['m_c_' + str(n)] = pyo.Reference(self.var['seq']['m_c'][:, :, n])
            self.port['m_d_' + str(n)] = pyo.Reference(self.var['seq']['m_d'][:, :, n])
            self.port['soc_' + str(n)] = pyo.Reference(self.var['seq']['soc'][:, :, n])

        # Constraints
        da.add_cap_lim(self, ['soc'])

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
        obj += self.obj['inv'].expr
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

        # Variables
        self.var['seq'] = dict()
        self.var['scalar'] = dict()
        self.var['seq']['s'] = pyo.Var(system.model.set_sc, system.model.set_t, domain=pyo.NonNegativeReals)
        self.var['scalar']['cap'] = pyo.Var(domain=pyo.NonNegativeReals)

        da.add_var_to_model(system, self)

        # Ports
        self.port['s'] = self.var['seq']['s']

        # Constraints
        da.add_op_lim(system, self, ['s'])
        da.add_cap_lim(self, ['s'])

        # Objectives
        obj = sum(
            self.var['seq']['s'][s, t] * self.param['seq'][s][t] * system.param['sc'][s][0] for s in system.model.set_sc
            for t in system.model.set_t) / system.param['dur_sc'] * 8760
        namestr = 'obj_' + self.name + '_energy'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['energy'] = system.model.component(namestr)

        if 'cost_max_s' in self.param:
            obj = self.var['scalar']['cap'] * self.param['cost_max_s']
            namestr = 'obj_' + self.name + '_max_s'
            system.model.add_component(namestr, pyo.Objective(expr=obj))
            system.model.component(namestr).deactivate()
            self.obj['max_s'] = system.model.component(namestr)

        obj = 0
        obj += self.obj['energy'].expr
        if 'cost_max_s' in self.param:
            obj += self.obj['max_s'].expr
        namestr = 'obj_' + self.name + '_total'
        system.model.add_component(namestr, pyo.Objective(expr=obj))
        system.model.component(namestr).deactivate()
        self.obj['total'] = system.model.component(namestr)


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
