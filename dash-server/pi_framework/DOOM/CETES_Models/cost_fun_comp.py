import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import warnings

# All cost data based on the year 2015

def c_tubes(tube_type, diameter, qty, unit, material, verbose=False):
    """
    Calculates costs for steel tubes according to the prices from 'DACE Price Booklet Edition 33'
    for certain tube types.

    INPUT:
    tube_types:
      tube_type == 1: B1005. Welded stainless steel pipes  # source: DACE price booklet
      tube_type == 2: B1003. Seamless steel pipes by ASME / ANSI, (XS)

    diameter:
      specifies the outer diameter of the tube (mm).
      Gets automatically adjusted if entered values are too small or too big. A warning will be displayed.

    qty:
      specifies the quantity (either m or kg) of the tubes.

    unit:
      string, shows the unit of the entered qty (either m or kg).
      Get automatically set to m if something other than m or kg gets passed. A warning will be displayed.

    material:
      needs to be specified for certain tube_type.
      If it is not required for tube_type, it gets ignored.
      If it is required input but a wrong material is specified, material gets set to the default material.
      A warning will be displayed.

    verbose (optional):
      If set to 'True', extra Info is printed.
      This is usefull to check inputs. I.e. non valid inputs get adjusted automatically.

    DESCRIPTION:
    Item: B1005. Welded stainless steel pipes
          Pipe according ANSI B36.19.
          304L: welded stainless steel pipe(ANSI - Schedule 10 S).

          316L: welded stainless steel pipe(ANSI - Schedule 10 S).

          Average prices for new build projects with a volume of max. 5,000 tons piping. Project discount is included.
          For larger volumes there is a volume discount.  # fixme: needs to be included
          By small volumes (modifications, plant site projects), prices can be significantly higher.  # fixme: needs to be included

          Variation Factor for welded stainless steel pipes by DIN:
              Nominal pipe size < 100 mm( = 4"): 0.85;
              Nominal pipe size > 100 mm( > 4"): 1.15.

    Item: B1003. Seamless steel pipes by ASME / ANSI, (XS)
          Pipe type: ASTM - A106.

          ASTM A106 seamless pressure pipe(also known as ASME SA106 pipe)
          is commonly used in the construction of oil and gas refineries,
          power plants, petrochemical plants, boilers, and ships
          where the piping must transport fluids and gases that exhibit higher temperatures and pressure levels.

          Average prices for new build projects with a volume of max. 5,000 tons piping.
          Project discount is included.
          For larger volumes there is a volume discount. # fixme: needs to be included
          By small volumes (modifications, plant site projects), prices can be significantly higher. # fixme: needs to be included

          Variation  Factor for seamless steel pipes by DIN:
              Nominal pipe size < 100 mm( < 4 "): 0.85;
              Nominal pipe size > 100 mm( > 4 "): 1.15."""

    # ==================================================================================================================
    if tube_type == 1:
        if (material != '304L') & (material != '316L'):
            if verbose == True:
                print('Select "304L" or "316L" as material! Material set to "304L"')

            material = '304L'

        type_name = 'Welded stainless steel pipes - ' + material


        # outer diameter - mm
        diameter_outer = np.array([21.30, 26.70, 33.40, 42.20, 48.30, 60.30, 73.00, 88.90, 114.30, 141.30, 168.30, 219.10, 273.10, 323.90])

        # wall thickness - mm
        wall_thickness = np.array([2.10, 2.10, 2.80, 2.80, 2.80, 2.80, 3.10, 3.10, 3.10, 3.40, 3.40, 3.80, 4.20, 4.60])

        # specific weight - kg/m
        spec_weight = np.array([1.00, 1.30, 2.10, 2.70, 3.10, 3.90, 5.30, 6.40, 8.30, 11.60, 13.80, 19.90, 27.80, 36.00])

        # specific costs - €/m
        spec_costs_304L_eur_m = np.array([10.00, 11.00, 18.00, 23.00, 25.00, 25.00, 33.00, 41.00, 52.00, 73.00, 88.00, 96.00, 140.00, 179.00, ])
        spec_costs_316L_eur_m = np.array([11.00, 13.00, 20.00, 25.00, 28.00, 32.00, 40.00, 50.00, 63.00, 88.00, 108.00, 121.00, 161.00, 206.00,])

        # specific costs - €/kg
        spec_costs_304L_eur_kg = spec_costs_304L_eur_m /spec_weight
        spec_costs_316L_eur_kg = spec_costs_316L_eur_m /spec_weight

        if material == '304L':
            spec_costs_eur_m = spec_costs_304L_eur_m
            spec_costs_eur_kg = spec_costs_304L_eur_kg

        elif material == '316L':
            spec_costs_eur_m = spec_costs_316L_eur_m
            spec_costs_eur_kg = spec_costs_316L_eur_kg

    # ==================================================================================================================
    if tube_type == 2:
        type_name = 'Seamless steel pipes by ASME / ANSI, (XS)'

       # COST CALCULATIONS

        # outer diameter - mm
        diameter_outer = np.array([21.30, 26.70, 33.40, 48.30, 60.30, 88.90, 114.30, 141.30, 168.30, 219.10, 273.00, 323.90, 355.60, 406.40, 508.00,])

        # wall thickness - mm
        # wall_thickness = np.array([3.70, 3.90, 4.50, 5.10, 5.50, 7.60, 8.60, 9.50, 11.00, 12.70, 12.70, 12.70, 12.70, 12.70, 12.70])  # fittings
        wall_thickness = np.array([2.80, 2.90, 3.40, 3.70, 3.90, 5.50, 6.00, 6.60,  7.10,  8.20,  9.30,  9.50,  9.50,  9.50, 9.50])

        # specific weight - kg/m
        # spec_weight = np.array([1.60, 2.20, 3.20, 5.40, 7.50, 15.30, 22.30, 31.00, 42.60, 64.60, 81.60, 97.50, 107.00, 123.20, 155.00])  # fittings
        spec_weight = np.array([1.27, 1.68, 2.50, 4.05, 5.44, 11.30, 16.10, 21.80, 28.30, 42.50, 60.30, 73.80,  81.30,  93.30, 117.00])

        # specific costs - €/m
        # spec_costs_eur_m = np.array([290.00, 360.00, 500.00, 780.00, 990.00, 1640.00, 2460.00, 3520.00, 4570.00, 7480.00, 9700.00, 11670.00, 14050.00, 16070.00, 20020.00])/100  # fittings
        spec_costs_eur_m = np.array([260.00, 320.00, 430.00, 660.00, 690.00, 1230.00, 1690.00, 2450.00, 3150.00, 4850.00, 6990.00, 8770.00, 10540.00, 12210.00, 15470.00])/100

        # specific costs - €/kg
        spec_costs_eur_kg = spec_costs_eur_m / spec_weight

    # ==================================================================================================================
    try:
        len(diameter)
    except:
        diameter = [diameter]

    for i, dia in enumerate(diameter):
        if (dia < min(diameter_outer)) | (dia > max(diameter_outer)):
            if verbose == True:
                print('Error: entered diameter exceeds diameter bounds {} mm - {} mm'.format(min(diameter_outer), max(diameter_outer)))
                print('Diameter set to nearest bound.')

            if dia < min(diameter_outer):
                diameter[i] = min(diameter_outer)
            elif dia > max(diameter_outer):
                diameter[i] = max(diameter_outer)

    else:
        if (unit != 'kg') & (unit != 'm'):
            if verbose == True:
                print('Select "kg" or "m" as input unit! Unit set to "kg"')

        if unit == 'kg':
            weight_calc = qty  # kg
            costs = weight_calc * np.interp(diameter, diameter_outer, spec_costs_eur_kg)
        elif unit == 'm':
            length_calc = qty  # m
            weight_calc = length_calc * np.interp(diameter, diameter_outer, spec_weight)
            costs = length_calc * np.interp(diameter, diameter_outer, spec_costs_eur_m)

        # fixme: Discout for quantities > 5000 tons needs to be included
        # fixme: Additional costs for small quantities need to be included

    plotting = 0
    if plotting == 1:
        plt.figure()
        plt.plot(diameter_outer, spec_costs_eur_kg)
        plt.title(type_name)
        plt.xlabel('outer diameter (mm)')
        plt.ylabel('specific costs (€/kg)')

        plt.figure()
        plt.plot(diameter_outer, spec_costs_eur_m)
        plt.title(type_name)
        plt.xlabel('outer diameter (mm)')
        plt.ylabel('specific costs (€/m)')

    return costs


