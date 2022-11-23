settings = {
    'SCHED': {
        'active': 1,    # toggles rescheduling
    },
    'UC': {
        'active': 0,    # toggles UC connection
    },
    'COSTS': {
        'beta': 0.9,  # cost exponent for HEX area (0 - 1)
        'HEX fix': 24000,  # cost for HEX installation
        # 'HEX fix': 0,  # cost for HEX installation
        'HEX var': 167,  # cost for HEX area
        # 'HEX var': 0,  # cost for HEX area
        'annualization': 10  # years for annualization
    },
    'OPT': {
        'timelimit': 60,  # seconds
    },
    'LIN': {
        'rel_err': 0.05,  # sets max. rel. error for LMTD approximation (0 - 1)
        'num_eq': 5,  # sets number of eq. used to approximate A^beta (default = 5)
        'res': 150,  # resolution for data points
        'dom_fact_load': 0.2,  # factor for discretization domain (dom_fact_load * qmax - qmax)
        'res_ut': 500,  # resolution for data points for ut
        'dom_fact_ut_min': 0.05,  # factor for discretization domain for ut (dom_fact_ut_min * qmax - dom_fact_ut_max * qmax)
        'dom_fact_ut_max': 0.7,  # factor for discretization domain for ut (dom_fact_ut_min * qmax - dom_fact_ut_max * qmax)
        'res_add_HEX': 100,  # resultion for the approximation of additional HEX area
    },
    'TIGHT': {
        'set': True,
        'LMTD': True,  # adds additional constraints for LMTD
        'zmin': True,  # adds additional constraints for minimum HEX units
        'dup': True,  # adds additional constraints to avoid redundant networks
        'z_add': 100,  # constant that is added to big-M for dT Calculations
    },
    'SIMP': {
        'min HR': 0,  # minimum percentage of maximum HR (0 - 1, 0 = off)
        'min HR TAM': 0,  # minimum percentage of maximum HR (0 - 1, 0 = off)
        'max_pair_hex': True,  # allow only one HEX per stream pair, # TODO: cannot be turned off for retrofit problems!!
        'equal z': True  # no HEX by-passing
    },
    'RETROFIT': {
        # 'max_changes': 6,  # number of changes allowed within the the HEN   # FIXME: die Optionen macht noch nichts!
        'reuse': True,  # reuse HEX elsewhere in the HEN
        'add_hex': 0.3  # factor for add HEX area to existing HEX (0 - )
    },
    'HEN': {
        'stages': 6,  # number of temperature stages (including utility states & storage)  (ideal (5)6-7)
        'dTmin': 30,  # minimum temperature differences in the HEN (default = 5)
        'soft': True,  # allow for 'soft' streams
    },
    'defaults': {
        'h': 0.2,
        'duration': 1,
        'interval': 1,
        'Medium': "Air",
    },
    'Heat Pumps': {
        'LIN': {
            'res': 20,  # Discretization for heat pump linearization
            'dom_fact': 0.5,  # factor for discretization domain (0 - 1*dom_fact)
            'Qc_Qe': 10,  #factor for relation between Qc and Qe (Qc <= Qc_Qe * Qe
        },
        'COSTS': {
            'P_el specific': 0,  # P_el_max * P_el specific - source: screw compressor from DACE price booklet (incl. motor)
            'Q_max specific': 0,
            'P_el fix': 0,  # step-fixed costs for HP interegration - - source: screw compressor from DACE price booklet (incl. motor)
            'HEX-cost related': 0,  # factor for additional HEX-related HP costs - 1 means double HEX costs
            'annualization': 10  # factor for additional HEX-related HP costs - 1 means double HEX costs
        }
    },
    'Storages': {
        'LIN': {
            'res': 20,  # Discretization for heat pump linearization
            'dom_fact': 0.2,  # factor for discretization domain (0.2 * dQmax - dQmax)
        },
        'cp': 4.21  # kJ/kg... specific heat capacity of storage material
    }


}
def load_settings():



    return settings

