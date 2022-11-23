#def calc_coeffs_Moltensalt(param_moltensalt, param_general, settings):

import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

#######################################################################################
# Description:
#
# This script is used to obtain a quadratic cost-function for a Ruths steam storage system
#
# Using given inputs, the geometry of the storage vessel and the corresponding capacities are calculated.
#
# A lot of data points (capacity/costs) are obtained which are then scaled to a capacity of 1 kWh
#
# Using this selection, new data points are extrapolated to cover the required domain for capacity and heat loads
#
# For these data-points a least-squares-regression is carried out to obtain a (nonconvex) quadratic cost-function
from numpy.core._multiarray_umath import ndarray

param_moltensalt = {
    'Type': 'Molten Salt - Yara MOST',
    'Tfreeze': 135,  # Celsius
    'cp': 2100,  # J/kg*K
    'rho_salt': 2137,  # kg/m3
    'c_salt': 0.8,  # €/kg - actually cost is in the range 0.7-1.5, depending on the volume
    'c_carbonsteel': 0.6,  # €/kg
    'charging': 1,
    'discharging': 1,
    'cost coefficients': []  # costs = c[0] + X*c[1] + Y*c[2] + X**2*c[3] + Y**2*c[4] + X*Y*c[5]
}

res = 40

max_capacity = 100 *10**3 # kWh
max_load = max_capacity*2 # kW
capacity_range = np.linspace(1000, max_capacity, res)
load_range = np.linspace(1000, max_load, res)
rho_carbonsteel = 7870

### INPUT
container_thickness = 0.01

## CONVERSION FACTORS
m3ps_2_Gpm = 15850.32
watt_2_Hp = 1341.022
dollar_2_eur = 0.90
m_2_feet = 3.2808399

T_min = 150  # param_general['temperature limits']['T_min']
T_max = 200  # param_general['temperature limits']['T_max']
# if T_min < param_moltensalt['Tfreeze'] + 10:
#     print('The system minimum temperature is too low considering the freezing point of the salt')
#     return


Msalt = capacity_range*3600*1000 / (
            param_moltensalt['cp'] * (T_max - T_min));  # Maximum total salt mass, to cover the entire capacity
# Corresponding maximum tank volume PER TANK (one hot, one cold)
Vtank = Msalt / param_moltensalt['rho_salt'] / 2
container_h = (4 * Vtank / np.pi) ** (1. / 3)  # assume equal aspect ratio: diameter = height
container_surface = container_h ** 2 * np.pi + (container_h / 2) ** 2 * np.pi * 2
container_mass = container_surface * container_thickness * rho_carbonsteel
print('Salt max mass = ', max(Msalt) / 1000, ' tonn')
print('Max tank volume  = ', max(Vtank), ' m3')
print('Max tank height  = ', max(container_h), ' m')
print('Container max mass = ', max(container_mass) / 1000, ' tonn')

######### STORAGE TANK COSTS
# The container surface and thus the costs are not linearly dependent on the volume. Thus it is more correct to
# calculate the surface areas and resulting costs from an array of linearly spaced volumes within [0,Vmax]
# The cost of salt should actually be piecewise linear - lower price above certain weight/volume
costs_salt = Msalt * param_moltensalt['c_salt']
# Container costs: multiplied by two to account for hot and cold tanks
costs_container = 2 * container_mass * param_moltensalt['c_carbonsteel']
costs_tank_tot = costs_container + costs_salt



r2 = 1

######## ELECTRIC MOTOR COSTS
eff_motor = 0.9  # assuming constant electric motor efficiency
mflow_salt = load_range*1000 / (param_moltensalt['cp'] * (T_max - T_min))  # in kg/s
Vflow_salt = mflow_salt / param_moltensalt['rho_salt']
Vflow_salt_Gpm = Vflow_salt * m3ps_2_Gpm
eff_pump = -0.316 + 0.24015 * np.log(Vflow_salt_Gpm) - 0.01199 * (
            np.log(Vflow_salt_Gpm) ** 2)  # Equation for pump efficiency from Seider et al.