def c_steel(steel_type, thickness, qty, verbose=False):
    """
    Calculates costs for steel according to the prices from 'DACE Price Booklet Edition 33'
    for certain steel types.

    INPUT:
    steel_type:
        steel_type == 1:  Steel plates up to 3 m wide (S234JR) (3-80mm)
        steel_type == 2:  Hot rolled thin plate (Trade quality) (1.5-2.75mm)
        steel_type == 3:  Cold rolled thin plate (Trade quality) (0.5-2.95mm)

    thickness:
        specifies thickness of steel plates (mm). If thickness is out of bounds for the selected steel_type,
        it gets set to the closest limit. A warning will be displayed.

    qty:
      specifies the quantity (in kg) for steel.
      For large quantities (> 1,000 kg), a discount of 1 € / 1,000 kg is considered.
      For small quantities (< 75 kg), a surcharge of 0.20 € / kg is considered.

    verbose (optional):
      If set to 'True', extra Info is printed.
      This is useful to check inputs. I.e. non valid inputs get adjusted automatically.

    DESCRIPTION:
    H1001.Carbon steel
      Density 7.85.
      Carbon steel 37.2 Din 17100, Fe360 - BEU 25.

      Remarks
          For orders between 1,000 and 25,000 kg apply a reduction of € 1. - per 1,000 kg.
          For orders up to 75 kg apply an addition of € 0.20. - per kg.

    """

    # ==================================================================================================================
    def correct_bounds(lb, ub, val):
        corr = 0
        if (val < lb) | (val > ub):
            if val < lb:
                val = lb
            if val > ub:
                val = ub
            corr = 1
        return val, corr

    if (type(qty) == int) | (type(qty) == float) | (type(qty) == np.float64):
        qty = np.array([qty])
    else:
        try:
            spec_costs = np.zeros(qty.__len__())
        except:
            print()

    # ==================================================================================================================
    if steel_type == 1:
        # Steel plates up to 3 m wide (S234JR) (3-80mm)

        # bounds for thickness
        lb = 3
        ub = 80

        thickness, corr = correct_bounds(lb, ub, thickness)
        if corr:
            if verbose == True:
                print('Entered thickness out of bounds for selected steel_type.')
                print('Thickness set to {} mm.'.format(thickness))

        if thickness <= 10:
            if qty.__len__() > 1:
                spec_costs[qty < 250] = 187
                spec_costs[qty < 500] = 157
                spec_costs[qty < 1000] = 142
                spec_costs[qty >= 1000] = 127
            else:

                if qty < 250:
                    spec_costs = 187  # €/100kg
                elif qty < 500:
                    spec_costs = 157  # €/100kg
                elif qty < 1000:
                    spec_costs = 142  # €/100kg
                elif qty >= 1000:
                    spec_costs = 127  # €/100kg

        else:
            if qty.__len__() > 1:
                spec_costs[qty < 250] = 199
                spec_costs[qty < 500] = 173
                spec_costs[qty < 1000] = 156
                spec_costs[qty >= 1000] = 143
            else:

                if qty < 250:
                    spec_costs = 199  # €/100kg
                elif qty < 500:
                    spec_costs = 173  # €/100kg
                elif qty < 1000:
                    spec_costs = 156  # €/100kg
                elif qty >= 1000:
                    spec_costs = 143  # €/100kg

    # ==================================================================================================================
    if steel_type == 2:
        # Hot rolled thin plate (Trade quality) (1.5-2.75mm)

        # bounds for thickness
        lb = 1.5
        ub = 2.75

        thickness, corr = correct_bounds(lb, ub, thickness)
        if corr:
            if verbose == True:
                print('Entered thickness out of bounds for selected steel_type.')
                print('Thickness set to {} mm.'.format(thickness))

        if qty.__len__() > 1:
            spec_costs[qty < 250] = 190
            spec_costs[qty < 500] = 161
            spec_costs[qty < 1000] = 147
            spec_costs[qty >= 1000] = 130
        else:
            if qty < 250:
                spec_costs = 190  # €/100kg
            elif qty < 500:
                spec_costs = 161  # €/100kg
            elif qty < 1000:
                spec_costs = 147  # €/100kg
            elif qty >= 1000:
                spec_costs = 130  # €/100kg

    # ==================================================================================================================
    if steel_type == 3:
        # Cold rolled thin plate (Trade quality) (0.5-2.95mm)

        # bounds for thickness
        lb = 0.5
        ub = 2.95

        thickness, corr = correct_bounds(lb, ub, thickness)
        if corr:
            if verbose == True:
                print('Entered thickness out of bounds for selected steel_type.')
                print('Thickness set to {} mm.'.format(thickness))

        if qty.__len__() > 1:
            spec_costs[qty < 250] = 197
            spec_costs[qty < 500] = 169
            spec_costs[qty < 1000] = 153
            spec_costs[qty >= 1000] = 141
        else:
            if qty < 250:
                spec_costs = 197  # €/100kg
            elif qty < 500:
                spec_costs = 169  # €/100kg
            elif qty < 1000:
                spec_costs = 153  # €/100kg
            elif qty >= 1000:
                spec_costs = 141  # €/100kg

    # ==================================================================================================================

    costs = qty * spec_costs / 100

    if qty.__len__() > 1:
        costs[qty < 75] = costs[qty < 75] + qty[qty < 75] * 0.20
        costs[qty > 1000] = costs[qty > 1000] - qty[qty > 1000] * 1 / 1000
    else:
        if qty < 75:  # extra costs for small quantities
            costs = costs + qty * 0.20
        elif qty > 1000:  # reduced costs for large quantities
            costs = costs - qty * 1 / 1000

    return costs

def c_elmotor(capacity, load, conv_units, verbose=False):
    """
    Costs for electric pumps calculated according to the functions from Product and Process Design Principles by Seider et al. (2016, Wiley)


    INPUT:
    capacity:
        specifies the required capacity in m³/h.

    load:
        required capacity in kW


    verbose (optional):
      If set to 'True', extra Info is printed.
      This is usefull to check inputs. I.e. non valid inputs get adjusted automatically.

    OUTPUT:
        F.o.b. cost for the electric motor

    DESCRIPTION:
    Type: Electric motor with open drip-proof enclosure

    Material:
        Fully cast iron,
        cast steel or
        stainless steel.

    Rotational speeds: 1,800 / 3,600 rpm.

    """

    vflow_gpm = capacity/3600*conv_units['m3ps2Gpm']

    # Type factor - omitted at the moment

    eff_pump = -0.316 + 0.24015 * np.log(vflow_gpm) - 0.01199 * (
            np.log(vflow_gpm) ** 2)  # Equation for pump efficiency from Seider et al.
    watt_2_Hp = conv_units['watt2Hp']
    if eff_pump > 0:
        Pm = load / (0.9 * eff_pump)  # Motor power consumption in MW
        el_motor_costs = conv_units['dollar2eur'] * (
                np.exp(5.9332 + 0.16829 * np.log(Pm * watt_2_Hp)) - 0.110056 * (np.log(Pm * watt_2_Hp)) ** 2 + 0.071413 * (
            np.log(Pm * watt_2_Hp)) ** 3 - 0.0063788 * (np.log(Pm * watt_2_Hp)) ** 4)
    else:
        el_motor_costs = 0

    return el_motor_costs

