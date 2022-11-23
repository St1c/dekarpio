# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 07:20:32 2020

@author: SchoenyM
"""

import numpy as np
import pandas as pd

#%%

def svalv_cfunc(mode, maxoverload):
    '''
    
    sizing of safety valve for RUTHS steam accumulator (pressure vessel)
    
    INPUT:
    
    maxoverload: 
        specifies highest overload demand when the accumulator is at its design pressure in kg / h
    
    temperature:
        specifies the operating temperature of steam accumulator in °C
        
    pressure:
        specifies the operating pressure of steam accumulator in bar
            
    DESCRIPTION:
        
    sizing of safety valve for steam applications according to AD2000 A2
    '''
    
# === Safety Valve SV 60 table for blow-out performance ======================
    
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
    
    DN_dict = {'17.1':'DN15',
               '23.8':'DN20',
               '30.7':'DN25',
               '38.1':'DN32',
               '50.2':'DN40',
               '59.0':'DN50',
               '73.0':'DN65',
               '91.0':'DN80',
               '105.0':'DN100',
               '125.0':'DN125'}
    
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
    
    p_res = input('Please choose response pressure from 0.5 to 10 bar, in 0.5 steps: ')
    
    
    
    mode_list = ['single', 'parallel']
    
    if mode == mode_list[1]:
        
        op_mode_num = float(input('Please choose number of parallel accumulators:'))
        maxoverload = float(maxoverload)
        maxoverload = maxoverload / op_mode_num
    
    for ID in DN_list:
        
        if SV60_table_df.iloc[int(p_res_dict['{}'.format(p_res)]),int(ID_dict['{}'.format(ID)])] >= maxoverload:
                        
            DN_Svalv = DN_dict['{}'.format(ID)] 
            
            break
    
    return DN_Svalv
        
    
    
    