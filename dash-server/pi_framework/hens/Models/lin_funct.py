#from bamboo.pi_framework.Stream table examples.settings import hex_spec
#from bamboo.pi_framework.Stream table examples.settings import hex_spec
import matplotlib
matplotlib.rcParams['text.usetex'] = True

def calc_LMTD_chen(dt1, dt2):
    import numpy as np
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


def cut_values(settings, LMTD_grid, q_grid, A_grid, LMTD_min, LMTD_max):
    from numpy import max, zeros, nonzero, append, logical_and
    """
    Cut infeasible values from domain for HEX area

    :param LMTD_min:
    :param LMTD_max:
    :param q:
    :return:
    """

    q_max = max(q_grid)
    q_min = settings['LIN']['dom_fact_load'] * q_max

    LMTD_cut = zeros((0, 1))
    q_cut = zeros((0, 1))
    A_cut = zeros((0, 1))

    for i in range(LMTD_min.shape[0]):
        if q_grid[i, 0] >= q_min:
            LMTD_slice = LMTD_grid[i, :]
            LMTD_min_slice = LMTD_min[i]
            LMTD_max_slice = LMTD_max[i]

            indices = nonzero(logical_and(LMTD_slice <= LMTD_max_slice, LMTD_slice >= LMTD_min_slice))

            LMTD_cut = append(LMTD_cut, LMTD_slice[indices])
            q_cut = append(q_cut, q_grid[i, indices])
            A_cut = append(A_cut, A_grid[i, indices])

    return LMTD_cut, q_cut, A_cut


def lin_LMTD(dTmin, rel_error):
    import numpy as np
    """
    Calculates coefficients for linearization of LMTD
    :return: coeffs['LMTD']
    """

    dt_max = 1000  # set arbitrary number for approximation
    discretization = 100000  # set arbitrary number for approximation

    dt_range = np.linspace(dTmin, dt_max,
                           discretization + 1)  # set values for temperature difference

    def calc_LMTD(dt):
        """
        :param dt: temperature difference
        :return: LMTD
        """
        if isinstance(dt, np.ndarray):
            if np.max(dt) >= dt_max:
                dt[-1] = dt_max - 0.0001
        else:
            if np.max(dt) >= dt_max:
                dt = dt_max - 0.0001

        LMTD = np.divide(dt - dt_max, np.log(dt / dt_max))  # calc LMTD
        return LMTD

    def calc_LMTD_approx(a, b, dt):
        """
        :param a: first coefficient
        :param b: second coefficient
        :param dt: temperature difference
        :return: LMTD approximation
        """
        LMTD = a * dt + b
        return LMTD

    # set first data point
    dt = np.array([dt_range[0]])  # corresponds to dTmin
    steps = np.array([0])

    stepsize = 10  # set stepsize

    while dt[-1] < dt_max:
        diff_max = 0

        # initialize next data point
        steps = np.append(steps, [steps[-1] + stepsize])  # set first step
        dt = np.append(dt, [dt_range[steps[-1]]])

        while diff_max < rel_error:
            # coefficients for initial linear approximation
            a = (calc_LMTD(dt[-1]) - calc_LMTD(dt[-2])) / (dt[-1] - dt[-2])
            b = calc_LMTD(dt[-1]) - a * dt[-1]

            diff_max = np.max(np.divide(calc_LMTD(dt_range[steps[-2]:steps[-1]]) -
                                        calc_LMTD_approx(a, b, dt_range[steps[-2]:steps[-1]]),
                                        calc_LMTD(dt_range[steps[-2]:steps[-1]])))

            # update next data point
            steps[-1] = steps[-1] + stepsize  # set first step

            if steps[-1] > discretization:
                steps[-1] = discretization
                dt[-1] = dt_range[steps[-1]]
                break

            dt[-1] = dt_range[steps[-1]]

    # calculate coefficients (c1, c2, c3)
    coeffs = np.zeros(((dt.shape[0] - 1) * 2, 3))  # initialize empty array

    for i in range(dt.shape[0] - 1):
        p1 = np.array([dt[i], dt_max, calc_LMTD(dt[i])])
        p2 = np.array([dt[i + 1], dt_max, calc_LMTD(dt[i + 1])])
        p3 = np.array([0, 0, 0])

        # These two vectors are in the plane
        v1 = p3 - p1
        v2 = p2 - p1

        # the cross product is a vector normal to the plane
        cp = np.cross(v1, v2)
        a, b, c = cp

        # This evaluates a * x3 + b * y3 + c * z3 which equals d
        d = np.dot(cp, p3)

        # Z = (d - a * X - b * Y) / c

        c1 = -a / c
        c2 = -b / c
        c3 = d / c

        coeffs[i, :] = [c1, c2, c3]
        coeffs[i + dt.shape[0] - 1] = [c2, c1, c3]

    # plt.figure()
    # plt.plot(dt_range, calc_LMTD(dt_range))
    # for i in range(dt.shape[0] - 1):
    #     plt.plot(dt, dt * coeffs['LMTD'][i, 0] + 1000 * coeffs['LMTD'][i, 1] + coeffs['LMTD'][i, 2])
    #
    # plt.show()

    return coeffs


