import base64
import time
import zipfile
import os
import pathlib
import cv2
# import scipy.io
from server import app
from flask import render_template, jsonify, request, send_file
from server.cam import Cam
from server.metrics import Metrics
from server.sensors import DS1621, LSM303, CPU_SENSOR
from server.db import Db
from io import BytesIO


CAM = Cam()
# Current file Path
FILE_PATH = pathlib.Path(__file__).parent.absolute()
DB = Db(f"{FILE_PATH}/data/granasat.db")


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
    _, frame = CAM.read()
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
    # Give some time to set the camera parameters
    time.sleep(1.5)
    _, frame = CAM.read()
    cv2.imwrite('test.tiff', frame)
    CAM.lock_release()

    return "Done"


@app.route("/get-camera-params")
def get_camera_params():
    """ Returns a JSON with the current parameters of the camera.
    """
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
        'accelerometer': lsm_sensor.read_accel(),
        'magnetometer': lsm_sensor.read_mag()
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

    if int(duration) / int(interval) > 600:
        return jsonify({
            'result': 'error',
            'id': -1,
            'msg': 'Maximum numer of frames(600) exceeded'
        })

    # Add a row to queue the burst
    row_id = DB.insert_burst(duration, interval, brightness, gamma,
                             gain, exposure)

    return jsonify({
        'result': 'ok',
        'id': row_id,
        'msg': 'The burst has been queued'
    })


@app.route("/get-bursts")
def get_bursts():
    """Returns an html table with the burst retrieved from the DB.
    """
    bursts = DB.get_bursts()
    return render_template('bursts.html', bursts=bursts)


@app.route("/download-burst")
def download_burst():
    """Returns an html table with the burst retrieved from the DB.
    """
    images_path = "server/data/bursts"
    burst_id = int(request.args.get('burstId'))
    burst_format = request.args.get('format')
    burst = DB.get_burst(burst_id)
    files = int(burst['duration'] / burst['interval'])

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for i in range(1, files+1):
            image_name = "{}/{}_{}.tiff".format(images_path, burst_id, i)
            image_data = cv2.imread(image_name)
            if burst_format == "jpeg":
                _, image_data = cv2.imencode(".jpeg", image_data)
            elif burst_format == "mat":
                pass
            image_bytes = image_data.tobytes()
            data = zipfile.ZipInfo("{}_{}.{}".format(burst_id, i, burst_format))
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(data, image_bytes)
    memory_file.seek(0)
    attachment_name = "burst_{}_{}.zip".format(burst_id, burst_format)

    return send_file(memory_file, attachment_filename=attachment_name,
                     as_attachment=True)


@app.route("/delete-burst")
def delete_burst():
    images_path = "server/data/bursts"
    burst_id = int(request.args.get('burstId'))
    burst = DB.get_burst(burst_id)
    files = int(burst['duration'] / burst['interval'])
    for i in range(1, files+1):
        image_name = "{}/{}_{}.tiff".format(images_path, burst_id, i)
        os.remove(image_name)
    DB.delete_burst(burst_id)

    return "Done"
