
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import CoolProp.CoolProp as cp
import operator
from scipy import constants
from mpl_toolkits.mplot3d import Axes3D

res = 20


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
        if idx < res-1:
            t_f = (t_w[idx] + t_w[idx+1]) / 2
            lmtd = ((t_s[idx] - t_w[idx]) - (t_s[idx+1] - t_w[idx+1]))/ np.log(
                (t_s[idx] - t_w[idx]) / (t_s[idx+1] - t_w[idx+1]))
            # Water properties at the present fluid temperature
            rho_w = cp.PropsSI('D', 'T', t_f + 273.15, 'Q', 0, 'Water')
            k_w = cp.PropsSI('conductivity', 'T', t_f + 273.15, 'Q', 0, 'Water')
            visc_dyn = cp.PropsSI('viscosity', 'T', t_f + 273.15, 'Q', 0, 'Water')
            visc_kin = visc_dyn / rho_w
            Pr = cp.PropsSI('Prandtl', 'T', t_f + 273.15, 'Q', 0, 'Water')

            v = mflow/ (rho_w * np.pi * (d_i / 2) ** 2)   # flow velocity m/s
            qflow_x = mflow*cp_w*(t_w[idx+1]-t_w[idx])

            Re_l = d_i * v / visc_kin
            # Gnielinski equation for internal flow, valid over a large range of Reynolds numbers
            # (according to Incropera)
            # HTC for liquid with the Gnielinski equation for internal flow
            if Re_l < 2300:
                Nu_l = 4.36
            elif 2300 <= Re_l < 10e4:
                Nu_l = 0.023 * Re_l ** (4 / 5) * Pr ** 0.4
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
    return np.average(htc_water), Ltube, Atot

def calcHTCevap(d_i, thick, Ntubes, load, p, h_in, h_out, tsalt_in, tsalt_out, htc_salt):
    # Calculates the heat transfer coefficient for the evaporator, considering the heat transfer coefficients for
    # boiling water and salt flowing across a tube bundle.
    # The htc for water boiling in a tube is calculated using the Gungor & Winterton correlation
    # Outputs:
    # htc_steam - Heat transfer coefficient for steam as a function of steam enthalpy
    # ua_tot - total UA-value for the heat exchanger as a function of steam enthalpy
    # Ltot - the required length of the HX

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

    return np.average(htc_steam), Ltube, Atot

def calcHTCsalt(D, d_o, mflow, Tave, Ntubes):
    # Calculates heat transfer coefficient for salt for flow across a tube bundle with correlations from VDI heat atlas.
    # The properties are calculated at the average fluid temperature, but the result is not very sensitive to temperature
    # It is assumed that the tubes have a staggered configuration, arranged as equilateral triangles with
    #           S = 1.25*d_o,
    # where S = triangle side length and d_o is the outer diameter of the tubes in the tube bundle
    # The HTC is calculated for a range of baffle spacings, and out of these the maximum HTC is returned

    # Allowed range of baffle spacings based on Design and Rating of Shell and Tube Heat Exchangers by John E. Edwards
    B = np.linspace(D/5, 75*d_o**0.75 , res) #
    cp_ave = -0.8611 * Tave + 1922.8
    rho_ave = -0.0018 * Tave ** 2 + 0.1438 * Tave + 2254.7
    viscosity_dyn = 42.686*Tave**(-1.729)
    viscosity_kin = viscosity_dyn/rho_ave
    k_s = 0.5 # Thermal conductivity of salt, estimated based on conductivities of other solar salts, may be wrong.
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

    return np.max(htc_salt), dp