def c_pumps_seider(capacity, d_p, material, type, conv_units, verbose=False):
    """
    Costs for pumps calculated according to the functions from Product and Process Design Principles by Seider et al. (2016, Wiley)
    Radial centrifugal pumps, 1,450 / 2,900 rpm.
    The function calculates the costs from the basis of a size factor S, which depends on the desired flow rate and pump head.
    The resulting costs are for cast iron, single stage VSC or HSC (vertical/horizontal split case) radial centrifugal
    pumps to up to 3600 rpm, however simple multiplication factors for obtaining costs for other pump types are included.

    INPUT:
    capacity:
        specifies the required capacity in m³/h.

    pressure:
        required pumping pressure in bar (pressure difference between outlet and inlet).

    material:
        can be set to "cast iron" (default), "cast steel" and "stainless steel".

    type:
        can be set to "vertical" (default) or  "horizontal".

    verbose (optional):
      If set to 'True', extra Info is printed.
      This is usefull to check inputs. I.e. non valid inputs get adjusted automatically.

    OUTPUT:
        F.o.b. cost for the pump

    DESCRIPTION:
    Type: Single-stage vertical split case radial centrifugal pump

    Material:
        Fully cast iron,
        cast steel or
        stainless steel.

    Rotational speeds: 1,800 / 3,600 rpm.

    Including:
        Foundation plate;
        Coupling;
    Excluding:
        Electric motor;
        Barrier fluid.
    """


    head = d_p/0.0981  # Pump head in meter
    vflow_gpm = capacity/3600*conv_units['m3ps2Gpm']

    # Material factor
    f_m = {
        'cast iron': 1.0,
        'cast steel': 1.35,
        'stainless steel': 2.00
    }

    # Type factor - not fully correct approach, pressure lift not considered:
    # a pump delivering the required capacity (volume flow) might still not be able to provide the required d_p
    # Also; now a horizontal pump should be selected if the required capacity is above 3500 Gpm, but is horizontal
    # pump correct for all applications?
    if type == 'vertical':
        if vflow_gpm <= 900:
            f_t = 1.0
        elif vflow_gpm <= 3500:
            f_t = 1.5
        else:
            print('Choose horizontal pump')
            return
    elif type == 'horizontal':
        if vflow_gpm <= 1500:
            f_t = 1.7
        else:
            f_t = 2.0

    S = (head * conv_units['m2feet'])**0.5 * vflow_gpm
    pump_cost_fun = np.exp(12.1656 - 1.1448 * np.log(S) + 0.0862 * (np.log(S)) ** 2)

    pump_costs = pump_cost_fun * f_m[material] * f_t * conv_units['dollar2eur']

    return pump_costs

