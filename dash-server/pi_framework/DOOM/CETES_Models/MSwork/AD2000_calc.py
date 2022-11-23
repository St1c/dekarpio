# -*- coding: utf-8 -*-
"""
Spyder Editor

Dies ist eine temporäre Skriptdatei.
"""

import numpy as np
import pandas as pd
from scipy import interpolate
from time import sleep

#%%

def shell_thickness(diameter, temperature, pressure, material_select=None, verbose=False):
    """
    Calculates thickness for shell of RUTHS steam accumulator (pressure vessel)
    according to AD2000 calculation sheet B01
    
    INPUT:
    diameter:
        specifies the outer diameter of shell in mm
        
    temperature:
        specifies the operating temperature of steam accumulator in °C
        
    pressure:
        specifies the operating pressure of steam accumulator in bar -> 0.1 MPa
        
        
    DESCRIPTION:
        
    Strength calculation of minimal shell thickness 's'
    """

    # Table for K-Value Calculation
    # =============================================================================
    AD2000_B01_table4_data = {}
    
    AD2000_B01_table4_data['calculation temperature - °C'] = np.array([
            100.0,200.0,250.0,300.0
            ])
    
    AD2000_B01_table4_data['strength value [1.0038, s <= 16 mm] - MPa'] = np.array([
            187.0,161.0,143.0,122.0, # S235JR <= 16 mm plate thickness
            ])
    
    AD2000_B01_table4_data['strength value [1.0038, s <= 40 mm] - MPa'] = np.array([
            180.0,155.0,136.0,117.0  # S235JR <= 40 mm plate thickness         
            ])
    
    AD2000_B01_table4_data['strength value [1.0044, s <= 16 mm] - MPa'] = np.array([
            220.0,190.0,180.0,150.0, # S275JR <= 16 mm plate thickness
            ])
    
    AD2000_B01_table4_data['strength value [1.0044, s <= 40 mm] - MPa'] = np.array([
            210.0,180.0,170.0,140.0  # S275JR <= 40 mm plate thickness         
            ])
    
    AD2000_B01_table4_data['strength value [1.0577, s <= 16 mm] - MPa'] = np.array([
            254.0,226.0,206.0,186.0, # S355JR <= 16 mm plate thickness
            ])
    
    AD2000_B01_table4_data['strength value [1.0577, s <= 40 mm] - MPa'] = np.array([
            249.0,221.0,202.0,181.0  # S355JR <= 40 mm plate thickness         
            ])
    
    AD2000_B01_table4_data['strength value [1.4301] - MPa'] = np.array([
            191.0,157.0,145.0,135.0,  #from Stainless Steel Handbook - 0.1% - Proof Stress
            ])
    AD2000_B01_table4_data['strength value [1.4571] - MPa'] = np.array([
            218.0,196.0,186.0,175.0,  #from Stainless Steel Handbook - 0.1% - Proof Stress
            ])
    
    strength_factor_df = pd.DataFrame(data=AD2000_B01_table4_data)

    # Calculation parameter
    # =============================================================================
    material_list = ['S235JR','S275JR','S355JR','1.4301','1.4571']
    safety_factor = 1.5  # according AD2000 B0 - Panel 2
    c1 = 0  # according to AD2000 B0
    c2 = 1  # according to AD2000 B0
    utility_factor = 1  # according AD2000 HP 0 - Panel 1b
    s = 1  # to get into while loop with a thickness up to 16 mm

    # =============================================================================
    # Calculation
    #==============================================================================

    if temperature > 300:
        if verbose:
            print('''
            ATTENTION              
                    
              -> Operating temperature above allowed calculation temperature according AD2000!
                 Temperature should be set to max. 300°C!
              
              -> Strength value will be calculated via linear extrapolation !''')
    
    # Choise of Material
    if material_select == None:
        print('''
        Please choose one of the following steel grades !
                  
          -> S235JR
          -> S275JR
          -> S355JR
          -> 1.4301
          -> 1.4571
                  ''')

        material = input("Type in steel grade: ")
    else:
        material = material_select
   
    while True:
            
        while True:
            
            s1 = s  # check at the end of the loop as a termination criterion
    
    # ===== S235JR ================================================================
            
            if material == (material_list[0]):
                
                if s <= 16:
                    
                    if temperature <= 300:
                        
                        strength_factor = np.interp(temperature,strength_factor_df['calculation temperature - °C'],
                                                    strength_factor_df['strength value [1.0038, s <= 16 mm] - MPa'])
                    
                    else:
                        
                        strength_factor = interpolate.interp1d(strength_factor_df['calculation temperature - °C'],
                                                               strength_factor_df['strength value [1.0038, s <= 16 mm] - MPa'],
                                                               fill_value = 'extrapolate')
                        strength_factor = strength_factor(temperature)
                        
                else:
                    
                    if temperature <= 300:
                        
                        strength_factor = np.interp(temperature,strength_factor_df['calculation temperature - °C'],
                                                    strength_factor_df['strength value [1.0038, s <= 40 mm] - MPa'])
                    
                    else:
                        
                        strength_factor_calc = interpolate.interp1d(strength_factor_df['calculation temperature - °C'],
                                                                    strength_factor_df['strength value [1.0038, s <= 40 mm] - MPa'],
                                                                    fill_value = 'extrapolate')
                        strength_factor = strength_factor_calc(temperature)
    
    # ===== S275JR ================================================================
            
            elif material == (material_list[1]):
                
                if s <= 16:
                    
                    if temperature <= 300:
                        
                        strength_factor = np.interp(temperature,strength_factor_df['calculation temperature - °C'],
                                                    strength_factor_df['strength value [1.0044, s <= 16 mm] - MPa'])
                    
                    else:
                        
                        strength_factor = interpolate.interp1d(strength_factor_df['calculation temperature - °C'],
                                                               strength_factor_df['strength value [1.0044, s <= 16 mm] - MPa'],
                                                               fill_value = 'extrapolate')
                        strength_factor = strength_factor(temperature)
                        
                else:
                    
                    if temperature <= 300:
                        
                        strength_factor = np.interp(temperature,strength_factor_df['calculation temperature - °C'],
                                                    strength_factor_df['strength value [1.0044, s <= 40 mm] - MPa'])
                    
                    else:
                        
                        strength_factor_calc = interpolate.interp1d(strength_factor_df['calculation temperature - °C'],
                                                                    strength_factor_df['strength value [1.0044, s <= 40 mm] - MPa'],
                                                                    fill_value = 'extrapolate')
                        strength_factor = strength_factor_calc(temperature)
    
    # ===== S355JR ================================================================
            
            elif material == (material_list[2]):
                
                if s <= 16:
                    
                    if temperature <= 300:
                        
                        strength_factor = np.interp(temperature,strength_factor_df['calculation temperature - °C'],
                                                    strength_factor_df['strength value [1.0577, s <= 16 mm] - MPa'])
                    
                    else:
                        
                        strength_factor = interpolate.interp1d(strength_factor_df['calculation temperature - °C'],
                                                               strength_factor_df['strength value [1.0577, s <= 16 mm] - MPa'],
                                                               fill_value = 'extrapolate')
                        strength_factor = strength_factor(temperature)
                        
                else:
                    
                    if temperature <= 300:
                        
                        strength_factor = np.interp(temperature,strength_factor_df['calculation temperature - °C'],
                                                    strength_factor_df['strength value [1.0577, s <= 40 mm] - MPa'])
                    
                    else:
                        
                        strength_factor_calc = interpolate.interp1d(strength_factor_df['calculation temperature - °C'],
                                                                    strength_factor_df['strength value [1.0577, s <= 40 mm] - MPa'],
                                                                    fill_value = 'extrapolate')
                        strength_factor = strength_factor_calc(temperature)
    
    # ===== 1.4301 ================================================================
    
            elif material == (material_list[3]):
                
                if s <= 16:
                    
                    if temperature <= 300:
                        
                        strength_factor = np.interp(temperature,strength_factor_df['calculation temperature - °C'],
                                                    strength_factor_df['strength value [1.4301] - MPa'])
                    
                    else:
                        
                        strength_factor = interpolate.interp1d(strength_factor_df['calculation temperature - °C'],
                                                               strength_factor_df['strength value [1.4301] - MPa'],
                                                               fill_value = 'extrapolate')
                        strength_factor = strength_factor(temperature)
                        
                else:
                    
                    if temperature <= 300:
                        
                        strength_factor = np.interp(temperature,strength_factor_df['calculation temperature - °C'],
                                                    strength_factor_df['strength value [1.4301] - MPa'])
                    
                    else:
                        
                        strength_factor_calc = interpolate.interp1d(strength_factor_df['calculation temperature - °C'],
                                                                    strength_factor_df['strength value [1.4301] - MPa'],
                                                                    fill_value = 'extrapolate')
                        strength_factor = strength_factor_calc(temperature)
    
    # ===== 1.4571 ================================================================
    
            elif material == (material_list[4]):
                
                if s <= 16:
                    
                    if temperature <= 300:
                        
                        strength_factor = np.interp(temperature,strength_factor_df['calculation temperature - °C'],
                                                    strength_factor_df['strength value [1.4571] - MPa'])
                    
                    else:
                        
                        strength_factor = interpolate.interp1d(strength_factor_df['calculation temperature - °C'],
                                                               strength_factor_df['strength value [1.4571] - MPa'],
                                                               fill_value='extrapolate')
                        strength_factor = strength_factor(temperature)
                        
                else:
                    
                    if temperature <=300:
                        
                        strength_factor = np.interp(temperature,strength_factor_df['calculation temperature - °C'],
                                                    strength_factor_df['strength value [1.4571] - MPa'])
                    
                    else:
                        
                        strength_factor_calc = interpolate.interp1d(strength_factor_df['calculation temperature - °C'],
                                                                    strength_factor_df['strength value [1.4571] - MPa'],
                                                                    fill_value='extrapolate')
                        strength_factor = strength_factor_calc(temperature)
            
            s = (diameter * pressure) / ((40 * ( strength_factor / safety_factor ) * utility_factor) + pressure) + c1 + c2
            
            if s <= 38:
                
                utility_factor = 1 
                
            else:
                
                utility_factor = 0.85
                        
            if s1 == s: # if inequality - new iteration - to take into account strenght values for plate thickness > 16 mm
                
                if s > 40:
                    if verbose:
                        print('\nShell thickness s = {0:2.2f} mm > 40 mm nominal plate thickness according AD2000 !!!\n'.format(s))
                
                if s > 150:
                    if verbose:
                        print('Shell thickness s = {0:2.2f} mm > 150 mm maximum plate thickness according DIN EN 10025-2 !!!\n'.format(s))
                
                break
        
        if (diameter > 200) & (diameter / (diameter - (2*s)) <= 1.2):
            
            break
        
        elif (diameter <= 200) & (diameter / (diameter - (2*s)) <= 1.7):
            
            break
            
        else:
            if verbose:
                print("""
    CALCULATION CRITERION NOT FEASIBLE !!! CALCULATION IS CANCELED - PLEASE INTERRUPT CONSOLE !!!\nYOU are in an INFINITE LOOP ...
                      """)
            
            # sleep(2)
            break
           
    if material_select == None:
        return '{0:2.2f}'.format(s)
    else:
        return s

