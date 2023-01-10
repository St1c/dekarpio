from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
import plotly.express as px
from flask import Flask
from flask import request, jsonify
import pandas as pd
import dash
import delfort_main
import json
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np
import plotly.colors as pclr
from def_names import units, costs, heat_types, capexopex





server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=[dbc.themes.FLATLY], url_base_pathname='/dash-server/')
app.title = 'Dashboard'

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')

r=open('output_1.json')
jsondata=json.load(r)

app.layout = html.Div([
#dbc.Container([


    dbc.Row(dbc.Col(html.H2("Simulation Results"), width={'size': 12, 'offset': 0, 'order': 0}), style = {'textAlign': 'center', 'paddingBottom': '1%'}),
    dbc.Row(dbc.Col(children=[
        html.H4("Description:"),
        html.P("Result found in 5.3 seconds.")
    ])),
    dbc.Card([
            dbc.Tabs(
            [
                dbc.Tab(children=[
                    dbc.CardBody(children=[
                        dbc.Row(
                            dbc.Col(id="ColDataTable",width=12
                            )
                        ),
                        dbc.Row(children=[
                            dbc.Col(children=[
                                html.H4("Costs per Unit:"),
                                dcc.Graph(id ='FigCostUnit'),
                            ],width=4),
                            dbc.Col(children=[
                                html.H4("Costs of Energy Sources:"),
                                dcc.Graph(id ='FigCostEso'),
                            ],width=4),
                            dbc.Col(children=[
                                html.H4("Production units:"),
                                dcc.Graph(id ='your-graph3')
                            ],width=4)
                        ]),
                    ]),
                    
                ], label="Tab 1", tab_id="tab-1"),

                dbc.Tab(children=[
                    dbc.CardBody(children=[
                        dbc.Row(children=[
                            dbc.Col(children=[
                                dcc.Graph(id="LinePlotPower")
                            ],width=12),
                        ]),
                    ]),
                    
                ], label="Tab 2", tab_id="tab-2"),
                
                dbc.Tab(children=[
                    dbc.CardBody(children=[
                        dbc.Row(children=[
                            dbc.Col(children=[
                                dcc.Graph(id="LinePlotHeat")
                            ],width=12),
                        ]),
                    ]),
                ], label="Tab 3", tab_id="tab-3"),

                dbc.Tab(children=[
                    dbc.CardBody(children=[
                        dbc.Row(children=[
                            dbc.Col(children=[
                                dcc.Graph(id="Bilanz-1")
                            ],width=12),
                            dbc.Col(children=[
                                dcc.Graph(id="Bilanz-2")
                            ],width=12),
                            dbc.Col(children=[
                                dcc.Graph(id="Bilanz-3")
                            ],width=12),
                            dbc.Col(children=[
                                dcc.Graph(id="Bilanz-4")
                            ],width=12),
                        ]),
                    ]),
                ], label="Tab 4", tab_id="tab-4"),

                dbc.Tab(children=[
                    dbc.CardBody(children=[
                        dbc.Row(children=[
                            dbc.Col(children=[
                                dcc.Graph(id="PurchaseConsumptionPlot")
                            ],width=12),
                        ]),
                    ]),
                ], label="Tab 5", tab_id="tab-5"),


                dbc.Tab(children=[
                    dbc.CardBody(children=[
                        dbc.Row(children=[
                            dbc.Col(children=[
                                dcc.Graph(id="SunBurst1")
                            ],width=4),
                            dbc.Col(children=[
                                dcc.Graph(id="SunBurst2")
                            ],width=4),
                            dbc.Col(children=[
                                dcc.Graph(id="SunBurst3")
                            ],width=4),
                        ]),
                    ]),
                    dbc.CardBody(children=[
                        dbc.Row(children=[
                            dbc.Col(id="CostTable",width=12)
                        ]),
                    ]),
                ], label="Tab 6", tab_id="tab-6"),

            ],id="card-tabs",active_tab="tab-1")
    ]
    ),
    dbc.Row([html.P(id="test"),
        html.Form([
            dcc.Input(name='name'),
            html.Button('Submit', type='submit')
        ], action='/validate', method='post')
    ])
])
# ,style={'overflow': 'hidden'}