def load_utilities():

    # UH, UC, UIC, UIH
    # -----
    # Tin       Inlet Temperature °C
    # Tout      Outlet Temperature °C
    # dTmin     minimum temperature difference °C
    # h         Heat transfer coefficient kW/m²K
    # costs     specific energy costs per year €/kWh/y

    # CU
    # -----
    # Heat Pumps
    # ---
    # Tmax              Maximum Condenser Temperature °C
    # Tmin              Minimum Evaporator Temperature °C
    # dTmin             minimum temperature difference °C
    # eta_c             Carnot efficiency factor
    # dT_lift_max       maximum Temperature lift °C
    # dT_lift_min       minimum temperature difference °C
    # h                 Heat transfer coefficient kW/m²K
    # phase change      determines whether a phase change takes place in the HEX
    # costs             specific electricity costs per year €/kWh/y

    # Storages
    # ---
    # Tmax              Maximum hot tank Temperature °C
    # Tmin              Minimum cold tank Temperature °C
    # dTmin             minimum temperature difference °C
    # dT_lift_min       minimum temperature difference between tanks °C
    # h                 Heat transfer coefficient kW/m²K
    # phase change      determines whether a phase change takes place in the HEX
    # costs var         specific storage costs €/kg
    # costs fix         step fixed storage costs €
    # annualization     years for annualization

    UIH_hot = 130
    UIH_cold = 120
    conversion_units = {
        'UH': {
            'Steam HP': {'Tin': 500, 'Tout': 450, 'dTmin': 5, 'h': 0.2, 'costs': 0.04*8760*0.9, 'Medium': 'steam condensing'},
            # 'Steam MP': {'Tin': 400, 'Tout': 350, 'dTmin': 5, 'h': 0.2, 'costs': 0.04*24*52*7}
        },
        'UC': {
            'Cooling Water': {'Tin': -10, 'Tout': -5, 'dTmin': 5, 'h': 0.2, 'costs': 0.001*8760*0.9, 'Medium': 'water'},
        },
        'UIC': {
            'LTD in': {'Tin': UIH_cold, 'Tout': UIH_hot, 'dTmin': 5, 'h': 0.2, 'costs': 0, 'Medium': 'water evaporating'},
        },

        'UIH': {
            'LTD out': {'Tin': UIH_hot, 'Tout': UIH_cold, 'dTmin': 5, 'h': 0.2, 'costs': 0, 'Medium': 'steam condensing'},
        },

        'CU': {
            'Compression Heat Pump 1': {'Tmax': 100, 'Tmin': 0, 'dTmin': 5, 'eta_c': 0.5, 'dT lift max': 70,
                    'dT lift min': 30, 'h': 7, 'phase change': 1, 'costs': 0.04*8760*0.9, 'Medium': 'water'},
            # 'Two-Tank Storage': {'Tmax': 100, 'Tmin': 30, 'dTmin': 5, 'dT lift min': 30, 'h': 0.2, 'phase change': 0,
            #     'costs var': 0.3*24, 'costs fix': 25000, 'annualization': 20},
            # 'Compression Heat Pump 2': {'Tmax': 120, 'Tmin': 30, 'dTmin': 5, 'eta_c': 0.5, 'dT lift max': 70,
            #                           'dT lift min': 30, 'h': 0.2, 'phase change': 1, 'costs': 0.1*24*52*7/10},
        }
    }

    for type in conversion_units.keys():
        for utility in conversion_units[type].keys():
            available_media = get_alpha_dict().keys()
            if conversion_units[type][utility]['Medium'] in available_media:
                conversion_units[type][utility]['h'] = alpha_sepc(conversion_units[type][utility]['Medium'])

    return conversion_units

def load_retrofit():
    # retrofit = {type: {nr.: {'location': (HS,CS,Stage), 'area': area}}}

    retrofit = {
        'existing HEX': {
            # 'UH': {
            #     1: {'location': (0, 8, 1), 'area': 100},
            # },
            # 'Direct': {
                # 1: {'location': (36, 33, 2), 'area': 1000},
                # 2: {'location': (39, 33, 2), 'area': 136}
            # },
        }
    }
    return retrofit


def get_alpha_dict():
    alpha_dict = {
        'water': 2.5,
        'steam condensing': 11.6,
        'steam superheated': 0.1,
        'water evaporating': 4,
        'gas': 0.05,
        'air': 0.02,
        'acid': 2.5
    }
    return alpha_dict




def alpha_sepc(med):
    alpha_dict = get_alpha_dict()

    if med in alpha_dict.keys():
        h = alpha_dict[med]
    else:
        h = None

    return h

def LTD_Length():
    LTD_Length = {
        tuple(['hot strip mill', 'pickling line']): 50*1.2, #m pip length distance + 20%
        tuple(['hot strip mill', 'continuous annealing']): 100*1.2,
        tuple(['hot strip mill', 'galvanizing line']): 300*1.2, 
    }
#exception  for ca + gv =350*1.2 


    #  LTD_Length_eval= {}
    #  for key in LTD_Length.keys():   
    #      LTD_Length_eval[key] = LTD_Length[key]
    #  return LTD_Length_eval

