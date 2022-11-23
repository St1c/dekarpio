import numpy as np
from pyomo.environ import *

def add_var(model, unit_name, var_name, domain):
    namestr = 'Var_' + unit_name + '_' + var_name
    model.add_component(namestr, Var(within=domain, bounds=(-10**10, 10**10)))
    return model.component(namestr)

def add_bounded_var(model, unit_name, var_name, bounds):
    namestr = 'Var_' + unit_name + '_' + var_name
    model.add_component(namestr, Var(bounds=bounds))
    return model.component(namestr)

def add_bounded_set_var(model, unit_name, var_name, set, bounds):
    namestr = 'Var_' + unit_name + '_' + var_name
    model.add_component(namestr, Var(set, bounds=bounds))
    return model.component(namestr)

def add_set_var(model, unit_name, var_name, set, domain):
    namestr = 'Var_' + unit_name + '_' + var_name
    model.add_component(namestr, Var(set, within=domain, bounds=(-10**10, 10**10)))
    return model.component(namestr)

def add_con(model, unit_name, con_name, constraint):
    namestr = 'Con_' + unit_name + '_' + con_name
    model.add_component(namestr, constraint)


class Energysystem:
    def __init__(self, energy_demand, settings, case_study):
        self.storages = []
        self.hthps = []
        self.e_boilers = []
        self.nodes = []
        self.connectors = []

        self.energy_demand = energy_demand
        self.stepsize = settings['stepsize']
        self.time_steps = case_study['profiles']['time_steps']
        self.case_study = case_study

    # ADD COMPONENTS
    def add_Storage(self, unit_name, model, settings, case_study, param_specific):
        self.storages.append(Storage(unit_name, model, settings, case_study, param_specific))

    def add_HTHP(self, unit_name, model, settings, case_study, param_specific):
        self.hthps.append(HTHP(unit_name, model, settings, case_study, param_specific))

    def add_E_boiler(self, unit_name, model, settings, case_study, param_specific):
        self.e_boilers.append(EBoiler(unit_name, model, settings, case_study, param_specific))

    def add_Node(self, node_name, model, case_study, mode):
        self.nodes.append(Node(self, node_name, mode, case_study, model))

    def add_Connector(self, connector_name, model):
        self.connectors.append(Connector(connector_name, model))

    def build_overall_objective(self, model):
        model.overall_obj = Objective(expr=0)
        for s in self.storages:
            model.overall_obj.expr += s.investment_costs/self.case_study['costs']['annualization factor']

        for s in self.hthps:
            model.overall_obj.expr += s.investment_costs/self.case_study['costs']['annualization factor']
            model.overall_obj.expr += s.energy_costs

        for s in self.e_boilers:
            model.overall_obj.expr += s.investment_costs/self.case_study['costs']['annualization factor']
            model.overall_obj.expr += s.energy_costs

        model.overall_obj.activate()
        self.overall_costs = model.overall_obj

    # POST PROCESSING
    # def plot_heat_loads_supply(self):
    #
    # def plot_heat_loads_storages(self):
    #
    # def plot_energy_content_storages(self):
    #
    # def plot_capacities(self):

    def print_capacities(self):
        print(' ')
        print(' ')
        print('------------------------------ COMPONENTS ------------------------------')
        print(' ')

        total_investment_costs = 0
        total_investment_costs_annualized = 0
        total_energy_costs = 0

        for s in self.storages:
            print('------ ' + s.type + ' (' + s.name + ') ------')
            print('Capacity:         ' + str(s.Q_delta[0].value) + ' kWh')
            print('Max. Power:       ' + str(s.Q_dot_max[0].value) + ' kW')
            investment_costs = round(s.investment_costs.__call__(), 1)
            investment_costs_annualized = investment_costs/self.case_study['costs']['annualization factor']
            total_investment_costs += investment_costs
            total_investment_costs_annualized += investment_costs_annualized
            print('Investment costs: ' + str(investment_costs_annualized) + ' €/y')
            print('Model Fit (R²):   ' + str(round(s.model_fit, 3)))
            print(' ')



        for s in self.hthps:
            print('------ ' + s.type + ' (' + s.name + ') ------')
            print('Max. Power:       ' + str(s.Q_dot_max.value) + ' kW')
            investment_costs = round(s.investment_costs.__call__(), 1)
            investment_costs_annualized = investment_costs / self.case_study['costs']['annualization factor']
            total_investment_costs += investment_costs
            total_investment_costs_annualized += investment_costs_annualized
            print('Investment costs: ' + str(investment_costs_annualized) + ' €/y')
            energy_costs = round(s.energy_costs.__call__(), 1)
            total_energy_costs += energy_costs
            print('Energy costs:     ' + str(energy_costs) + ' €/y')
            print(' ')

        for s in self.e_boilers:
            print('------ ' + s.type + ' (' + s.name + ') ------')
            print('Max. Power:       ' + str(s.Q_dot_max.value) + ' kW')
            investment_costs = round(s.investment_costs.__call__(), 1)
            investment_costs_annualized = investment_costs / self.case_study['costs']['annualization factor']
            total_investment_costs += investment_costs
            total_investment_costs_annualized += investment_costs_annualized
            print('Investment costs: ' + str(investment_costs_annualized) + ' €/y')
            energy_costs = round(s.energy_costs.__call__(), 1)
            total_energy_costs += energy_costs
            print('Energy costs:     ' + str(energy_costs) + ' €/y')
            print(' ')

        print('------ TOTAL ANNUAL COSTS ------')
        print('Total Costs: ' + str(round(self.overall_costs.__call__(), 1)) + ' €/y')
        print('Total Energy Costs: ' + str(total_energy_costs) + ' €/y')
        base_costs = sum((self.case_study['profiles']['heat_demand']) * self.case_study['profiles']['electricity_costs'])*self.stepsize
        print('Total Energy Costs base: ' + str(base_costs) + ' €/y')
        print('Total Investment costs: ' + str(total_investment_costs) + ' €')
        print('Total Annualized Investment costs: ' + str(total_investment_costs_annualized) + ' €/y')
        print(' ')

        print('----------------------------- CHECKS ----------------------------------')
        print(' ')
        energy_supply = 0
        for s in self.hthps:
            energy_supply += sum(s.Q_dot.get_values().values())

        for s in self.e_boilers:
            energy_supply += sum(s.Q_dot.get_values().values())

        print('Energy supply: ' + str(round(energy_supply*self.stepsize, 1)) + ' kWh')
        print('Energy demand: ' + str(round(sum(self.energy_demand)*self.stepsize)) + ' kWh')

        print(' ')
        for s in self.storages:
            print('------ ' + s.type + ' (' + s.name + ') ------')
            Q_dot_in = np.array(list(s.Q_dot_in.get_values().values()))
            Q_dot_out = np.array(list(s.Q_dot_out.get_values().values()))
            Q_dot_net = Q_dot_in - Q_dot_out
            print('Energy stored: ' + str(round(sum(Q_dot_net[Q_dot_net>0])*self.stepsize)) + ' kWh')
            print('Energy discharged: ' + str(round(sum(Q_dot_net[Q_dot_net<0])*self.stepsize)) + ' kWh')
            print(' ')

    def plot_supply(self):
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm

        cmap = cm.get_cmap('Set1')
        color_counter = 0

        plots = []
        fig, axs = plt.subplots()

        for s in self.storages:
            if s.Q_delta[0]() > 0:
                supply = np.array(list(s.Q_dot_in.get_values().values()))-np.array(list(s.Q_dot_out.get_values().values()))
                axs.fill_between(self.time_steps, -supply, step='post', alpha=0.4, color=cmap.colors[color_counter])  #, hatch='\\'
                plot, = axs.step(self.time_steps, -supply, label=s.name, where='post', color=cmap.colors[color_counter])
                plots.append(plot)

                color_counter += 1

        for s in self.hthps:
            supply = np.array(list(s.Q_dot.get_values().values()))
            if max(supply) > 0:
                axs.fill_between(self.time_steps, supply, step='post', alpha=0.4, color=cmap.colors[color_counter])
                plot, = axs.step(self.time_steps, supply, label=s.name, where='post', color=cmap.colors[color_counter])
                color_counter += 1
                plots.append(plot)

        for s in self.e_boilers:
            supply = np.array(list(s.Q_dot.get_values().values()))
            if max(supply) > 0:
                axs.fill_between(self.time_steps, supply, step='post', alpha=0.4, color=cmap.colors[color_counter])
                plot, = axs.step(self.time_steps, supply, label=s.name, where='post', color=cmap.colors[color_counter])
                color_counter += 1
                plots.append(plot)

        demand = 0
        for s in self.storages:
            demand = demand + np.array(list(s.Q_dot_out.get_values().values()))

        for s in self.connectors:
            demand = demand + np.array(list(s.Q_dot.get_values().values()))

        plot, = axs.step(self.time_steps, demand, label='Steam demand', where='post', color='black', linewidth=1)
        plots.append(plot)

        axs2 = axs.twinx()
        plot, = axs2.plot(self.time_steps, self.case_study['profiles']['electricity_costs']*100, drawstyle='steps-post', label='Electricity price', linestyle='--', color='black', linewidth=1)
        plots.append(plot)

        axs2.legend(handles=plots, fancybox=True, framealpha=0.8)

        axs2.set_ylabel('Electricity price (Cent/kWh)')
        axs.set_xlabel('time (h)')

        ylim = max(np.abs(axs.get_xlim()))

        fact = 0
        unit_string = 'kW'
        if ylim > 10**3:
            fact = 10**3
            unit_string = 'MW'
        if ylim > 10**6:
            fact = 10**6
            unit_string = 'GW'

        import matplotlib.ticker as ticker
        @ticker.FuncFormatter
        def major_formatter(x, pos):
            return '{:.0f}'.format(x/fact)


        axs.yaxis.set_major_formatter(major_formatter)
        axs.set_ylabel('heat load ({})'.format(unit_string))

        # plt.show()

    def plot_storage(self):
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm

        cmap = cm.get_cmap('Set1')
        color_counter = 0

        plots = []

        plt.figure()
        for s in self.storages:
            if s.Q_delta[0]() > 0:
                energy_stored = np.array(list(s.Q.get_values().values()))
                plt.fill_between(self.time_steps, energy_stored, step='post', alpha=0.4, color=cmap.colors[color_counter])
                plot, = plt.step(self.time_steps, energy_stored, label=s.name, where='post', color=cmap.colors[color_counter])
                color_counter += 1
                plots.append(plot)

        plt.legend(handles=plots)
        plt.ylabel('energy stored (kWh)')
        plt.xlabel('time (h)')
        # plt.show()

        plt.figure('cheapest')
        for s in self.storages:
            capacity = s.Q_delta[0]()
            max_heat_load = s.Q_dot_max[0]()
            plt.scatter(capacity, max_heat_load)
            plt.annotate(s.name, (capacity, max_heat_load))