@app.server.route('/validate', methods=['GET', 'POST'])
def validateJson():
    print("Hello")
    print(request.method)
    return "Hello World"
    #return jsonify({'id': 'no errors'})


@app.callback(
    Output('FigCostUnit', 'figure'),
    Output('FigCostEso', 'figure'),
    Output('your-graph3', 'figure'),
    Output('LinePlotPower', 'figure'),
    Output('LinePlotHeat', 'figure'),
    Output('Bilanz-1', 'figure'),
    Output('Bilanz-2', 'figure'),
    Output('Bilanz-3', 'figure'),
    Output('Bilanz-4', 'figure'),
    Output('PurchaseConsumptionPlot', 'figure'),
    Output('ColDataTable', 'children'),

    Output('SunBurst1', 'figure'),
    Output('SunBurst2', 'figure'),
    Output('SunBurst3', 'figure'),
    Output('CostTable', 'children'),
    Input('test', 'value'))
def update_figure(selected_year):
    # filtered_df = df[df.year == selected_year]

    # fig = px.scatter(filtered_df, x="gdpPercap", y="lifeExp",
    #                 size="pop", color="continent", hover_name="country",
    #                 log_x=True, size_max=55)

    # fig.update_layout(transition_duration=500)

   

    print("start simulation")

    #delfort_main.run_case()
    #result_dict = delfort_main.run_case()

    print("simulation finished")


    figCostUnit, dfCostUnit, sunBurstDf = drawCostPlotUnit()
    figCostEso, dfCostEso = drawCostPlotEso()
    fig3 = drawCostPlotEcuEsu()
    fig4 = drawLinePlotPower()
    fig5 = drawLinePlotHeat()

    ar = drawBilanzPlots()

    print(dfCostEso)

    figSunBurstType = px.sunburst(sunBurstDf, path=['Capex/Opex', 'Cost Type'], values='Costs')
    figSunBurstUnit = px.sunburst(sunBurstDf, path=['Capex/Opex', 'Unit'], values='Costs')
    figSunBurstUnitCosts = px.sunburst(sunBurstDf, path=['Unit', 'Cost Type'], values='Costs')


    table = dbc.Table.from_dataframe(dfCostEso, striped=True, bordered=True, hover=True, index=True)



    dashTable = dash.dash_table.DataTable(sunBurstDf.to_dict('records'), [{"name": i, "id": i} for i in sunBurstDf.columns],export_format="csv")

    


    return figCostUnit, figCostEso, fig3, fig4, fig5, ar[0], ar[1], ar[2], ar[3], drawPurchaseConsumptionPlot(), table, figSunBurstType, figSunBurstUnit, figSunBurstUnitCosts, dashTable

if __name__=='__main__':
    app.run_server(debug=True)
