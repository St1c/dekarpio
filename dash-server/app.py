from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
import plotly.express as px
import plotly.express as px
from flask import Flask
from flask import request, jsonify
import pandas as pd
import dash
import json
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np
import plotly.colors as pclr
import requests
from urllib.parse import parse_qs

## Diskcache
import diskcache
from dash.long_callback import DiskcacheLongCallbackManager
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)


from def_names import fuelsources, elsources, units_unit, units, costs, heat_types, capexopex, couplers
import auxiliary as da
import json_auxiliary as ja
import os



server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=[dbc.themes.FLATLY], url_base_pathname='/dash-server/', long_callback_manager=long_callback_manager)
app.title = 'Dashboard'

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')

# r=open('output_1.json')
# jsondata=json.load(r)

app.layout = html.Div([
#dbc.Container([


    dbc.Row(dbc.Col(html.H2("DekarPIO Simulation Tool"), width={'size': 12, 'offset': 0, 'order': 0}), style = {'textAlign': 'center', 'paddingBottom': '1%'}),
    dbc.Row(dbc.Col(children=[
        dcc.Location(id="url"),
        dcc.Store(id='simulationSetupStorage'),
        dcc.Store(id='timelineListStorage'),
        dcc.Store(id='simulationResultStorage'),
        html.H4("Description:", id="htmlTest"),
        html.P("", id="simulationInformation"),
        html.Progress(id="progress_bar", style= {'width': '99%', 'height': '25%'}),
    ])),
    dcc.Loading(id="loadingResults", type="dot", children=[
    dbc.Card(id="resultCard",children=[
            dbc.Tabs(
            [
                dbc.Tab(children=[
                    dbc.CardBody(children=[
                        dbc.Row(children=[
                            dbc.Col(children=[
                                html.H4("CAPEX vs. OPEX:"),
                                dcc.Graph(id ='FigCostUnit'),
                                # html.A(
                                #     html.Button("Download as HTML"),
                                #     id="download",
                                #     href="data:text/html;base64," + encoded,
                                #     download="Capex_vs_Opex.html"),  ## SK: funktioniert nicht, bringt dash server zum absturz
                            ],width=12)
                        ]),
                        dbc.Row(children=[
                            dbc.Col(children=[
                                html.H4("Costs of Energy Sources:"),
                                dcc.Graph(id ='FigCostEso'),
                            ],width=12)
                        ]),
                        dbc.Row(children=[
                            dbc.Col(children=[
                                html.H4("Cost of Production Units:"),
                                dcc.Graph(id ='your-graph3')
                            ],width=12)
                        ]),
                        dbc.Row(
                            dbc.Col(id="ColDataTable", width=12)
                        ),
                    ]),

                ], label="Summary - Costs (bar charts)", tab_id="tab-1"),

                dbc.Tab(children=[
                    dbc.CardBody(children=[
                        dbc.Row(children=[
                            dbc.Col(children=[
                                html.H4("Consumption of electricity:"),
                                dcc.Graph(id="LinePlotConsumptionEl")
                            ],width=12),
                            dbc.Col(children=[
                                html.H4("Consumption of fuels:"),
                                dcc.Graph(id="LinePlotConsumptionFuel")
                            ],width=12),
                        ]),
                    ]),
                    
                ], label="Details - External consumption of energy", tab_id="tab-2"),
                
                dbc.Tab(children=[
                    dbc.CardBody(children=[
                        dbc.Row(children=[
                            dbc.Col(children=[
                                html.H4("Electric on-site generation and consumption:"),
                                dcc.Graph(id="LinePlotPower")
                            ],width=12),
                            dbc.Col(children=[
                                html.H4("Thermal on-site generation and consumption:"),
                                dcc.Graph(id="LinePlotHeat")
                            ],width=12),
                        ]),
                    ]),
                ], label="Details - Generation & consumption of heat & power", tab_id="tab-3"),

                dbc.Tab(children=[
                    dbc.CardBody(children=[
                        dbc.Row(children=[
                            dbc.Col(children=[
                                html.H4("Live Steam Node:"),
                                dcc.Graph(id="Bilanz-1")
                            ],width=12),
                            dbc.Col(children=[
                                html.H4("High Pressure Steam Node 1 (inputs):"),
                                dcc.Graph(id="Bilanz-2")
                            ],width=12),
                            dbc.Col(children=[
                                html.H4("High Pressure Steam Node 2 (outputs):"),
                                dcc.Graph(id="Bilanz-3")
                            ],width=12),
                             dbc.Col(children=[
                                html.H4("Middle Pressure Steam Node 1 (inputs):"),
                                dcc.Graph(id="Bilanz-4")
                            ],width=12),
                            dbc.Col(children=[
                                html.H4("Middle Pressure Steam Node 2 (outputs):"),
                                dcc.Graph(id="Bilanz-5")
                            ],width=12),
                            dbc.Col(children=[
                                html.H4("Low Pressure Steam Node 1 (inputs):"),
                                dcc.Graph(id="Bilanz-6")
                            ],width=12),
                            dbc.Col(children=[
                                html.H4("Low Pressure Steam Node 2 (outputs):"),
                                dcc.Graph(id="Bilanz-7")
                            ],width=12),
                            dbc.Col(children=[
                                html.H4("Electricity Node 1:"),
                                dcc.Graph(id="Bilanz-8")
                            ],width=12),
                            dbc.Col(children=[
                                html.H4("Electricity Node 2:"),
                                dcc.Graph(id="Bilanz-9")
                            ],width=12),
                            dbc.Col(children=[
                                html.H4("Humid Air Node:"),
                                dcc.Graph(id="Bilanz-10")
                            ],width=12),
                        ]),
                    ]),
                ], label="Details - Balancing nodes for heat & power", tab_id="tab-4"),

                dbc.Tab(children=[
                    dbc.CardBody(children=[
                        dbc.Row(children=[
                            dbc.Col(children=[
                                dcc.Graph(id="PurchaseConsumptionPlot")
                            ],width=12),
                        ]),
                    ]),
                ], label="Summary - Supply and consumption", tab_id="tab-5"),


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
                ], label="Summary - Costs (sunburst charts)", tab_id="tab-6"),

                dbc.Tab(children=[
                    dbc.CardBody(children=[
                        dbc.Row(
                            dbc.Col(id="SummaryTable",
                                    width=8
                                    )
                        ),
                    ],
                    )
                ], label="Summary for csv-export", tab_id="tab-7"),

            ],id="card-tabs", active_tab="tab-1")
    ], style= {'display': 'none'}
    ),
    ]),
])
# ,style={'overflow': 'hidden'}