class Storage:
    def __init__(self, unit_name, model, settings, case_study, param_specific):

        self.name = unit_name
        self.type = param_specific['Type']

        self.model_fit = param_specific['integration parameters']['cost coefficients R2']

        # Optimization model

        ##############################
        # Init variables
        Q_max = add_var(model, unit_name, 'Q_max', NonNegativeReals)
        z = add_set_var(model, unit_name, 'z', [0], Binary)
        Q_min = add_var(model, unit_name, 'Q_min', NonNegativeReals)
        Q_delta = add_bounded_set_var(model, unit_name, 'Q_delta', [0], (0, param_specific['integration parameters']['max capacity']))
        Q = add_set_var(model, unit_name, 'Q', model.set_timesteps, NonNegativeReals)

        Q_dot_max = add_bounded_set_var(model, unit_name, 'Q_dot_max', [0], (0, param_specific['integration parameters']['max capacity']*case_study['storage limits']['ratio']))
        Q_dot_max_charge = add_var(model, unit_name, 'Q_dot_max_charge', NonNegativeReals)
        Q_dot_max_discharge = add_var(model, unit_name, 'Q_dot_max_discharge', NonNegativeReals)

        Q_dot_in = add_set_var(model, unit_name, 'Q_dot_in', model.set_timesteps, NonNegativeReals)
        Q_dot_out = add_set_var(model, unit_name, 'Q_dot_out', model.set_timesteps, NonNegativeReals)

        self.Q_max = Q_max
        self.z = z
        self.Q_min = Q_min
        self.Q_delta = Q_delta
        self.Q = Q

        self.Q_dot_max = Q_dot_max
        self.Q_dot_max_charge = Q_dot_max_charge
        self.Q_dot_max_discharge = Q_dot_max_discharge

        self.Q_dot_in = Q_dot_in
        self.Q_dot_out = Q_dot_out

        ##############################
        # Add general constraints

        # Maximum energy
        def con_fun(model, t):
            return Q_max >= Q[t]
        add_con(model, unit_name, 'Q_max', Constraint(model.set_timesteps, rule=con_fun))

        # Minimum energy
        def con_fun(model, t):
            return Q_min <= Q[t]
        add_con(model, unit_name, 'Q_min', Constraint(model.set_timesteps, rule=con_fun))

        # Capacity
        def con_fun(model):
            return Q_delta[0] == Q_max - Q_min
        add_con(model, unit_name, 'Q_delta', Constraint(rule=con_fun))

        # Maximum charging rate
        def con_fun(model, t):
            return Q_dot_max_charge >= Q_dot_in[t] - Q_dot_out[t]
        add_con(model, unit_name, 'Q_dot_max_charge', Constraint(model.set_timesteps, rule=con_fun))

        # Maximum discharging rate
        def con_fun(model, t):
            return Q_dot_max_discharge >= - Q_dot_in[t] + Q_dot_out[t]
        add_con(model, unit_name, 'Q_dot_max_discharge', Constraint(model.set_timesteps, rule=con_fun))

        # stepwise energy content
        def con_fun(model, t):
            try:
                loss = param_specific['losses']
            except:
                loss = 0

            if t == list(model.set_timesteps.data())[-1]:
                return Q[0] == Q[t] + (Q_dot_in[t] - Q_dot_out[t]) * settings['stepsize'] - (Q[0] + Q[t])/2*loss*settings['stepsize']
            else:
                return Q[t+1] == Q[t] + (Q_dot_in[t] - Q_dot_out[t]) * settings['stepsize'] - (Q[t+1] + Q[t])/2*loss*settings['stepsize']
        add_con(model, unit_name, 'Q_profile', Constraint(model.set_timesteps, rule=con_fun))

        # upper bound for storage capacity
        def con_fun(model):
            return Q_delta[0] <= param_specific['integration parameters']['max capacity']
        add_con(model, unit_name, 'Q_delta_max', Constraint(rule=con_fun))

        # max heat load/capacity ratio
        def con_fun(model):
            return Q_delta[0]*case_study['storage limits']['ratio'] >= Q_dot_max[0]
        add_con(model, unit_name, 'Q_dot_max_ratio', Constraint(rule=con_fun))

        # max heat load
        def con_fun(model):
            return Q_dot_max[0] <= param_specific['integration parameters']['max capacity']*case_study['storage limits']['ratio'] * z[0]
        add_con(model, unit_name, 'Q_dot_max_limit', Constraint(rule=con_fun))

        ##############################
        # Add specific constraints

        # Max charging & discharging heat loads
        def con_fun(model):
            return Q_dot_max[0] >= Q_dot_max_charge * param_specific['integration parameters']['charging']
        add_con(model, unit_name, 'Q_dot_max_charge_param', Constraint(rule=con_fun))

        def con_fun(model):
            return Q_dot_max[0] >= Q_dot_max_discharge * param_specific['integration parameters']['discharging']
        add_con(model, unit_name, 'Q_dot_max_discharge_param', Constraint(rule=con_fun))

        self.model = model

        ##############################
        # Quadratic cost function
        cost_coefficients = param_specific['integration parameters']['cost coefficients']
        cost_coefficients = np.array(cost_coefficients).round(6)

        if settings['optimization type'] == 'quadratic':
            investment_costs = 0
            round_prec = 5
            if np.round(cost_coefficients[0], 5) != 0:
                investment_costs += z[0] * np.round(cost_coefficients[0], 5)

            if np.round(cost_coefficients[1], 5) != 0:
                investment_costs += Q_delta[0] * np.round(cost_coefficients[1], 5)

            if np.round(cost_coefficients[3], 5) != 0:
                investment_costs += Q_dot_max[0] * np.round(cost_coefficients[2], 5)

            if np.round(cost_coefficients[3], round_prec) != 0:
                investment_costs += Q_delta[0] * Q_delta[0] * np.round(cost_coefficients[3], round_prec)

            if np.round(cost_coefficients[4], round_prec) != 0:
                investment_costs += Q_dot_max[0] * Q_dot_max[0] * np.round(cost_coefficients[4], round_prec)

            if np.round(cost_coefficients[5], round_prec) != 0:
                investment_costs += Q_delta[0] * Q_dot_max[0] * np.round(cost_coefficients[5], round_prec)

            # * z[0] + \
        elif settings['optimization type'] == 'linear':
            investment_costs = z[0] * cost_coefficients[0] + \
                    Q_delta[0] * cost_coefficients[1] + \
                    Q_dot_max[0] * cost_coefficients[2]

        self.investment_costs = investment_costs

        setattr(model, 'obj_' + unit_name + '_investment', Objective(expr=investment_costs/case_study['costs']['annualization factor']))
        objective = getattr(model, 'obj_' + unit_name + '_investment')
        objective.deactivate()


