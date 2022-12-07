# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 10:29:33 2022

@author: PaeffgenE
"""
import pandas as pd
import plotly.express as px
import json
import plotly.graph_objs as go
import plotly.io as pio
from dash import Dash, html , dcc, Output, Input

pio.renderers.default='browser'

r=open('results_0.json')
jsondata=json.load(r)



#List of units with relevant costs
units = {'gb1':'Gasboiler 1','gb2':'Gasboiler 2','gb3':'Gasboiler 3',
         'eb1':'Elektroboiler 1','st1':'Steamturbine 1',
         'supply_gas':'Purchase Gas','supply_h2':'Purchase Hydrogen',
         'supply_biomass':'Purchase Biomass', 'supply_biogas':'Purchase Biogas',
         'bmb1':'Bmb 1', 'hthp1':'Heat Pump', 'ssml1':'Ssml 1', 'ees1':'Ees 1',
         'pv1':'Photovoltaic 1', 'gt1':'Gasturbine 1',
         'supply_el_buy':'Purchase Electiricty'}


df_obj = pd.DataFrame()
for unit in units:
    obj = jsondata['units'][unit]['obj']
    df_temp = pd.DataFrame(obj,index=[unit])
    df_obj = pd.concat([df_obj, df_temp])
    df_obj = df_obj.rename(index = {unit : units[unit]})

df_obj = df_obj.rename({"opex_fix":"Operational Costs",
                        "inv":"Investment costs",
                        "cost_SU":"Cost for start of unit",
                        "cost_SD":"Costs for shut down of unit",
                        "energy":"Energy costs"}, axis='columns')


print(df_obj)

fig = px.bar(df_obj, x=df_obj.index,
              y=df_obj.columns, 
              title = 'costs per unit',
              labels ={'index':'units', 'value':'costs in EUR',
                        'variable':'costs'}
              )
fig.show()