@app.callback(
    Output("simulationSetupStorage", "data"),
    Input("url", "pathname"),
    Input("url", "href")
)
def getDataFromURL(pathname, href):
    # with open("tool_dekarpio_structure.json", "r") as f:
    #     structure = json.load(f)
    '''
    Get the UserID from the href and use it to retreive the settings in the Database by calling the API
    Simulation Settings are stored in a dcc.Store Component --> triggers the next Callback automatically
    '''
    path = href.split("?jwt=")[0]
    user_id = path.split("/")[-1]
    query_params = parse_qs(href.split("?")[1])
    config_id = query_params.get("configId", [""])[0]
    response = requests.get("http://api:3001/api/simulation-results/simulation/"+user_id+"/"+config_id)
    temp = response.json()
    dataDict = temp["data"][0]
    return dataDict["settings"]
    # return structure

@app.long_callback(
    Output("simulationResultStorage", "data"),
    Output("timelineListStorage", "data"),
    Output("simulationInformation", "children"),
    Input("simulationSetupStorage", "data"),
    running=[
        (Output("htmlTest", "children"), "Simulation is running...", "Simulation is Finished! Building Diagrams ..."),
        (Output("progress_bar", "style"),{"visibility": "visible", 'width': '99%', 'height': '25%'},{"visibility": "hidden"}),
    ],
    progress=[Output("progress_bar", "value"), Output("progress_bar", "max")],
    prevent_intial_callback=True
)
def startSimulation(set_progress, data):

    totalSteps = 9
    count=0

    count+=1
    set_progress((str(count), str(totalSteps)))

    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    timelines, period_list, label_list, no_timesteps, timeline_map = ja.read_timelines("tool_dekarpio_timelines.json")

    #structure = ja.read_structure('tool_dekarpio_structure.json')
    structure = json.loads(data)


    count+=1
    set_progress((str(count), str(totalSteps)))

    sysParam = ja.read_parameters(structure['par'], structure['eco'], period_list, label_list, no_timesteps)

    count+=1
    set_progress((str(count), str(totalSteps)))

    ini_out_str, res = ja.initialize_model(sysParam)

    count+=1
    set_progress((str(count), str(totalSteps)))

    add_out_str, res = ja.add_units_and_nodes(res, structure, timelines, timeline_map)

    count+=1
    set_progress((str(count), str(totalSteps)))

    bui_out_str, res = ja.build_pyomo_model(res)

    count+=1
    set_progress((str(count), str(totalSteps)))

    #ja.print_active_units(res)

    sol_out_str, slack_out_str, res = ja.solve_pyomo_model(res)

    count+=1
    set_progress((str(count), str(totalSteps)))

    resultsdict = ja.return_results_dict(res)
    #print(resultsdict.keys())


    count+=1
    set_progress((str(count), str(totalSteps)))

    outString = ini_out_str + "\n" + add_out_str + "\n" + bui_out_str + "\n" + sol_out_str + "\n\n" + slack_out_str

    return json.dumps(resultsdict), period_list, outString

@app.callback(
    Output('FigCostUnit', 'figure'),
    Output('FigCostEso', 'figure'),
    Output('your-graph3', 'figure'),
    Output('LinePlotConsumptionEl', 'figure'),
    Output('LinePlotConsumptionFuel', 'figure'),
    Output('LinePlotPower', 'figure'),
    Output('LinePlotHeat', 'figure'),
    Output('Bilanz-1', 'figure'),
    Output('Bilanz-2', 'figure'),
    Output('Bilanz-3', 'figure'),
    Output('Bilanz-4', 'figure'),
    Output('Bilanz-5', 'figure'),
    Output('Bilanz-6', 'figure'),
    Output('Bilanz-7', 'figure'),
    Output('Bilanz-8', 'figure'),
    Output('Bilanz-9', 'figure'),
    Output('Bilanz-10', 'figure'),
    Output('PurchaseConsumptionPlot', 'figure'),
    Output('ColDataTable', 'children'),
    Output('SunBurst1', 'figure'),
    Output('SunBurst2', 'figure'),
    Output('SunBurst3', 'figure'),
    Output('CostTable', 'children'),
    Output('SummaryTable', 'children'),
    Output("resultCard","style"),
    Output("htmlTest", "children"),
    #Input('htmlTest', 'data'),
    Input('simulationResultStorage', 'data'),
    State('timelineListStorage', 'data'),
    prevent_initial_call=True
    )