class HTHP:
    def __init__(self, unit_name, model, settings, case_study, param_specific):
        self.name = unit_name
        self.type = 'HTHP'

        # Optimization model

        ##############################
        # Init variables

        Q_dot = add_set_var(model, unit_name, 'Q_dot', model.set_timesteps, NonNegativeReals)
        Q_dot_max = add_var(model, unit_name, 'Q_dot_max', NonNegativeReals)
        Pel = add_set_var(model, unit_name, 'Pel', model.set_timesteps, NonNegativeReals)

        self.Q_dot = Q_dot
        self.Q_dot_max = Q_dot_max
        self.Pel = Pel

        ##############################
        # Add general constraints

        # Maximum thermal heat load
        def con_fun(model, t):
            return Q_dot_max >= Q_dot[t]
        add_con(model, unit_name, 'Q_dot_max', Constraint(model.set_timesteps, rule=con_fun))

        def con_fun(model, t):
            if param_specific['T_h'] >= 160:
                return Q_dot[t] - Pel[t] <= 0
            else:
                return Q_dot[t] - Pel[t] <= case_study['profiles']['surplus_heat'][t]
        add_con(model, unit_name, 'Q_dot_source', Constraint(model.set_timesteps, rule=con_fun))

        def con_fun(model, t):
            return Q_dot[t] == (param_specific['T_h'] + 273.15)/(param_specific['T_h'] - param_specific['T_c'])*param_specific['eta'] * Pel[t]
        add_con(model, unit_name, 'carnot', Constraint(model.set_timesteps, rule=con_fun))

        self.model = model

        ##############################
        # Linear cost function
        cost_coefficients = param_specific['cost coefficients']

        investment_costs = (cost_coefficients[0] + \
                cost_coefficients[1] * Q_dot_max)
        energy_costs = sum(Pel[t] * settings['stepsize'] * case_study['profiles']['electricity_costs'][t] for t in model.set_timesteps)

        self.investment_costs = investment_costs
        self.energy_costs = energy_costs

        setattr(model, 'obj_' + unit_name + '_investment', Objective(expr=investment_costs/case_study['costs']['annualization factor']))
        setattr(model, 'obj_' + unit_name + '_energy', Objective(expr=energy_costs))

        objective = getattr(model, 'obj_' + unit_name + '_investment')
        objective.deactivate()
        objective = getattr(model, 'obj_' + unit_name + '_energy')
        objective.deactivate()


