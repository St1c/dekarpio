# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 14:14:57 2022

@author: PaeffgenE
"""

import pandas as pd
import plotly.express as px
import json
import plotly.graph_objs as go
import plotly.io as pio
import numpy as np
from plotly.subplots import make_subplots
pio.renderers.default='browser'

r=open('results_0.json')
jsondata=json.load(r)


#List of units with relevant production
units = ['gb1','gb2','gb3','eb1','st1','bmb1', 'hthp1', 'ssml1', 'ees1',
         'pv1', 'gt1', 'hrb1']

#List of timeline
timeline =['one','two']

#List of 
sequences=['q','s','p']

timeshifts = {}
t_end = 0
for tl in timeline:
    timeshifts[tl] = t_end
    t_end = jsondata['units']['gb1']['var']['seq']['q'][tl]['timesteps'][-1]

data = {}
for tl in timeline:
    df_seq = pd.DataFrame()
    for unit in units:
        seq = jsondata['units'][unit]['var']['seq']
        for sequence in sequences:
            if sequence in seq.keys():
                dict_data = jsondata['units'][unit]['var']['seq'][sequence][tl]
                df_temp = pd.DataFrame(
                    dict_data['values'],
                    index=dict_data['timesteps'],
                    columns=[unit+'_'+sequence])
                df_seq = pd.concat([df_seq, df_temp], axis=1)
    data[tl] = df_seq

print(data)

fig = make_subplots(rows=len(timeline), cols=1,
                shared_xaxes=True,
                vertical_spacing=0.02)
i=1
for tl in timeline:
    for col in data['one'].columns:
        fig.add_trace(
            go.Scatter(
                x=data[tl][col].index,
                y=data[tl][col].values, 
                name=col),
                  row=i, col=1)
    i+=1
fig.update_layout(height=600, width=600,
              title_text="Heat Production units",  xaxis_title='Time in h',
              yaxis_title='KWh')
fig.show()








                  