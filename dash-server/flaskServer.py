from flask import Flask
from flask import request, jsonify
import json
import plotly.colors as pclr
import run
from flask_socketio import SocketIO, emit

server = Flask(__name__)
#app = dash.Dash(server=server, external_stylesheets=[dbc.themes.FLATLY], url_base_pathname='/dash-server/', long_callback_manager=long_callback_manager)
#app.title = 'Dashboard'

app = Flask(__name__)

#df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@app.route('/dash/<id>', methods=['GET'])
def startSimulation(id):
    print(id)
    results_dict = run.run()
    socketio.emit('message', {
            'status': "Message OK",
            }, namespace='/test')
    socketio.sleep(5)

    return app.index()

@app.route('/dash/validate', methods=['GET', 'POST'])
def validateJson():
    print("Hello")
    print(request.method)
    return "Hello"

@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.is_alive():
        print("Starting Thread")
        thread = socketio.start_background_task(randomNumberGenerator)

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')
    
if __name__=='__main__':
    app.run_server(debug=True)
