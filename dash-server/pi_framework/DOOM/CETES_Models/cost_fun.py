import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import CoolProp.CoolProp as cp
import pi_framework.DOOM.CETES_Models.cost_fun_comp as cfc
import pi_framework.DOOM.CETES_Models.htc_calculator as htc_saltHX
import time

def calc_costfun_LHTS(p_spec, p_gen, settings, solution=None):
    """
    Description:

    This script is used to obtain a quadratic cost-function for a PCM storage system

    Using given inputs, the geometry of a tube surrounded by PCM is varied and the corresponding
    heat loads and capacities are calculated.
    The heat loads are obtained using the average of heat load for a full charge of the PCM
    However, to consider the low heat load at the end of the charging process, the high heat loads at the beginning are
    neglected.
    The variable "fract_e" determines the percentage of the charging process that is neglected.
    For example "fract_e = 0.1" neglects the first 10% (in terms of time) of the charging process.

    A lot of data points (capacity/heat load/costs) are obtained which are then scaled to a capacity of 1 kWh
    This results in solutions for similar capacity/heat load combinations of which the most cost efficient solution
    is selected.

    Using this selection, new data points are extrapolated to cover the required domain for capacity and heat loads

    For these data-points a least-squares-regression is carried out to obtain a (nonconvex) quadratic cost-function
    """

    sto_type = 'LHTS'

    show_plots = settings['plotting']['show_plots']
    show_sim_plots = settings['plotting']['show_sim_plots']
    print_progress = settings['plotting']['print_progress']

    optimization_type = settings['optimization type']
    max_cap_kWh = p_spec['integration parameters']['max capacity']

    # ==================================================================================================================

    #  Parameters
    tube_wall = p_spec['storage geometry']['tube_wall']

    c_pcm = p_spec['cost parameters']['c_pcm']

    # Auxiliary params for unit conversion
    kWh2Ws = 3.6 * 10 ** 6

    # INPUT
    max_cap_Ws = max_cap_kWh * kWh2Ws  # Ws


    # ==================================================================================================================
    #  Variation of tube diameter and layer thickness -> DATA POINTS for COST FUNCTION

    res1 = p_spec['approximation parameters']['res 1']  # number of variations for tube diameter
    res2 = p_spec['approximation parameters']['res 2']  # number of variations for pcm layer thickness

    # Build Dataframe:
    dim = res1*res2
    dp_var = pd.DataFrame({
        'max. heat load (kW)': np.zeros(dim),
        'capacity (kWh)': np.zeros(dim),
        'total volume (m³)': np.zeros(dim),
        'storage material volume (m³)': np.zeros(dim),
        'tube volume (m³)': np.zeros(dim),
        'tube length (m)': np.zeros(dim),
        'storage material fraction': np.zeros(dim),
        'tube diameter (m)': np.zeros(dim),
        'storage material layer fraction': np.zeros(dim)
    })

    c = 0
    for i, dia in enumerate(steps_geom_series(res1, p_spec['storage geometry']['tube_diameters_range'])):
        for j, layer in enumerate(steps_geom_series(res2, p_spec['storage geometry']['pcm_layer_fract_range'])):
            nodes = p_spec['approximation parameters']['number of nodes']
            dp_var['max. heat load (kW)'][c], dp_var['capacity (kWh)'][c] = simulate_concrete_pcm(dia, layer, p_spec, p_gen, nodes, show_sim_plots)
            dp_var['total volume (m³)'][c] = ((dia * (1 + layer)) / 2) ** 2 * np.pi
            dp_var['storage material volume (m³)'][c] = (dia * (1 + layer) / 2) ** 2 * np.pi - (dia / 2) ** 2 * np.pi
            dp_var['tube volume (m³)'][c] = (dia / 2) ** 2 * np.pi - ((dia - 2 * tube_wall) / 2) ** 2 * np.pi  # not used
            dp_var['tube length (m)'][c] = 1
            dp_var['storage material fraction'][c] = dp_var['storage material volume (m³)'][c] / dp_var['total volume (m³)'][c]
            dp_var['tube diameter (m)'][c] = dia
            dp_var['storage material layer fraction'][c] = layer

            c += 1

            if print_progress:
                if c == 1:
                    print('Generation of data points LHTS:')

                tot = res1 * res2
                prog = c/tot * 100
                inc = 10
                if c % (tot/inc) <= ((tot/inc) % 1):
                    print('{:.2F} %'.format(prog))

    # ==================================================================================================================
    # rescale and extend data points
    if solution is None:
        rescale_factor = max_cap_Ws / kWh2Ws / dp_var['capacity (kWh)'].values
    else:
        rescale_factor = solution['capacity (kWh)'] / dp_var['capacity (kWh)'].values

    select_cols = [
        'max. heat load (kW)',
        'capacity (kWh)',
        'total volume (m³)',
        'storage material volume (m³)',
        'tube volume (m³)',
        'tube length (m)',
    ]

    if solution is None:
        res3 = p_spec['approximation parameters']['res 3']  # discretization of capacity range
        dp_all = rescale(dp_var, select_cols, rescale_factor, res3)
    else:
        res3 = 1
        dp_all = rescale(dp_var, select_cols, rescale_factor, res3)

    # ==================================================================================================================
    # cost calculation for every configuration

    dp_keys = [
        'vessel costs (€)',
        'tube costs (€)',
        'insulation costs (€)',
        'other steel parts costs (€)',
        'storage material costs (€)',
        'pump costs (€)',
        'motor costs (€)',
        'hx costs (€)',
        'valve costs (€)',
        'sensor costs (€)',
        'engineering costs (€)',
        'profit surcharge (€)',
        'total costs (€)']

    dim = res1 * res2 * res3

    Hlhts = 5  # Height lhts storage block (m)
    Wlhts = 10  # Width lhts storage block (m)
    Llhts = 12  # Length of lhts storage block (m)

    Hlhts = 2  # Height lhts storage block (m)
    Wlhts = 2  # Width lhts storage block (m)
    Llhts = 12  # Length of lhts storage block (m)

    Alhts = 2 * (Hlhts * Wlhts + Hlhts * Llhts + Wlhts * Llhts)
    Vlhts = Hlhts * Wlhts * Llhts

    areaInsulation = dp_all['total volume (m³)'] / Vlhts * Alhts

    for key in dp_keys:
        dp_all[key] = np.zeros(dim)


    dp_all['tube costs (€)'] = \
        cfc.c_tubes(2, dp_all['tube diameter (m)'].values*1000, dp_all['tube length (m)'].values, 'm', '304L')

    thickness = 3  #mm
    volume = areaInsulation*thickness/1000
    mass = volume*7850

    dp_all['vessel costs (€)'] = cfc.c_steel(1, thickness, mass.values)
    dp_all['number of storages'] = dp_all['total volume (m³)'] / Vlhts
    dp_all['total surface area (m²)'] = areaInsulation

    dp_all['insulation costs (€)'] = cfc.c_insulation(1, p_gen['temperature limits']['T_max'], areaInsulation, 1)


    dp_all['storage material costs (€)'] = \
        c_pcm * dp_all['storage material volume (m³)']


    dp_all['total vessel costs (€)'] = \
        dp_all[['tube costs (€)', 'vessel costs (€)', 'insulation costs (€)', 'other steel parts costs (€)', 'storage material costs (€)']].sum(axis=1)


    dp_all['valve costs (€)'] = dp_all['number of storages']*p_spec['cost parameters']['valves']
    dp_all['sensor costs (€)'] = dp_all['number of storages']*p_spec['cost parameters']['sensors']

    dp_all['additional equipment costs (€)'] = \
        dp_all[['pump costs (€)', 'valve costs (€)', 'sensor costs (€)']].sum(axis=1)

    # all internal costs
    dp_all['internal costs (€)'] = \
        dp_all[['total vessel costs (€)', 'additional equipment costs (€)', 'engineering costs (€)']].sum(axis=1)

    # total costs
    dp_all['profit surcharge (€)'] = \
        dp_all['internal costs (€)'] * 0.3  # fixme: right now dummy value


    dp_all['total costs (€)'] = \
        dp_all['internal costs (€)'] + dp_all['profit surcharge (€)']

    if show_plots & (solution is None):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        x = dp_all['capacity (kWh)'].values
        y = dp_all['max. heat load (kW)'].values
        z = dp_all['total costs (€)'].values
        ax.scatter(x, y, z)

        ax.set_xlabel('capacity (kWh)')
        ax.set_ylabel('maximum heat load (kW)')
        ax.set_zlabel('total costs (€)')


    # ==================================================================================================================
    # eliminate suboptimal data points

    if solution is not None:
        recover = 1
    else:
        recover = 0

    dp_red = suboptimal_datapoints(dp_all, p_gen, show_plots, recover)

    if solution is not None:
        dp_red.drop(dp_red[(dp_red['max. heat load (kW)'] < solution['max. heat load (kW)'])].index, inplace=True)
        dp_red.drop(dp_red[(dp_red['total costs (€)'] > np.min(dp_red['total costs (€)']))].index, inplace=True)


    if show_plots & (solution is None):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        x = dp_red['capacity (kWh)'].values
        y = dp_red['max. heat load (kW)'].values
        z = dp_red['total costs (€)'].values
        ax.scatter(x, y, z)

        ax.set_xlabel('capacity (kWh)')
        ax.set_ylabel('maximum heat load (kW)')
        ax.set_zlabel('total costs (€)')


    # if show_plots & (solution is None):
    #     plot_cost_structure(dp_red)

    # ==================================================================================================================
    # Calculate least-squares regression to obtain coeffs for the quadratic cost function
    if solution is None:
        X = dp_red['capacity (kWh)'].values
        Y = dp_red['max. heat load (kW)'].values
        B = dp_red['total costs (€)'].values

        if show_plots == 0:
            ax = None
        coeff, r2 = regression(X, Y, B, optimization_type, show_plots, ax)

        print(' ')
        print(' --- LHTS --- ')
        print('For LHTS, the average costs per kWh is {:.2f} €'.format(coeff[1]))
        print('For LHTS, the average costs per kW is {:.2f} €'.format(coeff[2]))
        print('-- coefficients:')
        for i, co in enumerate(coeff.tolist()):
            print('c{}: {:.3f}'.format(i, co))

        return coeff.tolist(), r2, dp_red
    else:
        return dp_red

