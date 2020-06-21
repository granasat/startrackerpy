from server import influx_cli
from datetime import datetime, timedelta


class Metrics:
    """Class to fetch metrics from the InfluxDB defined in the server.
    """
    @staticmethod
    def get_cpu_metrics(from_time: int = 5) -> []:
        """Retrieve CPU metrics since the last `from_time` minutes.

        :param from_time: Amount of minutes to query metrics for.
        """
        start_time = datetime.now() - timedelta(minutes=from_time)
        query = "select degrees from cpu_temp where time > '{}';".format(
            start_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        result = influx_cli.query(query)

        return list(result.get_points('cpu_temp'))

    @staticmethod
    def get_cam_metrics(from_time: int = 5) -> []:
        """Retrieve Camera temperature metrics since the last `from_time`
        minutes.

        :param from_time: Amount of minutes to query metrics for.
        """
        start_time = datetime.now() - timedelta(minutes=from_time)
        query = "select degrees from cam_temp where time > '{}';".format(
            start_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        result = influx_cli.query(query)

        return list(result.get_points('cam_temp'))

    @staticmethod
    def get_accelerometer_metrics(from_time: int = 5) -> []:
        """Retrieve Accelerometer metrics since the last `from_time`
        minutes.

        :param from_time: Amount of minutes to query metrics for.
        """
        start_time = datetime.now() - timedelta(minutes=from_time)
        query = "select x,y,z from accelerometer where time > '{}';".format(
            start_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        result = influx_cli.query(query)

        return list(result.get_points('accelerometer'))

    @staticmethod
    def get_magnetometer_metrics(from_time: int = 5) -> []:
        """Retrieve Magnetometer metrics since the last `from_time`
        minutes.

        :param from_time: Amount of minutes to query metrics for.
        """
        start_time = datetime.now() - timedelta(minutes=from_time)
        query = "select x,y,z from magnetometer where time > '{}';".format(
            start_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        result = influx_cli.query(query)

        return list(result.get_points('magnetometer'))

    @staticmethod
    def get_metrics(from_time: int = 5) -> {}:
        """Retrieve all metrics since the last `from_time` minutes.

        :param from_time: Amount of minutes to query metrics for.
        """
        return {
            'cpu-temp': Metrics.get_cpu_metrics(from_time),
            'camera-temp': Metrics.get_cam_metrics(from_time),
            'accelerometer': Metrics.get_accelerometer_metrics(from_time),
            'magnetometer': Metrics.get_magnetometer_metrics(from_time)
        }
