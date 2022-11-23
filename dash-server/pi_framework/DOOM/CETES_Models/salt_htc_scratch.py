
#def calc_heattransfercoeff_Moltensalt(param_moltensalt, param_general, volume_flow):

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import CoolProp.CoolProp as cp
import operator
from scipy import constants
import cost_fun_comp as cfc
from mpl_toolkits.mplot3d import Axes3D

param_moltensalt = {
    'Type': 'Molten Salt - Yara MOST',
    'Salt parameters': {
        'Tfreeze': 135,                 # Celsius
        'cp': 2100,                     # J/kg*K
        'rho_salt': 2210,               # kg/m3, at 200°C
        'viscosity_dyn': 0.0036,        # Dynamic viscosity at 200°C in Pa*s
        'c_salt': 0.7,                  # €/kg - actually cost is in the range 0.7-1.5, depending on the volume
    },
    'Tank parameters': {
        'container_thickness': 0.01,    # m
    },
    'Unit conversion': {
        'm3ps2Gpm': 15850.32,
        'watt2Hp': 1341.022,
        'dollar2eur': 0.90,
        'm2feet': 3.2808399,
    },
    'charging': 1,
    'discharging': 1,
    'integration parameters': {},   # costs = c[0] + X*c[1] + Y*c[2] + X**2*c[3] + Y**2*c[4] + X*Y*c[5]
}


res = 20


Ts_max = 250
Ts_min = 200
T_salt = np.linspace(Ts_min, Ts_max, res)
Tw_in = 90
Tw_out = 200
p_water = 1.5*10**6 # Pa

Tave = (Ts_max + Ts_min) / 2
cp_ave = -0.8611 * Tave + 1922.8
rho_ave = -0.0018 * Tave ** 2 + 0.1438 * Tave + 2254.7

# The tube/shell diameters, as well as the number of parallel tubes, should depend on load!!!
d_i = 0.02 # inner tube diameter, in m
thick = 0.0015 # tube thickness
d_o = d_i + 2*thick


def calcHTCpreheat(d_i, thick, Ntubes, load, tw_in, tw_out, ts_in, ts_out, htc_salt):
    t_w = np.linspace(tw_in, tw_out, res)
    t_s = np.linspace(ts_in, ts_out, res)
    cp_w = cp.PropsSI('Cpmass', 'T', (tw_out + tw_in)/2 + 273.15, 'Q', 0, 'Water')
    mflow = load*1000 / (cp_w * (tw_out - tw_in)) / Ntubes

    htc_water = np.zeros(res)
    Lx = np.zeros(res)
    ua_tot = np.zeros(res)

    idx = 0
    for i, t in enumerate(t_w):
        if idx <res-1:
            t_f = (t_w[idx] + t_w[idx+1]) / 2
            lmtd = ((t_s[idx] - t_w[idx]) - (t_s[idx+1] - t_w[idx+1]))/ np.log(
                (t_s[idx] - t_w[idx]) / (t_s[idx+1] - t_w[idx+1]))
            # Water properties at the present fluid temperature
            rho_w = cp.PropsSI('D', 'T', t_f + 273.15, 'Q', 0, 'Water')
            k_w = cp.PropsSI('conductivity', 'T', t_f + 273.15, 'Q', 0, 'Water')
            visc_dyn = cp.PropsSI('viscosity', 'T', t_f + 273.15, 'Q', 0, 'Water')
            visc_kin = visc_dyn / rho_w
            Pr = cp.PropsSI('Prandtl', 'T', t_f + 273.15, 'Q', 0, 'Water')

            v = mflow / (rho_w * np.pi * (d_i / 2) ** 2)   # flow velocity m/s
            qflow_x = mflow*cp_w*(t_w[idx+1]-t_w[idx])

            Re_l = d_i * v / visc_kin
            # Gnielinski equation for internal flow, valid over a large range of Reynolds numbers
            # (according to Incropera)
            if Re_l < 2300:
                Nu_l = 4.36
            #elif 2300 <= Re_l < 10e4:
            #    Nu_l = 0.023 * Re_l ** (4 / 5) * Pr ** 0.4
            else:
                f = (0.79 * np.log(Re_l) - 1.64) ** (-2)
                Nu_l = (f / 8) * (Re_l - 1000) * Pr / (1 + 12.7 * (f / 8) ** 0.5 * (Pr ** (2 / 3) - 1))

            htc_water[idx] = Nu_l*k_w/d_i

            Lx[idx] = qflow_x / (lmtd * np.pi) * (1 / (htc_water[idx] * d_i) + 1 / (htc_salt * (d_i + 2 * thick)))
            ua_tot[idx] = (1 / (htc_water[idx] * np.pi * d_i * Lx[idx]) + 1 / (
                    htc_salt * np.pi * (d_i + thick * 2) * Lx[idx])) ** (-1)
            idx += 1

    Ltube = np.sum(Lx)
    Atot = Ltube*Ntubes * np.pi * (d_i + thick * 2)
    UAtot = np.average(ua_tot)
    Utot = UAtot/Atot
    return np.average(htc_water), Utot, Ltube, Atot