def calc_costfun_lumenion(p_spec, p_gen, settings, solution=None):
    """
    Description:

    This script is used to obtain a linear or quadratic cost-function for the lumenion storage system.
    Costs for capacity (€/kWh), charging (€/kW) and discharging (€/kW) subsystems are calculated from given data.
    """

    sto_type = 'Lumenion'

    # show_plots = settings['plotting']['show_plots']
    # print_progress = settings['plotting']['print_progress']

    optimization_type = 'linear' # settings['optimization type']
    # max_cap_kWh = p_spec['integration parameters']['max capacity']

    # ==================================================================================================================

    #  Parameters
    # T_min = p_gen['temperature limits']['T_min']
    T_min = 130
    # T_max = p_gen['temperature limits']['T_max']
    T_max = 600

    # res1 = p_spec['approximation parameters']['res 1']  # discretization of temperature range

    # T = np.linspace(T_min, T_max, res1+1)[1:]

    # Auxiliary params for unit conversion
    kWh2Ws = 3.6 * 10 ** 6

    # ==================================================================================================================
    # Calculation Energy Capacity based on data

    import scipy.optimize

    tmin_nom = 309  # °C
    tmax_nom = 550  # °C
    dt_nom = tmax_nom - tmin_nom  # °C

    dt_actual = T_max - (T_min+100)  # °C

    cp_nom = 550  # kJ/kgK

    cap_correction = dt_actual/dt_nom

    if optimization_type == 'linear':
        def func(x, a, b):
            return a + b*x
    elif optimization_type == 'quadratic':
        def func(x, a, b, c):
            return a + b*x + c*x**2
    else:
        def func(x, a, b, c):
            return a + b*(x**c)

    def func_eval(x, coeffs, optimization_type):
        if optimization_type == 'linear':
            return coeffs[0] + coeffs[1]*x
        elif optimization_type == 'quadratic':
            return coeffs[0] + coeffs[1]*x + coeffs[2]*x**2
        else:
            return coeffs[0] + coeffs[1]*x**coeffs[2]


    def calc_fit(x,y, func):
        if optimization_type == 'linear':
            x0 = [10000, 100]
        else:
            x0 = [10000, 100, 0.9]
        popt, pcov = scipy.optimize.curve_fit(func, x, y, x0)
        return popt


    def prepare_approximation(input_dict, lim):
        keys = list(input_dict.keys())

        res = 10000
        input_dict_copy = input_dict.copy()

        x = [k for k in keys if 'power' in k or 'capacity' in k][0]
        costs = [k for k in keys if k != x]

        x_new = np.linspace(input_dict[x][0], input_dict[x][-1], res)
        input_dict_copy[x] = x_new

        for k in costs:
            input_dict_copy[k] = np.interp(input_dict_copy[x], input_dict[x], input_dict[k])

        input_dict = input_dict_copy

        input_dict['total_costs'] = input_dict[costs[0]]
        for k in costs[0:]:
            input_dict['total_costs'] += input_dict[k]

        keys = list(input_dict.keys())
        costs = [k for k in keys if k != x]

        plt.figure()
        for k in costs:
            plt.plot(input_dict[x], input_dict[k])

        coeffs = calc_fit(input_dict[x][np.where(input_dict[x]<=lim)], input_dict['total_costs'][np.where(input_dict[x]<=lim)], func)

        plt.plot(input_dict[x], func_eval(input_dict[x], coeffs, optimization_type))
        return input_dict, coeffs

    data_core = dict(
        storage_capacity=np.array([5, 10, 15, 20, 50, 100, 300, 380, 500, 1000]) * cap_correction * 1000,  #kWh, sensitive to temperature range
        storage_core=np.array([355, 729, 1055, 1247, 2780, 5240, 13500, 17130, 22400, 42700])*1000 * cap_correction,  #€, sensitive to temperature range
        storage_control=np.array([30, 60, 75, 100, 150, 240, 440, 500, 620, 950])*1000,  #€
        )

    data_core, coeffs_core = prepare_approximation(data_core, 1000*8)


    data_charging = dict(
        charging_power=np.array([1, 2, 3, 5, 7, 10, 15, 20, 30, 50]) * 1000,  #kW
        heating_elements=np.array([63.063, 126.126, 189.189, 315.315, 441.441, 630.631, 945.946, 1261.261, 1891.892, 3153.153])*1000,  #€
        heating_control=np.array([86.49, 114.21, 141.93, 197.39, 300, 330, 360, 400, 450, 500])*1000,  #€
    )

    data_charging, coeffs_charging = prepare_approximation(data_charging,2000)


    data_discharging = dict(
        discharging_power=np.array([0.1, 0.2, 0.5, 1, 2, 3, 5, 7, 10, 20]) * 1000,  #kW
        fans=np.array([50, 50, 80, 110, 200, 300, 450, 675, 1012.5, 1822.5])*1000,  #€, actually depends also on storage capacity
        ducts=np.array([100, 110, 130, 150, 180, 216, 259.2, 311.04, 373.248, 447.8976])*1000,  #€, actually depends also on storage capacity
        steam_generator=np.array([298.08, 331.2, 368, 460, 690, 828, 1159.2, 1506.96, 1959.048, 2938.572])*1000,  #€
    )

    data_discharging, coeffs_discharging = prepare_approximation(data_discharging, 700)

    # derive function c = f(cap, Q_c, Q_d)

    if optimization_type == 'linear':
        coeffs = [coeffs_core[0] + coeffs_charging[0] + coeffs_discharging[0],
                  coeffs_core[1],
                  coeffs_charging[1],
                  coeffs_discharging[1]]

    plt.show()

    coeffs = {'core': coeffs_core, 'charging':coeffs_charging, 'discharging': coeffs_discharging}
    return coeffs


