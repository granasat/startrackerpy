import base64
import time
import zipfile
import os
import uuid
import logging
from io import BytesIO
from pathlib import Path
import cv2
from flask import render_template, jsonify, request, send_file
from server import app, catalog
from server.cam import Cam
from server.metrics import Metrics
from server.sensors import DS1621, LSM303, CPU_SENSOR
from server.db import Db
from server.startracker.image import ImageUtils


CAM = Cam()
# Current file Path
FILE_PATH = Path(__file__).parent.absolute()
DB = Db(f"{FILE_PATH}/data/startrackerpy.db")


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
    images_path = f"{FILE_PATH}/data/images"
    # Get camera parameters
    cam_params = {
        'brightness': int(request.args.get('brightness')),
        'gamma': int(request.args.get('gamma')),
        'gain': int(request.args.get('gain')),
        'exposure': int(request.args.get('exposure')),
    }

    CAM.lock_acquire()
    CAM.set_camera_params(cam_params)
    time.sleep(1)
    _, frame = CAM.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    CAM.lock_release()
    Path(images_path).mkdir(parents=True, exist_ok=True)
    uid = uuid.uuid1()
    _, im_arr = cv2.imencode('.jpg', frame)
    cv2.imwrite(f"{images_path}/{uid}.jpg", frame)
    im_bytes = im_arr.tobytes()
    im_b64 = base64.b64encode(im_bytes).decode("ascii")

    return jsonify({
        'b64_img': im_b64,
        'uuid': f"{uid}.jpg",
    })


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
    """Deletes the burst id given as parameter, this includes all the
    images taken by that burst."""
    images_path = "server/data/bursts"
    burst_id = int(request.args.get('burstId'))
    burst = DB.get_burst(burst_id)
    files = int(burst['duration'] / burst['interval'])
    for i in range(1, files+1):
        try:
            image_name = "{}/{}_{}.tiff".format(images_path, burst_id, i)
            os.remove(image_name)
        except Exception as e:
            print(e)
    DB.delete_burst(burst_id)

    return "Done"


@app.route("/upload-image", methods=["POST"])
def upload_image():
    """Saves the image upload by the user and returns its base64 string
    to show it in the DOM"""
    images_path = f"{FILE_PATH}/data/images"
    Path(images_path).mkdir(parents=True, exist_ok=True)
    image = request.files['image']
    image_ext = image.filename.rsplit(".", 1)[1]
    uid = uuid.uuid1()
    image.save(f"{images_path}/{uid}.{image_ext}")
    saved_image = cv2.imread(f"{images_path}/{uid}.{image_ext}")
    _, im_arr = cv2.imencode('.jpg', saved_image)
    im_bytes = im_arr.tobytes()
    img_b64 = base64.b64encode(im_bytes).decode("ascii")

    return jsonify({
        'b64_img': img_b64,
        'uuid': f"{uid}.{image_ext}",
    })


@app.route("/process-image")
def process_image():
    """Process the given image to find stars and returns
    the image with the associated data"""
    auto_threshold = request.args.get('auto_threshold')
    label_guide_stars = request.args.get('label_guide_stars')
    images_path = f"{FILE_PATH}/data/images"
    response = {}
    response['results'] = {}
    uid = request.args.get('uuid')
    image = cv2.imread(f"{images_path}/{uid}")
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray_img, (3, 3), 0)

    # Check if auto threshold was selected
    logging.warning(auto_threshold)
    if auto_threshold == "true":
        threshold = ImageUtils.get_threshold(blurred, 170)
        msg = {'type': 'info', 'msg': f'Automatic threshold selected: {threshold}'}

    else:
        threshold = int(request.args.get('threshold'))
        msg = {'type': 'info', 'msg': f'Threshold selected by user input: {threshold}'}

    response['results']['threshold'] = msg

    # Get the threshold image
    thresh_image = cv2.threshold(blurred, threshold, 255, cv2.THRESH_BINARY)[1]
    # Convert to bytes and encode in base64 to send it in the response
    _, im_arr = cv2.imencode('.jpg', thresh_image)
    im_bytes = im_arr.tobytes()
    img_b64 = base64.b64encode(im_bytes).decode("ascii")
    response['b64_thresh_img'] = img_b64

    # Get possible image stars
    stars = ImageUtils.get_image_stars(thresh_image, gray_img)
    # Find pattern if there are at least 4 possible images
    pattern = []
    if len(stars) >= 4:
        pattern = catalog.find_stars_pattern(stars[0:4], err=0.010)
        _, im_arr = cv2.imencode('.jpg', image)
        im_bytes = im_arr.tobytes()
        img_b64 = base64.b64encode(im_bytes).decode("ascii")
        response['b64_img'] = img_b64
        msg = {'type': 'info', 'msg': f'Possible stars found in the image: {len(stars)}'}
    else:
        msg = {'type': 'info', 'msg': f'Possible stars found in the image: {len(stars)}'}
    response['results']['stars'] = msg

    # Histogram
    hist = cv2.calcHist([blurred], [0], None, [256], [0, 256])
    response['hist'] = hist.tolist()

    # If a pattern was found
    if len(pattern) > 0:
        response['pattern'] = True
        # Get original image with pattern drawn
        ImageUtils.draw_pattern(image, pattern[0])
        # If draw extra guide Stars
        if label_guide_stars == "true":
            labeled = ImageUtils.draw_guide_stars(image, stars, pattern[0], max=10)
            msg = {'type': 'info', 'msg': f'Extra guide stars labeled: {labeled}'}
            response['results']['labeled'] = msg
        _, im_arr = cv2.imencode('.jpg', image)
        im_bytes = im_arr.tobytes()
        img_b64 = base64.b64encode(im_bytes).decode("ascii")
        response['pattern_points'] = img_b64
        msg = {'type': 'success', 'msg': f'Pattern found: {pattern[1]}'}
    else:
        msg = {'type': 'Error', 'msg': f'Pattern not found'}

    response['results']['pattern'] = msg

    return jsonify(response)