def calcHTCevap(d_i, thick, Ntubes, load, p, h_in, h_out, tsalt_in, tsalt_out, htc_salt):
    # Calculates the heat transfer coefficient for the evaporator, considering the heat transfer coefficients for
    # boiling water and salt flowing across a tube bundle.
    # The htc for water boiling in a tube is calculated using the Gungor & Winterton correlation
    # Outputs:
    # htc_steam - Heat transfer coefficient for steam as a function of steam enthalpy
    # ua_tot - total UA-value for the heat exchanger as a function of steam enthalpy
    # Ltot - the required length of the HX
    # fixme In the LMTD, should somehow consider that the pipe is U-type/bent!

    mflow = load*1000/(h_out-h_in) /Ntubes
    dh = (h_out - h_in) / res
    dq = dh*mflow
    h_steam = np.linspace(h_in, h_out, res)
    t_salt = np.linspace(tsalt_in, tsalt_out, res)
    A_i = np.pi * (d_i/2) ** 2
    mflux = mflow / A_i  # mass flux in kg/(s*m2)

    p_c = cp.PropsSI('pcrit','Water')
    p_r = p /p_c

    rho_v = cp.PropsSI('D', 'P', p, 'Q', 1, 'Water')
    rho_l = cp.PropsSI('D', 'P', p, 'Q', 0, 'Water')
    visc_dyn_v = cp.PropsSI('viscosity', 'P', p, 'Q', 1, 'Water')
    visc_dyn_l = cp.PropsSI('viscosity', 'P', p, 'Q', 0, 'Water')
    k_l = cp.PropsSI('conductivity', 'P', p, 'Q', 0, 'Water')
    k_v = cp.PropsSI('conductivity', 'P', p, 'Q', 1, 'Water')
    Pr_l = cp.PropsSI('Prandtl', 'P', p, 'Q', 0, 'Water')
    Pr_v = cp.PropsSI('Prandtl', 'P', p, 'Q', 1, 'Water')
    visc_kin_l = visc_dyn_l / rho_l
    visc_kin_v = visc_dyn_v / rho_v

    v_l = mflow / (rho_l * A_i)  # liquid flow velocity m/s
    v_v = mflow / (rho_v * A_i)  # vapor flow velocity m/s
    Re_l = d_i * v_l / visc_kin_l
    Re_v = d_i * v_v / visc_kin_v

    # HTC for liquid with the Gnielinski equation for internal flow
    if Re_l < 2300:
        Nu_l = 4.36
    elif 2300 <= Re_l < 10e4:
        Nu_l = 0.023*Re_l**(4/5) * Pr_l**0.4
    else:
        f = (0.79 * np.log(Re_l) - 1.64) ** (-2)
        Nu_l = (f / 8) * (Re_l - 1000) * Pr_l / (1 + 12.7 * (f / 8) ** 0.5 * (Pr_l ** (2 / 3) - 1))
    htc_l = Nu_l * k_l / d_i

    # HTC for vapor with the Gnielinski equation for internal flow
    if Re_v < 2300:
        Nu_v = 4.36
    elif 2300 <= Re_v < 10e4:
        Nu_v = 0.023*Re_v**(4/5) * Pr_v**0.4
    else:
        f = (0.79 * np.log(Re_v) - 1.64) ** (-2)
        Nu_v = (f / 8) * (Re_v - 1000) * Pr_v / (1 + 12.7 * (f / 8) ** 0.5 * (Pr_v ** (2 / 3) - 1))
    htc_v = Nu_v * k_v / d_i

    htc_steam = np.zeros(res)
    ua_tot = np.zeros(res)
    Lx = np.zeros(res)
    Bo = np.zeros(res)

    idx = 1
    for i, h in enumerate(h_steam):
        # Water/steam properties at the present fluid temperature
        h_ave = (h_steam[idx - 1] + h_steam[idx]) / 2
        x = cp.PropsSI('Q', 'P', p, 'H', h_ave, 'Water')
        t_steam_ave = cp.PropsSI('T', 'P', p, 'H', h_ave, 'Water') - 273.15
        lmtd = (t_salt[idx - 1] - t_salt[idx]) / np.log(
            (t_salt[idx - 1] - t_steam_ave) / (t_salt[idx] - t_steam_ave))
        if x < 0.8:
            M = cp.PropsSI('M', 'P', p, 'H', h_ave, 'Water')
            eps = 10
            # First estimate for required tube segment length, using only HTF of salt
            Lx0 =  dq/(lmtd * np.pi)*(1/(htc_salt*(d_i+2*thick)))
            while eps > 0.0001:
                q_flux = dq/(np.pi*d_i*Lx0)
                Bo[idx] = q_flux/((h_out-h_in)*(1-x)*mflux)
                X_tt = ((1-x)/x)**0.9 * (rho_v/rho_l)**0.5 * (visc_dyn_l/visc_dyn_v)**0.1
                E = 1 + 24000*Bo[idx]**1.16 + 1.37*(1/X_tt)**0.86

                htc_pool = 55*p_r**0.12 * (-np.log10(p_r))**(-0.55) * M**(-0.5) * q_flux**0.67
                S = 1/(1 + 1.15e-6 * E**2 * Re_l**1.17)

                Fr = ((1-x)*mflux)**2 /(rho_l**2 * constants.g *d_i)
                if Fr < 0.05:
                     E = E * Fr**(0.1-2*Fr)
                     S = S*np.sqrt(Fr)

                htc_steam[idx] = E*htc_l + S*htc_pool
                # fixme: should include conduction??
                Lx[idx] = dq/(lmtd * np.pi)*(1/(htc_steam[idx]*d_i) + 1/(htc_salt*(d_i+2*thick)))
                eps = np.abs(Lx0-Lx[idx])
                Lx0 = Lx[idx]

            ua_tot[idx] = (1 / (htc_steam[idx] * np.pi * d_i * Lx[idx]) + 1 / (
                        htc_salt * np.pi * (d_i + thick * 2) * Lx[idx]))**(-1)
            idx += 1
        elif x - 0.8 < 0.02 and idx < res-1:
            idx_08 = idx-1
            htc_steam[idx] = htc_steam[idx_08] + (htc_v-htc_steam[idx_08])/(h_out-h_steam[idx_08])*(h_steam[idx]-h_steam[idx_08])
            Lx[idx] = dq / (lmtd * np.pi) * (1 / (htc_steam[idx] * d_i) + 1 / (htc_salt * (d_i + 2 * thick)))
            idx += 1
        elif x - 0.8 > 0.02 and idx < res-1:
            htc_steam[idx] = htc_steam[idx_08] + (htc_v-htc_steam[idx_08])/(h_out-h_steam[idx_08])*(h_steam[idx]-h_steam[idx_08])
            Lx[idx] = dq / (lmtd * np.pi) * (1 / (htc_steam[idx] * d_i) + 1 / (htc_salt * (d_i + 2 * thick)))
            idx += 1

    Ltube = np.sum(Lx)
    Atot = Ltube*Ntubes * np.pi * (d_i + thick * 2)
    UAtot = np.average(ua_tot[1:res-2])
    Utot = UAtot/Atot

    return np.average(htc_steam[1:res-2]), Utot, Ltube, Atot