def update_figure(jsonStorage, period_list):

    jsonStorage = json.loads(jsonStorage)
    figCostUnit, dfCostUnit, sunBurstDf, capDF, sunBurstDfPos, sumDF = drawCostPlotUnit(jsonStorage)
    figCostEso, dfCostEso = drawCostPlotEso(jsonStorage)
    fig3 = drawCostPlotEcuEsu(jsonStorage)
    fig4 = drawLinePlotPower(jsonStorage, period_list)
    figconsume = drawLinePlotConsumption(jsonStorage, period_list)
    figconsumefuel = drawLinePlotConsumptionF(jsonStorage, period_list)
    fig5 = drawLinePlotHeat(jsonStorage, period_list)

    ar = drawBilanzPlots(jsonStorage, period_list)

    # print(dfCostEso)


    figSunBurstType = px.sunburst(sunBurstDfPos, path=['Capex/Opex', 'Cost Type'], values='Costs', color='Capex/Opex', color_discrete_sequence=px.colors.qualitative.Dark2)
    figSunBurstUnit = px.sunburst(sunBurstDfPos, path=['Capex/Opex', 'Unit'], values='Costs', color='Capex/Opex', color_discrete_sequence=px.colors.qualitative.Set2)
    figSunBurstUnitCosts = px.sunburst(sunBurstDfPos, path=['Unit', 'Cost Type'], values='Costs',  color='Unit', color_discrete_sequence=np.concatenate((px.colors.qualitative.Set3, px.colors.qualitative.Pastel), axis=None))

    #energy_overview = drawPurchaseConsumptionPlot(jsonStorage, period_list)

    table = dbc.Table.from_dataframe(dfCostEso, striped=True, bordered=True, hover=True, index=True)



    dashTable = dash.dash_table.DataTable(sunBurstDf.to_dict('records'), [{"name": i, "id": i} for i in sunBurstDf.columns], export_format="xlsx")
    dashTable2 = dash.dash_table.DataTable(capDF.to_dict('records'), [{"name": i, "id": i} for i in capDF.columns], export_format="xlsx")
    dashTable3 = dash.dash_table.DataTable(sumDF.to_dict('records'), [{"name": i, "id": i} for i in sumDF.columns], export_format="xlsx")





    return figCostUnit, figCostEso, fig3, figconsume, figconsumefuel, fig4, fig5, \
           ar[0], ar[1], ar[2], ar[3], ar[4], ar[5], ar[6], ar[7], ar[8], ar[9],\
           drawPurchaseConsumptionPlot(jsonStorage, period_list), table, figSunBurstType, figSunBurstUnit, figSunBurstUnitCosts, \
           dashTable, dashTable3, {"display":"block"}, "Simulation Results:"