class EBoiler:
    def __init__(self, unit_name, model, settings, case_study, param_specific):
        self.name = unit_name
        self.type = 'E-Boiler'

        # Optimization model

        ##############################
        # Init variables

        Q_dot = add_set_var(model, unit_name, 'Q_dot', model.set_timesteps, NonNegativeReals)
        Q_dot_max = add_var(model, unit_name, 'Q_dot_max', NonNegativeReals)
        Pel = add_set_var(model, unit_name, 'Pel', model.set_timesteps, NonNegativeReals)

        self.Q_dot = Q_dot
        self.Q_dot_max = Q_dot_max
        self.Pel = Pel

        ##############################
        # Add general constraints

        # Maximum thermal heat load
        def con_fun(model, t):
            return Q_dot_max >= Q_dot[t]
        add_con(model, unit_name, 'Q_dot_max', Constraint(model.set_timesteps, rule=con_fun))

        def con_fun(model, t):
            return Q_dot[t] == param_specific['eta'] * Pel[t]
        add_con(model, unit_name, 'efficiency', Constraint(model.set_timesteps, rule=con_fun))

        self.model = model

        ##############################
        # Linear cost function
        cost_coefficients = param_specific['cost coefficients']

        investment_costs = (cost_coefficients[0] + \
                cost_coefficients[1] * Q_dot_max)
        energy_costs = sum(Pel[t] * settings['stepsize'] * case_study['profiles']['electricity_costs'][t] for t in model.set_timesteps)

        self.investment_costs = investment_costs
        self.energy_costs = energy_costs

        setattr(model, 'obj_' + unit_name + '_investment', Objective(expr=investment_costs/case_study['costs']['annualization factor']))
        setattr(model, 'obj_' + unit_name + '_energy', Objective(expr=energy_costs))

        objective = getattr(model, 'obj_' + unit_name + '_investment')
        objective.deactivate()
        objective = getattr(model, 'obj_' + unit_name + '_energy')
        objective.deactivate()


class Node:
    def __init__(self, energy_system, node_name, mode, case_study, model):

        self.name = node_name
        self.mode = mode

        def con_fun(model, t):
            lhs = 0
            rhs = 0
            if mode == 'in':
                for s in energy_system.e_boilers:
                    lhs += s.Q_dot[t]
                for s in energy_system.hthps:
                    lhs += s.Q_dot[t]


                for s in energy_system.storages:
                    rhs += s.Q_dot_in[t]
                for s in energy_system.connectors:
                    rhs += s.Q_dot[t]

            if mode == 'out':
                for s in energy_system.storages:
                    lhs += s.Q_dot_out[t]
                for s in energy_system.connectors:
                    lhs += s.Q_dot[t]

                rhs += case_study['profiles']['heat_demand'][t]

            return lhs == rhs
        add_con(model, node_name, mode, Constraint(model.set_timesteps, rule=con_fun))


class Connector:
    def __init__(self, connector_name, model):

        self.name = connector_name

        Q_dot = add_set_var(model, connector_name, 'Q_dot', model.set_timesteps, NonNegativeReals)
        self.Q_dot = Q_dot

        self.model = model


