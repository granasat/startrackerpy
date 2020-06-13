import time
from datetime import datetime
from sensors import CPU_SENSOR, DS1621, LSM303
from influxdb import InfluxDBClient
from db import Db
from cam import Cam
from pathlib import Path
import multiprocessing
import threading
import logging
import cv2

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
    db = Db("data/granasat.db")
    cam = Cam()
    interval = 5
    images_path = "data/bursts"
    Path(images_path).mkdir(parents=True, exist_ok=True)

    while True:
        bursts = db.get_bursts()
        for burst in bursts:
            if burst['finished'] is not None:
                continue

            logging.debug('Starting burst {}'.format(burst['id']))
            frames = int(burst['duration'] / burst['interval'])
            cam_params = {
                'brightness': int(burst['brightness']),
                'gamma': int(burst['gamma']),
                'gain': int(burst['gain']),
                'exposure': int(burst['exposure']),
            }
            cam.lock_acquire()
            cam.set_camera_params(cam_params)
            for i in range(1, frames+1):
                ret, frame = cam.read()
                img_name = "{}/{}_{}.TIFF".format(images_path, burst['id'], i)
                cv2.imwrite(img_name, frame)
                db.update_burst_progress(burst['id'], int(i*100/frames))
                time.sleep(burst['interval'])
            cam.lock_release()

        time.sleep(interval)

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