##########################################################################
# Cost Plot Functions
##########################################################################
def drawCostPlotUnit(jsondata):
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
    dictfordf_pos = {
        idUnit:[],
        idCAPOP:[],
        idCostType:[],
        idCosts:[]
    }

    sum_inv = 0
    for unit in units:
        if unit in jsondata['units']:
            obj = jsondata['units'][unit]['obj']  

            # if (('inv_fix' in obj.keys()) == True):
            #     sum_inv += obj['inv_fix']
            # if (('inv_power' in obj.keys()) == True):
            #     sum_inv += obj['inv_power']
            # if (('inv_energy' in obj.keys()) == True):
            #     sum_inv += obj['inv_energy']
            # if (('inv_cap' in obj.keys()) == True):
            #     sum_inv += obj['inv_cap']
            # if (('invest_cap' in obj.keys()) == True):
            #     sum_inv += obj['invest_cap']
            if (('inv' in obj.keys()) == True):
                sum_inv += obj['inv']

            for key, val in obj.items():
                if key not in capexopex.keys(): continue
                dictfordf[idUnit].append(units[unit])
                dictfordf[idCAPOP].append(capexopex[key])
                dictfordf[idCostType].append(costs[key])
                dictfordf[idCosts].append(val/(1e6))

            for key, val in obj.items():
                if key not in capexopex.keys(): continue
                if val > 0:
                    dictfordf_pos[idUnit].append(units[unit])
                    dictfordf_pos[idCAPOP].append(capexopex[key])
                    dictfordf_pos[idCostType].append(costs[key])
                    dictfordf_pos[idCosts].append(val/(1e6))

    annuity = (1 + jsondata['params']['interest_rate']) ** (jsondata['params']['depreciation_period']) * (jsondata['params']['interest_rate']) /\
              ((1 + jsondata['params']['interest_rate']) ** (jsondata['params']['depreciation_period'])-1)
    print("annuity")
    print(annuity)
    inv = sum_inv/annuity

    dictfordf_cap= {}

    idSize = "Size"
    idType = "Type"
    idValue = "Value"
    idEinheit = "Unit of Value"
    dictfordf_sum = {
        idSize: [],
        idType: [],
        idEinheit: [],
        idValue: [],
    }
    # RESULTS todo: energiemengen gesamt, ev. energiepreise und invpreise; optional: column componenten for filtering

    dictfordf_sum[idSize].append('Total Annual Cost (Total Costs - Savings from free certificates)')
    dictfordf_sum[idType].append('Result')
    dictfordf_sum[idValue].append(round(jsondata['objectives']['total_real'] / (1e6), 3))
    dictfordf_sum[idEinheit].append('M€/a')
    dictfordf_sum[idSize].append('Annualized Investment')
    dictfordf_sum[idType].append('Result')
    dictfordf_sum[idValue].append(round(sum_inv/1e6, 3))
    dictfordf_sum[idEinheit].append('M€/a')
    dictfordf_sum[idSize].append('Total Investment')
    dictfordf_sum[idType].append('Result')
    dictfordf_sum[idValue].append(round(inv/1e6, 3))
    dictfordf_sum[idEinheit].append('M€')
    dictfordf_sum[idSize].append('Total Fossil Emissions')
    dictfordf_sum[idType].append('Result')
    dictfordf_sum[idValue].append(round(jsondata['objectives']['em_fos'], 1))
    dictfordf_sum[idEinheit].append('t/a')
    dictfordf_sum[idSize].append('Total Biogen Emissions')
    dictfordf_sum[idType].append('Result')
    dictfordf_sum[idValue].append(round(jsondata['objectives']['em_bio'], 1))
    dictfordf_sum[idEinheit].append('t/a')



    dictfordf_sum[idSize].append('CO2 Price fossil')
    dictfordf_sum[idType].append('Parameter')
    dictfordf_sum[idValue].append(jsondata['params']['cost_co2_fossil'])
    dictfordf_sum[idEinheit].append('€/t')
    dictfordf_sum[idSize].append('CO2 Certificates fossil')
    dictfordf_sum[idType].append('Parameter')
    dictfordf_sum[idValue].append(jsondata['params']['free_certificate_fossil'])
    dictfordf_sum[idEinheit].append('t/a')
    dictfordf_sum[idSize].append('CO2 fossil target')
    dictfordf_sum[idType].append('Parameter')
    dictfordf_sum[idValue].append(jsondata['params']['decarb_target_fossil'])
    dictfordf_sum[idEinheit].append('-')

    dictfordf_sum[idSize].append('CO2 Price biogen')
    dictfordf_sum[idType].append('Parameter')
    dictfordf_sum[idValue].append(jsondata['params']['cost_co2_biogen'])
    dictfordf_sum[idEinheit].append('€/t')
    dictfordf_sum[idSize].append('CO2 Certificates biogen')
    dictfordf_sum[idType].append('Parameter')
    dictfordf_sum[idValue].append(jsondata['params']['free_certificate_bio'])
    dictfordf_sum[idEinheit].append('t/a')
    dictfordf_sum[idSize].append('CO2 fossil biogen')
    dictfordf_sum[idType].append('Parameter')
    dictfordf_sum[idValue].append(jsondata['params']['decarb_target_bio'])
    dictfordf_sum[idEinheit].append('-')

    dictfordf_sum[idSize].append('Depreciation period')
    dictfordf_sum[idType].append('Parameter')
    dictfordf_sum[idValue].append(jsondata['params']['depreciation_period'])
    dictfordf_sum[idEinheit].append('a')
    dictfordf_sum[idSize].append('Interest rate')
    dictfordf_sum[idType].append('Parameter')
    dictfordf_sum[idValue].append(jsondata['params']['interest_rate'])
    dictfordf_sum[idEinheit].append('-')

    for unit in units:
        if unit in jsondata['units']:
            # print(jsondata['units'][unit]['var']['scalar'].items())
            if 'cap' in jsondata['units'][unit]['var']['scalar'].keys():
                name = 'Integration of componentent - ' + str(units[unit])
                dictfordf_sum[idSize].append(name)
                dictfordf_sum[idType].append('Parameter')
                dictfordf_sum[idValue].append(str(jsondata['units'][unit]['integ']))
                dictfordf_sum[idEinheit].append('-')

                name = 'Existence of component ' + str(units[unit])
                einheit = '-'
                if 's' in jsondata['units'][unit]['var']['seq'].keys():
                    name = 'Initial upper bound for consumption capacity of ' + str(units[unit])
                    einheit = units_unit[unit]
                dictfordf_sum[idSize].append(name)
                dictfordf_sum[idType].append('Parameter')
                dictfordf_sum[idValue].append(jsondata['units'][unit]['exist'])
                dictfordf_sum[idEinheit].append(einheit)

                name = 'Capacity of ' + str(units[unit])
                type = 'Parameter'
                if jsondata['units'][unit]['exist'] == 'Considered as not existing':
                    type = 'Result'
                if 's' in jsondata['units'][unit]['var']['seq'].keys():
                    name = 'Technical upper bound for consumption capacity of ' + str(units[unit])
                dictfordf_sum[idSize].append(name)
                cap = round(jsondata['units'][unit]['var']['scalar']['cap'], 1)
                dictfordf_sum[idType].append(type)
                dictfordf_sum[idValue].append(cap)
                dictfordf_sum[idEinheit].append(units_unit[unit])

                if 's' in jsondata['units'][unit]['var']['seq'].keys():
                    name = 'Max. real consumption of ' + str(units[unit])
                    dictfordf_sum[idSize].append(name)
                    cont = 0
                    for i, j in jsondata['units'][unit]['var']['seq']['s'].items():
                        for element in jsondata['units'][unit]['var']['seq']['s'][i]['values']:
                            if element > cont:
                                cont = element
                    consume = round(cont, 1)
                    dictfordf_sum[idType].append('Result')
                    dictfordf_sum[idValue].append(consume)
                    dictfordf_sum[idEinheit].append(units_unit[unit])

            # else:
            #     cap = 0
            #     dictfordf_cap[idCap].append(cap)
            #     dictfordf_cap[idMW].append(units_unit[unit])




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

    
    #co2 costs : co2_fossil or co2_biogen
    sum_co2 = 0
    sum_co2 += 0 - \
               jsondata['params']['cost_co2_fossil']*jsondata['params']['free_certificate_fossil'] - \
               jsondata['params']['cost_co2_biogen']*jsondata['params']['free_certificate_bio']
    for unit in units:
        if unit in jsondata['units']:

            # dictfordf[idUnit].append(units[unit])
            # dictfordf[idCAPOP].append("OPEX")
            # dictfordf[idCostType].append("Maintenance Costs")

            obj = jsondata['units'][unit]['obj']  
            if (('co2_fossil' in obj.keys()) == True):
                sum_co2 += obj['co2_fossil']
            if (('co2_biogen' in obj.keys()) == True):
                sum_co2 += obj['co2_biogen']
            
            # dictfordf[idCosts].append(sum_main)


    #fuel costs
    sum_fuel = 0
    for unit in units:
        if unit in jsondata['units']:
            obj = jsondata['units'][unit]['obj']  

            # dictfordf[idUnit].append(units[unit])
            # dictfordf[idCAPOP].append("OPEX")
            # dictfordf[idCostType].append("Electricity Costs")

            if (('energy' in obj.keys()) == True):
                sum_fuel += obj['energy']
            if (('max_s' in obj.keys()) == True):
                sum_fuel += obj['max_s']
            
            # dictfordf[idCosts].append(sum_ele)

    


    df_opex = pd.DataFrame({ 'Start costs': sum_start/(1e6),
                'CO<sub>2</sub> costs <br>(free cert. considered)': sum_co2/(1e6),
                'Unit operation costs': sum_fix/(1e6),
                'Fuel costs <br>(purchase - sales)': sum_fuel/(1e6)},
                index= ['Opex']
                ) 
    df_capex = pd.DataFrame({'Investment costs': sum_inv/(1e6)},
                            index= ['Capex'])

    df_costs = pd.concat([df_opex, df_capex])
    color = len(df_costs.keys())

    sunburstdf_pos = round(pd.DataFrame(dictfordf_pos), 3)
    sunburstdf = round(pd.DataFrame(dictfordf), 3)

    capdf = round(pd.DataFrame(dictfordf_cap), 3)

    sumdf = round(pd.DataFrame(dictfordf_sum), 3)

    dfs_costs = [df_opex.loc['Opex'].sum(), df_capex.loc['Capex'].sum()]

    fig = px.bar(df_costs,
                #title = 'Total costs',
                labels = {'index': 'Cost Type', 'value': 'Costs in MEUR/a',
                            'variable': 'Cost Type'},
                barmode ='relative',
                orientation ='h',
                color = 'variable',
                color_discrete_sequence = pclr.qualitative.Set2[0:color],
                text_auto='.2f'
                )

    fig.update_traces(textfont_size=10, textangle=45, textposition='inside', cliponaxis=False)
    fig.update_layout(uniformtext_minsize=10, uniformtext_mode='hide')
    fig.add_trace(go.Scatter(
        y=['Opex', 'Capex'], x=dfs_costs, text=dfs_costs, mode='text',
        texttemplate=' <b>SUM</b><br> <b>%{text:.2f}</b><br> <b>MEUR/a</b> ', textposition='top right', textfont=dict(size=12,), showlegend=False))

    return fig, df_costs, sunburstdf, capdf, sunburstdf_pos, sumdf

