import cv2
import base64
import time
# import scipy.io
from server import app, cam
from flask import render_template, jsonify, request
from server.cam import Cam
from server.metrics import Metrics
from server.sensors import DS1621, LSM303, CPU_SENSOR
from server.db import Db


CAM = Cam()
DB = Db("server/data/granasat.db")

@app.route("/")
def index():
    """ Returns the index html template
    """
    return render_template('index.html')


@app.route("/current-frame")
def current_frame():
    """ Returns a base64 string with the data of an image.
    The image is taken when the function is called.
    """
    # Get camera parameters
    cam_params = {
        'brightness': int(request.args.get('brightness')),
        'gamma': int(request.args.get('gamma')),
        'gain': int(request.args.get('gain')),
        'exposure': int(request.args.get('exposure')),
    }

    CAM.lock_acquire()
    CAM.set_camera_params(cam_params)
    ret, frame = CAM.read()
    CAM.lock_release()
    # Resize image to 1024x768
    frame = cv2.resize(frame, (1024, 768), cv2.INTER_AREA)
    _, im_arr = cv2.imencode('.jpg', frame)
    im_bytes = im_arr.tobytes()
    im_b64 = base64.b64encode(im_bytes).decode("ascii")

    return jsonify({
        'b64_img': im_b64,
    })
    # return send_file(
    #     io.BytesIO(im_b64),
    #     mimetype='image/jpeg',
    #     as_attachment=True,
    #     attachment_filename='current.jpg')

@app.route("/current-frame-tiff")
def current_frame_tiff():
    """ Returns a base64 string with the data of an image.
    The image is taken when the function is called.
    """
    # Get camera parameters
    cam_params = {
        'brightness': int(request.args.get('brightness')),
        'gamma': int(request.args.get('gamma')),
        'gain': int(request.args.get('gain')),
        'exposure': int(request.args.get('exposure')),
    }
    CAM.lock_acquire()
    CAM.set_camera_params(cam_params)
    # Given some time to set the camera parameters
    time.sleep(1.5)
    ret, frame = CAM.read()
    cv2.imwrite('test.TIFF', frame)
    CAM.lock_release()

    return "Done"


@app.route("/get-camera-params")
def get_camera_params():
    """ Returns a JSON with the current parameters of the camera.
    """
    # TODO check if it is possible without lock
    params = CAM.get_camera_params()

    return jsonify(params)


@app.route("/get-monitor-data")
def get_monitor_data():
    """ Returns a JSON with data to be monitored;
    CPU temp,

    """
    ds_sensor = DS1621(1, 0x48)
    ds_sensor.wake_up()
    lsm_sensor = LSM303()
    cpu_sensor = CPU_SENSOR()
    camera_temp = round(float(ds_sensor.read_degreesC_hiRes_oneshot()), 1)

    data = {
        'cpu-temp': str(cpu_sensor.read_temp()),
        'camera-temp': camera_temp,
        'accelerometer': lsm_sensor.read_accel(string=True),
        'magnetometer': lsm_sensor.read_mag(string=True)
    }

    return jsonify(data)


@app.route("/get-metrics/<minutes>")
def get_metrics(minutes):
    """ Returns metrics from influxdb for the last
    X minutes.
    """
    metrics = Metrics.get_metrics(from_time=int(minutes))

    return jsonify(metrics)


@app.route("/queue-burst")
def queue_burst():
    """ Queues a burst of images.
    """
    duration = request.args.get('duration')
    interval = request.args.get('interval')
    brightness = int(request.args.get('brightness'))
    gamma = int(request.args.get('gamma'))
    gain = int(request.args.get('gain'))
    exposure = int(request.args.get('exposure'))

    if duration / interval > 600:
        return jsonify({
            'result': 'error',
            'id': -1,
            'msg': 'Maximum numer of frames(600) exceeded'
        })

    # Add a row to queue the burst
    id = DB.insert_burst(duration, interval, brightness, gamma, gain, exposure)

    return jsonify({
        'result': 'ok',
        'id': id,
        'msg': 'The burst has been queued'
    })