def c_pumps(capacity, d_p, material, verbose=False):
    """
    Costs for pumps are calculated according to the prices from 'DACE Price Booklet Edition 33'.
    Single-stage centrifugal pumps, 1,450 / 2,900 rpm.
    The algorithm checks which pumps (1,450 rpm and 2,900 rpm) are sufficient for the required capacity and pressure.
    If there are none,
    it considers multiple pumps for both pressure lift (pumps in series) and capacity (pumps in parallel).

    INPUT:
    capacity:
        specifies the required capacity in m³/h.

    pressure:
        required pumping pressure in bar (pressure difference between outlet and inlet).

    material:
        can be set to "cast iron" (default), "cast steel" and "AISI 316".

    verbose (optional):
      If set to 'True', extra Info is printed.
      This is usefull to check inputs. I.e. non valid inputs get adjusted automatically.

    DESCRIPTION:
    Type: Horizontal, single-stage, single suction centrifugal pump with volute, build to
        pump organic and inorganic fluid.

    Material:
        Fully cast iron,
        cast steel or
        AISI 316 (DIN 24256).

    Rotational speeds: 1,450 / 2,900 rpm.
    Base plate: DIN 24259. Mechanical sealing: DIN 24960.

    Including:
        Foundation plate;
        Coupling;
        Single mechanical seal;
        Assembly.
    Excluding:
        Electric motor;
        Barrier fluid.
    """

    # ==================================================================================================================
    # 1450 rpm
    data_1450 = {}
    # Pump size
    data_1450['Pump size according DIN'] = np.array([
        32, 32, 32,  # 32
        40, 40, 40, 40,  # 40
        50, 50, 50, 50,  # 50
        65, 65, 65, 65, 65,  # 65
        80, 80, 80, 80,  # 80
        100, 100, 100, 100,  # 100
        125, 125, 125,  # 125
        150, 150,  # 150
        250  # 250
    ])

    data_1450['Pump size in mm'] = np.array([
        125, 160, 200,  # 32
        125, 160, 200, 250,  # 40
        125, 160, 200, 250,  # 50
        125, 160, 200, 250, 315,  # 65
        160, 200, 250, 315,  # 80
        200, 250, 315, 400,  # 100
        250, 315, 400,  # 125
        315, 400,  # 150
        400,  # 250
    ])

    # Pump capacity in m³/h
    data_1450['Pump capacity in m³/h'] = np.array([
        6.3, 6.3, 6.3,  # 32
        12.5, 12.5, 12.5, 12.5,  # 40
        25, 25, 25, 25,  # 50
        50, 50, 50, 50, 50,  # 65
        80, 80, 80, 80,  # 80
        125, 125, 125, 125,  # 100
        200, 200, 200,  # 125
        315, 315,  # 150
        900  # 250
    ])

    # Pressure in Meter
    data_1450['Pressure in Meter'] = np.array([
        5, 8, 12.5,  # 32
        5, 8, 12.5, 20,  # 40
        5, 8, 12.5, 20,  # 50
        5, 8, 12.5, 20, 32,  # 65
        8, 12.5, 20, 32,  # 80
        12.5, 20, 32, 50,  # 100
        20, 32, 50,  # 125
        32, 50,  # 150
        40,  # 250
    ])

    data_1450['Pressure in bar'] = data_1450['Pressure in Meter'] * 0.0981

    # Max. required power in kW
    data_1450['Max. required power in kW'] = np.array([
        0.55, 0.75, 1.5,  # 32
        0.75, 1.1, 1.5, 3,  # 40
        1.1, 2.2, 3, 4,  # 50
        1.5, 2.2, 4, 5.5, 11,  # 65
        4, 5.5, 11, 18.5,  # 80
        11, 15, 30, 37,  # 100
        22, 37, 55,  # 125
        45, 75,  # 150
        140,  # 250
    ])

    # Costs each
    data_1450['Costs each in € - cast iron'] = np.array([
        3900, 4100, 4500,  # 32
        4000, 4200, 4700, 6100,  # 40
        4500, 5000, 5400, 6200,  # 50
        5100, 5800, 6600, 7800, 9100,  # 65
        7000, 8100, 9200, 10800,  # 80
        9000, 10200, 10100, 12100,  # 100
        10600, 11800, 12000,  # 125
        14600, 15600,  # 150
        20000,  # 250 # fixme: give realistic value for last element (replaced "none" with a guess)
    ])

    data_1450['Costs each in € - cast steel'] = np.array([
        4800, 5000, 5400,  # 32
        4900, 5100, 6000, 7600,  # 40
        5700, 6100, 6700, 7800,  # 50
        6500, 7000, 8200, 9000, 11200,  # 65
        8400, 9900, 11200, 13200,  # 80
        10800, 12200, 12300, 14500,  # 100
        12700, 14600, 16600,  # 125
        18400, 20500,  # 150
        31600,  # 250
    ])

    data_1450['Costs each in € - AISI 316'] = np.array([
        5700, 6200, 6800,  # 32
        5900, 6400, 7300, 10000,  # 40
        6800, 7700, 8200, 10300,  # 50
        8200, 9000, 10600, 11600, 13900,  # 65
        10700, 12500, 15100, 17200,  # 80
        14000, 16500, 15700, 19300,  # 100
        16600, 19100, 19600,  # 125
        24700, 26500,  # 150
        None,  # 250
    ])

    pumps_1450 = pd.DataFrame(data=data_1450)
    pumps_1450.name = '1450 rpm'

    # ==================================================================================================================
    # 2900 rpm
    data_2900 = {}
    # Pump size
    data_2900['Pump size according DIN'] = np.array([
        32, 32, 32,  # 32
        40, 40, 40, 40,  # 40
        50, 50, 50, 50,  # 50
        65, 65, 65, 65,  # 65
        80, 80, 80,  # 80
        100, 100,  # 100
    ])

    data_2900['Pump size in mm'] = np.array([
        125, 160, 200,  # 32
        125, 160, 200, 250,  # 40
        125, 160, 200, 250,  # 50
        125, 160, 200, 250,  # 65
        160, 200, 250,  # 80
        200, 250,  # 100
    ])

    # Pump capacity in m³/h
    data_2900['Pump capacity in m³/h'] = np.array([
        12.5, 12.5, 12.5,  # 32
        25, 25, 25, 25,  # 40
        50, 50, 50, 50,  # 50
        100, 100, 100, 100,  # 65
        160, 160, 160,  # 80
        250, 250,  # 100
    ])

    # Pressure in Meter
    data_2900['Pressure in Meter'] = np.array([
        20, 32, 50,  # 32
        20, 32, 50, 80,  # 40
        20, 32, 50, 80,  # 50
        20, 32, 50, 80,  # 65
        32, 50, 80,  # 80
        50, 80,  # 100
    ])

    data_2900['Pressure in bar'] = data_2900['Pressure in Meter'] * 0.0981

    # Max. required power in kW
    data_2900['Max. required power in kW'] = np.array([
        3, 4, 11,  # 32
        4, 7.5, 11, 18.5,  # 40
        7.5, 11, 18.5, 30,  # 50
        11, 15, 30, 37,  # 65
        22, 37, 55,  # 80
        55, 90,  # 100
    ])

    # Costs each
    data_2900['Costs each in € - cast iron'] = np.array([
        3900, 4200, 4600,  # 32
        4000, 4600, 5100, 6200,  # 40
        4600, 5700, 6100, 7100,  # 50
        5800, 5800, 6500, 7500,  # 65
        6700, 6600, 7800,  # 80
        7600, 8700,  # 100
    ])

    data_2900['Costs each in € - cast steel'] = np.array([
        5000, 5200, 5600,  # 32
        5200, 5700, 6600, 7900,  # 40
        6000, 7000, 7800, 9100,  # 50
        7500, 7300, 8000, 8900,  # 65
        8300, 8300, 9700,  # 80
        9300, 10700,  # 100
    ])

    data_2900['Costs each in € - AISI 316'] = np.array([
        5900, 6400, 7100,  # 32
        6200, 7000, 8100, 10200,  # 40
        7200, 8800, 9500, 11900,  # 50
        9500, 9400, 10300, 11400,  # 65
        10500, 10700, 12900,  # 80
        11900, 14200,  # 100
    ])

    pumps_2900 = pd.DataFrame(data=data_2900)
    pumps_2900.name = '2900 rpm'
    # ==================================================================================================================

    def find_suitable_pump(pumps, d_p, capacity):

        def search_pump(pumps, d_p, capacity):
            print_errors = 0

            avail_m = np.unique(pumps['Pressure in Meter'])
            avail_p = np.unique(pumps['Pressure in bar'])
            try:
                req_p = avail_p[np.searchsorted(avail_p, [d_p, ], side='right')[0]]
                req_m = avail_m[np.searchsorted(avail_p, [d_p, ], side='right')[0]]

                pot_pumps = pumps[pumps['Pressure in Meter'] >= req_m]
                avail_cap = np.unique(pot_pumps['Pump capacity in m³/h'])

                suitable_pumps = pot_pumps[pot_pumps['Pump capacity in m³/h'] >= capacity]

                if suitable_pumps.__len__() > 0:
                    flag = 0
                    return suitable_pumps, flag

                else:
                    if print_errors:
                        if verbose == True:
                            print('Error: No {} pump is sufficient for this capacity.'.format(pumps.name))
                            print('The maximum available capacity is {} m³/h.'.format(max(avail_cap)))

                    flag = 2
                    return None, flag

            except:
                if print_errors:
                    if verbose == True:
                        print('Error: No {} pump is sufficient for this pressure.'.format(pumps.name))
                        print('The maximum available pressure is {} bar.'.format(max(avail_p)))

                flag = 1
                return None, flag

        # identify best combination of pumps
        series = 1
        parallel = 1

        flag = 1
        while flag == 1:
            suitable_pumps, flag = search_pump(pumps, d_p / series, capacity / parallel)
            if flag == 1:
                series += 1

        flag = 2
        while flag == 2:
            suitable_pumps, flag = search_pump(pumps, d_p / series, capacity / parallel)
            if flag == 2:
                parallel += 1

        return suitable_pumps, series, parallel

    def calc_min_costs(pumps, d_p, capacity, material):
        material_list = ['cast iron', 'cast steel', 'AISI 316']
        if not material in material_list:
            material = material_list[0]

            if verbose == True:
                print('specified material not valid.')
                print('changed material to default ({})'.format(material_list[0]))
                print('valid materials: {}'.format(material_list))

        suitable_pumps, series, parallel = find_suitable_pump(pumps_1450, d_p, capacity)
        n_pumps = series * parallel
        costs_per_pump = min(suitable_pumps['Costs each in € - {}'.format(material)])

        return costs_per_pump, n_pumps, suitable_pumps

    costs_per_pump_1450, n_pumps_1450, suitable_pumps_1450 = calc_min_costs(pumps_1450, d_p, capacity, material)
    total_costs_1450 = costs_per_pump_1450 * n_pumps_1450
    
    costs_per_pump_2900, n_pumps_2900, suitable_pumps_2900 = calc_min_costs(pumps_2900, d_p, capacity, material)
    total_costs_2900 = costs_per_pump_2900 * n_pumps_2900

    total_costs = min([total_costs_1450, total_costs_2900])

    return total_costs