def drawCostPlotEso(jsondata):
    '''
    Draw Cost Plots of Eso working
    '''
    df = pd.concat([
                pd.DataFrame(
                    {
                        "Costs in Mio. Eur": round(jsondata['units'][unit_short]['obj'][cost_short]/(1e6),3),
                        "Cost Type": cost_long
                    },
                    index=[unit_long],

                )
                for unit_short, unit_long in units.items()
                if unit_short             in jsondata['units'] #1
                if unit_short.split('_')[0 ] == 'eso'
                for cost_short, cost_long in costs.items()
                for obj                   in jsondata['units'][unit_short]['obj']
                if cost_short             in obj
                #1 raus wenn alle units mit json übergeben werden aktuell nur 4 units
            ])
    
    df.index.set_names("Sources", inplace=True)
    dfs = df.groupby('Sources').sum()

    return (
        px.bar(
            df,
            color='Cost Type',
            color_discrete_sequence = pclr.qualitative.Set2,
            text_auto='.2f'
        )
        .update_traces(textfont_size=10, textangle=0, textposition='inside',cliponaxis=False)
        .update_layout(uniformtext_minsize=6, uniformtext_mode='hide', margin=dict(t=25, b=0, l=0, r=0))
        .add_trace(go.Scatter(
            x=dfs.index, y=dfs['Costs in Mio. Eur'],  text=dfs['Costs in Mio. Eur'], mode='text',
            texttemplate=' <b>%{text:.2f}</b>', textposition='top center', textfont=dict(size=10,), showlegend=False))
        .for_each_xaxis(lambda x: x.update(title=('<b>Energy sources</b><br>')))
        .for_each_yaxis(lambda x: x.update(title=('Costs in MEUR/a')))
    ), df