def linearization(data_input, conversion_units, settings, names_list, q_max):
    import numpy as np
    import pandas as pd
    import scipy
    import matplotlib.pyplot as plt

    streamdata = data_input['streamdata']

    # fixme: needs to be adjusted for rescheduling case!
    # if HEN_obj.settings['SCHED']['active']:
    #     streamdata = streamdata.reset_index()
    #     streamdata.set_index(['interval', 'requirement'], inplace=True)  # set multiindexing

    def lin_A(q_max, beta):
        """
        Calculates coefficients for approximation of the heat transfer area
        all steps are carried out according to

        A. Beck, R. Hofmann:
        "A Novel Approach for Linearization of a MINLP Stage-Wise Superstructure Formulation";
        Computers & Chemical Engineering, 112 (2018), S. 17 - 26.

        except for the nonlinear optimization step to optimize approximating coefficients of the individual planes

        :param q_max: maximum pairwise transferable heat
        :return coeffs_A:  returns coefficients for approximation of A
        """

        def lin_A_single(q_max_single, stream_hot, stream_cold, beta, hex_type, phasechange):
            # from .lin_funct import calc_LMTD_chen
            # from .lin_funct import calc_A
            # from .lin_funct import cut_values
            """
            Calculates coefficients for approximation of the heat transfer area for direct heat recovery
            :param self.settings: contains self.settings for approximation
            :param q_max: maximum pairwise transferable heat
            :param t: interval number
            :param stream: stream number

            :return coeffs_A_single: returns coefficients for approximation of A
            """

            # ----------------------------------------------------------------------------------------------------------

            show_plots = 0

            # ----------------------------------------------------------------------------------------------------------
            if beta < 1 and 'Hex_spec' in settings.keys():
                try:
                    key = [i for i in settings['Hex_spec'].keys() if set([stream_hot['Medium'], stream_cold['Medium']]) == set(i)][0]
                    beta = settings['Hex_spec'][key]['beta']
                except: 
                    print(stream_hot['Medium'], stream_cold['Medium'])

                    
    
        


            if hex_type in ['UH', 'UC']:
                if hex_type == 'UH':
                    utility = stream_hot
                    process_stream = stream_cold

                else:
                    utility = stream_cold
                    process_stream = stream_hot

                # extract in & outlet temperatures
                t_process_stream_in = process_stream['Tin']
                t_process_stream_out = process_stream['Tout']
                t_utility_in = utility['Tin']
                t_utility_out = utility['Tout']

                mcp = process_stream['mcp']
                q_max = np.abs(t_process_stream_in - t_process_stream_out) * mcp

                q_range = np.linspace(0, q_max, settings['LIN']['res_ut'])



                if t_process_stream_out < t_process_stream_in:
                    dt_1 = (t_utility_in - t_process_stream_out) * np.ones(q_range.shape[0])*(-1)
                    dt_2 = (t_utility_out - (t_process_stream_out + q_range / mcp)) * (-1)
                else:
                    dt_1 = (t_utility_in - t_process_stream_out) * np.ones(q_range.shape[0])
                    dt_2 = (t_utility_out - (t_process_stream_out - q_range / mcp))

                idx_feasible = np.where(np.logical_and(dt_2 >= settings['HEN']['dTmin'], dt_1 >= settings['HEN']['dTmin']))
                idx_range = np.where(np.logical_and(q_range >= settings['LIN']['dom_fact_ut_min']*q_max, q_range <= settings['LIN']['dom_fact_ut_max']*q_max))
                idx_approx = np.intersect1d(idx_feasible, idx_range)

                k = 1 / (1 / stream_hot['h'] + 1 / stream_cold['h'])

                LMTD = calc_LMTD_chen(dt_1[idx_approx], dt_2[idx_approx])   # Chen approximation

                A = (q_range[idx_approx] / k / LMTD) ** beta

                coeffs_A_ut = np.polyfit(q_range[idx_approx], A, 1)
                return np.append(coeffs_A_ut, 0), max(A), max(LMTD)

            else:
                res = settings['LIN']['res']  # resolution for mesh

                q = np.linspace(0, q_max_single, res)  # transferable heat (resolution 1)
                k = 1 / (1 / stream_cold['h'] + 1 / stream_hot['h']) # calculate overall heat transfer coefficient k

                # ----------------------------------------------------------------------------------------------------------
                # calculate maximum LMTD

                if hex_type in ['Direct']:
                    # extract in & outlet temperatures
                    t_hot_in = stream_hot['Tin']
                    t_hot_out = stream_hot['Tout']
                    t_cold_in = stream_cold['Tin']
                    t_cold_out = stream_cold['Tout']

                    # extract mcp
                    mcp_hot = stream_hot['mcp']
                    mcp_cold = stream_cold['mcp']

                    # calculate maximum temperature differences
                    dt_hot_max = (t_hot_in - t_cold_in) - q / mcp_cold
                    dt_cold_max = (t_hot_in - t_cold_in) - q / mcp_hot


                if hex_type in ['CUH','CUC']:

                    if hex_type in ['CUH']:
                        # extract in & outlet temperatures
                        t_hot_max = stream_hot['Tmax']
                        t_hot_min = stream_hot['Tmin']
                        t_cold_in = stream_cold['Tin']
                        t_cold_out = stream_cold['Tout']

                        # extract mcp
                        mcp_stream = stream_cold['mcp']

                        # calculate maximum temperature differences
                        dt_hot_max = (t_hot_max - t_cold_in)
                        dt_cold_max = (t_hot_max - t_cold_in) - q / mcp_stream

                    if hex_type in ['CUC']:
                        # extract in & outlet temperatures
                        t_hot_in = stream_hot['Tin']
                        t_hot_out = stream_hot['Tout']
                        t_cold_max = stream_cold['Tmax']
                        t_cold_min = stream_cold['Tmin']

                        # extract mcp
                        mcp_stream = stream_hot['mcp']

                        # calculate maximum temperature differences
                        dt_hot_max = (t_hot_in - t_cold_min)
                        dt_cold_max = (t_hot_in - t_cold_min) - q / mcp_stream


                if hex_type in ['UIH', 'UIC']:

                    # extract in & outlet temperatures
                    t_hot_in = stream_hot['Tin']
                    t_hot_out = stream_hot['Tout']
                    t_cold_in = stream_cold['Tin']
                    t_cold_out = stream_cold['Tout']

                    if hex_type in ['UIH']:
                        # extract mcp
                        mcp_stream = stream_cold['mcp']

                    if hex_type in ['UIC']:
                        # extract mcp
                        mcp_stream = stream_hot['mcp']

                    if hex_type in ['UIH']:
                        # calculate maximum temperature differences
                        dt_hot_max = (t_hot_in - t_cold_in) - q / mcp_stream
                        dt_cold_max = np.ones(res) * (t_hot_out - t_cold_in)

                    if hex_type in ['UIC']:
                        # calculate maximum temperature differences
                        dt_hot_max = np.ones(res) * (t_hot_in - t_cold_out)
                        dt_cold_max = (t_hot_in - t_cold_in) - q / mcp_stream

                try:
                    LMTD_max = calc_LMTD_chen(dt_hot_max, dt_cold_max)
                except:
                    print('error')

                # ----------------------------------------------------------------------------------------------------------
                # calculate minimum LMTD

                if hex_type in ['Direct']:
                    t_hot_in_shifted = t_hot_in - settings['HEN']['dTmin']
                    t_hot_out_shifted = t_hot_out - settings['HEN']['dTmin']

                    # introduce new variables for easier handling
                    t_hot = np.array([t_hot_in_shifted, t_hot_out_shifted])
                    t_cold = np.array([t_cold_out, t_cold_in])

                    # init dt
                    dt_1 = settings['HEN']['dTmin'] * np.ones((q.shape[0]))
                    dt_2 = settings['HEN']['dTmin'] * np.ones((q.shape[0]))

                    # Case 1:
                    if t_hot[0] >= t_cold[0] >= t_cold[1] >= t_hot[1] and mcp_cold >= mcp_hot:
                        q_kink = (t_cold[0] - t_cold[1]) * mcp_hot  # for higher heat recovery, dt deviates from dTmin
                        dt_kink = (t_cold[1] + settings['HEN']['dTmin'] + q / mcp_hot) - t_cold[0]

                        dt_1[q <= q_kink] = settings['HEN']['dTmin']
                        dt_1[q > q_kink] = dt_kink[q > q_kink]

                    # Case 2:
                    if t_cold[0] >= t_hot[0] >= t_hot[1] >= t_cold[1] and mcp_cold <= mcp_hot:
                        q_kink = (t_hot[0] - t_hot[1]) * mcp_cold  # for higher heat recovery, dt deviates from dTmin
                        dt_kink = t_hot[1] - (t_hot[0] - settings['HEN']['dTmin'] - q / mcp_cold)

                        dt_1[q <= q_kink] = settings['HEN']['dTmin']
                        dt_1[q > q_kink] = dt_kink[q > q_kink]

                    # Case 3:
                    if t_hot[0] >= t_cold[0] >= t_hot[1] >= t_cold[1] and mcp_cold <= mcp_hot:
                        q_kink = (t_cold[0] + settings['HEN']['dTmin'] - t_hot[
                            1]) * mcp_cold  # for higher heat recovery, dt deviates from dTmin
                        dt_kink = t_hot[1] - (t_cold[0] - q / mcp_cold)

                        dt_1[q <= q_kink] = settings['HEN']['dTmin']
                        dt_1[q > q_kink] = dt_kink[q > q_kink]

                    # Case 4:
                    if t_hot[0] >= t_hot[1] >= t_cold[0] >= t_cold[1]:
                        dt_1 = t_hot[1] - (t_cold[0] - q / mcp_cold)
                        dt_2 = (t_hot[1] + q / mcp_hot) - t_cold[0]

                if hex_type in ['CUH', 'CUC']:  # fixme: domain can be further reduced
                    if phasechange:
                        dt_1 = settings['HEN']['dTmin'] * np.ones((q.shape[0]))
                        dt_2 = settings['HEN']['dTmin'] + q / mcp_stream
                    else:
                        dt_1 = settings['HEN']['dTmin'] * np.ones((q.shape[0]))
                        dt_2 = settings['HEN']['dTmin'] * np.ones((q.shape[0]))

                if hex_type in ['UIH', 'UIC']:
                    if hex_type in ['UIC']:
                        dt_1 = (t_hot_out - t_cold_out) + q/mcp_stream
                        dt_2 = np.ones(res) * (t_hot_out - t_cold_in)

                    if hex_type in ['UIH']:
                        dt_1 = np.ones(res) * (t_hot_in - t_cold_out)
                        dt_2 = (t_hot_out - t_cold_out) + q/mcp_stream

                dt_1[dt_1 < settings['HEN']['dTmin']] = settings['HEN']['dTmin']
                dt_2[dt_2 < settings['HEN']['dTmin']] = settings['HEN']['dTmin']

                LMTD_min = calc_LMTD_chen(dt_1, dt_2)

                # ----------------------------------------------------------------------------------------------------------
                # calculate feasible domain for interpolation

                LMTD = np.linspace(min(LMTD_min), max(LMTD_max), res)

                LMTD_grid, q_grid = np.meshgrid(LMTD, q)
                A_grid = calc_A(settings, LMTD_grid, q_grid, k, beta)

                # calculate feasible values for LMTD, q, A
                LMTD_cut, q_cut, A_cut = cut_values(settings, LMTD_grid, q_grid, A_grid, LMTD_min, LMTD_max)

                # ----------------------------------------------------------------------------------------------------------
                # split domain into n "areas" and calculate coefficients for approximating planes

                A_max = max(A_cut)
                A_min = min(A_cut)

                def nonlinspace(start, stop, num):
                    linear = np.linspace(0, 1, num)
                    my_curvature = 2
                    curve = np.exp(my_curvature * linear) - 1
                    curve = curve / np.max(curve)  # normalize between 0 and 1
                    curve = curve * (stop - start - 1) + start
                    return curve

                # A_segments = np.linspace(A_min, A_max, settings['LIN']['num_eq'] + 1)
                A_segments = nonlinspace(A_min, A_max, settings['LIN']['num_eq'] + 1)

                coeffs_A_single_nonopt = np.zeros(
                    (settings['LIN']['num_eq'], 3))  # initialize array for coefficients

                apen_plots = 0
                beta_set = 0
                if beta < 1:
                    beta_set = 1

                if apen_plots & beta_set:
                    fig = plt.figure()
                    ax = fig.add_subplot(111, projection='3d')
                    ax.plot_surface(LMTD_grid, q_grid, A_grid, color='k', linewidth=1, alpha=0.5)

                for i in range(settings['LIN']['num_eq']):
                    indices = np.nonzero(np.logical_and(A_cut >= A_segments[i], A_cut <= A_segments[i + 1]))

                    A_seg = A_cut[indices]
                    LMTD_seg = LMTD_cut[indices]
                    q_seg = q_cut[indices]

                    # best-fit linear plane
                    # M
                    temp = np.c_[LMTD_seg, q_seg, np.ones(A_seg.shape[0])]
                    coeffs_nonopt, _, _, _ = scipy.linalg.lstsq(temp,
                                                                A_seg)  # nonoptimal coefficients; Z = coeffs_nonopt[0]*X + coeffs_nonopt[1]*Y + coeffs_nonopt[2]
                    coeffs_A_single_nonopt[i, :] = coeffs_nonopt

                if apen_plots & beta_set:
                    A_grid_max = A_grid * 0
                    for i in range(settings['LIN']['num_eq']):
                        A_grid_new = LMTD_grid * coeffs_A_single_nonopt[i, 0] + q_grid * coeffs_A_single_nonopt[i, 1] + coeffs_A_single_nonopt[i, 2]
                        A_grid_max = np.maximum(A_grid_max, A_grid_new)
                    ax.plot_wireframe(LMTD_grid, q_grid, A_grid_max, color='r', linewidth=1, rstride=10, cstride=8)

                    plt.rcParams['text.usetex'] = True
                    ax.set_title('beta = {}'.format(beta))
                    ax.set_xlabel('LMTD (°C)')
                    ax.set_ylabel('heat load (kW)')
                    ax.set_zlabel(r'discounted area $A^\beta$ (m$^{2\beta}$)')
                    plt.show()

                #     # if show_plots:
                #     fig = plt.figure()
                #     ax = fig.add_subplot(111, projection='3d')
                #     ax.scatter(LMTD_seg, q_seg,
                #                         A_seg)
                #
                #     plt.show()
                #
                # fig = plt.figure()
                # ax = fig.add_subplot(111, projection='3d')
                # ax.scatter(LMTD_cut, q_cut,
                #            A_cut)
                #
                # plt.show()

                # ----------------------------------------------------------------------------------------------------------
                # refine coefficients using nonlinear optimization step

                ########### MISSING !!!!!

                # ----------------------------------------------------------------------------------------------------------

                if show_plots:
                    fig = plt.figure()
                    ax = fig.add_subplot(111, projection='3d')
                    for i in range(settings['LIN']['num_eq']):
                        ax.plot_surface(LMTD_grid, q_grid, LMTD_grid * coeffs_A_single_nonopt[i, 0] + q_grid * coeffs_A_single_nonopt[i, 1] + coeffs_A_single_nonopt[i, 2])

                    plt.show()

                coeffs_A_single = coeffs_A_single_nonopt

                return coeffs_A_single, A_max, [LMTD_max[0], LMTD_max[-1]]


        coeffs_A = pd.DataFrame(
            columns=['type', 'hot', 'cold', 'coeff nr', 'C1', 'C2', 'C3', 'A_max', 'LMTD max'])

        for hex_type in names_list:
            phasechange = 0

            try:
                phasechange = conversion_units[hex_type]['phase change']
            except:
                pass

            if hex_type in ['Direct']:
                streams_hot = data_input['indices']['hot requirements']
                streams_cold = data_input['indices']['cold requirements']

            if hex_type in ['UH', 'UIH', 'CUH']:
                if hex_type == 'CUH':
                    streams_hot = [tuple((i, 1)) for i in range(len(conversion_units['CU']))]
                else:
                    streams_hot = [tuple((i, 1)) for i in range(len(conversion_units[hex_type]))]
                streams_cold = data_input['indices']['cold requirements']

            if hex_type in ['UC', 'UIC', 'CUC']:
                streams_hot = data_input['indices']['hot requirements']
                if hex_type == 'CUC':
                    streams_cold = [tuple((i, 1)) for i in range(len(conversion_units['CU']))]
                else:
                    streams_cold = [tuple((i, 1)) for i in range(len(conversion_units[hex_type]))]

            for i in streams_hot:
                if hex_type in ['Direct', 'UC', 'UIC', 'CUC']:
                    idx = (streamdata['stream nr'] == i[0]) & (streamdata['requirement nr'] == i[1])
                    stream_hot = {
                        'Tin': streamdata.loc[idx, 'T in'].values[0],
                        'Tout': streamdata.loc[idx, 'T out'].values[0],
                        'mcp': streamdata.loc[idx, 'm'].values[0] * streamdata.loc[idx, 'cp'].values[0],
                        'h': streamdata.loc[idx, 'h'].values[0]
                    }

                    if 'Medium' in streamdata.columns :
                        stream_hot['Medium'] = streamdata.loc[idx, 'Medium'].values[0]
                        
                elif hex_type in ['UH', 'UIH']:
                    key = list(conversion_units[hex_type].keys())[i[0]]
                    stream_hot = {
                        'Tin': conversion_units[hex_type][key]['Tin'],
                        'Tout': conversion_units[hex_type][key]['Tout'],
                        'h': conversion_units[hex_type][key]['h']
                    }

                    if 'Medium' in conversion_units[hex_type][key].keys() :
                        stream_hot['Medium'] = conversion_units[hex_type][key]['Medium']

                elif hex_type in ['CUH']:
                    key = list(conversion_units['CU'].keys())[i[0]]
                    stream_hot = {
                        'Tmin': conversion_units['CU'][key]['Tmin'],
                        'Tmax': conversion_units['CU'][key]['Tmax'],
                        'h': conversion_units['CU'][key]['h'],
                    }

                    if 'Medium' in conversion_units['CU'][key].keys() :
                        stream_hot['Medium'] = conversion_units['CU'][key]['Medium']

                for j in streams_cold:
                    if hex_type in ['Direct', 'UH', 'UIH', 'CUH']:
                        idx = (streamdata['stream nr'] == j[0]) & (streamdata['requirement nr'] == j[1])
                        stream_cold = {
                            'Tin': streamdata.loc[idx, 'T in'].values[0],
                            'Tout': streamdata.loc[idx, 'T out'].values[0],
                            'mcp': streamdata.loc[idx, 'm'].values[0] * streamdata.loc[idx, 'cp'].values[0],
                            'h': streamdata.loc[idx, 'h'].values[0]
                        }

                        if 'Medium' in streamdata.columns :
                            stream_cold['Medium'] = streamdata.loc[idx, 'Medium'].values[0]

                    elif hex_type in ['UC', 'UIC']:
                        key = list(conversion_units[hex_type].keys())[j[0]]
                        stream_cold = {
                            'Tin': conversion_units[hex_type][key]['Tin'],
                            'Tout': conversion_units[hex_type][key]['Tout'],
                            'h': conversion_units[hex_type][key]['h']
                        }

                        if 'Medium' in conversion_units[hex_type][key].keys() :
                            stream_cold['Medium'] = conversion_units[hex_type][key]['Medium']

                    elif hex_type in ['CUC']:
                        key = list(conversion_units['CU'].keys())[j[0]]
                        stream_cold = {
                            'Tmin': conversion_units['CU'][key]['Tmin'],
                            'Tmax': conversion_units['CU'][key]['Tmax'],
                            'h': conversion_units['CU'][key]['h']
                        }

                        if 'Medium' in conversion_units['CU'][key].keys() :
                            stream_cold['Medium'] = conversion_units['CU'][key]['Medium']

                    try:
                        q_max_single = q_max[hex_type].query('hot == @i & cold == @j')['q_max'].values[0]
                    except:
                        print('error')

                    if q_max_single > 0:
                        coeffs_A_single, A_max, LMTDmax = lin_A_single(q_max_single, stream_hot, stream_cold, beta, hex_type, phasechange)
                        if hex_type in ['UH', 'UC']:
                            coeffs_A = coeffs_A.append(
                                {'type': hex_type, 'hot': i, 'cold': j,
                                 'coeff nr': np.arange(0, 1),
                                 'C1': coeffs_A_single[0],
                                 'C2': coeffs_A_single[1],
                                 'C3': coeffs_A_single[2],
                                 'A_max': A_max,
                                 'LMTD max': LMTDmax}, ignore_index=True)
                        else:
                            coeffs_A = coeffs_A.append(
                                {'type': hex_type, 'hot': i, 'cold': j,
                                 'coeff nr': np.arange(0, settings['LIN']['num_eq']),
                                 'C1': coeffs_A_single[:, 0],
                                 'C2': coeffs_A_single[:, 1],
                                 'C3': coeffs_A_single[:, 2],
                                 'A_max': A_max,
                                 'LMTD max': LMTDmax}, ignore_index=True)

        return coeffs_A

    coeffs = {}

    coeffs['LMTD'] = lin_LMTD(settings['HEN']['dTmin'], settings['LIN']['rel_err'])

    for beta in [1, settings['COSTS']['beta']]:
        if beta == 1:
            string = 'beta_1'
        else:
            string = 'beta_x'

        coeffs['A_' +string] = lin_A(q_max, beta)

    return coeffs