def hex_spec():
    hex_spec = {
        tuple(['water', 'gas']): 'Shell and tube', # liste zweiter eintrag defoult, nur bei übergabe berücksichtigen 
        tuple(['water', 'steam superheated']): 'Shell and tube',
        tuple(['water', 'water evaporating']): 'Shell and tube',
        tuple(['water', 'water']): 'Shell and tube',
        tuple(['water', 'acid']): 'SHT Graphit',

        tuple(['gas', 'gas']): 'Plate st/st',
        tuple(['gas', 'steam superheated']): 'Plate st/st',
        tuple(['gas', 'water evaporating']): 'Shell and tube',
        tuple(['gas', 'water']): 'Shell and tube',
        tuple(['gas', 'acid']): 'SHT Graphit',

        tuple(['steam superheated', 'gas']): 'Plate st/st',
        tuple(['steam superheated', 'steam superheated']): 'Plate st/st',
        tuple(['steam superheated', 'water evaporating']): 'Shell and tube',
        tuple(['steam superheated', 'water']): 'Shell and tube',
        tuple(['steam superheated', 'acid']): 'SHT Graphit',

        tuple(['steam condensing', 'gas']): 'Shell and tube',
        tuple(['steam condensing', 'steam superheated']): 'Shell and tube',
        tuple(['steam condensing', 'water evaporating']): 'Shell and tube',
        tuple(['steam condensing', 'water']): 'Shell and tube',
        tuple(['steam condensing', 'acid']): 'SHT Graphit',

        tuple(['steam evaporating', 'gas']): 'Shell and tube',
        tuple(['steam evaporating', 'steam superheated']): 'Shell and tube',
        tuple(['steam evaporating', 'water evaporating']): 'Shell and tube',
        tuple(['steam evaporating', 'water']): 'Shell and tube',
        tuple(['steam evaporating', 'acid']): 'SHT Graphit'

    }

# limit m^2 
#limit_min m^2 

    hex_types = {
        'Shell and tube': { # Cost-Function derived from DACE Pricebooklet 2019
            'beta': 0.81103,
            'c_fix': 19394.56364,
            'c_var': 609.51257
            },
        'SHT Helix st/copper': {
            'beta': 0.627,
            'c_fix': 0,
            'c_var': 614,
            'limit': 47 #https://www.researchgate.net/publication/331540828_Total_costs_of_shell_and_tube_heat_exchangers_with_concentric_helical_tube_coils/link/5c84a8c9299bf1268d4c8548/download
            },    
        'SHT st/sst': { # Cost-Function derived from DACE Pricebooklet 2019
            'beta': 0.86747,
            'c_fix': 19593.16290,
            'c_var': 637.91914,
            },

        'SHT st/copper': { #https://www.researchgate.net/profile/Marko-Jaric/publication/331311675_Manufacturing_costs_of_Shell_and_Tube_Heat_Exchangers_with_Parallel_Helical_Tube_Coils/links/5c727735458515831f6a03a5/Manufacturing-costs-of-Shell-and-Tube-Heat-Exchangers-with-Parallel-Helical-Tube-Coils.pdf
            'beta': 1,
            'c_fix': 749,
            'c_var': 332,
            'limit': 38
            },
        'Plate st/st': {  # Cost-Function derived from DACE Pricebooklet 2019
            'beta': 0.83434,
            'c_fix': 12638.34538 ,
            'c_var': 526.08630 ,
            },
        'Plate braced sst/sst': { #https://www.researchgate.net/profile/Marko-Jaric/publication/331311675_Manufacturing_costs_of_Shell_and_Tube_Heat_Exchangers_with_Parallel_Helical_Tube_Coils/links/5c727735458515831f6a03a5/Manufacturing-costs-of-Shell-and-Tube-Heat-Exchangers-with-Parallel-Helical-Tube-Coils.pdf
            'beta': 0.637,
            'c_fix': 0,
            'c_var': 832,
            'limit': 61
            },
        'Plate gasket sst/sst': { #https://www.researchgate.net/profile/Marko-Jaric/publication/331311675_Manufacturing_costs_of_Shell_and_Tube_Heat_Exchangers_with_Parallel_Helical_Tube_Coils/links/5c727735458515831f6a03a5/Manufacturing-costs-of-Shell-and-Tube-Heat-Exchangers-with-Parallel-Helical-Tube-Coils.pdf
            'beta': 0.516,
            'c_fix': 0,
            'c_var': 1584,
            'limit': 200
            },
        'Plate Graphit': { #price booklet
            'beta': 0.74450,
            'c_fix': 10104.48536,
            'c_var': 5313.43382,
            'limit': 100
            }, 

        'SHT Graphit': { #price booklet
            'beta': 0.73615,
            'c_fix': 10750.97407,
            'c_var': 6175.33697,
            'limit': 100,
            'limit_min': 3
            },


    }

    hex_spec_eval= {}
    for key in hex_spec.keys():   
        hex_spec_eval[key] = hex_types[hex_spec[key]]
        hex_spec_eval[key]['Type'] = hex_spec[key]


    return hex_spec_eval