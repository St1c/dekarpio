import numpy as np
import pandas as pd

def calc_targets(data_input, settings):
    targ = calc_CCs(data_input, settings['HEN']['dTmin'], 0, [], [], [])
    targ_TAM = calc_CCs(data_input, settings['HEN']['dTmin'], 1, [], [], [])
    return {'targets': targ, 'targets TAM': targ_TAM}

def calc_CCs(data_input, dTmin, TAM, streams_hot_select, streams_cold_select, intervals_select):
    """
    Calculates Composite Curves, Grand Composite Curves and modified Grand Composite Curves


    :param dTmin: is float and determines the minimum temperature difference
    :param TAM: is boolean and defines whether TAM-Targets are calculated
    :param streams_hot_select: is np.ndarray; selected stream numbers ("all" to select all)
    :param streams_cold_select: is np.ndarray; selected stream numbers ("all" to select all)
    :param intervals_select: is np.ndarray; selected interval numbers ("all" to select all)

    :return: targets
    """

    if TAM == 1:
        intervals = [0]
        sd = data_input['streamdata TAM']
        streams_activity = data_input['activity TAM']
    else:
        intervals = data_input['intervals']['index']
        sd = data_input['streamdata']
        streams_activity = data_input['activity']

    streams_hot = data_input['indices']['hot requirements']
    streams_cold = data_input['indices']['cold requirements']



    # if HEN_obj.settings['SCHED']['active']:
    #     sd = sd.reset_index()
    #     sd.set_index(['interval', 'requirement'], inplace=True)    # set multiindexing
    #     streams_hot = HEN_obj.requirements_hot
    #     streams_cold = HEN_obj.requirements_cold

    length = intervals.__len__()

    # initialize python lists to store CCs for each time interval
    ccs = np.empty((2, length), dtype=np.ndarray)
    gccs = np.empty((1, length), dtype=np.ndarray)
    mgccs = np.empty((2, length), dtype=np.ndarray)

    hot_utility = np.zeros((1, length))
    cold_utility = np.zeros((1, length))
    recovery = np.zeros((1, length))

    if isinstance(streams_hot_select, np.ndarray):
        streams_hot = streams_hot_select

    if isinstance(streams_cold_select, np.ndarray):
        streams_cold = streams_cold_select

    if isinstance(intervals_select, np.ndarray):
        intervals = intervals_select

    def calc_cp(temp, streams, streamdata):
        """
        Calculates cumulated heat capacities for multiple streams

        :param temp: temperature nodes
        :param streams: stream numbers
        :param sd: sd
        :return: q
        """

        c_p = np.zeros((temp.size, streams.__len__()))  # initialize array with c_p values

        # fill c_p array with contributions from streams
        for i, tup in enumerate(streams):
            s = tup[0]
            r = tup[1]
            for u in range(temp.size - 1):
                idx = (streamdata['stream nr'] == s) & (streamdata['requirement nr'] == r)

                tin = streamdata.loc[idx, 'T in'].values
                tout = streamdata.loc[idx, 'T out'].values

                mcp = streamdata.loc[idx, 'm'].values * streamdata.loc[idx, 'cp'].values

                active = streams_activity.loc[idx, 'activity'].values[0][t]

                if tin >= temp[u] and tout <= temp[u + 1] and tin > tout:
                    c_p[u, i] = mcp*active
                elif tout >= temp[u] and tin <= temp[u + 1] and tin < tout:
                    c_p[u, i] = mcp*active

        dtemp = temp - np.append(temp[1:], 0)  # calculate temperature differences in individual temperature
        q = np.dot(np.triu(np.ones(dtemp.size)), (np.sum(c_p, axis=1) * dtemp))  # calculate cumulated energies

        return q

    # calculate CCS
    counter = 0
    for t in intervals:
        sd_hot = sd.loc[sd['type'] == 'hot']
        temp_hot = np.flip(np.sort(np.array(sd_hot[['T in', 'T out']]).flatten()))
        temp_hot = temp_hot[temp_hot != 0]  # temperature nodes of hot CC
        q_hot = calc_cp(temp_hot, streams_hot, sd)  # energy nodes of hot CC

        temp_hot = np.array([x for x in temp_hot])
        q_hot = np.array([x for x in q_hot])

        sd_cold = sd.loc[sd['type'] == 'cold']
        temp_cold = np.flip(np.sort(np.array(sd_cold[['T in', 'T out']]).flatten()))
        temp_cold = temp_cold[temp_cold != 0]  # temperature nodes of cold CC
        q_cold = calc_cp(temp_cold, streams_cold, sd)  # energy nodes of cold CC

        temp_cold = np.array([x for x in temp_cold])
        q_cold = np.array([x for x in q_cold])

        if np.max(q_cold) == 0 and np.max(q_hot) == 0:
            continue

        temp_hot_shifted = temp_hot - dTmin / 2  # shifted temperatures
        temp_cold_shifted = temp_cold + dTmin / 2  # shifted temperatures

        # variables that help interpolate temperature differences -> necessary to establish heat recovery potentials
        q_hot_aid = np.concatenate((q_hot[0:1], q_hot, np.array([0])))
        temp_hot_aid = np.concatenate((np.array([100000]), temp_hot_shifted, np.array([-100000])))
        q_cold_aid = np.concatenate((q_cold[0:1], q_cold, np.array([0])))
        temp_cold_aid = np.concatenate((np.array([100000]), temp_cold_shifted, np.array([-100000])))

        # energy difference between hot and cold CC at all temperature nodes
        delta_q_cold = - q_hot + np.flipud(
            np.interp(np.flipud(temp_hot_shifted), np.flipud(temp_cold_aid), np.flipud(q_cold_aid)))
        delta_q_hot = - np.flipud(
            np.interp(np.flipud(temp_cold_shifted), np.flipud(temp_hot_aid), np.flipud(q_hot_aid))) + q_cold

        # value to shift q_cold
        delta_q_corr = - np.min(np.concatenate((delta_q_cold, delta_q_hot)))
        q_cold = q_cold + delta_q_corr

        delta_q_cold = delta_q_cold + delta_q_corr  # delta_q correction
        delta_q_hot = delta_q_hot + delta_q_corr  # delta_q correction

        # store CCs
        if np.max(q_hot) > 0:
            ind = (q_hot == 0).argmax()
            ccs[0, t] = np.concatenate(
                (np.reshape(q_hot[0: ind + 1], (-1, 1)), np.reshape(temp_hot[0: ind + 1], (-1, 1))), axis=1)

        if np.max(q_cold) > np.min(q_cold):
            ind = (q_cold == np.min(q_cold)).argmax()
            ccs[1, t] = np.concatenate(
                (np.reshape(q_cold[0: ind + 1], (-1, 1)), np.reshape(temp_cold[0: ind + 1], (-1, 1))), axis=1)

        # plt.figure()
        # if ccs[0, t] is not None:
        #     plt.plot(ccs[0, t][:, 0], ccs[0, t][:, 1], 'r')
        #
        # if ccs[1, t] is not None:
        #     plt.plot(ccs[1, t][:, 0], ccs[1, t][:, 1], 'b')
        # plt.show()

        # plt.figure()
        # plt.scatter(np.concatenate((delta_q_cold, delta_q_hot)), np.concatenate((temp_hot_shifted, temp_cold_shifted)))
        # plt.show()

        # Calculate GCC
        if np.max(delta_q_cold) > 0:
            ind_cold = np.max(np.nonzero(delta_q_cold)) + 2
        else:
            ind_cold = 0

        if np.max(delta_q_hot) > 0:
            ind_hot = np.min(np.nonzero(delta_q_hot))
        else:
            ind_hot = delta_q_hot.size

        temp = np.concatenate(
            (temp_hot_shifted[: ind_cold], temp_cold_shifted[ind_hot:]))  # concatenate all temperature nodes
        delta_q = np.concatenate(
            (delta_q_cold[: ind_cold], delta_q_hot[ind_hot:]))  # concatenate all energy differences

        gcc_aid = np.concatenate((np.reshape(delta_q, (-1, 1)), np.reshape(temp, (-1, 1))), axis=1)
        gcc_aid = gcc_aid[gcc_aid[:, 1].argsort()[::-1]]

        while gcc_aid[0, 0] == gcc_aid[1, 0]:
            gcc_aid = gcc_aid[1:, :]

        while gcc_aid[-1, 0] == gcc_aid[-2, 0]:
            gcc_aid = gcc_aid[:-1, :]

        gccs[0, t] = gcc_aid

        # if gccs[0, t] is not None:
        #     plt.figure()
        #     plt.plot(gccs[0, t][:, 0], gccs[0, t][:, 1], 'k')
        #     plt.show()

        # Calculation of mGCCs
        ind_pinch = (gcc_aid[:, 0] == 0).argmax()  # identify pinch point

        # slicing of GCC
        if ind_pinch < gcc_aid[:, 0].size - 1:
            mgcc_hot = np.copy(gcc_aid[ind_pinch:, :])
        else:
            mgcc_hot = np.copy(gcc_aid[ind_pinch + 1:, :])

        if ind_pinch > 0:
            mgcc_cold = np.copy(gcc_aid[: ind_pinch + 1, :])
        else:
            mgcc_cold = np.copy(gcc_aid[: ind_pinch:, :])

        # shifting back GCC
        mgcc_hot[:, 1] = mgcc_hot[:, 1] + dTmin / 2
        mgcc_cold[:, 1] = mgcc_cold[:, 1] - dTmin / 2

        # removing pockets of hot mGCC
        mgcc_cold_flipped = np.flipud(mgcc_cold)

        def remove_pockets(mgcc_aid):
            """
            removes heat recovery pockets of mgccs
            """

            for i in range(1, mgcc_aid.shape[0] - 2):
                if np.min(mgcc_aid[i + 1:, 0]) < mgcc_aid[i, 0]:
                    ind = (mgcc_aid[i + 1:, 0]).argmin()  # find index of minimum value

                    temp_new = np.interp(mgcc_aid[i + 1:, 0][ind], mgcc_aid[i - 1:i + 1, 0], mgcc_aid[i - 1:i + 1, 1])

                    mgcc_aid[i: i + 2 + ind, 0] = mgcc_aid[i + 1 + ind, 0]
                    mgcc_aid[i, 1] = temp_new

            ind_first = (mgcc_aid[:, 0] == np.max(mgcc_aid[:, 0])).argmax()
            mgcc_aid = mgcc_aid[:ind_first + 1, :]

            return mgcc_aid

        # store mRCCs
        if mgcc_hot.shape[0] > 0:
            mgcc_hot = remove_pockets(mgcc_hot)
            mgccs[0, t] = mgcc_hot
        if mgcc_cold.shape[0] > 0:
            mgcc_cold = np.flipud(remove_pockets(mgcc_cold_flipped))
            mgccs[1, t] = mgcc_cold

            # plt.figure()
            # if mgccs[0, t] is not None:
            #     plt.plot(mgccs[0, t][:, 0], mgccs[0, t][:, 1], 'r')
            #
            # if mgccs[1, t] is not None:
            #     plt.plot(mgccs[1, t][:, 0], mgccs[1, t][:, 1], 'b')
            # plt.show()

        # Calculate hot/cold utility demand (kW), and heat recovery (kW)
        hot_utility[0, t] = np.max(q_cold) - np.max(q_hot)
        cold_utility[0, t] = - np.min(q_hot) + np.min(q_cold)
        recovery[0, t] = np.max(q_hot) - np.min(q_cold)

    targets = {
        'CCs': ccs,
        'GCCs': gccs,
        'mGCCs': mgccs,
        'UH': hot_utility,
        'UC': cold_utility,
        'Heat Recovery': recovery
    }
    return targets