# === Safety Valve ============================================================
    
def svalv_size(op_mode_num, maxoverload):
    '''
    
    sizing of safety valve for RUTHS steam accumulator (pressure vessel)
    
    INPUT:
    
    mode:
        operating mode of steam accumulator 'single' or 'parallel'
        
    maxoverload: 
        specifies highest overload demand when the accumulator is at its design pressure in kg / h
    
    temperature:
        specifies the operating temperature of steam accumulator in °C
        
    pressure:
        specifies the operating pressure of steam accumulator in bar
            
    DESCRIPTION:
        
    sizing of safety valve for steam applications, blow-off performance according to AD2000 A2 & TRD421
    '''
    
# === Safety Valve SV 60 table for blow-off performance ======================
    
    SV60_table_data = {}
    
    SV60_table_data['p_res in bar'] = np.array([0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,
                                              5.5,6,6.5,7,7.5,8,8.5,9,9.5,10])
    
    SV60_table_data['17.1'] = np.array([113,180,239,296,352,406,459,510,561,613,
                                         661,713,764,812,863,914,961,1012,1063,1114])
    
    SV60_table_data['23.8'] = np.array([238,381,508,630,748,862,973,1090,1198,1309,
                                         1412,1522,1633,1734,1843,1953,2052,2161,2270,2379])
    
    SV60_table_data['30.7'] = np.array([356,577,770,952,1125,1289,1447,1603,1792,1925,
                                         2077,2239,2401,2549,2710,2871,3017,3177,3338,3498])
    
    SV60_table_data['38.1'] = np.array([461,772,1045,1303,1548,1782,2007,2209,2428,2652,
                                         2862,3085,3308,3513,3735,3957,4157,4378,4599,4820])
    
    SV60_table_data['50.2'] = np.array([777,1251,1678,2089,2481,2859,3224,3610,3967,4333,
                                         4676,5040,5405,5740,6103,6466,6793,7154,7515,7876])
    
    SV60_table_data['59.0'] = np.array([1187,1919,2568,3194,3797,4381,4949,5531,6079,6641,
                                         7165,7724,8283,8796,9352,9908,10410,10963,11516,12069])
    
    SV60_table_data['73.0'] = np.array([1651,2683,3610,4514,5393,6249,7086,7872,8651,9450,
                                         10196,10992,11787,12517,13308,14100,14814,15601,16388,17175])
    
    SV60_table_data['91.0'] = np.array([2705,4373,5871,7334,8759,10133,11495,12973,14257,15575,
                                         16805,18116,19427,20630,21934,23238,24415,25712,27010,28307])
    
    SV60_table_data['105.0'] = np.array([3754,6043,8108,10130,12102,14028,15915,17766,19524,21329,
                                          23012,24807,26603,28250,30036,31822,33434,35210,36987,38764])
    
    SV60_table_data['125.0'] = np.array([5428,8703,11651,14551,17395,20184,22924,25528,28054,30647,
                                          33067,35646,38226,40593,43159,45725,48041,50594,53147,55700])
    
    SV60_table_df = pd.DataFrame(data = SV60_table_data)
    
    DN_dict = {'17.1':'15',
               '23.8':'20',
               '30.7':'25',
               '38.1':'32',
               '50.2':'40',
               '59.0':'50',
               '73.0':'65',
               '91.0':'80',
               '105.0':'100',
               '125.0':'125'}
    
    ID_dict = {'17.1':'0',
               '23.8':'1',
               '30.7':'2',
               '38.1':'3',
               '50.2':'4',
               '59.0':'5',
               '73.0':'6',
               '91.0':'7',
               '105.0':'8',
               '125.0':'9'}
    
    p_res_dict = {'0.5':'0',
               '1':'1',
               '1.5':'2',
               '2':'3',
               '2.5':'4',
               '3':'5',
               '3.5':'6',
               '4':'7',
               '4.5':'8',
               '5':'9',
               '5.5':'10',
               '6':'11',
               '6.5':'12',
               '7':'13',
               '7.5':'14',
               '8':'15',
               '8.5':'16',
               '9':'17',
               '9.5':'18',
               '10':'19'}
    
    DN_list = [17.1,23.8,30.7,38.1,50.2,59.0,73.0,91.0,105.0,125.0]
    
    for ID in DN_list:
        
        SV60_table_df['{}'.format(ID)] = SV60_table_df['{}'.format(ID)].astype(float)
        
# === Calculation for sizing
# =============================================================================
     
    maxoverload = float(maxoverload)
    maxoverload = maxoverload / float(op_mode_num)
    
    DN_svalv = 0 
    
    while DN_svalv == 0:

        # p_res = input('Please choose response pressure from 0.5, 1, 1.5 ... 10 bar, in 0.5 steps: ')
        p_res = 3

        for ID in DN_list:
                        
            if SV60_table_df.iloc[int(p_res_dict['{}'.format(p_res)]),int(ID_dict['{}'.format(ID)])] >= maxoverload:
                            
                DN_svalv = int(DN_dict['{}'.format(ID)])
                break
                        
            elif SV60_table_df.iloc[int(p_res_dict['{}'.format(p_res)]),int(ID_dict['{}'.format(ID)])] < maxoverload:
                
                DN_svalv = 0

        if DN_svalv == 0:
            DN_svalv = int(DN_dict['{}'.format(DN_list[-1])])
                
    return DN_svalv