def c_vertical_storage_tanks(tank_type, volume, verbose=False):
    """
    Costs for vertical storage tanks according to the prices from 'DACE Price Booklet Edition 33'.

    INPUT:
    tank_type:
        tank_type == 1: cone roof
        tank_type == 2: floating roof
        tank_type == 3: sphere

    volume:
        specifies the required volume in m³.

    verbose (optional):
      If set to 'True', extra Info is printed.
      This is usefull to check inputs. I.e. non valid inputs get adjusted automatically.

    DESCRIPTION:
    Material: Carbon steel.
    Type: Cone roof, floating roof, sphere.
    Including:
        1 Outside cage ladder;
        2 Manholes;
        Several nozzles;
        Hand railing;
        Assembly on site.
    Excluding:
        Internals;
        Civil work, painting and insulation.
    """

    # ==================================================================================================================
    if tank_type not in [1, 2, 3]:
        tank_type = 1
        if verbose == True:
            print('Specified tank type not in {}.'.format([1, 2, 3]))
            print('Tank type set to 1 (cone roof, default)')

    # ==================================================================================================================
    if tank_type == 1:
        # cone roof

        tank_data = {}

        tank_data['tank volume - m³'] = np.array([
            50, 100, 150, 200, 250, 300, 350, 400, 500, 1000, 1800, 6000, 13500, 17500, 25000, 31000, 53500
        ])

        tank_data['tank height - m'] = np.array([
            5.0, 6.0, 6.0, 7.5, 7.5, 7.5, 8.0, 8.0, 9.0, 9.15, 10.7, 12.9, 14.7, 14.7, 16.5, 16.5, 18.30
        ])

        tank_data['tank diameter - m'] = np.array([
            3.6, 4.6, 5.6, 5.8, 6.5, 7.1, 7.5, 8.0, 8.5, 12.2, 14.6, 24.4, 34.2, 39.1, 44.0, 48.8, 61.3, 
        ])

        tank_data['tank total surface area - m²'] = np.array([
            77, 120, 155, 190, 220, 247, 277, 302, 355, 585, 825, 1923, 3415, 4205, 5319, 6267, 9422.0
        ])

        tank_data['tank weight - kg'] = np.array([
            3.65, 5.65, 7.3, 9, 10.4, 11.7, 13.1, 14.25, 16.7, 38, 54, 137, 290, 380, 520, 640, 1070
        ])*1000

        tank_data['tank costs each - €'] = np.array([
            50, 62, 67, 80, 90, 98, 105, 116, 126, 226, 300, 670, 1245, 1550, 2060, 2590, 4350
        ])*1000

        tank_data_df = pd.DataFrame(data=tank_data)
        tank_data_df.name = 'cone roof'

    # ==================================================================================================================
    if tank_type == 2:
        # floating roof

        tank_data = {}

        tank_data['tank volume - m³'] = np.array([
            1000, 1800, 6000, 13500, 17500, 25000, 31000, 53500
        ])

        tank_data['tank height - m'] = np.array([
            9.15, 10.00, 12.90, 14.70, 14.70, 16.50, 16.50, 18.30
        ])

        tank_data['tank diameter - m'] = np.array([
            12.2, 14.6, 24.4, 34.2, 39.1, 44.0, 48.8, 61.3
        ])

        tank_data['tank total surface area - m²'] = np.array([
            585.00, 825.00, 1923.00, 3415.00, 4205.00, 5319.00, 6267.00, 9422.00
        ])

        tank_data['tank weight - kg'] = np.array([
            50.00, 67.00, 158.00, 290.00, 385.00, 530.00, 650.00, 1050.00
        ])*1000

        tank_data['tank costs each - €'] = np.array([
            450, 500, 920, 1440, 1790, 2275, 2745, 4250
        ])*1000

        tank_data_df = pd.DataFrame(data=tank_data)
        tank_data_df.name = 'floating roof'

    # ==================================================================================================================
    if tank_type == 3:
        # sphere

        tank_data['tank volume - m³'] = np.array([610, 3600])
        tank_data['tank diameter - m'] = np.array([10.5, 19.0])
        tank_data['tank weight - kg'] = np.array([100, 430])*1000
        tank_data['tank costs each - €'] = np.array([1160, 3270])*1000

        tank_data_df = pd.DataFrame(data=tank_data)
        tank_data_df.name = 'sphere'

    # ==================================================================================================================

    n_storages = 0
    surface_area = 0
    volume_aux = volume
    volume_max = max(tank_data_df['tank volume - m³'])

    if (volume < min(tank_data_df['tank volume - m³'])) | (volume > volume_max):
        costs = 0
        if (volume < min(tank_data_df['tank volume - m³'])):
            volume = min(tank_data_df['tank volume - m³'])
            costs = np.interp(volume, tank_data_df['tank volume - m³'], tank_data_df['tank costs each - €'])
            n_storages += 1

            height = np.interp(volume, tank_data_df['tank volume - m³'], tank_data_df['tank height - m'])
            diameter = np.interp(volume, tank_data_df['tank volume - m³'], tank_data_df['tank diameter - m'])

            surface_area += diameter * np.pi * height + 2 * (diameter/2)**2 * np.pi

            if verbose == True:
                print('Volume was too small. Set to the minimum available storage size ({} m³).'.format(min(tank_data_df['tank volume - m³'])))

        if volume > volume_max:
            while volume_aux >= volume_max:
                n_storages_aux = volume_aux // volume_max
                costs = costs + np.interp(volume_max, tank_data_df['tank volume - m³'], tank_data_df['tank costs each - €'])*n_storages_aux
                volume_aux = volume_aux - volume_max*n_storages_aux
                n_storages += n_storages_aux

                height = np.interp(volume_max, tank_data_df['tank volume - m³'], tank_data_df['tank height - m'])
                diameter = np.interp(volume_max, tank_data_df['tank volume - m³'], tank_data_df['tank diameter - m'])

                surface_area += (diameter * np.pi * height + 2 * (diameter / 2) ** 2 * np.pi)*n_storages_aux

            costs = costs + np.interp(volume_aux, tank_data_df['tank volume - m³'], tank_data_df['tank costs each - €'])
            n_storages += 1

            height = np.interp(volume_aux, tank_data_df['tank volume - m³'], tank_data_df['tank height - m'])
            diameter = np.interp(volume_aux, tank_data_df['tank volume - m³'], tank_data_df['tank diameter - m'])

            surface_area += diameter * np.pi * height + 2 * (diameter / 2) ** 2 * np.pi

            if verbose == True:
                print('Volume was too big. Multiple storages were selected.')
    else:
        costs = np.interp(volume, tank_data_df['tank volume - m³'], tank_data_df['tank costs each - €'])
        n_storages += 1

        height = np.interp(volume, tank_data_df['tank volume - m³'], tank_data_df['tank height - m'])
        diameter = np.interp(volume, tank_data_df['tank volume - m³'], tank_data_df['tank diameter - m'])

        surface_area += diameter * np.pi * height + 2 * (diameter / 2) ** 2 * np.pi

    return costs, n_storages, surface_area