def drawCostPlotEcuEsu(jsondata):
    '''
    Draw Cost Plots of Ecu Esu working
    '''
    df = pd.concat([
                pd.DataFrame(
                    {
                        "Costs in Mio. Eur": jsondata['units'][unit_short]['obj'][cost_short]/(1e6),
                        "Cost Type": cost_long
                    },
                    index= [unit_long],

                )
                for unit_short, unit_long in units.items()
                if unit_short.split('_')[0]=='ecu' or unit_short.split('_')[0]== 'esu'
                if unit_short             in jsondata['units'] #1
                for cost_short, cost_long in costs.items()
                for obj                   in jsondata['units'][unit_short]['obj']
                if cost_short             in obj
                #1 raus wenn alle units mit json übergeben werden aktuell nur 4 units

            ])
    df.index.set_names("Units", inplace=True)

    dfs = df.groupby('Units').sum()

    return (
        px.bar(
            df,
            color='Cost Type',
            color_discrete_sequence = pclr.qualitative.Set2,
            text_auto='.2f'
        )
        .update_traces(textfont_size=10, textangle=0, textposition='inside',cliponaxis=False)
        .update_layout(uniformtext_minsize=6, uniformtext_mode='hide', margin=dict(t=25, b=0, l=0, r=0))
        .add_trace(go.Scatter(
            x=dfs.index, y=dfs['Costs in Mio. Eur'],  text=dfs['Costs in Mio. Eur'], mode='text',
            texttemplate=' <b>%{text:.2f}</b>', textposition='top center', textfont=dict(size=10,), showlegend=False))
        .for_each_xaxis(lambda x: x.update(title=('<b>Energy conversion units and storages</b><br>')))
        .for_each_yaxis(lambda x: x.update(title=('Costs in MEUR/a')))
    )


def drawLinePlotPower(jsondata, period_list):
    '''
    Draw LinePlot Power Working 
    '''
    facet_col_wrap = 3

    sym_sequence = ["circle", "square", "triangle-up", "diamond", "diamond-wide"]
    color_discrete_sequence = pclr.qualitative.Bold
    return (
        px.line(
            pd.concat([
                pd.DataFrame(
                    dict(
                        values=seq['p'][per]['values'],
                        Unit=unit_long, Timeline=per
                    ),
                    index=[f'{timestep:02g}:00' for timestep in seq['p'][per]['timesteps']]
                )
                for per              in period_list
                for unit_short, unit_long in units.items()
                if unit_short             in jsondata['units'] #1
                for seq                   in [jsondata['units'][unit_short]['var']['seq']] 
                if 'p' in seq
                #1 raus wenn alle units mit json übergeben werden aktuell nur 4 units
            ]),
            color='Unit', symbol='Unit', markers=True,  facet_col='Timeline', line_shape='hvh',
            facet_col_wrap=facet_col_wrap,  symbol_sequence=sym_sequence,
            color_discrete_sequence=color_discrete_sequence
        )
        .update_layout(margin=dict(t=25, b=0, l=0, r=0))
        .for_each_xaxis(lambda x: x.update(title=None, showticklabels=True))
        .for_each_yaxis(lambda x: x.update(title=('MWh' if x.anchor=="x" or x.anchor=="x4"
                                                  or x.anchor=="x7" else None)))
    )

def drawLinePlotConsumption(jsondata, period_list):
    '''
    Draw LinePlot Consumption Working
    '''
    facet_col_wrap = 3

    sym_sequence = ["circle", "square", "triangle-up", "diamond", "diamond-wide", "triangle-down"]
    return (
        px.line(
            pd.concat([
                pd.DataFrame(
                    dict(
                        values=seq['s'][per]['values'],
                        Unit=unit_long, Timeline=per
                    ),
                    index=[f'{timestep:02g}:00' for timestep in seq['s'][per]['timesteps']]
                )
                for per              in period_list
                for unit_short, unit_long in elsources.items()
                if unit_short             in jsondata['units'] #1
                for seq                   in [jsondata['units'][unit_short]['var']['seq']]
                if 's' in seq
                #1 raus wenn alle units mit json übergeben werden aktuell nur 4 units
            ]),
            color='Unit', symbol='Unit', markers=True,  facet_col='Timeline', line_shape='hvh',
            facet_col_wrap=facet_col_wrap,  symbol_sequence=sym_sequence
        )
        .update_layout(margin=dict(t=25, b=0, l=0, r=0))
        .for_each_xaxis(lambda x: x.update(title=None, showticklabels=True))
        .for_each_yaxis(lambda x: x.update(title=('MWh' if x.anchor=="x" or x.anchor=="x4"
                                                  or x.anchor=="x7" else None)))
    )

def drawLinePlotConsumptionF(jsondata, period_list):
    '''
    Draw LinePlot Consumption Working
    '''
    facet_col_wrap = 3

    sym_sequence = ["circle", "square", "triangle-up", "diamond", "diamond-wide", "triangle-down"]
    return (
        px.line(
            pd.concat([
                pd.DataFrame(
                    dict(
                        values=seq['s'][per]['values'],
                        Unit=unit_long, Timeline=per
                    ),
                    index=[f'{timestep:02g}:00' for timestep in seq['s'][per]['timesteps']]
                )
                for per              in period_list
                for unit_short, unit_long in fuelsources.items()
                if unit_short             in jsondata['units'] #1
                for seq                   in [jsondata['units'][unit_short]['var']['seq']]
                if 's' in seq
                #1 raus wenn alle units mit json übergeben werden aktuell nur 4 units
            ]),
            color='Unit', symbol='Unit', markers=True,  facet_col='Timeline', line_shape='hvh',
            facet_col_wrap=facet_col_wrap,  symbol_sequence=sym_sequence
        )
        .update_layout(margin=dict(t=25, b=0, l=0, r=0))
        .for_each_xaxis(lambda x: x.update(title=None, showticklabels=True))
        .for_each_yaxis(lambda x: x.update(title=('MWh' if x.anchor=="x" or x.anchor=="x4"
                                                  or x.anchor=="x7" else None)))
    )