##########################################################################
# Cost Plot Functions
##########################################################################
def drawCostPlotUnit():
    '''
    Cost Plot working, why no pie chart?
    '''
    idUnit = "Unit"
    idCAPOP = "Capex/Opex"
    idCostType = "Cost Type"
    idCosts = "Costs"
    dictfordf = {
        idUnit:[],
        idCAPOP:[],
        idCostType:[],
        idCosts:[]
    }

    sum_inv=0
    for unit in units:
        if unit in jsondata['units']:
            obj = jsondata['units'][unit]['obj']  

            if (('inv_fix' in obj.keys()) == True):
                sum_inv += obj['inv_fix']
            if (('inv_power' in obj.keys()) == True):
                sum_inv += obj['inv_power']
            if (('inv_energy' in obj.keys()) == True):
                sum_inv += obj['inv_energy']
            if (('inv_cap' in obj.keys()) == True):
                sum_inv += obj['inv_cap']
            if (('invest_cap' in obj.keys()) == True):
                sum_inv += obj['invest_cap']

            for key, val in obj.items():
                if key not in capexopex.keys(): continue
                dictfordf[idUnit].append(units[unit])
                dictfordf[idCAPOP].append(capexopex[key])
                dictfordf[idCostType].append(costs[key])
                dictfordf[idCosts].append(val)



    #get DF with summed up opex costs
    #first unit operation costs : opex fix
    sum_fix=0
    for unit in units:
        if unit in jsondata['units']:

            # dictfordf[idUnit].append(units[unit])
            # dictfordf[idCAPOP].append("OPEX")
            # dictfordf[idCostType].append("Operation Costs")

            obj = jsondata['units'][unit]['obj']  
            if (('opex_fix' in obj.keys()) == True):
                sum_fix += obj['opex_fix']

            # dictfordf[idCosts].append(sum_fix)

            
    #start costs :opex_start
    sum_start=0
    for unit in units:
        if unit in jsondata['units']:

            # dictfordf[idUnit].append(units[unit])
            # dictfordf[idCAPOP].append("OPEX")
            # dictfordf[idCostType].append("Start Costs")

            obj = jsondata['units'][unit]['obj']  
            if (('opex_start' in obj.keys()) == True):
                sum_start += obj['opex_start']
            
            # dictfordf[idCosts].append(sum_start)

    
    #maintenance costs :opex_main
    sum_main=0
    for unit in units:
        if unit in jsondata['units']:

            # dictfordf[idUnit].append(units[unit])
            # dictfordf[idCAPOP].append("OPEX")
            # dictfordf[idCostType].append("Maintenance Costs")

            obj = jsondata['units'][unit]['obj']  
            if (('opex_main' in obj.keys()) == True):
                sum_main += obj['opex_main']
            
            # dictfordf[idCosts].append(sum_main)


    #electricity costs -> nochmal mit sophie besprechen ob aufteilung in brennstoff und electricity gerade gemeinsam
    sum_ele=0
    for unit in units:
        if unit in jsondata['units']:
            obj = jsondata['units'][unit]['obj']  

            # dictfordf[idUnit].append(units[unit])
            # dictfordf[idCAPOP].append("OPEX")
            # dictfordf[idCostType].append("Electricity Costs")

            if (('energy' in obj.keys()) == True):
                sum_ele += obj['energy']
            if (('energy' in obj.keys()) == True and ('grid' in obj.keys()) == True):
                sum_ele += obj['grid']
            
            # dictfordf[idCosts].append(sum_ele)

    


    df_opex = pd.DataFrame({ 'Start costs': sum_start,
                'Maintenance costs': sum_main,
                'Unit operation costs': sum_fix,
                'Electricity costs': sum_ele},
                index= ['Opex']
                ) 
    df_capex = pd.DataFrame({'Investment costs': sum_inv},
                            index= ['Capex'])

    df_costs = pd.concat([df_opex, df_capex])

    print("dataframe sunburst")

    print(len(dictfordf[idUnit]))
    print(len(dictfordf[idCostType]))
    print(len(dictfordf[idCAPOP]))
    print(len(dictfordf[idCosts]))

    sunburstdf = pd.DataFrame(dictfordf)
    print(sunburstdf)

    fig = px.bar(df_costs,
                title = 'Total costs',
                labels ={'index':'Cost type','value':'costs in EUR/a',
                            'variable':'costs'},
                barmode='relative',
                orientation='h'
                )
    return fig, df_costs, sunburstdf

def drawCostPlotEso():
    '''
    Draw Cost Plots of Eso working
    '''
    df = pd.concat([
                pd.DataFrame(
                    {
                        "Costs in Mio. Eur": jsondata['units'][unit_short]['obj'][cost_short],
                        "Energy Cost Type" : cost_long
                    },
                    index= [unit_long],
            
                )   
                for unit_short, unit_long in units.items()
                if unit_short             in jsondata['units'] #1
                if unit_short.split('_')[0]=='eso'
                for cost_short, cost_long in costs.items()
                for obj                   in jsondata['units'][unit_short]['obj']
                if cost_short             in obj
                #1 raus wenn alle units mit json übergeben werden aktuell nur 4 units
            ])
    
    df.index.set_names("Sources", inplace=True)

    return (
        px.bar(
            df,
            color='Energy Cost Type',
        )
        # .update_layout(margin=dict(t=25, b=0, l=0, r=0))
        # .for_each_xaxis(lambda x: x.update(title=('Energy sources')))
        # .for_each_yaxis(lambda x: x.update(title=('Costs in 10^6 EUR/a')))
    ), df