def c_cylindrical_storage_vessels(volume, thickness, material, selection, verbose=False):
    """
    Costs for horizontal or vertical cylindrical storage vessels
    according to the prices from 'DACE Price Booklet Edition 33'.

    INPUT:
    volume:
        specifies the required volume in m³.

    thickness:
        specifies the required wall thickness in mm.

    material:
        specifies tank material ('carbon steel', 'AISI 304')

    selection:
        1: next larger storage is selected
        2: storage is selected via interpolation

    verbose (optional):
      If set to 'True', extra Info is printed.
      This is usefull to check inputs. I.e. non valid inputs get adjusted automatically.

    DESCRIPTION:
    Horizontal or vertical vessels.

    Including:
        Supports;
        X-ray;
        Inspection;
        Blasting in- and outside;
        1 Manhole;
        Maximum 9 nozzles;
        Painting outside;
        Reinforcement rings if necessary.
    Excluding:
        Heat treatment.

    Variation: Different L/D relations do have an impact on price while having the same volume.
    """

    # ==================================================================================================================
    material_list = ['carbon steel', 'AISI 304']
    if material not in material_list:
        material = material_list[0]
        if verbose == True:
            print('No valid material was specified.')
            print('Valid materials are {}. Material set to default ({}).'.format(material_list, material_list[0]))

    # ==================================================================================================================
    tank_data = {}

    tank_data['tank volume - m³'] = np.array([
        1, 1, 1, 1, 1, 1,  # 1 m³
        5, 5, 5, 5, 5, 5,  # 5 m³
        10, 10, 10, 10, 10, 10,  # 10 m³
        20, 20, 20, 20, 20, 20,  # 20 m³
        40, 40, 40, 40, 40, 40,  # 40 m³
        60, 60, 60, 60, 60,  # 60 m³
        80, 80, 80, 80,  # 80 m³
        100, 100, 100, 100,  # 100 m³
    ])

    tank_data['tank length - m'] = np.array([
        1.1, 1.1, 1.1, 1.1, 1.1, 1.1,  # 1 m³
        1.7, 1.7, 1.7, 1.7, 1.7, 1.7,  # 5 m³
        2.1, 2.1, 2.1, 2.1, 2.1, 2.1,  # 10 m³
        4.5, 4.5, 4.5, 4.5, 4.5, 4.5,  # 20 m³
        5.2, 5.2, 5.2, 5.2, 5.2, 5.2,  # 40 m³
        8, 8, 8, 8, 8,  # 60 m³
        10.9, 10.9, 10.9, 10.9,  # 80 m³
        13.7, 13.7, 13.7, 13.7,  # 100 m³
    ])

    tank_data['tank diameter - m'] = np.array([
        1, 1, 1, 1, 1, 1,  # 1 m³
        1.8, 1.8, 1.8, 1.8, 1.8, 1.8,  # 5 m³
        2.3, 2.3, 2.3, 2.3, 2.3, 2.3,  # 10 m³
        2.3, 2.3, 2.3, 2.3, 2.3, 2.3,  # 20 m³
        3, 3, 3, 3, 3, 3,  # 40 m³
        3, 3, 3, 3, 3,  # 60 m³
        3, 3, 3, 3,  # 80 m³
        3, 3, 3, 3,  # 100 m³
    ])

    tank_data['tank total surface area - m²'] = np.array([
        5.3, 5.3, 5.3, 5.3, 5.3, 5.3,  # 1 m³
        15.3, 15.3, 15.3, 15.3, 15.3, 15.3,  # 5 m³
        25, 25, 25, 25, 25, 25,  # 10 m³
        38, 38, 38, 38, 38, 38,  # 20 m³
        67, 67, 67, 67, 67, 67,  # 40 m³
        91, 91, 91, 91, 91,  # 60 m³
        118, 118, 118, 118,  # 80 m³
        145, 145, 145, 145,  # 100 m³
    ])

    tank_data['average plate thickness - mm'] = np.array([
        3, 5, 8, 10, 13, 16,  # 1 m³
        3, 5, 8, 10, 13, 16,  # 5 m³
        3, 5, 8, 10, 13, 16,  # 10 m³
        3, 5, 8, 10, 13, 16,  # 20 m³
        3, 5, 8, 10, 13, 16,  # 40 m³
        5, 8, 10, 13, 16,  # 60 m³
        8, 10, 13, 16,  # 80 m³
        8, 10, 13, 16,  # 100 m³
    ])

    tank_data['tank weight - kg'] = np.array([
        255, 405, 615, 745, 940, 1130,  # 1 m³
        670, 1045, 1575, 1915, 2405, 2910,  # 5 m³
        1010, 1570, 2370, 2900, 3700, 4485,  # 10 m³
        1515, 2365, 3630, 4465, 5685, 6930,  # 20 m³
        2235, 3550, 5475, 6755, 8660, 10510,  # 40 m³
        4725, 7335, 9045, 11570, 14255,  # 60 m³
        9215, 11345, 14765, 18195,  # 80 m³
        10985, 13720, 17855, 22000,  # 100 m³
    ])

    tank_data['tank costs each - € - carbon steel'] = np.array([
        14, 15, 16, 16, 18, 19,  # 1 m³
        22, 27, 31, 34, 35, 38,  # 5 m³
        26, 28, 30, 32, 34, 39,  # 10 m³
        32, 37, 41, 44, 47, 50,  # 20 m³
        39, 44, 51, 55, 62, 67,  # 40 m³
        52, 64, 71, 80, 89,  # 60 m³
        74, 84, 96, 106,  # 80 m³
        94, 106, 120, 133,  # 100 m³
    ])*1000

    if selection == 3:
        X = tank_data['tank volume - m³']
        Y = tank_data['average plate thickness - mm']
        B = tank_data['tank costs each - € - carbon steel']
        B2 = tank_data['tank total surface area - m²']
        A = np.array([X * 0 + 1, X, Y, X ** 2, Y ** 2, X * Y]).T

        coeff, r, rank, s = np.linalg.lstsq(A, B, rcond=-1)
        coeff_surf, _, _, _ = np.linalg.lstsq(A, B2, rcond=-1)
        #
        # fig_0 = plt.figure()
        # ax_0 = fig_0.add_subplot(111, projection='3d')
        # ax_0.scatter(X, Y, coeff[0]+X*coeff[1]+Y*coeff[2]+X**2*coeff[3]+Y**2*coeff[4] + X*Y*coeff[5])
        # ax_0.scatter(X, Y, B)

        max_volume = max(tank_data['tank volume - m³'])
        if volume > max_volume:
            divisor = 2
            while volume/divisor > max_volume:
                divisor += 1
            volume_aux = volume/divisor
            n_storages = divisor
        else:
            n_storages = 1
            volume_aux = volume

        costs = coeff[0]+volume_aux*coeff[1]+thickness*coeff[2]+volume_aux**2*coeff[3]+thickness**2*coeff[4] + volume_aux*thickness*coeff[5]
        costs = costs * n_storages
        surface_area = coeff_surf[0]+volume_aux*coeff_surf[1]+thickness*coeff_surf[2]+volume_aux**2*coeff_surf[3]+thickness**2*coeff_surf[4] + volume_aux*thickness*coeff_surf[5]
        surface_area = surface_area * n_storages
        total_volume = volume

        return costs, n_storages, surface_area, total_volume

    tank_data['tank costs each - € - AISI 304'] = np.array([
        18, 19, 22, np.NaN, np.NaN, np.NaN,  # 1 m³
        28, 35, 42, np.NaN, np.NaN, np.NaN,  # 5 m³
        35, 38, 45, np.NaN, np.NaN, np.NaN,  # 10 m³
        47, 53, 64, np.NaN, np.NaN, np.NaN,  # 20 m³
        56, 67, 86, np.NaN, np.NaN, np.NaN,  # 40 m³
        81, 106, 121, np.NaN, np.NaN,  # 60 m³
        124, 147, np.NaN, np.NaN,  # 80 m³
        155, 183, 217, np.NaN,  # 100 m³
    ]) * 1000

    tank_data_df = pd.DataFrame(data=tank_data)

    # ==================================================================================================================
    warnings.simplefilter('ignore', np.RankWarning)

    try:
        len(volume)
    except:
        volume = np.array([volume])

    n_storages = np.zeros(len(volume))
    surface_area = np.zeros(len(volume))
    costs = np.zeros(len(volume))

    volume_max = max(tank_data_df['tank volume - m³'])
    volume_min = min(tank_data_df['tank volume - m³'])
    total_volume = np.zeros(len(volume))

    thickness_max = max(tank_data_df['average plate thickness - mm'])

    # Indices for categories of vessel volumes
    idx_too_small = volume < volume_min
    idx_too_big = (volume > volume_max) & (volume < 3 * volume_max)
    idx_too_big_3 = (volume >= 3 * volume_max)
    idx_rest = (volume >= volume_min) & (volume <= volume_max)

    if (thickness > thickness_max) & (selection == 1):
        if verbose == True:
            print('Specified wall thickness ({} mm) exceeds maximum available wall thickness ({} mm).'. format(thickness, thickness_max))
            print('Thickness set to maximum available thicknes. Please select a smaller wall thickness!')

        thickness = thickness_max


    if idx_too_small.any():

        idxmin_vol = tank_data_df['tank volume - m³'].idxmin(axis=0)
        min_vol = tank_data_df['tank volume - m³'][idxmin_vol]

        volume[idx_too_small] = min_vol
        total_volume[idx_too_small] += min_vol

        if selection == 2:
            pot_tanks = tank_data_df[tank_data_df['tank volume - m³'] >= min_vol]
            pot_tanks = pot_tanks[pot_tanks['tank volume - m³'] == min(pot_tanks['tank volume - m³'])]
            fit = np.polyfit(pot_tanks['average plate thickness - mm'], pot_tanks['tank costs each - € - {}'.format(material)], 1)

            idxmin_costs = pot_tanks['tank costs each - € - {}'.format(material)].idxmin(axis=0)
            min_costs = np.poly1d(fit)(thickness)
            min_surface_area = pot_tanks['tank total surface area - m²'][idxmin_costs]

        if selection == 1:
            pot_tanks = tank_data_df[(tank_data_df['tank volume - m³'] >= min_vol) & (
                        tank_data_df['average plate thickness - mm'] >= thickness)]
            idxmin_costs = pot_tanks['tank costs each - € - {}'.format(material)].idxmin(axis=0)
            min_costs = pot_tanks['tank costs each - € - {}'.format(material)][idxmin_costs]
            min_surface_area = pot_tanks['tank total surface area - m²'][idxmin_costs]

        costs[idx_too_small] = min_costs
        n_storages[idx_too_small] += 1
        surface_area[idx_too_small] = min_surface_area

        if verbose == True:
            print('Volume was too small. Set to the minimum available storage size ({} m³).'.format(min(tank_data_df['tank volume - m³'])))

    if idx_too_big.any():
        idx_number = [i for i, x in enumerate(idx_too_big) if x]
        for i, vol in enumerate(volume[idx_number]):
            volume_aux = vol

            big_storages = vol//volume_max

            if selection == 2:
                pot_tanks = tank_data_df[tank_data_df['tank volume - m³'] >= volume_max]
                pot_tanks = pot_tanks[pot_tanks['tank volume - m³'] == min(pot_tanks['tank volume - m³'])]
                fit = np.polyfit(pot_tanks['average plate thickness - mm'],
                                 pot_tanks['tank costs each - € - {}'.format(material)], 1)

                idxmin_costs = pot_tanks['tank costs each - € - {}'.format(material)].idxmin(axis=0)
                min_costs = np.poly1d(fit)(thickness)
                min_surface_area = pot_tanks['tank total surface area - m²'][idxmin_costs]

            if selection == 1:
                pot_tanks = tank_data_df[(tank_data_df['tank volume - m³'] >= volume_max) & (
                        tank_data_df['average plate thickness - mm'] >= thickness)]
                idxmin_costs = pot_tanks['tank costs each - € - {}'.format(material)].idxmin(axis=0)
                min_costs = pot_tanks['tank costs each - € - {}'.format(material)][idxmin_costs]
                min_surface_area = pot_tanks['tank total surface area - m²'][idxmin_costs]

            total_volume[idx_number[i]] = volume_max * big_storages
            costs[idx_number[i]] = min_costs * big_storages
            n_storages[idx_number[i]] += big_storages
            surface_area[idx_number[i]] = min_surface_area * big_storages

            ##########

            volume_aux = volume_aux - volume_max*big_storages

            if selection == 2:
                pot_tanks = tank_data_df[tank_data_df['tank volume - m³'] >= volume_aux]
                pot_tanks = pot_tanks[pot_tanks['tank volume - m³'] == min(pot_tanks['tank volume - m³'])]
                fit = np.polyfit(pot_tanks['average plate thickness - mm'],
                                 pot_tanks['tank costs each - € - {}'.format(material)], 1)

                idxmin_costs = pot_tanks['tank costs each - € - {}'.format(material)].idxmin(axis=0)
                min_costs = np.poly1d(fit)(thickness)
                min_surface_area = pot_tanks['tank total surface area - m²'][idxmin_costs]

            if selection == 1:
                pot_tanks = tank_data_df[(tank_data_df['tank volume - m³'] >= volume_aux) & (
                        tank_data_df['average plate thickness - mm'] >= thickness)]
                idxmin_costs = pot_tanks['tank costs each - € - {}'.format(material)].idxmin(axis=0)
                min_costs = pot_tanks['tank costs each - € - {}'.format(material)][idxmin_costs]
                min_surface_area = pot_tanks['tank total surface area - m²'][idxmin_costs]

            total_volume[idx_number[i]] = pot_tanks['tank volume - m³'][idxmin_costs]
            costs[idx_number[i]] += min_costs
            n_storages[idx_number[i]] += 1
            surface_area[idx_number[i]] = min_surface_area

        if verbose == True:
            print('Volume was too big. Multiple storages were selected.')

    if idx_too_big_3.any():
        big_storages = np.ceil(volume[idx_too_big_3] / volume_max)

        if selection == 2:
            pot_tanks = tank_data_df[tank_data_df['tank volume - m³'] >= volume_max]
            pot_tanks = pot_tanks[pot_tanks['tank volume - m³'] == min(pot_tanks['tank volume - m³'])]
            fit = np.polyfit(pot_tanks['average plate thickness - mm'],
                             pot_tanks['tank costs each - € - {}'.format(material)], 1)

            idxmin_costs = pot_tanks['tank costs each - € - {}'.format(material)].idxmin(axis=0)
            min_costs = np.poly1d(fit)(thickness)
            min_surface_area = pot_tanks['tank total surface area - m²'][idxmin_costs]

        if selection == 1:
            pot_tanks = tank_data_df[(tank_data_df['tank volume - m³'] >= volume_max) & (
                    tank_data_df['average plate thickness - mm'] >= thickness)]
            idxmin_costs = pot_tanks['tank costs each - € - {}'.format(material)].idxmin(axis=0)
            min_costs = pot_tanks['tank costs each - € - {}'.format(material)][idxmin_costs]
            min_surface_area = pot_tanks['tank total surface area - m²'][idxmin_costs]

        total_volume[idx_too_big_3] = volume_max * big_storages
        n_storages[idx_too_big_3] = big_storages
        costs[idx_too_big_3] += min_costs * big_storages
        surface_area[idx_too_big_3] += min_surface_area * big_storages

        if verbose == True:
            print('Volume was too big. Multiple storages were selected.')

    if idx_rest.any():
        idx_number = [i for i, x in enumerate(idx_rest) if x]
        for i, vol in enumerate(volume[idx_number]):
            if selection == 2:
                pot_tanks = tank_data_df[tank_data_df['tank volume - m³'] >= vol]
                pot_tanks = pot_tanks[pot_tanks['tank volume - m³'] == min(pot_tanks['tank volume - m³'])]
                fit = np.polyfit(pot_tanks['average plate thickness - mm'],
                                 pot_tanks['tank costs each - € - {}'.format(material)], 1)

                idxmin_costs = pot_tanks['tank costs each - € - {}'.format(material)].idxmin(axis=0)
                min_costs = np.poly1d(fit)(thickness)
                min_surface_area = pot_tanks['tank total surface area - m²'][idxmin_costs]

            if selection == 1:
                pot_tanks = tank_data_df[(tank_data_df['tank volume - m³'] >= vol) & (
                        tank_data_df['average plate thickness - mm'] >= thickness)]
                idxmin_costs = pot_tanks['tank costs each - € - {}'.format(material)].idxmin(axis=0)
                min_costs = pot_tanks['tank costs each - € - {}'.format(material)][idxmin_costs]
                min_surface_area = pot_tanks['tank total surface area - m²'][idxmin_costs]

            total_volume[idx_number[i]] = pot_tanks['tank volume - m³'][idxmin_costs]
            costs[idx_number[i]] += min_costs
            surface_area[idx_number[i]] += min_surface_area
            n_storages[idx_number[i]] += 1

    return costs, n_storages, surface_area, total_volume


