# -*- coding: utf-8 -*-
"""
Created on Mon Dec  5 13:35:25 2022

@author: PaeffgenE
"""

import pandas as pd
import plotly.express as px
import json
import plotly.graph_objs as go
import plotly.io as pio
import numpy as np
pio.renderers.default='browser'

r=open('results_0.json')
jsondata=json.load(r)



#List of all values supply gas
units = ['pv1','supply_gas','supply_h2','supply_biomass', 'supply_biogas', 
          'supply_el_buy', 'supply_waste_heat_1','demand_steam_2', 'demand_el',
          'demand_gas', 'geo1', 'sales_ele_grid']

#List of timeline
timeline =['one','two']

#List of 
sequences=['s','q','p','d']

sum_values=0


df_seq = pd.DataFrame()

for unit in units:
    sum_values=0  
    seq = jsondata['units'][unit]['var']['seq']
    for sequence in sequences:
        if sequence in seq.keys():
            for tl in timeline:
                sum_values += sum(seq[sequence][tl]['values'])
            dict = {sequence : sum_values}
            df_temp = pd.DataFrame(dict,index=[unit])
            df_seq = pd.concat([df_seq, df_temp])


print(df_seq)


# fig = px.bar(df_seq, y=df_seq.index ,
#               x=['s','q','p'], 
#               title = 'purchase, consumption, sales and local production',
#               labels ={'index':'units', 'value':'MWh', 'variable':'MWh'},
#               barmode='stack', orientation='h'
    
#               )
# fig.show()

fig = go.Figure()
fig.add_trace(go.Bar(
    y=['consumption'],
    x=[ df_seq['q']['demand_steam_2']],
    name='demand steam',
    orientation='h',
    # marker=dict(
    #     color='rgba(112, 0, 0, 0.62)',
    #     line=dict(color='rgba(112, 0, 0, 0.62)', width=3)
#    )
))
fig.add_trace(go.Bar(
    y=['consumption'],
    x=[df_seq['d']['demand_el'] ],
    name='demand ele',
    orientation='h',
    # marker=dict(
    #     color='rgba(112, 89, 0, 0.62)',
    #     line=dict(color='rgba(112, 89, 0, 0.62)', width=3)
    # )
))
fig.add_trace(go.Bar(
    y=[ 'consumption'],
    x=[df_seq['d']['demand_gas']],
    name='demand gas',
    orientation='h',
    # marker=dict(
    #     color='rgba(0, 112, 2, 0.62)',
    #     line=dict(color='rgba(0, 112, 2, 0.62)', width=3)
    #)
))
fig.add_trace(go.Bar(
    y=[ 'purchase'],
    x=[df_seq['s']['supply_el_buy']],
    name='supply ele',
    orientation='h',
))
fig.add_trace(go.Bar(
    y=[ 'purchase'],
    x=[df_seq['s']['supply_gas']],
    name='supply gas',
    orientation='h',
))
fig.add_trace(go.Bar(
    y=[ 'purchase'],
    x=[df_seq['q']['supply_waste_heat_1']],
    name='supply waste heat',
    orientation='h',
))
fig.add_trace(go.Bar(
    y=[ 'sales'],
    x=[df_seq['s']['sales_ele_grid']],
    name='sales ele grid',
    orientation='h',
))
fig.add_trace(go.Bar(
    y=[ 'local production'],
    x=[df_seq['p']['pv1']],
    name='pv1',
    orientation='h',
))
fig.add_trace(go.Bar(
    y=[ 'local production'],
    x=[df_seq['q']['geo1']],
    name='geo1',
    orientation='h',
))


fig.update_layout(barmode='stack' ,legend_title='Units',
                  title='Total consumption, purchase, sales and local production',
                  xaxis_title='MW',
                  yaxis_title='Total')


fig.show()