def drawCostPlotEcuEsu():
    '''
    Draw Cost Plots of Ecu Esu working
    '''
    return (
        px.bar(
            pd.concat([
                pd.DataFrame(
                    dict(
                        values= jsondata['units'][unit_short]['obj'][cost_short],
                        Costs = cost_long
                        
                    ),
                    index= [unit_long],
            
                )   
                for unit_short, unit_long in units.items()
                if unit_short.split('_')[0]=='ecu' or unit_short.split('_')[0]== 'esu' 
                if unit_short             in jsondata['units'] #1
                for cost_short, cost_long in costs.items()
                for obj                   in jsondata['units'][unit_short]['obj']
                if cost_short             in obj
                #1 raus wenn alle units mit json übergeben werden aktuell nur 4 units
               
            ]),
            color='Costs',
        )
        .update_layout(margin=dict(t=25, b=0, l=0, r=0))
        .for_each_xaxis(lambda x: x.update(title=('Energy conversion units and storages')))
        .for_each_yaxis(lambda x: x.update(title=('Costs in 10^6 EUR/a')))
    )

def drawPurchasePlot():
    #List of all relevant units in order as legend
    units ={  'supply_gas':'Purchase gas',
            'supply_h2':'Purchase Hydrogen','supply_el_buy':'Purchase electricity',
            'supply_waste_heat_1':'Supply waste heat 1', 'pv1':'Photovoltaic 1',
            'geo1':'Geothermal energy',
            'demand_steam_2':'Demand steam 2', 'demand_el':'Demand electricity',
            'demand_gas':'Demand gas',
            'sales_ele_grid':'Sales to power grid'}

    #List of timeline
    timeline =['one','two']

    #List of all purchases
    purchase_list = ['Purchase gas', 'Purchase electricity',
                    'Supply waste heat 1']

    #List of all consumptions
    consumption_list = ['Demand electricity','Demand steam 2','Demand gas']

    #List of all sales
    sales_list = ['Sales to power grid']

    #List of local production
    production_list = ['Geothermal energy','Photovoltaic 1']

    #List of sequences
    sequences=['s','q','p','d']

    #Define order of barcharts
    order=('Sales of energy','Consumption of energy in processes and units',
        'Local production of energy','Purchase of energy')

    sum_values=0

    df_seq = pd.DataFrame()

    for unit in units.keys():
        sum_values=0  
        seq = jsondata['units'][unit]['var']['seq']
        for sequence in sequences:
            if sequence in seq.keys():
                for tl in timeline:
                    sum_values += sum(seq[sequence][tl]['values'])
                dict_data = {sequence : sum_values}
                df_temp = pd.DataFrame(dict_data,index=[unit])
                df_seq = pd.concat([df_seq, df_temp])
                df_seq = df_seq.rename(index = {unit : units[unit]})


    fig = go.Figure()

    for i, row in df_seq.iterrows():
        for purchase in purchase_list:
            if purchase == i :
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Purchase of energy'],
                    x=[ df_seq[val][i]],
                    orientation='h',
                    name=purchase
                    ))

        for consumption in consumption_list:
            if consumption == i :
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Consumption of energy in processes and units'],
                    x=[ df_seq[val][i]],
                    orientation='h',
                    name=consumption
                    ))

        for sales in sales_list:
            if sales == i :
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Sales of energy'],
                    x=[ df_seq[val][i]],
                    orientation='h',
                    name=sales
                    ))
                
        for production in production_list:
            if production == i :
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Local production of energy'],
                    x=[ df_seq[val][i]],
                    orientation='h',
                    name=production
                    ))

    fig.update_layout(barmode='stack',legend_title='Units',
                    yaxis= {'title' :'Supply vs. Demand', 'categoryorder': 'array', 
                            'categoryarray' : order},
                    xaxis_title='MWh',
                    legend_traceorder= "normal"
                  )
    return fig