def calc_costfun_ruths(p_spec, p_gen, settings, solution=None):
    """
    Description:

    This script is used to obtain a linear or quadratic cost-function for a Ruths steam storage system.
    Using given inputs, the geometry of the storage vessel and the corresponding capacities are calculated.
    A lot of data points (capacity/costs) are obtained which are then scaled to a capacity of 1 kWh
    Using this selection, new data points are extrapolated to cover the required domain for capacity and heat loads
    For these data-points a least-squares-regression is carried out 
    to obtain a (nonconvex) quadratic or linear cost-function.
    """

    sto_type = 'Ruths'

    from pi_framework.DOOM.CETES_Models.MSwork.AD2000_calc import shell_thickness, svalv_size
    from pi_framework.DOOM.CETES_Models.MSwork.PIPEWORK_calc import pipework_cfunc

    show_plots = settings['plotting']['show_plots']
    print_progress = settings['plotting']['print_progress']

    optimization_type = settings['optimization type']
    max_cap_kWh = p_spec['integration parameters']['max capacity']

    # ==================================================================================================================

    #  Parameters
    T_min = p_gen['temperature limits']['T_min']
    T_max = p_gen['temperature limits']['T_max']

    res1 = p_spec['approximation parameters']['res 1']  # discretization of temperature range

    T = np.linspace(T_min, T_max, res1+1)

    # Auxiliary params for unit conversion
    kWh2Ws = 3.6 * 10 ** 6

    # ==================================================================================================================
    # Calculation Energy Capacity
    T0 = 273.15
    x0 = 0.5

    T_ref = 20 + T0
    p_ref = 10**5
    h_ref = 84000  #cp.PropsSI('U', 'P', p_ref, 'T', T_ref, 'Water')

    dH = []
    T_end = []
    # T_start=[]
    for T_0 in T[1:]:
        f_0 = p_spec['construction']['f_0']
        p_0 = cp.PropsSI('P', 'T', T_0 + T0, 'Q', 0.5, 'Water')
        rho_d = cp.PropsSI('D', 'P', p_0, 'Q', 1, 'Water')
        rho_w = cp.PropsSI('D', 'P', p_0, 'Q', 0, 'Water')
        rho_ges = (rho_d * (1 - f_0) + rho_w * f_0)
        x_0 = rho_d * (1 - f_0) / rho_ges
        h_ges_0 = cp.PropsSI('H', 'P', p_0, 'Q', x_0, 'Water') - h_ref # J/kg
        h_ges_0v = h_ges_0 * rho_ges  # J/m³

        # T_start=[T_start T_0_C]

        rho_ges_new = rho_w * f_0  # density after all steam has been removed from the storage
        rho_d_new = rho_d
        f_new = f_0
        h_ges_v_new = h_ges_0v
        T_new_C = 1000
        h_sum = 0
        p_new = p_0
        while T_new_C >= min(T):
            h_d_v = (cp.PropsSI('H', 'P', p_new, 'Q', 1, 'Water') - h_ref) * rho_d_new * (1 - f_new)
            h_ges_v_new = h_ges_v_new - h_d_v
            h_sum = h_sum + h_d_v
            h_ges_new = h_ges_v_new / rho_ges_new

            x_new = cp.PropsSI('Q', 'D', rho_ges_new, 'H', h_ges_new+h_ref, 'Water')
            T_new = cp.PropsSI('T', 'D', rho_ges_new, 'H', h_ges_new+h_ref, 'Water')
            p_new = cp.PropsSI('P', 'D', rho_ges_new, 'H', h_ges_new+h_ref, 'Water')

            T_new_C = T_new - 273.15
            rho_d_new = cp.PropsSI('D', 'T', T_new, 'Q', 1, 'Water')
            f_new = 1 - x_new * rho_ges_new / rho_d_new

            rho_ges_new = cp.PropsSI('D', 'P', p_new, 'Q', 0, 'Water') * f_new

            print('f: {}, x: {}, T_0: {}°C, T_C: {}°C'.format(f_new, x_new, T_0, T_new_C))

        h_sum_ = h_sum / kWh2Ws
        dH.append(h_sum_)
        T_end.append(T_new_C)

    T = T[1:]
    coeffs_poly_dH = np.polyfit(T, dH, 3)  # 3rd degree polynomial fit for T as a function of dH
    poly_dH = np.poly1d(coeffs_poly_dH)  # volume specific enthalpy depending on max. temperature

    # =================================================================================================================

    # V_max = max(max_cap_kWh / poly_dH(T))
    # V_min = 1


    # available sizes for cylindrical vessels according to DACE Price Booklet Edition 33
    DACE_volumes = np.array([1, 5, 10, 20, 40, 60, 80, 100])  # m³
    DACE_length = np.array([1.1, 1.7, 2.1, 4.5, 5.2, 8, 10.9, 13.7])  # m
    DACE_diameter = np.array([1, 1.8, 2.3, 2.3, 3, 3, 3, 3])  # m

    S = p_spec['construction']['Safety coefficient']  # Safety Coefficient
    s1 = p_spec['construction']['s1']  # Minimum Wall Thickness Pressure Vessel



    # ==================================================================================================================
    # Correlation: Pressure/Temperature

    P = np.zeros(res1)

    for i in range(res1):
        P[i] = cp.PropsSI('P', 'T', T0 + T[i], 'Q', x0, 'Water')

    sig_ad_Nmm2 = p_spec['steel properties']['sig_ad']
    T_steel = p_spec['steel properties']['T_steel']
    sig_ad = sig_ad_Nmm2 * 10 ** 6 / S



    # ==================================================================================================================
    # Calculation Pressure Vessel Costs


    if solution is not None:
        res2 = 1
        cap_range = np.linspace(solution['capacity (kWh)'], solution['capacity (kWh)'], res2)
        # load_range = np.linspace(solution['max. heat load (kW)'], solution['max. heat load (kW)'], res2)
    else:
        res2 = p_spec['approximation parameters']['res 2']  # discretization of capacity range
        cap_range = np.linspace(1, max_cap_kWh, res2)
        # load_range = np.linspace(1, max_cap_kWh*p_gen['storage limits']['ratio'], res2)

    res3 = p_spec['approximation parameters']['res 3']  # discretization of heat load range

    dim = res1 * res2 * res3

    # Build Dataframe:
    dp_all = pd.DataFrame({
        'max. heat load (kW)': np.zeros(dim),
        'capacity (kWh)': np.zeros(dim),
        'material': np.zeros(dim),
        'total volume (m³)': np.zeros(dim),
        'min. temperature (°C)': np.zeros(dim),
        'min. thickness (m)': np.zeros(dim),
        'admissible tension (N/m²)': np.zeros(dim),
        'max. temperature (°C)': np.zeros(dim),
        'max. pressure (Pa)': np.zeros(dim),
    })

    dp_all['material'] = dp_all['material'].astype(str)

    c = 0
    for j, cap in enumerate(cap_range):
        for i, T_i in enumerate(T):
            for load in np.linspace(cap*p_gen['storage limits']['ratio']*0.1, cap*p_gen['storage limits']['ratio'], res3):
                vol = cap / poly_dH(T_i)

                n_sto_min = np.ceil(vol / max(DACE_volumes))
                L = np.interp(vol / n_sto_min, DACE_volumes, DACE_length)
                D = np.interp(vol / n_sto_min, DACE_volumes, DACE_diameter)

                # dp_all['admissible tension (N/m²)'][c] = np.interp(T_i, T_steel, sig_ad)
                # dp_all['min. thickness (m)'][c] = (P[i] * D) / (2 * dp_all['admissible tension (N/m²)'][c]) + s1
                # print(dp_all['min. thickness (m)'][c])
                dp_all.at[c, 'material'] = 'S355JR'
                dp_all.at[c, 'min. thickness (m)'] = shell_thickness(D*1000, T_i, P[i]/10**5, dp_all['material'][c])/1000  # calculations according to AD2000 norm
                # print(dp_all['min. thickness (m)'][c])
                dp_all.at[c, 'total volume (m³)'] = vol
                dp_all.at[c, 'capacity (kWh)'] = cap
                dp_all.at[c, 'max. heat load (kW)'] = load
                dp_all.at[c, 'max. temperature (°C)'] = T_i
                dp_all.at[c, 'max. pressure (Pa)'] = P[i]
                dp_all.at[c, 'min. temperature (°C)'] = T_min
                c += 1

                if print_progress:
                    if c == 1:
                        print('Generation of data points Ruths:')

                    tot = dim
                    prog = c / tot * 100
                    inc = 10
                    if c % (tot / inc) <= ((tot / inc) % 1):
                        print('{:.2F} %'.format(prog))




    # cost calculation for every configuration

    dp_keys = [
        'vessel costs (€)',
        'tube costs (€)',
        'insulation costs (€)',
        'other steel parts costs (€)',
        'storage material costs (€)',
        'pump costs (€)',
        'motor costs (€)',
        'hx costs (€)',
        'valve costs (€)',
        'sensor costs (€)',
        'engineering costs (€)',
        'profit surcharge (€)',
        'total costs (€)']

    for key in dp_keys:
        dp_all[key] = np.zeros(dim)


    for c in range(len(dp_all)):
        dp_all.at[c, 'vessel costs (€)'], dp_all.at[c, 'number of storages'], dp_all.at[c, 'total surface area (m²)'],_ = \
            cfc.c_cylindrical_storage_vessels(dp_all['total volume (m³)'][c], dp_all['min. thickness (m)'][c] * 1000,
                                              'carbon steel', 3)
        dp_all.at[c, 'insulation costs (€)'] = cfc.c_insulation(2, dp_all['max. temperature (°C)'][c], dp_all['total surface area (m²)'][c], 1.1)

    dp_all['total vessel costs (€)'] = \
        dp_all[['tube costs (€)', 'vessel costs (€)', 'insulation costs (€)', 'other steel parts costs (€)',
         'storage material costs (€)']].sum(axis=1)

    for c in range(len(dp_all)):
        load = dp_all['max. heat load (kW)'][c] / (cp.PropsSI('H', 'P', dp_all['max. pressure (Pa)'][c], 'Q', 1, 'Water')/1000) * 3600  # steam flow (kg/h)
        dp_all.at[c, 'valve costs (€)'] = pipework_cfunc(load, 0, dp_all['max. temperature (°C)'][c], dp_all['max. pressure (Pa)'][c]/10**5, material_select=dp_all['material'][c], n_sto=dp_all['number of storages'][c], op_mode_select='parallel', ball_valve_DN=50, verbose=False)

    dp_all['additional equipment costs (€)'] = dp_all[
        ['pump costs (€)', 'valve costs (€)', 'sensor costs (€)']].sum(axis=1)

    # all internal costs
    dp_all['internal costs (€)'] = dp_all[
        ['total vessel costs (€)', 'additional equipment costs (€)', 'engineering costs (€)']].sum(axis=1)

    # total costs
    dp_all['profit surcharge (€)'] = dp_all[
                                                  'internal costs (€)'] * 0.3  # fixme: right now dummy value
    dp_all['total costs (€)'] = dp_all['internal costs (€)'] + dp_all['profit surcharge (€)']

    if show_plots & (solution is None):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        x = dp_all['capacity (kWh)'].values
        y = dp_all['max. heat load (kW)'].values
        z = dp_all['total costs (€)'].values
        ax.scatter(x, y, z)

        ax.set_xlabel('capacity (kWh)')
        ax.set_ylabel('maximum heat load (kW)')
        ax.set_zlabel('total costs (€)')


    # ==================================================================================================================
    # eliminate suboptimal data points
    dp_all['capacity (kWh)'] = dp_all['capacity (kWh)'].round(5)
    dp_all.drop(dp_all[dp_all['capacity (kWh)'] > round(max_cap_kWh, 5)].index, inplace=True)

    dp_red = dp_all.copy()

    for cap in np.unique(dp_all['capacity (kWh)'].values)[:]:
        min_costs = np.min(dp_all[dp_all['capacity (kWh)'] == cap]['total costs (€)'])
        dp_red.drop(dp_red[(dp_red['capacity (kWh)'] <= cap) & (dp_red['total costs (€)'] > min_costs)].index, inplace=True)

        if solution is not None:
            dp_red.drop(dp_red[(dp_red['total costs (€)'] > min_costs)].index,
                        inplace=True)

    if solution is not None:
        recover = 1
    else:
        recover = 0

    dp_red = suboptimal_datapoints(dp_all, p_gen, show_plots, recover)

    if show_plots & (solution is None):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        x = dp_red['capacity (kWh)'].values
        y = dp_red['max. heat load (kW)'].values
        z = dp_red['total costs (€)'].values
        ax.scatter(x, y, z)

        ax.set_xlabel('capacity (kWh)')
        ax.set_ylabel('maximum heat load (kW)')
        ax.set_zlabel('total costs (€)')


    # if show_plots & (solution is None):
    #     plot_cost_structure(dp_red)

    # ==================================================================================================================
    # Calculate least-squares regression to obtain coeffs for the quadratic cost function

    if solution is None:
        X = dp_red['capacity (kWh)'].values
        Y = dp_red['max. heat load (kW)'].values
        B = dp_red['total costs (€)'].values

        if show_plots == 0:
            ax = None
        coeff, r2 = regression(X, Y, B, optimization_type, show_plots, ax)

        print(' ')
        print(' --- Ruths steam storage --- ')
        print('For Ruths storages, the average costs per kWh is {:.2f} €'.format(coeff[1]))
        print('For Ruths storages, the average costs per kW is {:.2f} €'.format(coeff[2]))
        print('-- coefficients:')
        for i, co in enumerate(coeff.tolist()):
            print('c{}: {:.3f}'.format(i, co))

        return coeff.tolist(), r2, dp_red
    else:
        return dp_red