def calcHTCsalt(D, d_o, mflow, Tave, Ntubes):
    # Calculates the heat transfer coefficient for salt for flow across a tube bundle using the  Zukauskas correlation
    # The properties are calculated at the average fluid temperature, but the result is not very sensitive to temperature
    # It is assumed that the number of tubes in longitudinal direction is > 20, and that the tubes have a staggered
    # configuration, arranged as equilateral triangles with
    #           S = 1.25*d_o,
    # where S = triangle side length and d_o is the outer diameter of the tubes in the tube bundle


    # Allowed range of baffle spacings based on Design and Rating of Shell and Tube Heat Exchangers by John E. Edwards
    B = np.linspace(D/5, 75*d_o**0.75, res) #

    cp_ave = -0.8611 * Tave + 1922.8
    rho_ave = -0.0018 * Tave ** 2 + 0.1438 * Tave + 2254.7
    viscosity_dyn = 42.686*Tave**(-1.729)
    viscosity_kin = viscosity_dyn/rho_ave
    k_s = 0.5 # Thermal conductivity of salt, based on Y.Y. Chen, C.Y. Zhao / Solar Energy 146 (2017) 172–179
    Pr = cp_ave*viscosity_dyn/k_s

    # Characteristic length
    d_s = np.pi * d_o / 2
    void_frac = 1 - np.pi / 5
    a = 1.25
    f_a = 1+2/(3*a)

    htc_salt = np.zeros(res)
    # Number of lines and rows estimated as if the tubes had a square arrangement
    Nlines = np.round(np.sqrt(Ntubes))

    for idx, b in enumerate(B):
        # Shellside crossflow area based on Design and Rating of Shell and Tube Heat Exchangers by John E. Edwards
        #A_s = D * b / 5

        # FLow area in between the tubes
        A_s = b*Nlines*1.25*d_o

        v = mflow / (rho_ave * A_s)
        Re = v*d_s/(void_frac*viscosity_kin)
        Nu_lam = 0.664*np.sqrt(Re)*Pr**(1/3)
        Nu_turb = 0.037*Re**0.8*Pr / (1 + 2.443*Re**(-0.1)*(Pr**(2/3)-1))

        if Nlines < 10:
            Nu_bundle = (1 + (Nlines-1)*f_a)/Nlines * (0.3 + np.sqrt(Nu_lam**2 + Nu_turb**2))
        else:
            Nu_bundle = f_a *(0.3 + np.sqrt(Nu_lam**2 + Nu_turb**2))

        htc_salt[idx] = Nu_bundle*k_s/d_s


    maxidx = np.argmax(htc_salt)
    A_s_max = B[maxidx]*Nlines*1.25*d_o
    vmax = mflow / (rho_ave * A_s_max)
    Re_max = vmax*d_s/(void_frac*viscosity_kin)
    if Re_max < 1000:
        Eu = 0.795 + 0.247e3/Re_max + 0.335e3/Re_max**2 - 0.155/Re_max**3
    else:
        Eu = 0.245 + 0.339e4 / Re_max - 0.984e7 / Re_max ** 2
    dp = Nlines*(rho_ave*vmax**2/2)*Eu

    return np.max(htc_salt), dp, Re_max



