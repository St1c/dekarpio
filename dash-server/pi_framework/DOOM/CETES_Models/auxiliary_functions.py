from pi_framework.DOOM.CETES_Models.cost_fun import *


def prep_lhts(param_lhts, case_study, settings):
    dT = min([case_study['temperature limits']['T_max'] - param_lhts['PCM parameters']['melting temperature'],
              param_lhts['PCM parameters']['melting temperature'] - case_study['temperature limits']['T_min']])

    dT_charging = case_study['temperature limits']['T_max'] - param_lhts['PCM parameters']['melting temperature']
    dT_discharging = param_lhts['PCM parameters']['melting temperature'] - case_study['temperature limits']['T_min']

    cap_days = case_study['storage limits']['maximum capacity']
    nr_timesteps = int(24 / settings['stepsize'])

    demand_profile = case_study['profiles']['heat_demand']

    param_lhts['integration parameters'] = {
        'dT': dT,
        'charging': 1,
        'discharging': dT_charging/dT_discharging,

    }

    max_capacity = 0
    for day in range(int(len(demand_profile) / nr_timesteps)):
        max_capacity = max([max_capacity, sum(demand_profile[nr_timesteps * day:nr_timesteps * (day + 1)]) * settings[
            'stepsize'] * cap_days])

    param_lhts['integration parameters']['max capacity'] = max_capacity

    coeffs, R2, dp_red = calc_costfun_LHTS(param_lhts, case_study, settings)

    param_lhts['integration parameters']['cost coefficients'] = coeffs
    param_lhts['integration parameters']['cost coefficients R2'] = R2
    param_lhts['integration parameters']['dp'] = dp_red

    return param_lhts


def prep_ruths(param_ruths, case_study, settings):
    demand_profile = case_study['profiles']['heat_demand']

    cap_days = case_study['storage limits']['maximum capacity']
    nr_timesteps = int(24 / settings['stepsize'])

    max_capacity = 0
    for day in range(int(len(demand_profile) / nr_timesteps)):
        max_capacity = max([max_capacity, sum(demand_profile[nr_timesteps * day:nr_timesteps * (day + 1)]) * settings[
            'stepsize'] * cap_days])
    param_ruths['integration parameters']['max capacity'] = max_capacity

    param_ruths['integration parameters']['cost coefficients'], param_ruths['integration parameters'][
        'cost coefficients R2'], param_ruths['integration parameters']['dp'] = calc_costfun_ruths(param_ruths, case_study,
                                                     settings)  # costs = c[0] + X*c[1] + Y*c[2] + X**2*c[3] + Y**2*c[4] + X*Y*c[5]
    param_ruths['integration parameters']['charging'] = 1
    param_ruths['integration parameters']['discharging'] = 1

    return param_ruths


def prep_moltensalt(param_moltensalt, case_study, settings):
    demand_profile = case_study['profiles']['heat_demand']

    cap_days = case_study['storage limits']['maximum capacity']
    nr_timesteps = int(24 / settings['stepsize'])

    # Calculates the max required storage capacity: the heat demand over cap_days (=1 day) in kWh
    max_capacity = 0
    # RUnning over the demand profile in 0.5h time steps
    for day in range(int(len(demand_profile) / nr_timesteps)):
        max_capacity = max([max_capacity, sum(demand_profile[nr_timesteps * day:nr_timesteps * (day + 1)]) * settings[
            'stepsize'] * cap_days])

    param_moltensalt['integration parameters']['max capacity'] = max_capacity

    param_moltensalt['integration parameters']['cost coefficients'], param_moltensalt['integration parameters'][
        'cost coefficients R2'], param_moltensalt['integration parameters']['dp'] = calc_costfun_moltensalt(param_moltensalt, case_study, settings)  # costs = c[0] + X*c[1] + Y*c[2] + X**2*c[3] + Y**2*c[4] + X*Y*c[5]

    param_moltensalt['integration parameters']['charging'] = 1
    param_moltensalt['integration parameters']['discharging'] = 1


    return param_moltensalt


def prep_concrete(param_concrete, case_study, settings):
    maxdT = (case_study['temperature limits']['T_max'] - case_study['temperature limits']['T_min'])
    dT = float(maxdT) # * param_concrete['Concrete parameters']['effective use of T range']

    demand_profile = case_study['profiles']['heat_demand']

    cap_days = case_study['storage limits']['maximum capacity']
    nr_timesteps = int(24 / settings['stepsize'])

    # Calculates the max required storage capacity: the heat demand over cap_days (=1 day) in kWh
    max_capacity = 0
    # Running over the demand profile in 0.5h time steps
    for day in range(int(len(demand_profile) / nr_timesteps)):
        max_capacity = max([max_capacity, sum(demand_profile[nr_timesteps * day:nr_timesteps * (day + 1)]) * settings[
            'stepsize'] * cap_days])

    param_concrete['integration parameters']['dT'] = dT
    param_concrete['integration parameters']['max capacity'] = max_capacity

    param_concrete['integration parameters']['cost coefficients'], param_concrete['integration parameters'][
        'cost coefficients R2'], param_concrete['integration parameters']['dp'] = calc_costfun_concrete(param_concrete, case_study, settings)
    # costs = c[0] + X*c[1] + Y*c[2] + X**2*c[3] + Y**2*c[4] + X*Y*c[5]
    param_concrete['integration parameters']['charging'] = 1
    param_concrete['integration parameters']['discharging'] = 1

    return param_concrete