def calc_qmax(data_input, dTmin, streams_hot_select, streams_cold_select):
    """
    Calculates q max between two or more streams


    :param dTmin: is float and determines the minimum temperature difference
    :param TAM: is boolean and defines whether TAM-Targets are calculated
    :param streams_hot_select: is np.ndarray; selected stream numbers ("all" to select all)
    :param streams_cold_select: is np.ndarray; selected stream numbers ("all" to select all)
    :param intervals_select: is np.ndarray; selected interval numbers ("all" to select all)

    :return: targets
    """

    sd = data_input['streamdata']

    streams_hot = streams_hot_select

    streams_cold = streams_cold_select

    def calc_cp(temp, streams, streamdata):
        """
        Calculates cumulated heat capacities for multiple streams

        :param temp: temperature nodes
        :param streams: stream numbers
        :param sd: sd
        :return: q
        """

        c_p = np.zeros((temp.size, streams.__len__()))  # initialize array with c_p values

        # fill c_p array with contributions from streams
        for i, tup in enumerate(streams):
            s = tup[0]
            r = tup[1]
            for u in range(temp.size - 1):
                idx = (streamdata['stream nr'] == s) & (streamdata['requirement nr'] == r)

                tin = streamdata.loc[idx, 'T in'].values
                tout = streamdata.loc[idx, 'T out'].values

                mcp = streamdata.loc[idx, 'm'].values * streamdata.loc[idx, 'cp'].values

                if tin >= temp[u] and tout <= temp[u + 1] and tin > tout:
                    c_p[u, i] = mcp
                elif tout >= temp[u] and tin <= temp[u + 1] and tin < tout:
                    c_p[u, i] = mcp

        dtemp = temp - np.append(temp[1:], 0)  # calculate temperature differences in individual temperature
        q = np.dot(np.triu(np.ones(dtemp.size)), (np.sum(c_p, axis=1) * dtemp))  # calculate cumulated energies

        return q


    sd_hot = sd.loc[sd['type'] == 'hot']
    temp_hot = np.flip(np.sort(np.array(sd_hot[['T in', 'T out']]).flatten()))
    temp_hot = temp_hot[temp_hot != 0]  # temperature nodes of hot CC
    q_hot = calc_cp(temp_hot, streams_hot, sd)  # energy nodes of hot CC

    sd_cold = sd.loc[sd['type'] == 'cold']
    temp_cold = np.flip(np.sort(np.array(sd_cold[['T in', 'T out']]).flatten()))
    temp_cold = temp_cold[temp_cold != 0]  # temperature nodes of cold CC
    q_cold = calc_cp(temp_cold, streams_cold, sd)  # energy nodes of cold CC


    temp_hot_shifted = temp_hot - dTmin / 2  # shifted temperatures
    temp_cold_shifted = temp_cold + dTmin / 2  # shifted temperatures

    # variables that help interpolate temperature differences -> necessary to establish heat recovery potentials
    q_hot_aid = np.concatenate((q_hot[0:1], q_hot, np.array([0])))
    temp_hot_aid = np.concatenate((np.array([100000]), temp_hot_shifted, np.array([-100000])))
    q_cold_aid = np.concatenate((q_cold[0:1], q_cold, np.array([0])))
    temp_cold_aid = np.concatenate((np.array([100000]), temp_cold_shifted, np.array([-100000])))

    # energy difference between hot and cold CC at all temperature nodes
    delta_q_cold = - q_hot + np.flipud(
        np.interp(np.flipud(temp_hot_shifted), np.flipud(temp_cold_aid), np.flipud(q_cold_aid)))
    delta_q_hot = - np.flipud(
        np.interp(np.flipud(temp_cold_shifted), np.flipud(temp_hot_aid), np.flipud(q_hot_aid))) + q_cold

    # value to shift q_cold
    delta_q_corr = - np.min(np.concatenate((delta_q_cold, delta_q_hot)))
    q_cold = q_cold + delta_q_corr

    qmax = np.max(q_hot) - np.min(q_cold)

    return qmax