h_w_start = cp.PropsSI('H','T',Tw_in+273.15, 'P', p_water, 'water') #inlet enthalpy for water in J/kg*K
h_s_start = cp.PropsSI('H','P',p_water,'Q',0,'water')   #start enthalpy for evaporating water (saturated) in J/kg*K
h_s_final = cp.PropsSI('H','P',p_water,'Q',1,'water')   #final enthalpy for water (saturated steam) in J/kg*K
h_total = np.linspace(h_w_start, h_s_final, res)
h_steam = np.linspace(h_s_start, h_s_final, res)
h_preheat = np.linspace(h_w_start, h_s_start, res)


T_water = cp.PropsSI('T','H',h_total, 'P', p_water, 'water') - 273.15 #inlet enthalpy for water in J/kg*K

pinch_idx, Tpinch = min(enumerate(T_salt - T_water), key=operator.itemgetter(1))
Ts_pinch = T_salt[pinch_idx]
Tw_pinch = T_water[pinch_idx]
h_w_pinch = h_total[pinch_idx]

lmtd1 = ((Ts_min - Tw_in) - (Ts_pinch - Tw_pinch)) / (np.log((Ts_min - Tw_in)) / (Ts_pinch - Tw_pinch))
lmtd2 = ((Ts_max - Tw_out) - (Ts_pinch - Tw_pinch)) / (np.log((Ts_max - Tw_out)) / (Ts_pinch - Tw_pinch))

