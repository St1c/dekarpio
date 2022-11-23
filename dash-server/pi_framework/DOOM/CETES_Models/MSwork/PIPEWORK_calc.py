# -*- coding: utf-8 -*-
"""
Created on Mon May 18 15:41:21 2020

@author: SchoenyM
"""
import numpy as np
import pandas as pd
from math import sqrt, pow, pi
from pi_framework.DOOM.CETES_Models.MSwork.AD2000_calc import shell_thickness, svalv_size
import CoolProp.CoolProp as cp
import matplotlib.pyplot as plt

#%%

def pipework_cfunc(load, maxoverload, temperature, pressure, material_select=None, n_sto=None, op_mode_select=None, ball_valve_DN=None, verbose=False):
    '''
    
    Cost estimation regarding pipework, valve and instruments for RUTHS steam accumulator (pressure vessel)
    
    INPUT:
    
    load:
        specifies maximum operating load of boiler in kg / h
    maxoverload: 
        specifies highest overload demand when the accumulator(s) is at its design pressure in kg / h
    
    temperature:
        specifies the operating temperature of steam accumulator in °C
        
    pressure:
        specifies the operating pressure of steam accumulator in bar
            
    DESCRIPTION:
        
    Cost estimation calculation regarding pipework, valve and instruments for RUTHS steam accumulator for
    
    Variant a) single steam accumulator (large volume))
    
    Variant b) parallel situated steam accumulators (small volume))
    
    '''
    
# === Fixed valves and instruments per vessel =================================
    '''
                                                                            Total Costs per steam accumulator in EUR
    
    3x bourdon pressure gauge incl. ring type syphon tube, liquid damping   1.260 .-
    
    3x bimetallic temperature gauge incl. thermo wells                      1.455 .-
    
    1x drain valve DN50 PN40                                                830 .-
    
    1x vacuum breaker DN15 PN40                                             340 .-
    
    All prices according to DACE price booklet or https://www.cooneybrothers.com/
                                                  https://www.chryssafidis.com/en/cat.6

    
    '''
    Misc_valv_c = 1260 + 1455 + 830 + 340 # Fix equipment costs total EUR 3.885 .-

    if verbose:
        print('\nFix costs for valve & instruments on accumulator equipped: EUR {0:2.2f}.-'.format(Misc_valv_c))
 

# === Calculation of steam density =
    
    rho_steam = cp.PropsSI('D', 'T', temperature + 273.15, 'Q', 1 , 'IF97::Water')  # in kg / m^3
    
# === Operating mode ==========================================================
    
    op_mode_list = ['single','parallel']

    if op_mode_select == None:
        op_mode = input('Please choose operating mode of accumulator (single / parallel):')
    else:
        op_mode = op_mode_select
    
    c_steam_sup = 40 # steam fluid velocity over supply pipe in m/s
    c_steam_dis = 40 # steam fluid velocity over discharge pipe in m/s

# === Calculation of supply/discharge pipe - single vessel ====================
    if verbose:
        print('=== CALCULATION OF NOMINAL DIAMETER SUPPLY / DISCHARGE PIPE ===')
    
    if op_mode == op_mode_list[0]:
                          
        op_mode_num = 1
        
        iD_calc_sup = sqrt((4 * load) / (3600 * pi * rho_steam * c_steam_sup)) * 1000 # calc. inner diameter of supply pipe in mm
        
        iD_calc_dis = sqrt((4 * (load + maxoverload)) / (3600 * pi * rho_steam * c_steam_dis)) * 1000 # calc. inner diameter of discharge pipe in mm
                           
    else:
        
# === Calculation of supply/discharge pipe - parallel vessels =================
        if n_sto == None:
            op_mode_num = int(input('Please choose number of parallel accumulators:'))
        else:
            op_mode_num = n_sto
        
        load_p = load / op_mode_num
        
        maxoverload_p = maxoverload / op_mode_num
        
        iD_calc_sup = sqrt((4 * load_p) / (3600 * pi * rho_steam * c_steam_sup)) * 1000 # calc. inner diameter of supply pipe in mm
        
        iD_calc_dis = sqrt((4 * (load_p + maxoverload_p)) / (3600 * pi * rho_steam * c_steam_dis)) * 1000 # in mm
        
