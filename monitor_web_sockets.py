# sudo apt-get install libevent-dev
# sudo apt-get install python-all-dev
# pip install greenlet
# pip install gevent

#from gevent import monkey
#monkey.patch_all()
from flask_socketio import SocketIO
from flask import Flask, render_template
from time import sleep
from time import strftime
from threading import Thread, Event
from grovepi import *


__author__ = 'marcoafs'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a12bc34d5e'
app.config['DEBUG'] = True

socketio = SocketIO(app)

dht_thread = Thread()
thread_stop_event = Event()


led_port = 2
led_status = "off"
pinMode(led_port, "OUTPUT")
digitalWrite(led_port, 0)


class DHTThread(Thread):
    def __init__(self):
        self.delay = 1
        self.dht_port = 7
        super(DHTThread, self).__init__()

    def monitorDHT(self):
        while not thread_stop_event.isSet():
            try:
                [temp, hum] = dht(self.dht_port, 0)
                data = {
                    'success': True,
                    'temp': temp,
                    'hum': hum,
                    'date_time': strftime("%c")}
            except (IOError, TypeError) as e:
                data = {
                    'success': False,
                    'err_msg': str(e),
                    'date_time': strftime("%c")}
            socketio.emit('dht_measure', data, namespace='/monitor')
            sleep(self.delay)

    def run(self):
        self.monitorDHT()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect', namespace='/monitor')
def connect():
    global dht_thread
    global led_status
    print('Client connected')
    socketio.emit('led_status_change', {
                  'status': led_status}, namespace='/monitor')
    if not dht_thread.isAlive():
        print("Starting Thread")
        dht_thread = DHTThread()
        dht_thread.start()


@socketio.on('disconnect', namespace='/monitor')
def disconnect():
    print('Client disconnected')


@socketio.on('led_command', namespace='/monitor')
def control_led(data):
    print(data)
    global led_status
    if data['command'] == 'turn_on':
        digitalWrite(led_port, 1)
        led_status = "on"
    elif data['command'] == 'turn_off':
        digitalWrite(led_port, 0)
        led_status = "off"
    socketio.emit('led_status_change', {
                  'status': led_status}, namespace='/monitor')


if __name__ == '__main__':
    try:
        print('Iniciando servidor na porta 5000.')
        socketio.run(app, debug=True, host='0.0.0.0')
    finally:
        print('Desligando...')
        digitalWrite(led_port, 0)
        if dht_thread.isAlive():
            thread_stop_event.clear()
            dht_thread.join()
        print('Servidor terminado.')
