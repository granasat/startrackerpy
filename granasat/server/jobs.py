import time
import threading
import logging
from pathlib import Path
from datetime import datetime
import cv2
from influxdb import InfluxDBClient
from server.sensors import CPU_SENSOR, DS1621, LSM303
from server.db import Db
from server.cam import Cam


class Jobs:
    def __init__(self, interval: int = 5):
        self._interval = interval

    def __write_cpu_metrics(self, influx_cli: InfluxDBClient,
                          cpu_sensor: CPU_SENSOR) -> None:
        """Write metrics of the current CPU temperature.

        :param influx_cli: InfluxDBClient to write metrics to.
        :param cpu_sensor: CPU_SENSOR to read the temp from.
        """
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

    def __write_cam_temp_metrics(self, influx_cli: InfluxDBClient,
                               ds_sensor: DS1621) -> None:
        """Write metrics of the current camera temperature.

        :param influx_cli: InfluxDBClient to write metrics to.
        :param ds_sensor: camera sensor to read the temp from.
        """
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

    def __write_accelerometer_metrics(self, influx_cli: InfluxDBClient,
                                    lsm_sensor: LSM303) -> None:
        """Write metrics of the current accelerometer values.

        :param influx_cli: InfluxDBClient to write metrics to.
        :param lsm_sensor: sensor to read the values from.
        """
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

    def __write_magnetometer_metrics(self, influx_cli: InfluxDBClient,
                                   lsm_sensor: LSM303) -> None:
        """Write metrics of the current magnetometer values.

        :param influx_cli: InfluxDBClient to write metrics to.
        :param lsm_sensor: sensor to read the values from.
        """
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

    def __write_metrics(self) -> None:
        """Write all the metrics in a loop every `interval` seconds.
        """
        logging.info("Starting metrics thread")
        cpu_sensor = CPU_SENSOR()
        ds_sensor = DS1621(1, 0x48)
        lsm_sensor = LSM303()
        influx_cli = InfluxDBClient('influxdb', 8086, 'admin', '12345',
                                    'granasat')

        try:
            while True:
                self.__write_cpu_metrics(influx_cli, cpu_sensor)
                self.__write_cam_temp_metrics(influx_cli, ds_sensor)
                self.__write_accelerometer_metrics(influx_cli, lsm_sensor)
                self.__write_magnetometer_metrics(influx_cli, lsm_sensor)
                time.sleep(self._interval)

        except KeyboardInterrupt:
            print("Manual break by user")

    def __check_bursts(self) -> None:
        """ Check for burst to be processed every `interval` seconds.
        """
        logging.info("Starting burst thread")
        FILE_PATH = Path(__file__).parent.absolute()
        db = Db(f"{FILE_PATH}/data/granasat.db")
        cam = Cam()
        images_path = f"{FILE_PATH}/data/bursts"
        Path(images_path).mkdir(parents=True, exist_ok=True)

        while True:
            bursts = db.get_bursts()
            for burst in bursts:
                if burst['finished'] is not None:
                    continue

                logging.debug("Starting burst {}".format(burst['id']))
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
                    _, frame = cam.read()
                    img_name = "{}/{}_{}.tiff".format(images_path,
                                                      burst['id'], i)
                    cv2.imwrite(img_name, frame)
                    db.update_burst_progress(burst['id'], int(i*100/frames))
                    time.sleep(burst['interval'])
                cam.lock_release()

            time.sleep(self._interval)

    def run(self) -> None:
        """Main function to start threads.
        """
        # Logging
        logging_format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=logging_format,
                            level=logging.INFO,
                            datefmt="%H:%M:%S")
        metrics = threading.Thread(target=self.__write_metrics, args=(),
                                   daemon=True)
        burst = threading.Thread(target=self.__check_bursts, args=(),
                                 daemon=True)
        # Start threads
        metrics.start()
        burst.start()

        # Join threads
        metrics.join()
        burst.join()