# === Calculation of pipe outer diameter and pipe wall thickness ==============
    if verbose:
        print('\n=== Calculating thickness of supply pipe ===')
    t_calc_sup = float(shell_thickness(iD_calc_sup, temperature, pressure, material_select))

    if verbose:
        print('\n=== Calculating thickness of discharge pipe ===')
    t_calc_dis = float(shell_thickness(iD_calc_dis, temperature, pressure, material_select))

    if verbose:
        print('\nCalculated pipe wall thickness: Supply Pipe min. {} mm, Discharge Pipe min. {} mm '.format(t_calc_sup,t_calc_dis))
    
    oD_calc_sup = iD_calc_sup + 2 * t_calc_sup # calculated outer diameter of supply pipe
    
    oD_calc_dis = iD_calc_dis + 2 * t_calc_dis # calculated outer diameter of supply pipe
    
    DN_dict = {'21.3':'15',
               '26.9':'20',
               '33.7':'25',
               '42.4':'32',
               '48.3':'40',
               '60.3':'50',
               '76.1':'65',
               '88.9':'80',
               '114.3':'100',
               '139.7':'125',
               '168.3':'150',
               '219.1':'200'}


    
    DN_list = [21.3,26.9,33.7,42.4,48.3,60.3,76.1,88.9,114.3,139.7,168.3,219.1]


    coeff_DN = np.polyfit(DN_list, [int(list(DN_dict.values())[i]) for i in range(len(DN_dict))], 1)

    # plt.figure()
    # plt.plot(DN_list, [float(list(DN_dict.values())[i]) for i in range(len(DN_dict.keys()))])
    # plt.plot(np.array(DN_list), np.array(DN_list)*coeff_DN[0] + coeff_DN[1])

    oD_pipe_sup = oD_calc_sup
    for i in DN_list:
        
        if oD_calc_sup <= i:
            
            oD_pipe_sup = i

            break
    if (oD_pipe_sup == oD_calc_sup) & (oD_calc_sup not in DN_list):
        print('Required DN for supply not available. Proceeding with nearest DN')

        DN_pipe_sup = coeff_DN[0] * oD_pipe_sup + coeff_DN[1]
    else:
        DN_pipe_sup = DN_dict['{}'.format(oD_pipe_sup)]

    oD_pipe_dis = oD_calc_dis
    for i in DN_list:
        
        if oD_calc_dis <= i:
            
            oD_pipe_dis = i

            break
    if (oD_pipe_dis == oD_calc_dis) & (oD_calc_dis not in DN_list):
        print('Required DN for discharging not available. Proceeding with calculated DN')

        DN_pipe_dis = coeff_DN[0] * oD_pipe_dis + coeff_DN[1]
    else:
        DN_pipe_dis = DN_dict['{}'.format(oD_pipe_dis)]

    if verbose:
        print('\n=== Choosing nominal diameter supply/discarge pipe ===')


    if verbose:
        print('\n=== Calculating thickness of chosen supply pipe ===')
    t_pipe_sup = shell_thickness(oD_pipe_sup, temperature, pressure, material_select)

    if verbose:
        print('\n=== Calculating thickness of chosen discharge pipe ===')
    t_pipe_dis = shell_thickness(oD_pipe_dis, temperature, pressure, material_select)

    if verbose:
        print('\nSUPPLY SIDE - Nominal diameter: DN{} \nOuter diameter: {} mm \nPipe wall thickness: min. {} mm'.format(DN_pipe_sup,oD_pipe_sup,t_pipe_sup))
        print('\nDISCHARGE SIDE - Nominal diameter: DN{} \nOuter diameter: {} mm \nPipe wall thickness: min. {} mm'.format(DN_pipe_dis,oD_pipe_dis,t_pipe_dis))

# === VALVE COST CALCULATION ==================================================

# === Cost calculation of pressure relief valve / pressure reducing valve
    
    prv_in_c = 148.92 * float(DN_pipe_sup) + 3922.9 # pressure relief valve   
    
    prv_out_c = 148.92 * float(DN_pipe_dis) + 3922.9 # pressure reducing valve 
    
    if pressure > 40:
        if verbose:
            print('\nATTENTION: Operating pressure is to high for pressure relief valve / pressure reducing valve !!!')
    
    if temperature > 350:
        if verbose:
            print('\nATTENTION: Operating temperature is to high for pressure relief valve / pressure reducing valve !!!')

    if verbose:
        print('\nPRESSURE CONTROL ON SUPPLY / DISCHARGE SIDE')
        print('\nPressure relief valve cost for accumulator: EUR {0:2.2f}.-'.format(prv_in_c))
        print('\nPressure reducing valve cost for accumulator: EUR {0:2.2f}.-'.format(prv_out_c))
    
