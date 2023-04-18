# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 12:39:14 2022

@author: PaeffgenE
"""
fuelsources = dict(
    eso_eso1_nga = 'Natural gas',
    eso_eso2_big = 'Biogas',
    eso_eso4_bim = 'Biomethane',
    eso_eso5_slu = 'Sludge',
    eso_eso6_iwa = 'Internal waste',
    eso_eso7_ewa = 'External waste',
    eso_eso8_coa = 'Coal',
    eso_eso9_oil = 'Oil',
    eso_eso10_hyd = 'Hydrogen',
    eso_eso11_bio = 'Biomass',
    eso_eso16_geo = 'Geothermal',
    eso_eso17_ste = 'Steam extern',
    eso_eso18_dhe = 'District heat',
    eso_eso20_bif = 'Biofuel',
    eso_eso22_ots = 'Other solid',
    eso_eso23_otg = 'Other gas',
    eso_eso24_pdh = 'Purchased district heat',


)

elsources = dict(
    eso_eso3_elg = 'Electricity grid',
    eso_eso12_elp = 'Electricity PV',
    eso_eso13_elw = 'Electricity Wind',
    eso_eso14_elh = 'Electricity Hydro',
    eso_eso15_ppapv = 'Electricity PPA PV',
    eso_eso19_feg = 'Feed electricity grid',
    eso_eso21_ppaw = 'Electricity PPA Wind',
    eso_eso25_ppah = 'Electricity PPA Hydro',
    eso_eso26_elr = 'Renewable electricity grid',
)
units = dict(
    eso_supply_electric = 'Power Grid',
    eso_supply_gaseous = 'Gas Grid',
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
    eso_eso13_elw = 'Electricity Wind',
    eso_eso14_elh = 'Electricity Hydro',
    eso_eso15_ppapv = 'Electricity PPA PV',
    eso_eso16_geo = 'Geothermal',
    eso_eso17_ste = 'Steam extern',
    eso_eso18_dhe = 'District heat',
    eso_eso19_feg = 'Feed electricity grid',
    eso_eso20_bif = 'Biofuel',
    eso_eso21_ppaw = 'Electricity PPA Wind',
    eso_eso22_ots = 'Other solid',
    eso_eso23_otg = 'Other gas',
    eso_eso24_pdh = 'Purchased district heat',
    eso_eso25_ppah = 'Electricity PPA Hydro',
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
    dem_dem1_pro1_input1 = 'Process 1 Gas',
    dem_dem1_pro1_input2 = 'Process 1 Power',
    dem_dem1_pro1_input3 = 'Process 1 Steam_hp',
    dem_dem1_pro1_input4 = 'Process 1 Steam_mp',
    dem_dem1_pro1_input5 = 'Process 1 Steam_lp',
    dem_dem2_pro2_input1 = 'Process 2 Gas',
    dem_dem2_pro2_input2 = 'Process 2 Power',
    dem_dem2_pro2_input3 = 'Process 2 Steam_hp',
    dem_dem2_pro2_input4 = 'Process 2 Steam_mp',
    dem_dem2_pro2_input5 = 'Process 2 Steam_lp',
    dem_dem3_pro3_input1 = 'Process 3 Gas',
    dem_dem3_pro3_input2 = 'Process 3 Power',
    dem_dem3_pro3_input3 = 'Process 3 Steam_hp',
    dem_dem3_pro3_input4 = 'Process 3 Steam_mp',
    dem_dem3_pro3_input5 = 'Process 3 Steam_lp',
    dem_dem4_pro4_input1 = 'Process 4 Gas',
    dem_dem4_pro4_input2 = 'Process 4 Power',
    dem_dem4_pro4_input3 = 'Process 4 Steam_hp',
    dem_dem4_pro4_input4 = 'Process 4 Steam_mp',
    dem_dem4_pro4_input5 = 'Process 4 Steam_lp',
)

couplers = dict(
    coupler_ecu_ecu1_sbo1_heat_out_node_to_col_col2_mis1_node_out_col_col2_mis1_node='Solid Boiler 1 to Middle Pressure Steam',
)

costs = dict(
    opex_fix='Fixed operational costs',
    inv='Investment costs',
    inv_fix='Fixed investment costs for limit extension',
    inv_power='Power-related costs for limit extension',
    inv_energy='Energy-related costs for limit extension',
    inv_cap='Specific investment costs',
    #opex_main='Annual maintenance costs',
    opex_start='Costs for start of unit',
    invest_cap='Specific energy related investment costs',
    energy='Energy costs',
    max_s='Grid costs',
    co2_fossil="Fossil CO2 costs",
    co2_biogen="Biogen CO2 costs"
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
    q='ST',
    q_sink='ST'
    )