load = np.linspace(800,80000,10) # in kW


res_t = 40
Ntubes = np.linspace(10,400,res_t)
#Dshell = np.linspace(0.25, 5, 20) # Shell diameter

htc_salt_preheat = np.zeros((res_t,10))
htc_salt_evap = np.zeros((res_t,10))
htc_water = np.zeros((res_t,10))
htc_steam = np.zeros((res_t,10))

Atot_preheat = np.zeros((res_t,10))
Atot_evap = np.zeros((res_t,10))
Utot_preheat = np.zeros((res_t,10))
Utot_evap = np.zeros((res_t,10))
Ltube_preheat = np.zeros((res_t,10))
Ltube_evap = np.zeros((res_t,10))
dp_preh = np.zeros((res_t,10))
dp_evap = np.zeros((res_t,10))
hx_area_preheat= np.zeros(10)
hx_area_evap = np.zeros(10)
hx_preheat_costs= np.zeros(10)
hx_evap_costs= np.zeros(10)
n_hx_preh = np.zeros(10)
n_hx_evap = np.zeros(10)
pump_costs= np.zeros(10)
htc_salt_ph_chosen = np.zeros(10)
htc_water_ph_chosen = np.zeros(10)
htc_salt_eva_chosen = np.zeros(10)
htc_steam_chosen = np.zeros(10)
Utot_preheat_chosen = np.zeros(10)
Utot_eva_chosen = np.zeros(10)

Ntubes_evap_chosen = np.zeros(10)
Ntubes_preh_chosen = np.zeros(10)
Re_max_ph = np.zeros(10)
Re_max_ev = np.zeros(10)

# Coefficients for calculating bundle diameter
k_bdl = 0.319
n_bdl = 2.142
d_bdl_ph = d_o * (Ntubes / k_bdl) ** (1 / n_bdl)
# In evap:considering that it is a U-type -> twice the nr of tubes
d_bdl_evap = d_o * (2*Ntubes / 0.249) ** (1 /2.207)
mflow_salt = load * 1000 / (cp_ave * (Ts_max - Ts_min))  # in kg/s
vflow_salt = mflow_salt / rho_ave * 3600  # in m3/h

