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
import threading
#import grovepi
#from grovepi import *

__author__ = 'OsTerriveis'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a12bc34d5e'
app.config['DEBUG'] = False

socketio = SocketIO(app)

dht_thread = Thread()
ldr_thread = Thread()
sound_thread = Thread()
thread_stop_event = Event()


# Conexões
sound_sensor = 0 # porta A0
light_sensor = 1 # porta A1
#temperature_sensor = 7 # port D7

led_port = 2
led_status = "off"
#pinMode(led_port, "OUTPUT")
#digitalWrite(led_port, 0)

######## INICIO LCD IMPORTS #######
"""import time,sys

if sys.platform == 'uwp':
    import winrt_smbus as smbus
    bus = smbus.SMBus(1)
else:
    import smbus
    import RPi.GPIO as GPIO
    rev = GPIO.RPI_REVISION
    if rev == 2 or rev == 3:
        bus = smbus.SMBus(1)
    else:
        bus = smbus.SMBus(0)

# this device has two I2C addresses
DISPLAY_RGB_ADDR = 0x62
DISPLAY_TEXT_ADDR = 0x3e

# set backlight to (R,G,B) (values from 0..255 for each)
def setRGB(r,g,b):
    bus.write_byte_data(DISPLAY_RGB_ADDR,0,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,1,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,0x08,0xaa)
    bus.write_byte_data(DISPLAY_RGB_ADDR,4,r)
    bus.write_byte_data(DISPLAY_RGB_ADDR,3,g)
    bus.write_byte_data(DISPLAY_RGB_ADDR,2,b)

# send command to display (no need for external use)    
def textCommand(cmd):
    bus.write_byte_data(DISPLAY_TEXT_ADDR,0x80,cmd)

# set display text \n for second line(or auto wrap)     
def setText(text):
    textCommand(0x01) # clear display
    time.sleep(.05)
    textCommand(0x08 | 0x04) # display on, no cursor
    textCommand(0x28) # 2 lines
    time.sleep(.05)
    count = 0
    row = 0
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            textCommand(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))

#Update the display without erasing the display
def setText_norefresh(text):
    textCommand(0x02) # return home
    time.sleep(.05)
    textCommand(0x08 | 0x04) # display on, no cursor
    textCommand(0x28) # 2 lines
    time.sleep(.05)
    count = 0
    row = 0
    while len(text) < 32: #clears the rest of the screen
        text += ' '
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            textCommand(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))
"""
##### FIM LCD IMPORTS ######

class SoundThread(Thread):
    def __init__(self):
        self.delay = 0.5
        threading.Thread.__init__(self)

    def monitorSound(self):
        while not thread_stop_event.isSet():
            try:
                # Obtendo dado sensor
                # ler o nível do som
               # sound_value = grovepi.analogRead(sound_sensor)
                # Agrupando os dados para enviar
                data = {
                    'success': True,
                    'sound': sound_value,
                    'date_time': strftime("%c")}
            except (IOError, TypeError) as e:
                data = {
                    'success': False,
                    'err_msg': str(e),
                    'date_time': strftime("%c")}
            socketio.emit('sound_db_measure', data, namespace='/monitor')
            sleep(self.delay)

    def run(self):
        self.monitorSound() 

class LDRThread(Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.delay = 0.5

    def monitorLDR(self):
        while not thread_stop_event.isSet():
            try:
                # Obtendo dado sensor
                # obter o valor do sensor de luz
               # sensor_value = grovepi.analogRead(light_sensor)
                # calcular a resistência do sensor em Kohm
                resistance = \
                (float)(1023 - sensor_value) * 10 / sensor_value
                

                # Agrupando os dados para enviar
                data = {
                    'success': True,
                    'lux': round(resistance,2),
                    'date_time': strftime("%c")}
            except (IOError, TypeError) as e:
                data = {
                    'success': False,
                    'err_msg': str(e),
                    'date_time': strftime("%c")}
            socketio.emit('ldr_measure', data, namespace='/monitor')
            sleep(self.delay)

    def run(self):
        self.monitorLDR()        

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

@app.route('/temperatura')
def temperatura():
    return render_template('temperatura.html')

@app.route('/luminosidade')
def luminosidade():
    return render_template('luminosidade.html')

@app.route('/ruidos_sonoros')
def ruidos_sonoros():
    return render_template('ruidos_sonoros.html')

@app.route('/humidade')
def humidade():
    return render_template('humidade.html')

@socketio.on('connect', namespace='/monitor')
def connect():
    global dht_thread
    global ldr_thread
    global sound_thread

   # setText_norefresh("Vasco Calabresa em")
    #setRGB(0,255,0)
    
    global led_status
    print('Client connected')
    socketio.emit('led_status_change', {
                  'status': led_status}, namespace='/monitor')
    if not dht_thread.isAlive():
        print("Starting Thread de humidade e temperatura")
        dht_thread = DHTThread()
        #dht_thread.start()

    # Iniciando thread de luminosidade
    if not ldr_thread.isAlive():
        print("Iniciando thread de luminosidade")
        ldr_thread = LDRThread()
        #ldr_thread.start()
        
    # Iniciando thread de som
    if not sound_thread.isAlive():
        print("Iniciando Thread de detecao de ruidos")
        sound_thread = SoundThread()
        #sound_thread.start()

@socketio.on('disconnect', namespace='/monitor')
def disconnect():
    print('Client disconnected')

@socketio.on('troca_cor_lcd', namespace='/monitor')
def troca_cor(data):
    print(data['r'],data['g'],data['b'])
    #setRGB(data['r'],data['g'],data['b'])
    

@socketio.on('led_command', namespace='/monitor')
def control_led(data):
    #print(data)
    global led_status
    
    socketio.emit('sound_db_measure', {'success':True, 'sound':200}, namespace='/monitor')
#    if data['command'] == 'turn_on':
     #   digitalWrite(led_port, 1)
 #       print ("Led Ligado")
  #      led_status = "on"
#    elif data['command'] == 'turn_off':
  #      digitalWrite(led_port, 0)
#        led_status = "off"
#    socketio.emit('led_status_change', {
 #                 'status': led_status}, namespace='/monitor')


if __name__ == '__main__':
    try:
        print('Iniciando servidor na porta 5000.')
        #setRGB(0,0,255)
        socketio.run(app, debug=False, host='0.0.0.0')
    finally:
        print('Desligando...')
   #     digitalWrite(led_port, 0)
        if dht_thread.isAlive():
            thread_stop_event.clear()
            dht_thread.join()

        if sound_thread.isAlive():
            thread_stop_event.clear()
            sound_thread.join()            

        if ldr_thread.isAlive():
            thread_stop_event.clear()
            ldr_thread.join()                        
        print('Servidor terminado.')