def calc_costfun_moltensalt(p_spec, p_gen, settings, solution=None):
    sto_type = 'molten salt'

    optimization_type = settings['optimization type']
    max_cap_kWh = p_spec['integration parameters']['max capacity']

    import operator
    show_plots = settings['plotting']['show_plots']
    print_progress = settings['plotting']['print_progress']

    if solution is None:
        res1 = p_spec['approximation parameters']['res 1']  # discretization of capacity range
        res2 = p_spec['approximation parameters']['res 1']  # discretization of heat load range
        cap_range = np.linspace(1, max_cap_kWh, res1)
    else:
        res1 = 1
        res2 = res1
        cap_range = np.linspace(solution['capacity (kWh)'], solution['capacity (kWh)'], res1)

    Tsalt_min = np.max([p_gen['temperature limits']['T_min'], p_spec['Salt parameters']['Tfreeze']])
    Tsalt_max = p_gen['temperature limits']['T_max']
    #Tsteam = p_gen['temperature limits']['T_steam']
    p_water = p_gen['temperature limits']['p_water']
    #T_salt = np.linspace(Tsalt_min, Tsalt_max, res1)

    Tsalt_ave = (Tsalt_max + Tsalt_min) / 2
    cp_ave = -0.8611 * Tsalt_ave + 1922.8
    rho_ave = -0.0018 * Tsalt_ave ** 2 + 0.1438 * Tsalt_ave + 2254.7

    dim = res1 * res2

    # available sizes for cylindrical vessels according to DACE Price Booklet Edition 33
    DACE_volumes = np.array([1, 5, 10, 20, 40, 60, 80, 100])  # m³
    DACE_length = np.array([1.1, 1.7, 2.1, 4.5, 5.2, 8, 10.9, 13.7])  # m
    DACE_diameter = np.array([1, 1.8, 2.3, 2.3, 3, 3, 3, 3])  # m

    volume = np.zeros(dim)
    vessel_costs = np.zeros(dim)
    storage_material_costs = np.zeros(dim)
    pump_costs = np.zeros(dim)
    elmotor_costs = np.zeros(dim)
    n_storages = np.zeros(dim)
    surface_area = np.zeros(dim)
    capacity = np.zeros(dim)
    load = np.zeros(dim)
    insulation_HT = np.zeros(dim)
    insulation_LT = np.zeros(dim)
    hx_evap_costs = np.zeros(dim)
    n_hx_evap = np.zeros(dim)

    # Includes: tank, pump, electric motor, heat exchangers
    c = 0
    for j, cap in enumerate(cap_range):
        if solution is None:
            load_range = np.linspace(0.1*cap*p_gen['storage limits']['ratio'], cap*p_gen['storage limits']['ratio'], res2)
        else:
            load_range = np.linspace(solution['max. heat load (kW)'], solution['max. heat load (kW)'], res2)

        for i, ld in enumerate(load_range):
            # Salt mass for each capacity
            mass = cap * 3600 * 1000 / (cp_ave * (Tsalt_max - Tsalt_min))  # Maximum total salt mass, to cover the entire capacity
            # Tank volume PER TANK (one hot, one cold)
            vol = mass / rho_ave  # fixed
            mflow_salt = ld * 1000 / (cp_ave * (Tsalt_max - Tsalt_min))  # in kg/s
            vflow_salt = mflow_salt / rho_ave * 3600  # in m3/h


            # STORAGE TANK COST
            volume[c] = vol  # fixed
            vessel_costs[c], n_storages[c], surface_area[c] = cfc.c_vertical_storage_tanks(1, vol, verbose=False)
            storage_material_costs[c] = mass * p_spec['Salt parameters'][
                'c_salt']  # Should include economy of scale
            insulation_HT[c] = cfc.c_insulation(2, Tsalt_max, surface_area[c], 1.1)
            insulation_LT[c] = cfc.c_insulation(2, Tsalt_min, surface_area[c], 1.1)


            # HEAT EXCHANGER COSTS
            # Includes pre-heater + evaporator
            d_i = 0.02  # inner tube diameter, in m
            thick = 0.0015  # tube thickness
            d_o = d_i + 2 * thick  # outer tube diameter, in m

            h_s_start = cp.PropsSI('H', 'P', p_water, 'Q', 0, 'water')  # start enthalpy for evaporating water (saturated) in J/kg*K
            h_s_final = cp.PropsSI('H', 'P', p_water, 'Q', 1, 'water')  # final enthalpy for water (saturated steam) in J/kg*K
            h_total = np.linspace(h_s_start, h_s_final, res1)

            T_water = cp.PropsSI('T', 'H', h_total, 'P', p_water, 'water') - 273.15  # temperature curve for water in degC

            # HX area and number of tubes approximated based on a linear correlation as a function of load, based on previous calculations
            # Polynomial fit may have been more accurate, but would eventually lead to decreasing and even negative area
            Ahx_evap = 0.0003*ld/n_storages[c] + 5.9265
            hx_evap_costs[c], n_hx_evap[c] = cfc.c_heat_exchangers(4, Ahx_evap, 'AISI 304')
            hx_evap_costs[c] = hx_evap_costs[c]*n_storages[c]
            n_hx_evap[c] = n_hx_evap[c]*n_storages[c]

            # PUMP COSTS BASED ON PRESSURE DROP IN THE HXs
            # Number of tubes related to pressure loss through the nr of tube rows the fluids need to pass

            #Evaporator
            # Assumed U-type HX -> nr of tube rows the fluid passes multiplied with two
            k_bdl = 0.249
            n_bdl = 2.207
            ntubes_evap = np.round(0.0008*ld/n_storages[c] + 30.612)
            d_bdl_evap = d_o * (2*ntubes_evap / k_bdl) ** (1 / n_bdl)


            htc_salt_evap, dp_evap = htc_saltHX.calcHTCsalt(1.1 * d_bdl_evap, d_o, mflow_salt/n_storages[c], Tsalt_ave, 2*ntubes_evap)

            dp_hx = dp_evap/1e5
            pump_costs[c] = (cfc.c_pumps(vflow_salt/n_storages[c], dp_hx, 'cast iron')*n_storages[c])
            elmotor_costs[c] = (cfc.c_elmotor(vflow_salt/n_storages[c], ld/n_storages[c], p_spec['Unit conversion'])*n_storages[c])

            capacity[c] = cap
            load[c] = ld

            c += 1

            if print_progress:
                if c == 1:
                    print('Generation of data points Molten Salt:')

                tot = cap_range.__len__() * res1
                prog = c / tot * 100
                inc = 10
                if c % (tot / inc) <= ((tot / inc) % 1):
                    print('{:.2F} %'.format(prog))

    # Build Dataframe:

    # Vessel costs and number of vessels in total, incl. hot and cold tanks
    dp_all = pd.DataFrame({
        'max. heat load (kW)': load,
        'capacity (kWh)': capacity,
        # 'total volume (m³)': volume
        'total volume (m³)': volume * 2
    })
    # idx_min = np.argmin(vessel_costs / capacity)

    # ==================================================================================================================
    # cost calculation for every configuration

    dp_keys = [
        'vessel costs (€)',
        'tube costs (€)',
        'insulation costs (€)',
        'other steel parts costs (€)',
        'storage material costs (€)',
        'pump costs (€)',
        'motor costs (€)',
        'hx costs (€)',
        'valve costs (€)',
        'sensor costs (€)',
        'engineering costs (€)',
        'profit surcharge (€)',
        'total costs (€)']

    for key in dp_keys:
        dp_all[key] = np.zeros(dim)

    dp_all['vessel costs (€)'] = vessel_costs * 2
    dp_all['number of storages'] = n_storages * 2
    dp_all['total surface area (m²)'] = surface_area * 2
    dp_all['insulation costs (€)'] = insulation_HT + insulation_LT
    dp_all['storage material costs (€)'] = storage_material_costs

    dp_all['total vessel costs (€)'] = dp_all[
        ['tube costs (€)', 'vessel costs (€)', 'insulation costs (€)', 'other steel parts costs (€)',
         'storage material costs (€)']].sum(axis=1)

    # costs for additional equipment
    dp_all['pump costs (€)'] = pump_costs
    dp_all['motor costs (€)'] = elmotor_costs
    dp_all['hx costs (€)'] = hx_evap_costs*n_hx_evap

    dp_all['valve costs (€)'] = dp_all['number of storages']*p_spec['Cost parameters']['valves']
    dp_all['sensor costs (€)'] = dp_all['number of storages']*p_spec['Cost parameters']['sensors']

    dp_all['additional equipment costs (€)'] = dp_all[
        ['pump costs (€)', 'motor costs (€)', 'hx costs (€)', 'valve costs (€)', 'sensor costs (€)']].sum(axis=1)

    # all internal costs
    dp_all['internal costs (€)'] = dp_all[
        ['total vessel costs (€)', 'additional equipment costs (€)', 'engineering costs (€)']].sum(axis=1)

    # total costs
    dp_all['profit surcharge (€)'] = dp_all[
                                                  'internal costs (€)'] * 0.3  # fixme: right now dummy value
    dp_all['total costs (€)'] = dp_all['internal costs (€)'] + dp_all['profit surcharge (€)']

    if show_plots & (solution is None):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        x = dp_all['capacity (kWh)'].values
        y = dp_all['max. heat load (kW)'].values
        z = dp_all['total costs (€)'].values
        ax.scatter(x, y, z)

        ax.set_xlabel('capacity (kWh)')
        ax.set_ylabel('maximum heat load (kW)')
        ax.set_zlabel('total costs (€)')


    # ==================================================================================================================
    # eliminate suboptimal data points
    if solution is not None:
        recover = 1
    else:
        recover = 0

    dp_red = suboptimal_datapoints(dp_all, p_gen, show_plots, recover)

    if show_plots & (solution is None):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        x = dp_red['capacity (kWh)'].values
        y = dp_red['max. heat load (kW)'].values
        z = dp_red['total costs (€)'].values
        ax.scatter(x, y, z)

        ax.set_xlabel('capacity (kWh)')
        ax.set_ylabel('maximum heat load (kW)')
        ax.set_zlabel('total costs (€)')


    # if show_plots & (solution is None):
    #     plot_cost_structure(dp_red)

    # ==================================================================================================================
    # Calculate least-squares regression to obtain coeffs for the quadratic cost function

    if solution is None:
        X = dp_red['capacity (kWh)'].values
        Y = dp_red['max. heat load (kW)'].values
        B = dp_red['total costs (€)'].values

        if show_plots == 0:
            ax = None
        coeff, r2 = regression(X, Y, B, optimization_type, show_plots, ax)

        print(' ')
        print(' --- Molten salt storage --- ')
        print('For Molten salt storages, the average costs per kWh is {:.2f} €'.format(coeff[1]))
        print('For Molten salt storages, the average costs per kW is {:.2f} €'.format(coeff[2]))
        print('-- coefficients:')
        for i, co in enumerate(coeff.tolist()):
            print('c{}: {:.3f}'.format(i, co))

        return coeff.tolist(), r2, dp_red
    else:
        return dp_red