for j,ld in enumerate(load):
    load_preheat = ld * (h_w_pinch - h_w_start) / (h_s_final - h_w_start)
    load_evaporation = ld * (h_s_final - h_w_pinch) / (h_s_final - h_w_start)
    for i, n_t in enumerate(Ntubes):
        htc_salt_preheat[i,j], dp_preh[i,j], Re_max_ph[j] = calcHTCsalt(1.1*d_bdl_ph[i], d_o, mflow_salt[j], (Ts_min + Ts_pinch) / 2, n_t)
        htc_water[i,j], Utot_preheat[i,j], Ltube_preheat[i,j], Atot_preheat[i,j] = calcHTCpreheat(d_i, thick, n_t, load_preheat, Tw_in, Tw_pinch, Ts_min, Ts_pinch, htc_salt_preheat[i,j])

        if Ltube_preheat[i,j] < 5.5*d_bdl_ph[i] or Ltube_preheat[i,j] > 11*d_bdl_ph[i]:
            Atot_preheat[i,j] = 0

        htc_salt_evap[i,j], dp_evap[i,j], Re_max_ev[j] = calcHTCsalt(1.1*d_bdl_evap[i], d_o, mflow_salt[j], (Ts_pinch + Ts_max) / 2, 2*n_t)
        htc_steam[i,j], Utot_evap[i,j], Ltube_evap[i,j], Atot_evap[i,j] = calcHTCevap(d_i, thick, n_t, load_evaporation, p_water, h_s_start, h_s_final, Ts_pinch, Ts_max, htc_salt_evap[i,j])

        if Ltube_evap[i,j] < 5.5*d_bdl_evap[i] or Ltube_evap[i,j] > 11*d_bdl_evap[i]:  # fixme should the tube length here be divided by 2 or not? Leads to unrealistically high HTCs..
            Atot_evap[i,j] = 0

    if np.size(Atot_preheat[Atot_preheat[:,j] > 0, j]) > 0:
        min_loc = np.where(Atot_preheat[:,j] == np.min(Atot_preheat[np.nonzero(Atot_preheat[:,j]),j]))
        idx_min = min_loc[0][0]
        dp_preh_min = dp_preh[idx_min,j]
        hx_area_preheat[j] = Atot_preheat[idx_min,j]
        hx_preheat_costs[j], n_hx_preh[j] = cfc.c_heat_exchangers(3, hx_area_preheat[j], 'AISI 304')
        htc_salt_ph_chosen[j] = htc_salt_preheat[idx_min,j]
        Utot_preheat_chosen[j] = Utot_preheat[idx_min,j]
        htc_water_ph_chosen[j] = htc_water[idx_min, j]
        Ntubes_preh_chosen[j] = Ntubes[idx_min]
    else:
        dp_preh_min = 0
    if np.size(Atot_evap[Atot_evap[:,j] > 0, j]) > 0:
        min_loc = np.where(Atot_evap[:,j] == np.min(Atot_evap[np.nonzero(Atot_evap[:,j]),j]))
        idx_min = min_loc[0][0]
        dp_evap_min = dp_evap[idx_min,j]
        hx_area_evap[j] = Atot_evap[idx_min,j]
        hx_evap_costs[j], n_hx_evap[j] = cfc.c_heat_exchangers(4, hx_area_evap[j], 'AISI 304')
        htc_salt_eva_chosen[j] = htc_salt_preheat[idx_min, j]
        htc_steam_chosen[j] = htc_steam[idx_min, j]
        Utot_eva_chosen[j] = Utot_evap[idx_min, j]
        Ntubes_evap_chosen[j] = Ntubes[idx_min]
    else:
        dp_evap_min = 0

    dp_hx = (dp_preh_min + dp_evap_min) / 1e5
    pump_costs[j] = cfc.c_pumps(vflow_salt[j], dp_hx, 'cast iron')#, 'horizontal', param_moltensalt['Unit conversion'])


plt.close('all')
pol_coeff_preh = np.polyfit(load, hx_area_preheat, 1)
pol_preheat = pol_coeff_preh[0]*load + pol_coeff_preh[1]

