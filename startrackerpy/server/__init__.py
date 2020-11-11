from flask import Flask
from pathlib import Path
from influxdb import InfluxDBClient
import threading
from server.jobs import Jobs
from server.startracker.catalog import Catalog

lock = threading.Lock()
influx_cli = InfluxDBClient('192.168.1.74', 8086, 'admin', '12345', 'startrackerpy')
# Probably need to fix this path for docker
FILE_PATH = Path(__file__).parent.absolute()
catalogs_path = f"{FILE_PATH}/startracker/catalogs/out"
catalog = Catalog(f"{catalogs_path}/hip_2000.csv",
                  f"{catalogs_path}/guide_stars_2000_5.csv",
                  f"{catalogs_path}/guide_stars_2000_5_labels.csv")
app = Flask(__name__, template_folder='../client/templates',
            static_folder='../client/static')
jobs = Jobs()

from server import views