def calc_costfun_concrete(p_spec, p_gen, settings, solution=None):
    sto_type = 'concrete'

    show_plots = settings['plotting']['show_plots']
    show_sim_plots = settings['plotting']['show_sim_plots']
    print_progress = settings['plotting']['print_progress']

    optimization_type = settings['optimization type']
    max_cap_kWh = p_spec['integration parameters']['max capacity']

    # ==================================================================================================================

    #  Parameters
    tube_wall = p_spec['Storage geometry']['tube_wall']

    c_concrete = p_spec['Cost parameters']['c concrete']

    # Auxiliary params for unit conversion
    kWh2Ws = 3.6 * 10 ** 6

    # INPUT
    max_cap_Ws = max_cap_kWh * kWh2Ws  # Ws


    # ==================================================================================================================
    #  Variation of tube diameter and layer thickness -> DATA POINTS for COST FUNCTION

    res1 = p_spec['approximation parameters']['res 1']  # number of variations for tube diameter
    res2 = p_spec['approximation parameters']['res 2']  # number of variations for concrete layer thickness

    # Build Dataframe:
    dim = res1*res2
    dp_var = pd.DataFrame({
        'max. heat load (kW)': np.zeros(dim),
        'capacity (kWh)': np.zeros(dim),
        'total volume (m³)': np.zeros(dim),
        'storage material volume (m³)': np.zeros(dim),
        'tube volume (m³)': np.zeros(dim),
        'tube length (m)': np.zeros(dim),
        'storage material fraction': np.zeros(dim),
        'tube diameter (m)': np.zeros(dim),
        'storage material layer fraction': np.zeros(dim)
    })

    c = 0
    for i, dia in enumerate(steps_geom_series(res1, p_spec['Storage geometry']['tube_diameters_range'])):
        for j, layer in enumerate(steps_geom_series(res2, p_spec['Storage geometry']['concrete_layer_fract_range'])):
            nodes = p_spec['approximation parameters']['number of nodes']
            dp_var['max. heat load (kW)'][c], dp_var['capacity (kWh)'][c] = simulate_concrete_pcm(dia, layer, p_spec, p_gen, nodes, show_sim_plots)
            dp_var['total volume (m³)'][c] = ((dia * (1 + layer)) / 2) ** 2 * np.pi
            dp_var['storage material volume (m³)'][c] = (dia * (1 + layer) / 2) ** 2 * np.pi - (dia / 2) ** 2 * np.pi
            dp_var['tube volume (m³)'][c] = (dia / 2) ** 2 * np.pi - (
                        (dia - 2 * tube_wall) / 2) ** 2 * np.pi  # not used
            dp_var['tube length (m)'][c] = 1
            dp_var['storage material fraction'][c] = dp_var['storage material volume (m³)'][c] / dp_var['total volume (m³)'][c]
            dp_var['tube diameter (m)'][c] = dia
            dp_var['storage material layer fraction'][c] = layer

            c += 1

            if print_progress:
                if c == 1:
                    print('Generation of data points Concrete:')

                tot = res1 * res2
                prog = c / tot * 100
                inc = 10
                if c % (tot / inc) <= ((tot / inc) % 1):
                    print('{:.2F} %'.format(prog))

    # ==================================================================================================================
    # rescale and extend data points

    if solution is None:
        rescale_factor = max_cap_Ws / kWh2Ws / dp_var['capacity (kWh)'].values
    else:
        rescale_factor = solution['capacity (kWh)'] / dp_var['capacity (kWh)'].values

    select_cols = [
        'max. heat load (kW)',
        'capacity (kWh)',
        'total volume (m³)',
        'storage material volume (m³)',
        'tube volume (m³)',
        'tube length (m)',
    ]

    if solution is None:
        res3 = p_spec['approximation parameters']['res 3']  # discretization of capacity range
        dp_all = rescale(dp_var, select_cols, rescale_factor, res3)
    else:
        res3 = 1
        dp_all = rescale(dp_var, select_cols, rescale_factor, res3)

    # ==================================================================================================================
    # cost calculation for every configuration

    dp_keys = [
        'vessel costs (€)',
        'tube costs (€)',
        'insulation costs (€)',
        'other steel parts costs (€)',
        'storage material costs (€)',
        'pump costs (€)',
        'motor costs (€)',
        'hx costs (€)',
        'valve costs (€)',
        'sensor costs (€)',
        'engineering costs (€)',
        'profit surcharge (€)',
        'total costs (€)']

    dim = res1*res2*res3

    Hconcrete = 5  # Height concrete storage block (m)
    Wconcrete = 10  # Width concrete storage block (m)
    Lconcrete = 12  # Length of concrete storage block (m)

    Hconcrete = 2  # Height concrete storage block (m)
    Wconcrete = 2  # Width concrete storage block (m)
    Lconcrete = 12  # Length of concrete storage block (m)

    Aconcrete = 2 * (Hconcrete * Wconcrete + Hconcrete * Lconcrete + Wconcrete * Lconcrete)
    Vconcrete = Hconcrete * Wconcrete * Lconcrete

    extraAreaInsulation = 20  # percent of insulation area covering void zones
    areaInsulation = (1 + extraAreaInsulation / 100) * 2 * (Hconcrete * Wconcrete + dp_all['total volume (m³)'] * (Hconcrete + Wconcrete) / (Hconcrete * Wconcrete))  # Considering a given height and width, the length is dependent on total volume. Added XX more area of insulation for dead volumes between tubes
    areaInsulation = (1 + extraAreaInsulation / 100) * dp_all['total volume (m³)'] / Vconcrete * Aconcrete

    for key in dp_keys:
        dp_all[key] = np.zeros(dim)

    dp_all['tube costs (€)'] = cfc.c_tubes(2, dp_all['tube diameter (m)'].values * 1000,
                                           dp_all['tube length (m)'].values, 'm', '304L')

    # dp_all['insulation costs (€)'] = cfc.c_insulation(1, p_gen['temperature limits']['T_max'], dp_all['total volume (m³)']**(1/3)*6, 1, 'True')
    # dp_all['insulation costs (€)'] = dp_all['capacity (kWh)'] * cfc.c_insulation(1, p_gen['temperature limits']['T_max'], 52, 1, 'True') / 1000  # #Using calculated amount of insulation per MWh/1000 based on EnergyNest module geometry (a stack of 2m*12m*2m gives 2MWh)
    areaInsulation = (1 + p_spec['Storage geometry']['insulation void zones'] / 100) * 2 * (
                p_spec['Storage geometry']['height concrete storage'] * p_spec['Storage geometry']['width concrete storage'] + dp_all['total volume (m³)'] * (p_spec['Storage geometry']['height concrete storage'] + p_spec['Storage geometry']['width concrete storage']) / (
                    p_spec['Storage geometry']['height concrete storage'] * p_spec['Storage geometry']['width concrete storage']))  # Considering a given height and width, the length is dependent on total volume. Added XX% more area of insulation for dead volumes between tubes

    dp_all['insulation costs (€)'] = cfc.c_insulation(1, p_gen['temperature limits']['T_max'], areaInsulation, 1, 'True')
    dp_all['other steel parts costs (€)'] = cfc.c_steel(1, 5, dp_all['total volume (m³)'] * p_spec['Storage geometry']['steel structure factor'], 'True')

    dp_all['storage material costs (€)'] = c_concrete * dp_all['storage material volume (m³)'] / p_spec['Concrete parameters']['effective use of T range']
    # dp_all['storage material costs (€)'] = c_concrete * dp_all['storage material volume (m³)']

    dp_all['total vessel costs (€)'] = dp_all[
        ['vessel costs (€)', 'tube costs (€)', 'insulation costs (€)', 'other steel parts costs (€)',
         'storage material costs (€)']].sum(axis=1)

    dp_all['number of storages'] = dp_all['total volume (m³)'] / Vconcrete

    dp_all['valve costs (€)'] = dp_all['number of storages']*p_spec['Cost parameters']['valves']
    dp_all['sensor costs (€)'] = dp_all['number of storages']*p_spec['Cost parameters']['sensors']

    dp_all['additional equipment costs (€)'] = dp_all[
        ['pump costs (€)', 'valve costs (€)', 'sensor costs (€)']].sum(axis=1)

    # all internal costs
    dp_all['internal costs (€)'] = dp_all[
        ['total vessel costs (€)', 'additional equipment costs (€)', 'engineering costs (€)']].sum(axis=1)

    # total costs
    dp_all['profit surcharge (€)'] = dp_all['internal costs (€)'] * 0.3  # fixme: right now dummy value
    dp_all['total costs (€)'] = dp_all['internal costs (€)'] + dp_all['profit surcharge (€)']

    if show_plots & (solution is None):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        x = dp_all['capacity (kWh)'].values
        y = dp_all['max. heat load (kW)'].values
        z = dp_all['total costs (€)'].values
        ax.scatter(x, y, z)

        ax.set_xlabel('capacity (kWh)')
        ax.set_ylabel('maximum heat load (kW)')
        ax.set_zlabel('total costs (€)')

    # ==================================================================================================================
    # eliminate suboptimal data points
    if solution is not None:
        recover = 1
    else:
        recover = 0

    dp_red = suboptimal_datapoints(dp_all, p_gen, show_plots, recover)

    if solution is not None:
        dp_red.drop(dp_red[(dp_red['max. heat load (kW)'] < solution['max. heat load (kW)'])].index, inplace=True)
        dp_red.drop(dp_red[(dp_red['total costs (€)'] > min(dp_red['total costs (€)']))].index, inplace=True)


    if show_plots & (solution is None):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        x = dp_red['capacity (kWh)'].values
        y = dp_red['max. heat load (kW)'].values
        z = dp_red['total costs (€)'].values
        ax.scatter(x, y, z)

        ax.set_xlabel('capacity (kWh)')
        ax.set_ylabel('maximum heat load (kW)')
        ax.set_zlabel('total costs (€)')

    # if show_plots & (solution is None):
    #     plot_cost_structure(dp_red)

    # ==================================================================================================================
    # Calculate least-squares regression to obtain coeffs for the quadratic cost function
    if solution is None:
        X = dp_red['capacity (kWh)'].values
        Y = dp_red['max. heat load (kW)'].values
        B = dp_red['total costs (€)'].values

        if show_plots == 0:
            ax = None
        coeff, r2 = regression(X, Y, B, optimization_type, show_plots, ax)

        print(' ')
        print(' --- Concrete --- ')
        print('For Concrete, the average costs per kWh is {:.2f} €'.format(coeff[1]))
        print('For Concrete, the average costs per kW is {:.2f} €'.format(coeff[2]))
        print('-- coefficients:')
        for i, co in enumerate(coeff.tolist()):
            print('c{}: {:.3f}'.format(i, co))

        return coeff.tolist(), r2, dp_red
    else:
        return dp_red


