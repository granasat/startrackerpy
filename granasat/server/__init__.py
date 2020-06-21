from flask import Flask
from influxdb import InfluxDBClient
import threading
from server.jobs import Jobs

lock = threading.Lock()
influx_cli = InfluxDBClient('influxdb', 8086, 'admin', '12345', 'granasat')
app = Flask(__name__, template_folder='../client/templates',
            static_folder='../client/static')
jobs = Jobs()

from server import views