def drawLinePlotHeat(jsondata, period_list):
    '''
    Draw Line Plot Heat Working
    '''
    facet_col_wrap = 3
    # print(period_list, units.items(), jsondata['units'], heat_types.items(), )
    symbol_sequence = ["circle", "square", "triangle-up", "diamond", "diamond-wide", "triangle-down"]
    color_discrete_sequence = pclr.qualitative.Dark24
    return (
        px.line(
            pd.concat([
                pd.DataFrame(
                    dict(
                        values= jsondata['units'][unit_short]['var']['seq'][heat_short][per]['values'],
                        Unit=unit_long, Steamlevel = heat_long, Timeline=per
                    ),
                    index=[f'{timestep:02g}:00'
                           for timestep in jsondata['units'][unit_short]['var']['seq']
                           [heat_short][per]['timesteps']]
                )
                for per               in period_list
                for unit_short, unit_long  in units.items()
                if unit_short             in jsondata['units'] #1
                for heat_short, heat_long  in heat_types.items()
                for seq                    in [jsondata['units'][unit_short]['var']['seq']]
                if heat_short              in seq
                #1 raus wenn alle units mit json übergeben werden aktuell nur 4 units

            ]),
            color='Unit', symbol='Steamlevel', facet_col='Timeline', line_shape='hvh',
            facet_col_wrap=facet_col_wrap, markers=True, symbol_sequence=symbol_sequence,
            color_discrete_sequence=color_discrete_sequence
        )
        .update_layout(margin=dict(t=25, b=0, l=0, r=0))
        .for_each_xaxis(lambda x: x.update(title=None, showticklabels=True))
        .for_each_yaxis(lambda x: x.update(title=('MWh' if x.anchor=='x' or x.anchor=='x4'
                                                  or x.anchor=='x7' else None)))
    )

def drawBilanzPlots(jsondata, period_list):
    ar = []
    for fig in make_nodes(jsondata, period_list):
        ar.append(fig)

    #print("BilanzPlots!!!!!!!!!")
    return ar

def make_fig_Bilanz(jsondata, period_list, steam: str, side: str, alt_colors=False):
    #todo exchange steam - as also electricity is now plotted here
    facet_col_wrap = 3
    symbol_sequence = ['circle', 'square', 'triangle-up', 'diamond', 'diamond-wide', 'triangle-down']
    color_discrete_sequence = pclr.qualitative.Plotly if not alt_colors else pclr.qualitative.Vivid
    return (
        px.area(
            pd.concat([
                pd.DataFrame(
                    dict(
                        values=jsondata['nodes'][steam][side][unit][per]['values'],
                        Unit=unit, Timeline=per
                    ),
                    index=[f'{timestep}:00' for timestep in jsondata['nodes'][steam][side][unit][per]['timesteps']]
                )
                for per in period_list
                for unit in jsondata['nodes'][steam][side]
            ]),
            color='Unit', facet_col='Timeline', 
            facet_col_wrap=facet_col_wrap, markers=True, symbol_sequence=symbol_sequence,
            color_discrete_sequence=color_discrete_sequence,
            facet_col_spacing=0.04
        )
        .update_layout(margin=dict(t=25, b=0, l=0, r=0))
        .for_each_xaxis(lambda x: x.update(title=None, showticklabels=True))
        .for_each_yaxis(lambda x: x.update(title=('MWh' if x.anchor=="x4" else None)))
    )

def make_pos_neg(jsondata: dict, period_list, steam: str) -> go.Figure:
    fig_lhs = make_fig_Bilanz(jsondata, period_list, steam, 'lhs')
    fig_rhs = make_fig_Bilanz(jsondata, period_list, steam, 'rhs', alt_colors=True)
    
    for trc in fig_rhs.data:
        trc.stackgroup = "2"
        trc.y = [-i for i in trc.y] 

    return fig_lhs.add_traces(fig_rhs.data)

def make_nodes(jsondata: dict, period_list) -> list[go.Figure]:
    steams = dict(
        col_col3_lis1_node='Live Steam Node',
        col_col8_his1_node='High pressure steam Node 1',
        col_col9_his2_node='High pressure steam Node 2',
        col_col2_mis1_node='Middle pressure steam Node 1',
        col_col4_mis2_node='Middle pressure steam Node 2',
        col_col7_los1_node='Low pressure steam Node 1',
        col_col5_los2_node='Low pressure steam Node 2',
        col_col1_ele1_node='Electricity 1',
        col_col6_ele2_node='Electricity 2',
        col_col10_hua_node='humid air'
    )
    return [make_pos_neg(jsondata, period_list, steam) for steam in steams]