def c_heat_exchangers(hex_type, area, material, verbose=False):
    """
    Calculates costs for different types of heat exchangers.

    INPUT:
    hex_type:
        hex_type == 1:  A1009. Carbon steel heat exchangers (pipe bundle and shell of carbon steel)
        hex_type == 2:  A1009. Carbon steel heat exchangers (pipe bundle and shell of carbon steel) - U-type
        hex_type == 3:  A1010. Stainless steel heat exchangers (pipe bundle and shell of carbon steel)
        hex_type == 4:  A1010. Stainless steel heat exchangers (pipe bundle and shell of carbon steel) - U-type

    area:
        specifies heat exchanger area (m²).
        If specified area exceeds maximum available HEX area, multiple HEX are selected.

    material:
        specifies hex material.

    verbose (optional):
      If set to 'True', extra Info is printed.
      This is useful to check inputs. I.e. non valid inputs get adjusted automatically.

    DESCRIPTION:
    A1009. Carbon steel heat exchangers
    Pipe bundle and shell of carbon steel, fixed tube sheet, without expansion bellows, Ø 20 mm.
    Design: 'U' tube bundle 10 - 15% cost increase and 5 - 12% weight increase.

    A1010. Stainless steel heat exchangers
    Pipe bundle and shell of stainless steel, fixed tube sheet, without expansion bellows, Ø 20 mm.
    Variation: 'U' tube bundle 10 - 15% cost increase and 5 - 12% weight increase.
    """

    # ==================================================================================================================
    if hex_type in [1, 2]:
        if verbose == True:
            print('Material selection not considered. Material for hex_type 1&2 is carbon steel!')

        material = 'carbon steel'

        hex_data = {}
        
        hex_data['heat transfer area - m²'] = np.array([
            2, 4, 6, 8, 10, 15, 20, 30, 40, 50, 70, 100, 200, 300, 500, 700, 1000
        ])

        hex_data['weight - kg'] = np.array([
            200, 300, 400, 450, 500, 800, 900, 1300, 1600, 1900, 2600, 3600, 6500, 10000, 15000, 21000, 29000
        ])

        hex_data['costs - € - carbon steel'] = np.array([
            16, 20, 22, 23, 23, 27, 29, 31, 32, 36, 38, 46, 62, 76, 112, 152, 181
        ]) * 1000

        hex_data_df = pd.DataFrame(data=hex_data)

        if hex_type == 2:
            hex_data_df['weight - kg'] = hex_data_df['weight - kg'] * 1.1
            hex_data_df['costs - € - carbon steel'] = hex_data_df['costs - € - carbon steel'] * 1.1

    # ==================================================================================================================
    if hex_type in [3, 4]:
        material_list = ['AISI 304', 'AISI 316L']
        if material not in material_list:
            if verbose == True:
                print('Material selection not in {}. Material set to {} (default)!'.format(material_list, material_list[0]))

            material = material_list[0]

        hex_data = {}

        hex_data['heat transfer area - m²'] = np.array([
            2, 4, 6, 8, 10, 15, 20, 30, 40, 50, 70, 100, 200, 300, 500, 700, 1000
        ])

        hex_data['weight - kg'] = np.array([
            150, 250, 300, 400, 450, 600, 700, 1000, 1200, 1500, 1900, 2500, 4700, 6600, 11000, 15000, 20000
        ])

        hex_data['costs - € - AISI 304'] = np.array([
            21, 25, 28, 30, 31, 34, 38, 41, 44, 50, 54, 68, 90, 118, 180, 244, 305,
        ]) * 1000

        hex_data['costs - € - AISI 316L'] = np.array([
            23, 27, 30, 32, 34, 37, 40, 43, 48, 55, 62, 78, 106, 133, 203, 274, 338,
        ]) * 1000

        hex_data_df = pd.DataFrame(data=hex_data)

        if hex_type == 4:
            hex_data_df['weight - kg'] = hex_data_df['weight - kg'] * 1.1
            hex_data_df['costs - € - AISI 304'] = hex_data_df['costs - € - AISI 304'] * 1.1
            hex_data_df['costs - € - AISI 316L'] = hex_data_df['costs - € - AISI 316L'] * 1.1

    # ==================================================================================================================

    n_hex = 0
    area_min = min(hex_data_df['heat transfer area - m²'])
    area_max = max(hex_data_df['heat transfer area - m²'])
    area_aux = area

    if area < area_min:
        area = area_min

        if verbose == True:
            print('Specified area was smaller than the minimum available HEX-area ({} m²).'.format(area_min))
            print('Area was set to the minimum availbale HEX-area.')

    if area > area_max:
        costs = 0
        while area_aux >= area_max:
            costs = costs + np.interp(area_aux, hex_data_df['heat transfer area - m²'], hex_data_df['costs - € - {}'.format(material)])
            area_aux = area_aux - area_max
            n_hex += 1

        if verbose == True:
            print('Specified area was bigger than the maximum available HEX-area ({} m²).'.format(area_max))
            print('Multiple HEX are used.')
    else:
        costs = np.interp(area, hex_data_df['heat transfer area - m²'], hex_data_df['costs - € - {}'.format(material)])
        n_hex += 1

    return costs, n_hex