Pm = load_range / (eff_motor * eff_pump)  # Motor power consumption in MW
costs_motor = dollar_2_eur * (
            np.exp(5.9332 + 0.16829 * np.log(Pm * watt_2_Hp)) - 0.110056 * (np.log(Pm * watt_2_Hp)) ** 2 + 0.071413 * (
        np.log(Pm * watt_2_Hp)) ** 3 - 0.0063788 * (np.log(Pm * watt_2_Hp)) ** 4)




######## PUMP COSTS
S = np.zeros((res, res))
C_pump = np.zeros((res, res))
for i in range(0, res,1):
    for j in range(0, res, 1):
        S[i, j] = ((container_h[i] * m_2_feet) ** 0.5) * Vflow_salt_Gpm[j]
        C_pump[i, j] = np.exp(12.1656 - 1.1448 * np.log(S[i, j]) + 0.0862 * (np.log(S[i, j])) ** 2) * dollar_2_eur



fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
CAP, HL = np.meshgrid(capacity_range, load_range)
ax.scatter(CAP/1000, HL/1000, C_pump/1000) #
ax.set_ylabel('Heat load [MW]')
ax.set_xlabel('Storage capacity [MWh]')
ax.set_zlabel('Pump costs [k€]')
plt.title('Pump costs')



## TOTAL COSTS
# Creating a matrix for tank and motor costs
# Tank: Constant along HL; Motor: Constant along CAP
C_tank = np.reshape(np.repeat(costs_tank_tot, res, axis=0),(res,res)).transpose()
C_motor = np.reshape(np.repeat(costs_motor, res, axis=0),(res,res))

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(CAP/1000, HL/1000, C_tank/1000)
ax.set_ylabel('Heat load [MW]')
ax.set_xlabel('Storage capacity [MWh]')
ax.set_zlabel('Total costs [k€]')
plt.title('Tank costs')

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(CAP/1000, HL/1000, C_motor/1000)
ax.set_ylabel('Heat load [MW]')
ax.set_xlabel('Storage capacity [MWh]')
ax.set_zlabel('Total costs [k€]')
plt.title('Electric motor costs')


CTOT = C_tank + C_motor + C_pump

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(CAP, HL, CTOT/1000)
ax.set_ylabel('Heat load [MW]')
ax.set_xlabel('Storage capacity [MWh]')
ax.set_zlabel('Total costs [k€]')
plt.title('Total costs')


# Calculate least-squares regression to obtain coeffs for the quadratic cost function
X = np.reshape(CAP, res*res)    # capacity_range /10**6 / (3600) #/ (10**3)    # In kWh
Y = np.reshape(HL, res*res)    #load_range / 10**6  #/ 10**3      # In MW!!!!

optimization_type = 'linear'

if optimization_type == 'quadratic':
    A = np.array([X * 0 + 1, X, Y, X ** 2, Y ** 2, X * Y]).T
elif optimization_type == 'linear':
    A = np.array([X * 0 + 1, X, Y]).T

B = np.reshape(CTOT, res*res)

coeff, r, rank, s = np.linalg.lstsq(A, B, rcond=-1)

print(coeff.tolist())


def poly2Dreco(X, Y, c):
    if optimization_type == 'quadratic':
        return (c[0] + X * c[1] + Y * c[2] + X ** 2 * c[3] + Y ** 2 * c[4] + X * Y * c[5])
    elif optimization_type == 'linear':
        return (c[0] + X * c[1] + Y * c[2])



fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(CAP, HL, poly2Dreco(CAP, HL, coeff))

r2 = 1 #compute_r2_score(poly2Dreco(X, Y, coeff), specific_costs_extended)
plt.show()

print('Minimal specific costs (€/kWh): ' + str(round(CTOT.min().min() / max_capacity, 2)))
print('Minimal specific costs (€/kW): ' + str(round(CTOT.min().min() / max_load, 2)))

#return coeff.tolist(), r2


