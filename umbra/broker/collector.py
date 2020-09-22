import logging

from google.protobuf import json_format
from influxdb import InfluxDBClient

from umbra.common.protobuf.umbra_pb2 import Status


logger = logging.getLogger(__name__)


class Collector:
    def __init__(self, info):
        self.info = info
        self.influx_client = None
        self.sources = {}
        self._is_connected = False
        self.connect()

    def connect(self):
        host = "localhost"
        port = 8086
        user = "umbra-influxdb"
        password = "umbra-influxdb"
        dbname = "umbra"

        try:
            client = InfluxDBClient(host, port, user, password, dbname)
        except Exception as e:
            logger.debug(f"Could not connect to influx db - {repr(e)}")
            self._is_connected = False
        else:
            logger.debug(f"Connected to influx db")
            self.influx_client = client
            self._is_connected = True

    def dbs(self):
        dbs = self.influx_client.get_list_database()
        dbs = [db["name"] for db in dbs]
        return dbs

    def init_db(self, dbname):
        if dbname not in self.dbs():
            self.influx_client.create_database(dbname)

    def end_db(self, dbname):
        if dbname in self.dbs():
            self.influx_client.drop_database(dbname)

    def write(self, info, database):
        if not self._is_connected:
            self.connect()

        if self._is_connected:
            self.influx_client.write_points(
                info, database=database, time_precision="ms"
            )
            err = ""
            return True, err
        else:
            err = "Could not write points do DB - not connected"
            return False, err

    def parse_message(self, message):
        data = []

        source = message["source"]
        environment = message["environment"]

        if source not in self.sources:
            self.init_db(source)
            logger.debug(f"New database: {source}, {environment}")

        self.sources[source] = environment

        measurements = message.get("measurements", [])
        for measurement in measurements:
            frmt_measurement = {}

            fields = measurement.get("fields")
            frmt_fields = {}
            for f, v in fields.items():
                vvalue = v.get("value")
                vtype = v.get("type")

                if vtype == "int":
                    value = int(vvalue)
                elif vtype == "float":
                    value = float(vvalue)
                else:
                    value = str(vvalue)

                frmt_fields[f] = value

            frmt_measurement = {
                "measurement": measurement.get("name"),
                "tags": measurement.get("tags"),
                "fields": frmt_fields,
            }

            data.append(frmt_measurement)

        return data, source

    def collect(self, message):
        msg = json_format.MessageToDict(message, preserving_proto_field_name=True)

        data, database = self.parse_message(msg)
        ack, err = self.write(data, database)

        reply = Status(info=str(ack), error=err)
        return reply