def c_insulation(insulation_type, temperature, area, factor, verbose=False):
    """
    Calculates insulation costs depending on equipment temperature
    according to 'DACE Price Booklet Edition 33'.

    INPUT:
    insulation_type:
        insulation_type == 1: Flat parts, walls, channels and tank roofs
        insulation_type == 2: Vessels, tanks and heat exchangers

    temperature:
        Equipment temperature in °C.

    area:
        specifies area to be insulated (m²).

    factor:
        Other parts like heads, bottom, caps, manholes, support and vacuum rings are
        calculated using a factor. Overlaps and spaces less than 1 m2 are not included in the
        calculations.

        Part -- Equipment -- Factor on m2
        =================================
        Spherical top, bottom or front -- Tanks/vessels/columns/heat exchangers -- 3.0 body part
        Segment cap, ring cap, conical piece or point cap -- Tanks/vessels/columns/heat exchangers -- 2.5 body part
        Transition piece, conical piece, point cap -- Tanks/vessels/columns/heat exchangers -- 2.0 body part
        Flat head, cap, lid or end piece whether or not removable -- Tanks/vessels/columns/heat exchangers -- 1.5 flat surface
        Cabinets or doors -- Turbines, pumps -- 2.0 flat surface

    verbose (optional):
      If set to 'True', extra Info is printed.
      This is useful to check inputs. I.e. non valid inputs get adjusted automatically.

    DESCRIPTION:
    C2001. Thermal insulation of equipment
    Cost per square meter. The total costs are defined by the sum of all calculated
    surface areas. The surface area is calculated over the exterior of the insulation. The
    body runs from tangent line to tangent line.

    Other parts like heads, bottom, caps, manholes, support and vacuum rings are
    calculated using a factor. Overlaps and spaces less than 1 m2 are not included in the
    calculations.

    The surface area of connections (nozzles) and supports must be calculated
    separately. The height is defined as the distance from the exterior of the equipment to
    the outside layer of the insulation (see also comments on measurement C2002).

    The factors could deviate somewhat and are simplified compared to general
    industrial measuring methods.

    Material: glass wool with aluminum sheeting.
    """
    # ==================================================================================================================

    insulation_data = {}
    insulation_data['temperature - °C'] = np.array([
        80, 130, 185, 245, 300, 360, 430
    ])

    insulation_data['thickness - mm'] = np.array([
        30, 60, 80, 100, 120, 140, 160
    ])

    if insulation_type == 1:
        insulation_data['costs per m² - €'] = np.array([
            92, 102, 105, 114, 121, 126, 134
        ])

    if insulation_type == 2:
        insulation_data['costs per m² - €'] = np.array([
            99, 108, 113, 122, 131, 137, 143
        ])

    insulation_data_df = pd.DataFrame(data=insulation_data)

    # ==================================================================================================================

    temperature_min = min(insulation_data_df['temperature - °C'])
    temperature_max = max(insulation_data_df['temperature - °C'])

    if temperature < temperature_min:
        temperature = temperature_min
        if verbose == True:
            print('Specified temperature too low. Temperature set to the minimum available temperature ({} °C).'.format(temperature_min))

    if temperature > temperature_max:
        temperature = temperature_max
        if verbose == True:
            print('Specified temperature too high. Temperature set to the maximum available temperature ({} °C).'.format(
            temperature_max))

    costs = factor * area * np.interp(temperature, insulation_data_df['temperature - °C'], insulation_data_df['costs per m² - €'])

    return costs




