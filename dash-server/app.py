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



server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=[dbc.themes.FLATLY], url_base_pathname='/dash-server/')
app.title = 'Dashboard'

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')

r=open('results_0.json')
jsondata=json.load(r)



app.layout = html.Div([
#dbc.Container([


    dbc.Row(dbc.Col(html.H2("Simulation Results"), width={'size': 12, 'offset': 0, 'order': 0}), style = {'textAlign': 'center', 'paddingBottom': '1%'}),
    dbc.Row(
        dbc.Col(
            dcc.Loading(children=
            [
                dcc.Graph(id ='your-graph'),
                dcc.Graph(id ='your-graph2'),
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
                title = 'Costs per Unit',
                labels ={'index':'units', 'value':'costs in EUR',
                            'variable':'costs'}
                )
    return fig

def drawPurchasePlot():

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
    return fig

def drawLinePlot():
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
    return fig