def drawLinePlotPower():
    '''
    Draw LinePlot Power Working 
    '''
    facet_col_wrap = 2
    timelines = ['one', 'two', 'three', 'four', 'five'] # TODO: get from jsondata?

    sym_sequence = ["circle", "square", "triangle-up", "diamond", "diamond-wide"]
    return (
        px.line(
            pd.concat([
                pd.DataFrame(
                    dict(
                        values=seq['p'][timeline]['values'],
                        Unit=unit_long, Timeline=timeline
                    ),
                    index=[f'{timestep:02g}:00' for timestep in seq['p'][timeline]['timesteps']] 
                )
                for timeline              in timelines
                for unit_short, unit_long in units.items()
                if unit_short             in jsondata['units'] #1
                for seq                   in [jsondata['units'][unit_short]['var']['seq']] 
                if 'p' in seq
                #1 raus wenn alle units mit json übergeben werden aktuell nur 4 units
            ]),
            color='Unit', symbol='Unit', markers=True,  facet_col='Timeline', line_shape='hvh',
            facet_col_wrap=facet_col_wrap,  symbol_sequence=sym_sequence
        )
        .update_layout(margin=dict(t=25, b=0, l=0, r=0))
        .for_each_xaxis(lambda x: x.update(title=None, showticklabels=True))
        .for_each_yaxis(lambda x: x.update(title=('MWh' if x.anchor=="x" or x.anchor=="x3"
                                                  or x.anchor=="x5" else None)))
    )

def drawLinePlotHeat():
    '''
    Draw Line Plot Heat Working
    '''
    facet_col_wrap = 2
    timelines = ['one', 'two', 'three', 'four', 'five'] # TODO: get from jsondata?

    symbol_sequence = ["circle", "square", "triangle-up", "diamond", "diamond-wide"]
    return (
        px.line(
            pd.concat([
                pd.DataFrame(
                    dict(
                        values= jsondata['units'][unit_short]['var']['seq'][heat_short][timeline]['values'],
                        Unit=unit_long, Steamlevel = heat_long, Timeline=timeline
                    ),
                    index=[f'{timestep:02g}:00' 
                           for timestep in jsondata['units'][unit_short]['var']['seq']
                           [heat_short][timeline]['timesteps']] 
                )
                for timeline               in timelines
                for unit_short, unit_long  in units.items()
                if unit_short             in jsondata['units'] #1
                for heat_short, heat_long  in heat_types.items()
                for seq                    in [jsondata['units'][unit_short]['var']['seq']]
                if heat_short              in seq
                #1 raus wenn alle units mit json übergeben werden aktuell nur 4 units
                
            ]),
            color='Unit', symbol='Steamlevel', facet_col='Timeline', line_shape='hvh',  
            facet_col_wrap=facet_col_wrap, markers=True, symbol_sequence=symbol_sequence
        )
        .update_layout(margin=dict(t=25, b=0, l=0, r=0))
        .for_each_xaxis(lambda x: x.update(title=None, showticklabels=True))
        .for_each_yaxis(lambda x: x.update(title=('MWh' if x.anchor=='x' or x.anchor=='x3' 
                                                  or x.anchor=='x5' else None)))
    )

def drawBilanzPlots():
    ar = []
    for fig in make_nodes(jsondata):
        ar.append(fig)

    print("BildanzPlots!!!!!!!!!")
    return ar

def make_fig_Bilanz(steam: str, side: str, alt_colors=False):
    facet_col_wrap = 2
    timelines = ['one','two','three','four','five'] # TODO: get from jsondata?
    symbol_sequence = ['circle', 'square', 'triangle-up', 'diamond', 'diamond-wide']
    color_discrete_sequence = pclr.qualitative.Plotly if not alt_colors else pclr.qualitative.Vivid
    return (
        px.area(
            pd.concat([
                pd.DataFrame(
                    dict(
                        values=jsondata['nodes'][steam][side][unit][timeline]['values'],
                        Unit=unit, Timeline=timeline
                    ),
                    index=[f'{timestep}:00' for timestep in jsondata['nodes'][steam][side][unit][timeline]['timesteps']] 
                )
                for timeline in timelines
                for unit     in jsondata['nodes'][steam][side]
            ]),
            color='Unit', facet_col='Timeline', 
            facet_col_wrap=facet_col_wrap, markers=True, symbol_sequence=symbol_sequence,
            color_discrete_sequence=color_discrete_sequence,
            facet_col_spacing=0.04
        )
        .update_layout(margin=dict(t=25, b=0, l=0, r=0))
        .for_each_xaxis(lambda x: x.update(title=None, showticklabels=True))
        .for_each_yaxis(lambda x: x.update(title=('MWh' if x.anchor=="x3" else None)))
    )

