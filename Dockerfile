FROM python:3.9-buster
COPY . .
RUN pip3 install influxdb-client[ciso]
CMD [ "python3", "-u", "./Bridge_Jeedom_InfluxDB.py"]