def plot_costfun(param_specific_list, case_study, settings):

    res = 50

    cost_list = []
    cap_list = []
    hl_list = []

    min_cost = np.ones((res, res)) * 10000000000

    for sto in param_specific_list:
        max_capacity = sto['integration parameters']['max capacity']
        max_heat_load = max_capacity * case_study['storage limits']['ratio']

        capacity = np.linspace(0, max_capacity, res)
        heat_load = np.linspace(0, max_heat_load, res)

        CAP, HL = np.meshgrid(capacity, heat_load)

        coeffs = sto['integration parameters']['cost coefficients']

        if settings['optimization type'] == 'linear':
            COSTS = coeffs[0] + CAP * coeffs[1] + HL * coeffs[2]
        elif settings['optimization type'] == 'quadratic':
            COSTS = coeffs[0] + CAP * coeffs[1] + HL * coeffs[2] + CAP ** 2 * coeffs[3] + HL ** 2 * coeffs[
                4] + HL * CAP * coeffs[5]

        min_cost = np.minimum(min_cost, COSTS)

        cost_list.append(COSTS)
        cap_list.append(CAP)
        hl_list.append(HL)

    show_3d_plot = 1
    if show_3d_plot:
        plots = []
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for i, s in enumerate(param_specific_list):
            # if i > 0:
                x = np.where((HL <= CAP * case_study['storage limits']['ratio']), cap_list[i], np.nan)
                y = np.where((HL <= CAP * case_study['storage limits']['ratio']), hl_list[i], np.nan)
                z = np.where((HL <= CAP * case_study['storage limits']['ratio']), cost_list[i], np.nan)
                plot = ax.scatter(x, y, z, label=s['Type'])
                plots.append(plot)

        plt.legend(handles=plots)
        plt.title('cheapest storage technology')
        ax.set_xlabel('capacity (kWh)')
        ax.set_ylabel('maximum heat load (kW)')
        ax.set_zlabel('total costs (€)')

    plots = []
    plt.figure('cheapest')
    for i, s in enumerate(param_specific_list):
        x = np.where((cost_list[i] == min_cost) & (HL <= CAP * case_study['storage limits']['ratio']), CAP, np.nan)
        y = np.where((cost_list[i] == min_cost) & (HL <= CAP * case_study['storage limits']['ratio']), HL, np.nan)
        plot = plt.scatter(x, y, label=s['Type'])
        plots.append(plot)

    plt.legend(handles=plots)
    plt.title('cheapest storage technology')
    plt.xlabel('capacity (kWh)')
    plt.ylabel('maximum heat load (kW)')


    labels = ['Low Cap./Low HL', 'High Cap./Low HL', 'High Cap./High HL']
    fig, ax = plt.subplots()
    nr_sto = len(param_specific_list)
    labels_idx = [i for i in range(3)]

    x = np.where((HL <= CAP * case_study['storage limits']['ratio']), cap_list[0], np.nan)
    y = np.where((HL <= CAP * case_study['storage limits']['ratio']), hl_list[0], np.nan)

    cap_range = np.linspace(np.nanmin(x), np.nanmax(x), 3)
    hl_range = np.linspace(np.nanmin(y), np.nanmax(y), 3)

    x_nonan = x.flatten()[~np.isnan(x.flatten())]
    y_nonan = y.flatten()[~np.isnan(y.flatten())]

    box = [(x_nonan >= cap_range[0]) & (x_nonan < cap_range[1]) & (y_nonan >= hl_range[0]) & (y_nonan < hl_range[1]),
           (x_nonan >= cap_range[1]) & (x_nonan <= cap_range[2]) & (y_nonan >= hl_range[0]) & (y_nonan < hl_range[1]),
           (x_nonan >= cap_range[1]) & (x_nonan <= cap_range[2]) & (y_nonan >= hl_range[1]) & (y_nonan <= hl_range[2])]

    costs = [np.where((HL <= CAP * case_study['storage limits']['ratio']), cost_list[i], np.nan).flatten() for i in range(nr_sto)]
    for i in range(nr_sto):
        costs[i] = costs[i][~np.isnan(costs[i])]

    ylim = np.max(costs)

    if ylim > 10 ** 6:
        fact = 10 ** 6
        unit_string = 'M€'
    elif (ylim <= 10 ** 6) & (ylim > 10 ** 3):
        fact = 10 ** 3
        unit_string = 'k€'
    else:
        fact = 10 ** 0
        unit_string = '€'

    for i in range(nr_sto):
        ax.bar(np.array(labels_idx) + i/(nr_sto+1) - (nr_sto-1)/(nr_sto+1)/2, np.array([np.mean(costs[i][box[j]]) for j in range(3)])/fact, width=1/(nr_sto+1), label=param_specific_list[i]['Type'])

    plt.legend()
    plt.ylabel('Costs ({})'.format(unit_string))
    plt.xticks(labels_idx, labels)



def compute_r2_score(y, f):
    # Calculate R^2 explicitly
    yminusf2 = (y - f) ** 2
    sserr = sum(yminusf2)
    mean = float(sum(y)) / float(len(y))
    yminusmean2 = (y - mean) ** 2
    sstot = sum(yminusmean2)
    R2 = 1. - (sserr / sstot)
    return R2


def regression(X, Y, B, optimization_type, show_plots, ax, force_zero=0):
    if force_zero:
        d = 0
    else:
        d = 1
    if optimization_type == 'quadratic':
        A = np.array([X * 0 + d, X, Y, X ** 2, Y ** 2, X * Y]).T
    elif optimization_type == 'linear':
        A = np.array([X * 0 + d, X, Y]).T

    coeff, r, rank, s = np.linalg.lstsq(A, B, rcond=-1)

    def poly2Dreco(X, Y, c):
        if optimization_type == 'quadratic':
            return (c[0] + X * c[1] + Y * c[2] + X ** 2 * c[3] + Y ** 2 * c[4] + X * Y * c[5])
        elif optimization_type == 'linear':
            return (c[0] + X * c[1] + Y * c[2])

    res_fit = 20

    x_new = np.linspace(0, max(X), res_fit)
    y_new = np.linspace(0, max(Y), res_fit)

    if show_plots:
        X_new, Y_new = np.meshgrid(x_new, y_new)
        ax.scatter(X_new, Y_new, poly2Dreco(X_new, Y_new, coeff))

    r2 = compute_r2_score(poly2Dreco(X, Y, coeff), B)

    return coeff, r2