fig = plt.figure()
plt.plot(load, hx_area_preheat)
plt.plot(load, pol_preheat)
plt.xlabel('Load [MW]')
plt.ylabel('HX area')
plt.title('HX costs')
plt.legend(['data','fit'])
plt.show()



fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
X,Y = np.meshgrid(Ntubes,load)
ax.scatter(X, Y, Atot_preheat)
ax.set_xlabel('Ntubes')
ax.set_ylabel('Load [MW]')
ax.set_zlabel('HX area [m$^2$]')
plt.title('Atot_preh')


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(X,Y, Atot_evap)
ax.set_xlabel('Load [MW]')
ax.set_zlabel('HX area [m$^2$]')
plt.show()
plt.title('Atot_evap')

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
X,Y = np.meshgrid(Ntubes,vflow_salt)
ax.scatter(X, Y, Utot_preheat)
ax.set_xlabel('Ntubes')
ax.set_ylabel('Salt V-flow')
ax.set_zlabel('Utot [W/(m$^2$K)]')
plt.title('Utot_preh')


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(X,Y, Utot_evap)
ax.set_xlabel('Ntubes')
ax.set_ylabel('Salt V-flow')
ax.set_zlabel('Utot [W/(m$^2$K)]')
plt.show()
plt.title('Utot_evap')

fig = plt.figure()
plt.plot(load, hx_evap_costs+hx_preheat_costs)
plt.xlabel('Load [MW]')
plt.ylabel('Costs')
plt.title('HX costs')




fig = plt.figure()
plt.plot(load, pump_costs)
plt.xlabel('Load [MW]')
plt.title('Pump costs')
plt.show()




#Ltot_evap = np.sum(Lx_steam)*Ntubes



plt.figure()
plt.plot(h_total/1000, T_salt)
plt.plot(h_total/1000, T_water)
plt.plot(h_total[pinch_idx]/1000, Ts_pinch,'ro')
plt.plot(h_total[pinch_idx]/1000, Tw_pinch,'bo')
plt.xlabel('Enthalpy [kJ/kg]')
plt.ylabel('Temperature[$^o$C]')
plt.legend(['T_salt', 'Twater','T_salt,pinch', 'Twater,pinch'])
plt.show()

# plt.figure()
# plt.plot(h_steam[1:res-1]/1000, htc_steam[1:res-1]/1000)
# plt.plot(h_preheat[0:res-1]/1000, htc_water[0:res-1]/1000)
# plt.plot(h_preheat/1000, htc_salt_preheat*np.ones(res)/1000)
# plt.legend(['htc_steam', 'htc_water', 'htc_salt_preheat'])
# plt.xlabel('Enthalpy [kJ/kg]')
# plt.ylabel('Heat transfer coefficient [kW/(m$^2$K)]')
# plt.show()

# plt.figure()
# plt.plot(h_preheat/1000, UAtot_preheat/Atot_preheat)
# plt.plot(h_steam/1000, UAtot_evap/Atot_evap)
# plt.title('U tot')
# plt.legend(['Utot_preheat', 'Utot_evap'])
# plt.xlabel('Enthalpy [kJ/kg]')
# plt.ylabel('U-value [kW/(K*m^2)]')
# plt.show()



# Drange = np.linspace(0.2,2,50)
# htc_salt_drange = np.zeros(50)
# for i,d in enumerate(Drange):
#     htc_salt_drange[i] = np.max(calcHTCsalt(d, d_i + 2 * thick, load, (Ts_pinch + Ts_max) / 2), Ntubes)

# plt.figure()
# plt.plot(Drange, htc_salt_drange)
# plt.title('Salt htc as a function of shell diameter')
# plt.xlabel('Shell diameter [m]')
# plt.ylabel('Htc salt [W/(K*m^2)]')
#plt.show()




