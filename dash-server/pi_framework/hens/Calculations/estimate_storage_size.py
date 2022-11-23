import numpy as np


def estimate_storage_size(self, dTmin, Tmax, Tmin):
    """
    This function uses already calculated mGCCs to determine a target for storge size
    :return:
    """

    # targets.calc_targets(self, dTmin, 0, self.streams_hot, self.streams_cold, self.data_input['intervals']['index'])
    targets = self.targets['targets']
    
    temp_hot = []
    temp_cold = []
    for t in self.data_input['intervals']['index']:
        if targets['mGCCs'][0][t] is not None:
            temp_hot.extend(targets['mGCCs'][0][t][:, 1].tolist())
        if targets['mGCCs'][1][t] is not None:
            temp_cold.extend(targets['mGCCs'][1][t][:, 1].tolist())

    temp_hot_unique = np.unique(temp_hot)
    temp_cold_unique = np.unique(temp_cold)

    q_hot = np.zeros((len(temp_hot_unique), len(self.data_input['intervals']['index'])))
    q_cold = np.zeros((len(temp_cold_unique), len(self.data_input['intervals']['index'])))

    for t in self.data_input['intervals']['index']:
        for i in range(len(temp_hot_unique)):
            if targets['mGCCs'][0][t] is not None:
                temp_hot_t = np.flip(np.concatenate(([10000], targets['mGCCs'][0][t][:, 1], [0])))
                q_hot_t = np.flip(np.concatenate(([targets['mGCCs'][0][t][0, 0]],
                                                  targets['mGCCs'][0][t][:, 0],
                                                  [targets['mGCCs'][0][t][-1, 0]])))
                q_hot_t = (q_hot_t - q_hot_t[0]) * (-1)
                q_hot[i, t] = np.interp(temp_hot_unique[i], temp_hot_t, q_hot_t) * self.data_input['intervals']['durations'][t]

        for j in range(len(temp_cold_unique)):
            if targets['mGCCs'][1][t] is not None:
                temp_cold_t = np.flip(np.concatenate(([10000], targets['mGCCs'][1][t][:, 1], [0])))
                q_cold_t = np.flip(np.concatenate(([targets['mGCCs'][1][t][0, 0]],
                                                   targets['mGCCs'][1][t][:, 0],
                                                   [targets['mGCCs'][1][t][-1, 0]])))
                q_cold[j, t] = np.interp(temp_cold_unique[j], temp_cold_t, q_cold_t) * self.data_input['intervals']['durations'][t]

    q_hot_sum = np.sum(q_hot, axis=1)
    q_cold_sum = np.sum(q_cold, axis=1)

    # plt.figure()
    # plt.plot(q_hot_sum, temp_hot_unique, 'r')
    # plt.plot(q_cold_sum, temp_cold_unique, 'b')
    # plt.show()

    temp_hot_shifted = temp_hot_unique - dTmin / 2  # shifted temperatures
    temp_cold_shifted = temp_cold_unique + dTmin / 2  # shifted temperatures

    # variables that help interpolate temperature differences -> necessary to establish heat recovery potentials
    q_hot_aid = np.concatenate((q_hot_sum[0:1], q_hot_sum, q_hot_sum[-1:]))
    temp_hot_aid = np.concatenate((np.array([-100000]), temp_hot_shifted, np.array([100000])))
    q_cold_aid = np.concatenate((q_cold_sum[0:1], q_cold_sum, q_cold_sum[-1:]))
    temp_cold_aid = np.concatenate((np.array([-100000]), temp_cold_shifted, np.array([100000])))

    if (len(q_hot_aid) == 0) or (len(q_cold_aid) == 0):
        return 0

    # energy difference between hot and cold CC at all temperature nodes
    delta_q_cold = - q_hot_sum + np.interp(temp_hot_shifted, temp_cold_aid, q_cold_aid)
    delta_q_hot = - np.interp(temp_cold_shifted, temp_hot_aid, q_hot_aid) + q_cold_sum

    # value to shift q_cold
    delta_q_corr = - np.min(np.concatenate((delta_q_cold, delta_q_hot)))
    q_cold_sum = q_cold_sum + delta_q_corr

    # plt.figure()
    # plt.plot(q_hot_sum, temp_hot_unique, 'r')
    # plt.plot(q_cold_sum, temp_cold_unique, 'b')
    # plt.show()

    dQ_cold = np.interp(Tmax - dTmin, np.concatenate((np.array([-100000]), temp_cold_unique, np.array([100000]))),
                        np.concatenate((q_cold_sum[0:1], q_cold_sum, q_cold_sum[-1:]))) - q_cold_sum[0]
    dQ_hot = q_hot_aid[-1] - np.interp(Tmin + dTmin,
                                       np.concatenate((np.array([-100000]), temp_hot_unique, np.array([100000]))),
                                       q_hot_aid)

    dQmin = min(dQ_cold, dQ_hot)

    T_cut_hot = np.interp(q_hot_sum[-1] - dQmin, q_hot_sum, temp_hot_unique)
    T_cut_cold = np.interp(dQmin, q_cold_sum - np.min(q_cold_sum), temp_cold_unique)

    Q_hot_t = np.zeros((len(self.data_input['intervals']['index'])))
    Q_cold_t = np.zeros((len(self.data_input['intervals']['index'])))

    dQ = np.zeros((len(self.data_input['intervals']['index']) + 1))
    for t in self.data_input['intervals']['index']:
        if targets['mGCCs'][0][t] is not None:
            temp_hot_t = np.flip(np.concatenate(([10000], targets['mGCCs'][0][t][:, 1], [-1000])))
            q_hot_t = np.flip(np.concatenate(([targets['mGCCs'][0][t][0, 0]],
                                              targets['mGCCs'][0][t][:, 0],
                                              [targets['mGCCs'][0][t][-1, 0]])))
            q_hot_t = (q_hot_t - q_hot_t[0]) * (-1)
            Q_hot_t[t] = (q_hot_t[-1] - np.interp(T_cut_hot, temp_hot_t, q_hot_t)) * self.data_input['intervals']['durations'][t]

        if targets['mGCCs'][1][t] is not None:
            temp_cold_t = np.flip(np.concatenate(([10000], targets['mGCCs'][1][t][:, 1], [-1000])))
            q_cold_t = np.flip(np.concatenate(([targets['mGCCs'][1][t][0, 0]],
                                               targets['mGCCs'][1][t][:, 0],
                                               [targets['mGCCs'][1][t][-1, 0]])))
            Q_cold_t[t] = np.interp(T_cut_cold, temp_cold_t, q_cold_t) * self.data_input['intervals']['durations'][t]

        dQ[t] = dQ[t] + Q_hot_t[t] - Q_cold_t[t]

    dQ_target = max(dQ) - min(dQ)

    return dQ_target