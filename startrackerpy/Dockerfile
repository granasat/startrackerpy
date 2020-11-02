# Use the Python3.7.2 image
FROM arm32v7/python:3.7.7-buster

# Set the working directory to /app
WORKDIR /app

RUN echo "[global]" > /etc/pip.conf && \
        echo "extra-index-url=https://www.piwheels.org/simple/" >> /etc/pip.conf && \
        echo "deb http://mirror.de.leaseweb.net/raspbian/raspbian/ buster main contrib non-free rpi" >> /etc/apt/sources.list && \
        echo "deb https://archive.raspberrypi.org/debian/ buster main ui" >> /etc/apt/sources.list && \
        apt-key adv --keyserver hkp://pool.sks-keyservers.net:80 --recv-keys 9165938D90FDDD2E

RUN apt-key adv --keyserver hkp://pool.sks-keyservers.net:80 --recv-keys 82B129927FA3303E

RUN apt update && \
        apt install -y liblapack-dev libhdf5-103 \
        libatlas-base-dev libjasper-dev libavcodec-dev \
        libavformat-dev libswscale-dev libqtgui4 libqt4-test \
        libraspberrypi-bin libv4l-dev

# Set timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Madrid /etc/localtime

# Copy requirements file
ADD requirements.txt /requirements.txt

# Install the dependencies
RUN pip install -r /requirements.txt

# run the command to start uWSGI
CMD ["uwsgi", "--wsgi-disable-file-wrapper", "app.ini"]