def drawPurchaseConsumptionPlot(jsondata, period_list):
    #List of all purchases (selber anpassen aus Units)
    purchase_list = ['Electricity grid', 'Renewable electricity grid',
                     'Electricity PPA PV', 'Electricity PPA Wind', 'Electricity PPA Hydro',
                     'Natural gas', 'Biogas', 'Biomethane', 'Biomass', 'Coal', 'Oil', 'Hydrogen', 'Biofuel',
                     'Other solid', 'Other gas',
                     'External waste', 'Purchased district heat', 'Steam extern']

    #List of all consumptions (selber anpassen)
    consumption1_list = ['Process 1 Gas', 'Process 1 Power', 'Process 1 Steam High Pr', 'Process 1 Steam Middle Pr', 'Process 1 Steam Low Pr']
    consumption2_list = ['Process 2 Gas', 'Process 2 Power', 'Process 2 Steam High Pr', 'Process 2 Steam Middle Pr', 'Process 2 Steam Low Pr']
    consumption3_list = ['Process 3 Gas', 'Process 3 Power', 'Process 3 Steam High Pr', 'Process 3 Steam Middle Pr', 'Process 3 Steam Low Pr']
    consumption4_list = ['Process 4 Gas', 'Process 4 Power', 'Process 4 Steam High Pr', 'Process 4 Steam Middle Pr', 'Process 4 Steam Low Pr']


    #List of all sales (selber anpassen)
    sales_list = ['District heat', 'Feed electricity grid']

    #List of local production (selber anpassen)
    production_list = ['Geothermal',
                       'Electricity PV', 'Electricity Wind', 'Electricity Hydro',
                       'Sludge', 'Internal waste',
                       'Gasturbine 1', 'Gasturbine 2']

    #List of sequences (selber anpassen)
    sequences = ['s', 'p', 'd']

    
    '''
    TODO List of Sequences zuordnen mit Sophie
    '''

    #Define order of barcharts
    order=('Sales of energy', 'Consumption of energy (process 1)', 'Consumption of energy (process 2)',
           'Consumption of energy (process 3)', 'Consumption of energy (process 4)',
           'Local production of energy', ' Purchase of energy')


    print('general')
    print(jsondata['general'])

    df_seq = pd.DataFrame()
    for unit_short, unit_long in units.items():
        sum_values=0

        if unit_short in jsondata["units"]:
            seq = jsondata['units'][unit_short]['var']['seq']
            # print(unit_short)
        else:
            continue
        dict_data = {}
        #print('Period_list')
        #print(period_list)

        for sequence in sequences: 
            if sequence in seq.keys():

                for i, per in enumerate(period_list):
                    #print(seq[sequence].keys())
                    sum_values += sum(seq[sequence][per]['values']) * jsondata['general']['weight'][str(i)] * 8760 / 24 # todo - mit params aus res.param updaten
                dict_data[sequence] = sum_values
                #dict_data = {sequence : sum_values}
            #df_temp = pd.DataFrame(dict_data,index=[unit_long])
        df_seq = pd.concat([df_seq, pd.DataFrame(dict_data, index=[unit_long])])

    fig = go.Figure()

    for i, row in df_seq.iterrows():
        for n, purchase in enumerate(purchase_list):
            if purchase == i:
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Purchase of energy'],
                    x=[df_seq[val][i]],
                    legendgroup="purchase",
                    legendgrouptitle_text="Purchase",
                    orientation='h',
                    name=purchase,
                    marker_pattern_shape="x",
                    marker_color = pclr.qualitative.Alphabet[n]
                ))

        for n, consumption in enumerate(consumption1_list):
            if consumption == i:
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Consumption of energy (process 1)'],
                    x=[df_seq[val][i]],
                    legendgroup="consumption",
                    legendgrouptitle_text="Consumption",
                    orientation='h',
                    name=consumption,
                    marker_pattern_shape="\\",
                    marker_color = pclr.qualitative.Vivid[n]
                    ))
        for n, consumption in enumerate(consumption2_list):
            if consumption == i:
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Consumption of energy (process 2)'],
                    x=[df_seq[val][i]],
                    legendgroup="consumption",
                    orientation='h',
                    name=consumption,
                    marker_pattern_shape="\\",
                    marker_color = pclr.qualitative.Prism[n]
                    ))
        for n, consumption in enumerate(consumption3_list):
            if consumption == i:
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Consumption of energy (process 3)'],
                    x=[df_seq[val][i]],
                    legendgroup="consumption",
                    orientation='h',
                    name=consumption,
                    marker_pattern_shape="\\",
                    marker_color = pclr.qualitative.Bold[n]
                    ))
        for n, consumption in enumerate(consumption4_list):
            if consumption == i:
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Consumption of energy (process 4)'],
                    x=[df_seq[val][i]],
                    legendgroup="consumption",
                    orientation='h',
                    name=consumption,
                    marker_pattern_shape="\\",
                    marker_color = pclr.qualitative.Pastel[n]
                    ))

        for n, sales in enumerate(sales_list):
            if sales == i:
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Sales of energy'],
                    x=[df_seq[val][i]],
                    legendgroup="sale",
                    legendgrouptitle_text="Sale",
                    orientation='h',
                    name=sales,
                    marker_pattern_shape="+",
                    marker_color = pclr.qualitative.Set2[n]
                    ))
                
        for n, production in enumerate(production_list):
            if production == i:
                # Get sequence where there is a value in df
                val = [seq for seq in sequences if not np.isnan(df_seq[seq][i])][0]
                fig.add_trace(go.Bar(
                    y=['Local production of energy'],
                    x=[ df_seq[val][i]],
                    legendgroup="production",
                    legendgrouptitle_text="Production",
                    orientation='h',
                    name=production,
                    marker_color = pclr.qualitative.Antique[n]
                    ))

    fig.update_layout(barmode='stack', legend_title='Units',
                      #category_orders={[]},
                      title='Total consumption, purchase, sales and local production',
                      yaxis={'title': 'Supply vs. Demand in MWh', 'categoryorder': 'array',
                            'categoryarray' : order},
                      xaxis_title='MWh',
                      height=600,
                      #legend_traceorder= "normal"
                      )
    return fig

if __name__=='__main__':
    app.run_server(debug=True)