# === Cost calculation of safety valve ========================================
    if verbose:
        print('\nSIZING OF SAFETY VALVE')
    
    # DN_svalv = svalv_size(op_mode_num, maxoverload)
    DN_svalv = svalv_size(op_mode_num, load)

    if pressure <= 20:
                
        svalv_c = 0.0695 * pow(float(DN_svalv),2) + 25.305 * float(DN_svalv) + 1002.8
        if verbose:
            print('\nSafety valve DN',DN_svalv,'costs for accumulator: EUR {0:2.2f}.-'.format(svalv_c))
    
    elif 20 < pressure <= 50:
        
        if pressure > 40:
            if verbose:
                print('\nATTENTION: Operating pressure is to high for safety valve SV60 !!!')
        
        svalv_c = 0.0565 * pow(float(DN_svalv),2) + 50.909 * float(DN_svalv) + 333.14
        if verbose:
            print('\nSafety valve DN',DN_svalv,'costs for accumulator: EUR {0:2.2f}.-'.format(svalv_c))
        
    elif 50 < pressure <= 110:
        if verbose:
            print('\nATTENTION: Operating pressure is to high for safety valve SV60 !!!')
        
        svalv_c = 0.0873 * pow(float(DN_svalv),2) + 53.802 * float(DN_svalv) - 308.3
        if verbose:
            print('\nSafety valve DN',DN_svalv,'costs for accumulator: EUR {0:2.2f}.-'.format(svalv_c))
        
    else:
        if verbose:
            print('Operating pressure is TOO HIGH !!!')
 
# === Calculation of float ball valve =========================================

    if ball_valve_DN == None:
        DN = input('Please choose DN (up to DN50) for float ball valve: ')
    else:
        DN = ball_valve_DN
    
    if pressure <= 16:
            
        fbv_c = 3.4164 * pow(float(DN),2) - 10.278 * float(DN) + 2462.3 # up to PN16   
    
    else:
        
        fbv_c = 97.552 * float(DN) + 12774 # up to PN80
        
        if pressure > 80:
            if verbose:
                print('\nATTENTION: Nominal pressure is to high for ball float valve !!!')
    if verbose:
        print('\nFloat ball valve cost for accumulator: EUR {0:2.2f}.-'.format(fbv_c))

# === Total costs for pipework, valves and instruments ========================                  
    
    Pipe_inst_c_dict = {'15':'164',
                        '20':'186',
                        '25':'207',
                        '32':'231',
                        '40':'254',
                        '50':'286',
                        '65':'348',
                        '80':'403',
                        '100':'499',
                        '125':'603',
                        '150':'717',
                        '200':'908'}

    coeff_pipe_inst_c = np.polyfit([int(list(Pipe_inst_c_dict.keys())[i]) for i in range(len(Pipe_inst_c_dict))], [int(list(Pipe_inst_c_dict.values())[i]) for i in range(len(Pipe_inst_c_dict))], 1)

    # plt.figure()
    # plt.plot([int(list(Pipe_inst_c_dict.keys())[i]) for i in range(len(Pipe_inst_c_dict))], [int(list(Pipe_inst_c_dict.values())[i]) for i in range(len(Pipe_inst_c_dict))])
    # plt.plot(np.array([int(list(Pipe_inst_c_dict.keys())[i]) for i in range(len(Pipe_inst_c_dict))]), np.array([int(list(Pipe_inst_c_dict.keys())[i]) for i in range(len(Pipe_inst_c_dict))])*coeff_pipe_inst_c[0] + coeff_pipe_inst_c[1])
    
    sup_lenght = 5.0 # supply side including fitting and installation work in m
    dis_lenght = 5.0 # discharge side ... in m

    try:
        Pipework_c = (sup_lenght * float(Pipe_inst_c_dict[DN_pipe_sup]) + dis_lenght * float(Pipe_inst_c_dict[DN_pipe_dis])) * op_mode_num
    except:
        Pipework_c = (sup_lenght * float(coeff_pipe_inst_c[0]*DN_pipe_sup + coeff_pipe_inst_c[1]) + dis_lenght * float(coeff_pipe_inst_c[0]*DN_pipe_dis + coeff_pipe_inst_c[1])) * op_mode_num
    
    Valv_Inst_cost = (Misc_valv_c + prv_in_c + prv_out_c + fbv_c + svalv_c) * op_mode_num
    
    Total_costs = Pipework_c + Valv_Inst_cost
    
    return '{0:2.2f}'.format(Total_costs)
    
    