def suboptimal_datapoints(dp_all, case_study, show_plots, recover):
    dp_all['capacity (kWh)'] = dp_all['capacity (kWh)'].round(5)
    dp_all.sort_values(['capacity (kWh)', 'max. heat load (kW)'], ascending=[True, False], inplace=True)
    dp_red = dp_all.copy()

    for cap in np.unique(dp_all['capacity (kWh)'].values)[:]:
        max_heat_load_aux = dp_red['max. heat load (kW)']
        capacity_aux = dp_red['capacity (kWh)']
        ratio = case_study['storage limits']['ratio']

        if recover == 0:
            index_to_drop = dp_red[((max_heat_load_aux >= cap * ratio) & (capacity_aux == cap)) == True].index
            dp_red.drop(index_to_drop, inplace=True)

        unique_heat_loads = np.unique(dp_red['max. heat load (kW)'][dp_red['capacity (kWh)'] == cap])

        for h in unique_heat_loads:
            max_heat_load_aux = dp_red['max. heat load (kW)']
            capacity_aux = dp_red['capacity (kWh)']

            min_costs = np.min(dp_red['total costs (€)'][((max_heat_load_aux == h) & (capacity_aux == cap))])
            index_to_drop = dp_red[((max_heat_load_aux == h) & (capacity_aux == cap)) & (dp_red['total costs (€)'] > min_costs)].index
            dp_red.drop(index_to_drop, inplace=True)

        heat_loads = dp_red['max. heat load (kW)'][dp_red['capacity (kWh)'] == cap]
        max_heat_load = np.max(heat_loads)
        total_costs_aux = dp_red['total costs (€)'][dp_red['capacity (kWh)'] == cap]

        for i in range(0, len(total_costs_aux)):
            try:
                idx = dp_red['total costs (€)'][dp_red['capacity (kWh)'] == cap].index[i:]
                costs_aux = dp_red['total costs (€)'][idx[0]]

                idx_remove = (dp_red.loc[idx[0:]]['total costs (€)'][
                    dp_red.loc[idx[0:]]['total costs (€)'] > costs_aux]).index

                dp_red.drop(idx_remove, inplace=True)
                if len(idx) - len(idx_remove) < 2:
                    break
            except:
                print('error')

    return dp_red

def steps_geom_series(res, range_vals):
    nums = range(1, res+1)
    min_dia = range_vals[0]
    max_dia = range_vals[1]
    geom_series = np.array([i**2 for i in nums])-1
    conv_fact = geom_series[-1]/(max_dia - min_dia)
    geom_series_conv = geom_series/conv_fact + min_dia
    return geom_series_conv


