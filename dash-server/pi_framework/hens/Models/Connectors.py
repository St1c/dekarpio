import numpy as np

from pyomo.environ import *


def connector_HEN_UC(model, port_hen, port_uc, connector_name, HEN, UC):
    ##########################################################################
    ### EQUATIONS interface HENS/UC
    ##########################################################################

    int_uc = [UC['tss']*i for i in range(UC['nt'])]
    

    intervals = HEN.data_input['intervals']['index']
    durations = HEN.data_input['intervals']['durations']

    int_hens = [sum(durations[:i]) for i in intervals]
    int_hens.append(sum(durations))

    l = int_hens[-1] / (UC['nt'])

    m_conv = np.zeros((len(int_hens)-1, len(int_uc)))
    for i in intervals:
        m_conv[i, int(int_hens[i]/l):int(int_hens[i+1]/l)] = 1

    def confun(model, t_uc):
        t_hens = model.set_TS
        return port_uc[t_uc]*1000 == sum(m_conv[t, t_uc]*port_hen[t] for t in t_hens)

    con = Constraint(model.set_t, rule=confun)
    setattr(model, 'con_connector_' + connector_name, con)
    return model


def connector_UC(model, ports1, ports2, connector_name):
    con = Constraint(model.set_t, rule=lambda model, t: sum(ports1) == sum(ports2))
    setattr(model, 'con_connector_' + connector_name, con)
    return model
