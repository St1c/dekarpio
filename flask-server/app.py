from flask import Flask
from flask import request, jsonify
from flask_socketio import SocketIO, emit
import requests
import json

server = Flask(__name__)

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/dash/validate', methods=['GET', 'POST'])
def validateJson():
    '''
    Get User ID from json File submitted in the request
    Get Simulation Setup from the API and test the Rules
    '''
    response = requests.get("http://api:3001/api/simulation-results/"+str(request.json['user_id']))

    temp = response.json()
    dataDict = temp["data"][0]["settings"]
    dataDict = json.loads(dataDict)

    resultDict = ecuRule(dataDict)

    if resultDict:
        return jsonify({
            'status': 'NOK',
            'data': jsonify(resultDict)
        })
    else:
        return jsonify({
        'status': 'OK',
        'data': ''
        })

def ecuRule(jsondata):
    print("ECU Rule")
    resultDict = {}
    for ecu in jsondata['ecu']:
    
    # Get list of all inputs
        inputs = jsondata['ecu'][ecu]['inp'].keys()
    
    # Check if all input max_shares are >= 0, if not error
        for inp in inputs:
            if (jsondata['ecu'][ecu]['inp'][inp]['max_share'] < 0):
                resultDict[ecu]=jsondata["ecu"][ecu]["inp"][inp]
                resultDict[ecu]["message"]=f'For {ecu}: {inp} max_share is not greater or equal 0 '
                print (f'For {ecu}: {inp} max_share is not greater or equal 0 ')
    return resultDict

def collectorRule(jsondata):
    # Check if connectors are coming to collector, if not: no outputs
    # Check if connectors going away to collector, if not: no inputs

    for col in jsondata['col']:
        
        # Get list of all inputs
        inputs = jsondata['col'][col]['inp'].keys()
        # Get list of all ouputs
        outputs = jsondata['col'][col]['out'].keys()
        
        # Check if there are any connectors active coming in collector
        sum_inputs_active = True
        for inp in inputs:
            sum_inputs_active = (
                sum_inputs_active
                and (jsondata['col'][col]['inp'][inp]['active'] == 'False'))
        if sum_inputs_active == True:
            print(f'For {col}: '
                'all Connectors coming to this collector are inactive '
                f'so there can not be any connectors going away from {col}')
            
        # Check if there are any connectors active going away from collector
        sum_outputs_active = True
        for out in outputs:
            sum_outputs_active = (
                sum_outputs_active
                and (jsondata['col'][col]['out'][out]['active'] == 'False'))
        if sum_outputs_active == True:
            print(f'For {col}: '
                'all Connectors going away from this collector are inactive '
                f'so there can not be any connectors coming to {col}')
            
def demandsRule(jsondata):
    # Check if demand is 0, if yes inputX.active = false
    # it is not possible that there is no demand but things are still delivered

    for dem in jsondata['dem']:
        
        # get list of all inputs
        inputs = jsondata['dem'][dem]['inp'].keys()
        
        if (jsondata['dem'][dem]['param'][0]['p_gas_max']) == 0 :
            print(f'There is no gas needed for {dem}')
            jsondata['dem'][dem]['inp']['input1']['active'] = "False"

        if (jsondata['dem'][dem]['param'][0]['p_his_max']) == 0 :
            print(f'There is no high pressure steam needed for {dem}')
            jsondata['dem'][dem]['inp']['input4']['active'] = "False"

        if (jsondata['dem'][dem]['param'][0]['p_mis_max']) == 0 :
            print(f'There is no middle pressure steam needed for {dem}')
            jsondata['dem'][dem]['inp']['input2']['active'] = "False"

        if (jsondata['dem'][dem]['param'][0]['p_los_max']) == 0 :
            print(f'There is no low pressure steam needed for {dem}')
            jsondata['dem'][dem]['inp']['input3']['active'] = "False"

        if (jsondata['dem'][dem]['param'][0]['p_ele_max']) == 0 :
            print(f'There is no electricity needed for {dem}')
            jsondata['dem'][dem]['inp']['input5']['active'] = "False" 

# @app.route('/dash/simulate/<id>', methods=['GET'])
# def startSimulation(id):
#     print(id)
#     # results_dict = run.run()
#     socketio.emit('message', {
#             'status': "Message OK",
#             }, namespace='/test')
#     socketio.sleep(5)

#     return app.index()

# @app.route('/dash/test', methods=['GET', 'POST'])
# def validateJson2():
#     print(request.method)
#     print("validation received")
#     # return object with data property and status
#     return jsonify({
#         'status': 'OK',
#         'data': ''
#     })

# @socketio.on('connect', namespace='/test')
# def test_connect():
#     # need visibility of the global thread object
#     global thread
#     print('Client connected')

#     #Start the random number generator thread only if the thread has not been started before.
#     if not thread.is_alive():
#         print("Starting Thread")
#         thread = socketio.start_background_task(randomNumberGenerator)

# @socketio.on('disconnect', namespace='/test')
# def test_disconnect():
#     print('Client disconnected')
    
if __name__=='__main__':
    # app.run_server(host="0.0.0.0", port=3003, debug=True)
    socketio.run(app, host="0.0.0.0", port=3003, debug=True)