def plot_cost_structure(dps):
    import matplotlib.cm as cm
    cmap = cm.get_cmap('tab20')

    if type(dps) != list:
        dps = [dps]

    subplots = dps.__len__()

    ylim = 0
    for dp in dps:
        ylim = np.max([np.max(dp['internal costs (€)']), ylim])

    if subplots > 1:
        cols = 2
    else:
        cols = 1

    fig, ax = plt.subplots(subplots // 2 + subplots % 2, cols, squeeze=False, figsize=(6, 6))

    for i, dp in enumerate(dps):

        color_counter = 0

        dp.sort_values(['capacity (kWh)', 'max. heat load (kW)'], ascending=[True, True], inplace=True)
        dp.reset_index(inplace=True)
        name_list = [
            'total vessel costs (€)',
            'additional equipment costs (€)',
            'internal costs (€)',
            'total costs (€)',
            'tube costs (€)',
            'insulation costs (€)',
            'storage material costs (€)'
        ]
        name_list = [name for name in dp.keys() if '€' in name]




        # plt.figure()
        # for name in name_list:
        #     plt.plot(dp.index, dp[name], label=name)
        #
        # plt.legend()
        # plt.ylabel('Costs (€)')



        cap_range = np.linspace(min(dp['capacity (kWh)']), max(dp['capacity (kWh)']), 3)
        hl_range = np.linspace(min(dp['max. heat load (kW)']), max(dp['max. heat load (kW)']), 3)

        box = [(dp['capacity (kWh)'] >= cap_range[0]) & (dp['capacity (kWh)'] < cap_range[1]) & (
                    dp['max. heat load (kW)'] >= hl_range[0]) & (dp['max. heat load (kW)'] < hl_range[1]),
            (dp['capacity (kWh)'] >= cap_range[1]) & (dp['capacity (kWh)'] <= cap_range[2]) & (
                    dp['max. heat load (kW)'] >= hl_range[0]) & (dp['max. heat load (kW)'] < hl_range[1]),
            (dp['capacity (kWh)'] >= cap_range[1]) & (dp['capacity (kWh)'] <= cap_range[2]) & (
                    dp['max. heat load (kW)'] >= hl_range[1]) & (dp['max. heat load (kW)'] <= hl_range[2])]

        labels = ['Low Cap./Low HL', 'High Cap./Low HL', 'High Cap./High HL']


        # bot = np.zeros(3)
        exclude = ['total vessel costs (€)', 'additional equipment costs (€)', 'internal costs (€)', 'total costs (€)', 'profit surcharge (€)']
        bot = np.zeros(3)
        for name in name_list:
            if name not in exclude:
                new_vals = np.array([np.mean(dp[name][i]) for i in box])
                new_vals_perc = np.array([np.mean(dp[name][i]) / np.mean(dp['total costs (€)'][i]) for i in box]) * 100
                if np.max(new_vals) > 0:
                    ax[i % 2, i//2].bar(labels, new_vals, bottom=bot, label=name, color=cmap.colors[color_counter])

                    for anno in range(3):
                        ax[i % 2, i//2].text(labels[anno], bot[anno] + new_vals[anno]/2, '{:.2F} %'.format(new_vals_perc[anno]), ha='center', va='center')

                    bot += new_vals

                color_counter += 1
                if color_counter == len(cmap.colors):
                    color_counter = 0

        ax[i % 2, i//2].legend(fontsize=6)
        ax[i % 2, i//2].set_ylabel('Costs (€)')
        ax[i % 2, i//2].set_ylim(0,ylim)

    print('cost structure plotted')



def plot_cost_structure_2(dps, sto_names):
    import matplotlib.cm as cm
    cmap = cm.get_cmap('tab10')

    if type(dps) != list:
        dps = [dps]

    subplots = dps.__len__()

    ylim = 0
    for dp in dps:
        ylim = np.max([np.max(dp['internal costs (€)']), ylim])

    if ylim > 10**6:
        fact = 10**6
        unit_string = 'M€'
    elif (ylim <= 10**6) & (ylim > 10**3):
        fact = 10**3
        unit_string = 'k€'
    else:
        fact = 10 ** 0
        unit_string = '€'

    if subplots > 1:
        cols = 2
    else:
        cols = 1

    fig, ax = plt.subplots(1, 1, squeeze=False, figsize=(6, 6))

    color_counter = 0
    name_lists = []
    for i, dp in enumerate(dps):
        dp.sort_values(['capacity (kWh)', 'max. heat load (kW)'], ascending=[True, True], inplace=True)
        dp.reset_index(inplace=True)
        dps[i] = dp
        name_lists += [name for name in dp.keys() if '€' in name]

    name_list = np.unique(np.array(name_lists)).tolist()

    cap_ranges = []
    hl_ranges = []
    boxes = []
    for i, dp in enumerate(dps):
        cap_range = np.linspace(min(dp['capacity (kWh)']), max(dp['capacity (kWh)']), 3)
        hl_range = np.linspace(min(dp['max. heat load (kW)']), max(dp['max. heat load (kW)']), 3)

        box = [(dp['capacity (kWh)'] >= cap_range[0]) & (dp['capacity (kWh)'] < cap_range[1]) & (
                    dp['max. heat load (kW)'] >= hl_range[0]) & (dp['max. heat load (kW)'] < hl_range[1]),
            (dp['capacity (kWh)'] >= cap_range[1]) & (dp['capacity (kWh)'] <= cap_range[2]) & (
                    dp['max. heat load (kW)'] >= hl_range[0]) & (dp['max. heat load (kW)'] < hl_range[1]),
            (dp['capacity (kWh)'] >= cap_range[1]) & (dp['capacity (kWh)'] <= cap_range[2]) & (
                    dp['max. heat load (kW)'] >= hl_range[1]) & (dp['max. heat load (kW)'] <= hl_range[2])]

        boxes += [box]
        cap_ranges += cap_range.tolist()
        hl_ranges += hl_range.tolist()
        labels_names = ['Low Cap./Low HL', 'High Cap./Low HL', 'High Cap./High HL']
        labels_names_num = ['1', '2', '3']

    labels0 = [1,2,3]
    labels = [i+4*j for j in range(subplots) for i in labels0]

    # bot = np.zeros(3)
    exclude = ['engineering costs (€)', 'total vessel costs (€)', 'additional equipment costs (€)', 'internal costs (€)', 'total costs (€)', 'profit surcharge (€)']
    name_list = [name for name in name_list if name not in exclude]

    bot = np.zeros(3*subplots)
    for name in name_list:
        if name not in exclude:
            new_vals = np.array([np.mean(dps[j][name][i]) for j in range(subplots) for i in boxes[j]]) / fact
            new_vals_perc = np.array([np.mean(dps[j][name][i]) / np.mean(dps[j]['internal costs (€)'][i]) for j in range(subplots) for i in boxes[j]]) * 100
            print(name)
            print(new_vals)
            print(new_vals_perc)
            if np.max(new_vals) > 0:
                if name == 'hx costs (€)':
                    ax[0,0].bar(labels, new_vals, bottom=bot, label='HX costs (€)', color=cmap.colors[color_counter])
                else:
                    ax[0,0].bar(labels, new_vals, bottom=bot, label=name, color=cmap.colors[color_counter])

                for anno in range(3*subplots):
                    if new_vals[anno] > ylim/20 / fact:
                        ax[0,0].text(labels[anno], bot[anno] + new_vals[anno]/2, '{:.0F}%'.format(new_vals_perc[anno]), ha='center', va='center', fontsize=8)

                bot += new_vals

            color_counter += 1
            if color_counter == len(cmap.colors):
                color_counter = 0

    ax[0,0].legend(fontsize=8)
    ax[0,0].set_ylabel('Costs ({})'.format(unit_string))
    ax[0,0].set_ylim(0,ylim / fact)
    ax[0,0].set_xlim(0,4.5*subplots)
    ax[0, 0].set_xticks(labels)
    labels_used = labels_names_num*subplots + ['']*4
    for i in range(subplots):
        labels_used[1+(i)*3] = labels_used[1+(i)*3] + '\n' + sto_names[i]
    # ax[0, 0].set_xticklabels(labels_used, rotation=0, ha='center')
    from matplotlib.ticker import MultipleLocator, NullLocator
    ax[0, 0].set_axisbelow(True)
    ax[0, 0].yaxis.set_minor_locator(MultipleLocator(250))
    ax[0, 0].grid(b=None, which='both', axis='y', color=(0.9,0.9,0.9))

    print('cost structure plotted')

def rescale(dp_var, select_cols, rescale_factor, steps):
    dp_resc = dp_var.copy()

    dp_resc[select_cols] = dp_resc[select_cols].mul(rescale_factor, axis=0)
    dp_resc = dp_resc.sort_values('max. heat load (kW)').reset_index(drop=True)

    # if show_plots:
    #     plt.figure()
    #     plt.plot(dp_resc['tube length (m)'].values)
    #     plt.figure()
    #     plt.plot(dp_resc['total volume (m³)'].values)
    #     plt.figure()
    #     plt.plot(dp_resc['tube diameter (m)'].values)
    #     plt.figure()
    #     plt.plot(dp_resc['concrete fraction'].values)

    # Generate data points for regression

    res_final = steps
    increment = 1 / res_final

    dp_all = dp_resc.copy()
    for i in range(1, res_final):
        data_points_aux = dp_resc.copy()
        data_points_aux[select_cols] = data_points_aux[select_cols] * (increment * i)
        dp_all = dp_all.append(data_points_aux).reset_index(drop=True)

    return dp_all


def simulate_concrete_pcm(d_tube, layer, p_spec, p_gen, n, show_sim_plots):
    """
    calculation of heat load and capacity for a given combination of tube diameter and storage material layer thickness
    :param d_tube: tube diameter - m
    :param layer: concrete layer - m
    :return: heat load - W/m & capacity Ws/m
    """

    kWh2Ws = 3.6 * 10 ** 6

    if p_spec['Type'] == 'LHTS':
        phasechange = True
    else:
        phasechange = False

    if phasechange:
        energy_density = {
            'sensible': p_spec['PCM parameters']['energy_density_sensible'],
            'latent': p_spec['PCM parameters']['energy_density_latent'],
        }
        dT = p_spec['integration parameters']['dT']
        dT_effective = p_spec['PCM parameters']['effective use of T range']
        alpha = p_spec['PCM parameters']['alpha']
        lambda_sto_mat = p_spec['PCM parameters']['lambda_pcm']
        fract_e = p_spec['approximation parameters']['fract_e']
        T_melt = p_spec['PCM parameters']['melting temperature']

    else:
        energy_density = {
            'sensible': p_spec['Concrete parameters']['specific heat storage density']
        }
        dT = p_spec['integration parameters']['dT']
        dT_effective = p_spec['Concrete parameters']['effective use of T range']
        alpha = p_spec['Concrete parameters']['alpha']
        lambda_sto_mat = p_spec['Concrete parameters']['lambda_concrete']
        fract_e = p_spec['approximation parameters']['fract_e']

    # Calculations
    d_sto_mat = d_tube * (1 + layer)  # diameter of storage material layer - m
    V_sto_mat = (d_sto_mat / 2) ** 2 * np.pi - (d_tube / 2) ** 2 * np.pi

    d_nodes = np.linspace(d_tube, d_sto_mat, n + 1)
    Vn = (d_nodes[1:] / 2) ** 2 * np.pi - (d_nodes[:-1] / 2) ** 2 * np.pi

    # capacity - kWh - Using dT with applied effectivity
    if phasechange:
        capacity_Ws = V_sto_mat * (energy_density['latent'] + energy_density['sensible'] * dT * dT_effective)
    else:
        capacity_Ws = V_sto_mat * (kWh2Ws * energy_density['sensible'] * dT * dT_effective)

    # Quasi-stationary simulation
    nt = 100000

    T_heat = p_gen['temperature limits']['T_max']
    T_0 = np.ones(n) * (p_gen['temperature limits']['T_min'] + (
                p_gen['temperature limits']['T_max'] - p_gen['temperature limits']['T_min']) * (
                                    1 - dT_effective) / 2)
    Q_0 = np.ones(n) * 0
    Q = Q_0

    dTx = np.concatenate((np.array([T_heat]), T_0))[:-1] - np.concatenate((np.array([T_heat]), T_0))[1:]

    if show_sim_plots:
        plt.figure()
        plt.ion()
        plt.ylim(p_gen['temperature limits']['T_min'], p_gen['temperature limits']['T_max'])

    dt_0 = 0.1

    q_dot_0 = np.zeros(nt)
    Q_stored = np.zeros(nt)
    t = np.zeros(nt + 1)
    t[0] = 0

    ka_0 = alpha * d_tube * np.pi
    ka_i = [2 * lambda_sto_mat / i * np.pi for i in np.log(d_nodes[1:] / d_nodes[:-1])]

    ka = np.array([1 / (1 / ka_0 + 1 / ka_i[0])] + ka_i[1:])

    if phasechange:
        Q_01 = (T_melt - T_0) * (Vn * energy_density['sensible']) + Q_0
        Q_12 = (T_melt - T_0) * (Vn * energy_density['sensible']) + (
                    Vn * energy_density['latent']) + Q_0

    dt = dt_0

    def simulation(dt, nt, t, q_dot_0, Q_stored, dTx, Q):
        for i in range(nt):
            convergence = 0
            while convergence == 0:

                t[i + 1] = t[i] + dt

                q_dot = ka * dTx

                Q_new = Q + (np.append(q_dot, 0)[:-1] - np.append(q_dot, 0)[1:]) * dt

                if phasechange:
                    T_new_01 = ((Q_new - Q_0) / (Vn * energy_density['sensible']) + T_0) * (Q_new < Q_01)
                    T_new_12 = T_melt * ((Q_new >= Q_01) & (Q_new < Q_12))
                    T_new_23 = ((Q_new - Q_0 - (Vn * energy_density['latent'])) / (
                            Vn * energy_density['sensible']) + T_0) * (Q_new >= Q_12)

                    T_new = T_new_01 + T_new_12 + T_new_23
                else:
                    T_new = (Q_new - Q_0) / (kWh2Ws * Vn * energy_density['sensible']) + T_0

                if (max(T_new) < p_gen['temperature limits']['T_max']) & (min(T_new[:-1] - T_new[1:]) >= -1) & (
                        min((T_new[:-1] - T_new[1:])[:-1] - (T_new[:-1] - T_new[1:])[1:]) >= -0.01):
                    convergence = 1

                    q_dot_0[i] = q_dot[0]
                    Q = Q_new
                    dTx = np.concatenate((np.array([T_heat]), T_new))[:-1] - np.concatenate(
                        (np.array([T_heat]), T_new))[1:]

                    Q_stored[i] = sum(Q_new) - sum(Q_0)

                    dt = dt * 1.03

                    if show_sim_plots:
                        if i % 10 == 0:
                            plt.cla()
                            plt.plot(d_nodes[1:], T_new)
                            plt.ylim(p_gen['temperature limits']['T_min'], p_gen['temperature limits']['T_max'])
                            plt.draw()
                            plt.pause(0.001)

                    if sum(Q_new) > capacity_Ws:
                        return Q_stored, q_dot_0, t, i

                else:
                    printwarnings = 0
                    if printwarnings:
                        print('Convergence issues!!')
                        print('reducing timestep')
                        print('current dt: {}'.format(dt))
                        print('current timestep: {}'.format(i))
                    dt = dt / 1.1

    Q_stored, q_dot_0, t, i = simulation(dt, nt, t, q_dot_0, Q_stored, dTx, Q)

    end = time.time()
    # print(end-start)
    stored_energy_sim_cut = Q_stored[:i]
    q_dot_0 = q_dot_0[:i]
    timesteps_cut = t[:i]

    if show_sim_plots:
        plt.figure()
        plt.plot(timesteps_cut, stored_energy_sim_cut)
        plt.xlabel('time (s)')
        plt.ylabel('stored energy (Ws)')
        plt.figure()
        plt.plot(timesteps_cut, q_dot_0)
        plt.xlabel('time (s)')
        plt.ylabel('heat load (W)')

    # interpolation of simulated results
    timesteps_interp = np.linspace(max(timesteps_cut) * fract_e, max(timesteps_cut), 100)
    stored_energy_interp = np.interp(timesteps_interp, timesteps_cut, stored_energy_sim_cut)

    # calculation of coefficients for linear interpolation (coeffs[0] ... average heat load)
    # coeffs = np.polyfit(timesteps_interp, stored_energy_interp, 1)  # fixme
    coeffs = np.array([stored_energy_interp[-1] / timesteps_interp[-1], 0])  # fixme
    if show_sim_plots:
        plt.figure()
        plt.plot(timesteps_cut, stored_energy_sim_cut)
        plt.plot(timesteps_cut, timesteps_cut * coeffs[0] + coeffs[1])
        plt.xlabel('time (s)')
        plt.ylabel('stored energy (Ws)')

    heat_load_ave = coeffs[0]
    # print('melting time original: ' + str(max(timesteps_cut)) + ' s')
    # print('melting time approximation: ' + str(capacity/heat_load_ave) + ' s')
    # print('melting time fraction: ' + str((capacity/heat_load_ave)/max(timesteps_cut)))
    return heat_load_ave / 1000, capacity_Ws / kWh2Ws


if __name__ == '__main__':
    coeffs = calc_costfun_lumenion(1, 2, 3)
    print(coeffs)