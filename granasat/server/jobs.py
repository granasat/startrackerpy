import time
from datetime import datetime
from sensors import CPU_SENSOR, DS1621, LSM303
from influxdb import InfluxDBClient
from db import Db
import multiprocessing
import threading
import logging

def write_cpu_metrics(influx_cli, cpu_sensor):
    cpu_temp = cpu_sensor.read_temp()
    json_body = [
        {
            "measurement": "cpu_temp",
            "tags": {
                "type": "system"
            },
            "time": datetime.strftime(datetime.now(),
                                      '%Y-%m-%dT%H:%M:%SZ'),
            "fields": {
                "degrees": cpu_temp
            }
        }
    ]
    influx_cli.write_points(json_body)


def write_cam_temp_metrics(influx_cli, ds_sensor):
    ds_sensor.wake_up()
    cam_temp = ds_sensor.read_degreesC_hiRes_oneshot()

    json_body = [
        {
            "measurement": "cam_temp",
            "tags": {
                "type": "system"
            },
            "time": datetime.strftime(datetime.now(),
                                      '%Y-%m-%dT%H:%M:%SZ'),
            "fields": {
                "degrees": cam_temp
            }
        }
    ]
    influx_cli.write_points(json_body)


def write_accelerometer_metrics(influx_cli, lsm_sensor):
    data = lsm_sensor.read_accel()

    json_body = [
        {
            "measurement": "accelerometer",
            "tags": {
                "type": "system"
            },
            "time": datetime.strftime(datetime.now(),
                                      '%Y-%m-%dT%H:%M:%SZ'),
            "fields": {
                "x": data[0],
                "y": data[1],
                "z": data[2]
            }
        }
    ]
    influx_cli.write_points(json_body)


def write_magnetometer_metrics(influx_cli, lsm_sensor):
    data = lsm_sensor.read_mag()

    json_body = [
        {
            "measurement": "magnetometer",
            "tags": {
                "type": "system"
            },
            "time": datetime.strftime(datetime.now(),
                                      '%Y-%m-%dT%H:%M:%SZ'),
            "fields": {
                "x": data[0],
                "y": data[1],
                "z": data[2]
            }
        }
    ]
    influx_cli.write_points(json_body)


def write_metrics():
    logging.info("Starting metrics thread")
    cpu_sensor = CPU_SENSOR()
    ds_sensor = DS1621(1, 0x48)
    lsm_sensor = LSM303()
    influx_cli = InfluxDBClient('influxdb', 8086, 'admin', '12345', 'granasat')
    interval = 5

    try:
        while True:
            write_cpu_metrics(influx_cli, cpu_sensor)
            write_cam_temp_metrics(influx_cli, ds_sensor)
            write_accelerometer_metrics(influx_cli, lsm_sensor)
            write_magnetometer_metrics(influx_cli, lsm_sensor)
            time.sleep(interval)

    except KeyboardInterrupt:
        print("Manual break by user")
    except Exception as e:
        print(e)

def burst():
    logging.info("Starting burst thread")
    DB = Db("data/granasat.db")
    interval = 5
    while True:
        bursts = DB.get_bursts()
        time.sleep(10)

if __name__ == "__main__":
    # Logging
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    metrics = threading.Thread(target=write_metrics, args=(), daemon=True)
    burst = threading.Thread(target=burst, args=(), daemon=True)
    # Start threads
    metrics.start()
    burst.start()

    # Join threads
    metrics.join()
    burst.join()
