# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 12:39:14 2022

@author: PaeffgenE
"""

units = dict(
    eso_eso1_nga = 'Natural gas',
    eso_eso2_big = 'Biogas',
    eso_eso3_elg = 'Electricity grid',
    eso_eso4_bim = 'Biomethane',
    eso_eso5_slu = 'Sludge',
    eso_eso6_iwa = 'Internal waste',
    eso_eso7_ewa = 'External waste',
    eso_eso8_coa = 'Coal',
    eso_eso9_oil = 'Oil',
    eso_eso10_hyd = 'Hydrogen',
    eso_eso11_bio = 'Biomass',
    eso_eso12_elp = 'Electricity PV',
    eso_eso13_elw = 'Electricity wind',
    eso_eso14_elh = 'Electricity hydro',
    eso_eso15_ppapv = 'Electricity PPA PV',
    eso_eso16_geo = 'Geothermal',
    eso_eso17_ste = 'Steam extern',
    eso_eso18_dhe = 'District heat',
    eso_eso19_feg = 'Feed electricity grid',
    eso_eso20_bif = 'Biofuel',
    eso_eso21_ppaw = 'Electricity PPA wind',
    eso_eso22_ots = 'Other solid',
    eso_eso23_otg = 'Other gas',
    eso_eso24_pdh = 'Purchased district heat',
    eso_eso25_ppah = 'Electricity PPA hydro',
    eso_eso26_elr = 'Renewable electricity grid',
    ecu_ecu1_sbo1 = 'Solid boiler 1',
    ecu_ecu2_sbo2 = 'Solid boiler 2',
    ecu_ecu3_sbo3 = 'Solid boiler 3',
    ecu_ecu4_boi1 = 'Boiler 1',
    ecu_ecu5_boi2 = 'Boiler 2',
    ecu_ecu6_boi3 = 'Boiler 3',
    ecu_ecu7_boi4 = 'Boiler 4',
    ecu_ecu8_boi5 = 'Boiler 5',
    ecu_ecu9_boi6 = 'Boiler 6',
    ecu_ecu10_gtu1 = 'Gasturbine 1',
    ecu_ecu11_gtu2 = 'Gasturbine 2',
    ecu_ecu12_stu1 = 'Steam turbine backpressure 1',
    ecu_ecu13_stu2 = 'Steam turbine backpressure 2',
    ecu_ecu14_whp1 = 'Water heat pump 1',
    ecu_ecu15_shp1 = 'Steam heat pump 1',
    ecu_ecu16_shp2 = 'Steam heat pump 2',
    ecu_ecu17_cst1 = 'Condensation steam turbine 1',
    ecu_ecu18_cst2 = 'Condensation steam turbine 2',
    esu_esu1_bat = 'Battery',
    esu_esu2_ste = 'Steam storage',
    esu_esu3_how = 'Hot water storage',
    esu_esu4_wwa = 'Warm water storage',
    dem_dem1_pro1 = 'Demand process 1',
    dem_dem2_pro2 = 'Demand process 2',
    dem_dem3_pro3 = 'Demand process 3',
    dem_dem4_pro4 = 'Demand process 4',
    
)

costs = dict(
    opex_fix='Fixed operational costs',
    inv='Investment cost',
    inv_fix='Fixed investment costs for limit extension',
    inv_power='Power-related costs for limit extension',
    inv_energy='Energy-related costs for limit extension',
    inv_cap='Specific investment costs',
    #opex_main='Annual maintenance costs',
    opex_start='Cost for start of unit',
    invest_cap='Specific energy related investment costs',
    energy='Energy costs',
    max_s='Grid costs',
    co2_fossil='Fossil co2 cost',
    co2_biogen='biogen co2 cost'
    )

capexopex = dict(
    opex_fix='OPEX',
    inv='CAPEX',
    inv_fix='CAPEX',
    inv_power='CAPEX',
    inv_energy='CAPEX',
    inv_cap='CAPEX',
    #opex_main='OPEX',
    opex_start='OPEX',
    invest_cap='CAPEX',
    energy='OPEX',
    max_s='OPEX',
    co2_fossil='OPEX',
    co2_biogen='OPEX'
    )

#List of all heat types
heat_types = dict (
    q_los='ST lp',
    q_mis='ST mp',
    q_his='ST hp',
    q_lis='ST vhp',
    q='ST'
    )

