from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from flask import Flask
import pandas as pd
import dash
import delfort_main
import json
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np




server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=[dbc.themes.FLATLY], url_base_pathname='/dash-server/')
app.title = 'Dashboard'

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')

r=open('results_1.json')
jsondata=json.load(r)



app.layout = html.Div([
#dbc.Container([


    dbc.Row(dbc.Col(html.H2("Simulation Results"), width={'size': 12, 'offset': 0, 'order': 0}), style = {'textAlign': 'center', 'paddingBottom': '1%'}),
    dbc.Row(dbc.Col(children=[
        html.H4("Description:"),
        html.P("Result found in 5.3 seconds.")
    ])),
    dbc.Row(
        dbc.Col(
            dcc.Loading(children=
            [
                html.H4("Costs per Unit:"),
                dcc.Graph(id ='your-graph'),
                html.H4("Total consumption, purchase, sales and local production:"),
                dcc.Graph(id ='your-graph2'),
                html.H4("Production units:"),
                dcc.Graph(id ='your-graph3')
            ], color = '#000000', type = 'dot', fullscreen=True 
            )
        )
    ),
    dbc.Row(html.P(id="test"))
])
# ,style={'overflow': 'hidden'})

@app.callback(
    Output('your-graph', 'figure'),
    Output('your-graph2', 'figure'),
    Output('your-graph3', 'figure'),
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


    fig = drawCostPlot()
    fig2 = drawPurchasePlot()
    fig3 = drawLinePlot()
    return fig, fig2, fig3

if __name__=='__main__':
    app.run_server(debug=True)

def drawCostPlot():
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
                labels ={'index':'units', 'value':'costs in tEUR',
                            'variable':'costs'}
                )
    return fig

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

    print(df_seq)


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

def drawLinePlot():
    #List of units with relevant production
    units = {'gb1':'Gasboiler 1','gb2':'Gasboiler 2','gb3':'Gasboiler 3',
            'eb1':'Elektroboiler 1','st1':'Steamturbine 1',
            'supply_gas':'Purchase gas','supply_h2':'Purchase hydrogen',
            'supply_biogas':'Purchase biogas',
            'bmb1':'Biomass boiler 1', 'hthp1':'Heat pump 1',
            'ssml1':'Thermal storage 1', 'ees1':'Electric energy storage 1',
            'pv1':'Photovoltaic 1', 'gt1':'Gasturbine 1',
            'supply_el_buy':'Purchase electiricty'}

    #List of timeline
    timeline =['one','two']

    #List of 
    sequences=['q','s','p']

    #List of colors
    colors = [
        '#f44336',  
        '#9c27b0',  
        '#3f51b5',  
        '#2196f3',  
        '#00bcd4', 
        '#009688',  
        '#4caf50',   
        '#8bc34a',
        '#cddc39',
        '#ffc107',
        '#ff5722',
        '#795548',
        '#9e9e9e',
        'black'
        ]

    #List of symbols
    symbols= [
        "circle", "square", "triangle-up", "diamond", "diamond-wide",
        "circle", "square", "triangle-up", "diamond", "diamond-wide",
        "circle", "square", "triangle-up", "diamond", "diamond-wide"
        ]

    data = {}
    for tl in timeline:
        df_seq = pd.DataFrame()
        for unit in units.keys():
            seq = jsondata['units'][unit]['var']['seq']
            for sequence in sequences:
                if sequence in seq.keys():
                    dict_data = jsondata['units'][unit]['var']['seq'][sequence][tl]
                    df_temp = pd.DataFrame(
                        dict_data['values'],
                        index=[str(time)+':00' for time in dict_data['timesteps']],
                        columns=[unit])
                    df_seq = pd.concat([df_seq, df_temp], axis=1,)
                    df_seq = df_seq.rename(columns = {unit : units[unit]})
        data[tl] = df_seq

    print(data)

    fig = make_subplots(rows=1, cols=len(timeline),
                    shared_xaxes=True,
                    vertical_spacing=0.02,
                    subplot_titles=['Day 1', 'Day 2'])


    i=1
    for tl in timeline:
        ii = 0
        for col in data['one'].columns:
            if tl == 'one':
                plot_legend = True
            else:
                plot_legend = False
            fig.add_trace(
                go.Scatter(
                    x=data[tl][col].index,
                    y=data[tl][col].values, 
                    name=col,
                    showlegend=plot_legend,
                    line={'shape': 'hvh', 'color': colors[ii]},
                    marker={'size': 8, 'symbol': symbols[ii]}
                    ),
                    
                    row=1, col=i)

            ii+=1
        i+=1
    fig.update_layout(height=600,
                xaxis_title='Time in h',
                yaxis_title='kWh')

    fig.update_xaxes(title_text="Time in h", row=1, col=2)
    return fig