def make_pos_neg(jsondata: dict, steam: str) -> go.Figure:
    fig_lhs = make_fig_Bilanz(steam, 'lhs')
    fig_rhs = make_fig_Bilanz(steam, 'rhs', alt_colors=True)
    
    for trc in fig_rhs.data:
        trc.stackgroup = "2"
        trc.y = [-i for i in trc.y] 

    return fig_lhs.add_traces(fig_rhs.data)

def make_nodes(jsondata: dict) -> list[go.Figure]:
    steams = dict(
        col_col2_mis1='Middle pressure steam 1',
        col_col4_mis2='Middle pressure steam 2',
        col_col8_his1='High pressure steam 2',
        col_col9_his2='High pressure steam 2'
    )
    return [make_pos_neg(jsondata, steam) for steam in steams]

def drawPurchaseConsumptionPlot():
    #List of timeline
    timeline =['one','two','three','four','five']

    #List of all purchases (selber anpassen aus Units)
    purchase_list = ['Electricirty PPA PV','Electricity PPA wind',
                    'Purchased district heat','Electricity grid']

    #List of all consumptions (selber anpassen)
    consumption_list = ['Demand process 1', 'Demand process 2','Demand process 3',
                        'Demand process 4','Demand process 5','Demand process 6',
                        ]

    #List of all sales (selber anpassen)
    sales_list = ['District heat','Feed electricity grid']

    #List of local production (selber anpassen)
    production_list = ['Geothermal','Electricity PV','Electricity wind',
                    'Steam extern','Gasturbine 1','Gasturbine 2']

    #List of sequences (selber anpassen)
    sequences=['s','q_lis','q_mis','q_his','p']

    
    '''
    TODO List of Sequences zuordnen mit Sophie
    '''

    #Define order of barcharts
    order=('Sales of energy','Consumption of energy in processes and units',
        'Local production of energy','Purchase of energy')



    df_seq = pd.DataFrame()

    for unit_short, unit_long in units.items():
        sum_values=0  

        if unit_short in jsondata["units"]:
            seq = jsondata['units'][unit_short]['var']['seq']
            print(unit_short)
        else:
            continue
        dict_data = {}

        for sequence in sequences: 
            if sequence in seq.keys():
                for tl in timeline:
                    sum_values += sum(seq[sequence][tl]['values'])
                dict_data[sequence] = sum_values
                #dict_data = {sequence : sum_values}
            #df_temp = pd.DataFrame(dict_data,index=[unit_long])
        df_seq = pd.concat([df_seq, pd.DataFrame(dict_data,index=[unit_long])])

    fig = go.Figure()

    for i, row in df_seq.iterrows():
        for purchase in purchase_list:
            if purchase == i :
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Purchase of energy'],
                    x=[ df_seq[val][i]],
                    orientation='h',
                    name=purchase
                    ))

        for consumption in consumption_list:
            if consumption == i :
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Consumption of energy in processes and units'],
                    x=[ df_seq[val][i]],
                    orientation='h',
                    name=consumption
                    ))

        for sales in sales_list:
            if sales == i :
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Sales of energy'],
                    x=[ df_seq[val][i]],
                    orientation='h',
                    name=sales
                    ))
                
        for production in production_list:
            if production == i :
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Local production of energy'],
                    x=[ df_seq[val][i]],
                    orientation='h',
                    name=production
                    ))

    fig.update_layout(barmode='stack',legend_title='Units',
                    title='Total consumption, purchase, sales and local production',
                    yaxis= {'title' :'Supply vs. Demand', 'categoryorder': 'array', 
                            'categoryarray' : order},
                    xaxis_title='MWh',
                        legend_traceorder= "normal"
                    )
    return fig