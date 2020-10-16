import logging
import aiohttp
import asyncio
import copy

from google.protobuf import json_format
from influxdb import InfluxDBClient

from umbra.common.protobuf.umbra_pb2 import Status
from umbra.broker.visualization import dashboard_template, panels_template


logger = logging.getLogger(__name__)


class GraphanaInterface:
    def __init__(self):
        self._ds_ids = 1
        self._datasources = {}
        self._dashboards = {}
        self._dashboard_on = False
        self._dashboard_version = 0
        self._dashboard_panel_ids = 1
        self._dashboard_panels = []

    def graphana_datasource_url(self, address):
        port = str(3000)
        suffix = "/api/datasources"
        url = "http://" + address + ":" + port + suffix
        return url

    def graphana_dashboad_url(self, address, uid=None):
        port = str(3000)

        if uid:
            suffix = "/api/dashboards/uid/{uid}".format(uid=uid)
        else:
            suffix = "/api/dashboards/db"

        url = "http://" + address + ":" + port + suffix
        return url

    async def post(self, user, password, url, data):
        async with aiohttp.ClientSession() as session:

            auth = aiohttp.BasicAuth(user, password)

            async with session.post(url, auth=auth, json=data) as resp:
                reply = await resp.json()
                stats = resp.status

                logger.debug(
                    f"Post sent to graphana {url} - stats {stats} - response {reply}"
                )
                return reply

        return None

    async def get(self, user, password, url):
        async with aiohttp.ClientSession() as session:

            auth = aiohttp.BasicAuth(user, password)

            async with session.get(url, auth=auth) as resp:
                reply = await resp.json()
                stats = resp.status

                logger.debug(
                    f"Get sent to graphana {url} - stats {stats} - response {reply}"
                )

                return reply

        return None

    def format_datasource(
        self, influx_url, influx_database, influx_user, influx_password
    ):
        ds_id = self._ds_ids
        data = {
            "id": ds_id,
            "orgId": 1,
            "name": influx_database,
            "type": "influxdb",
            "typeLogoUrl": "public/app/plugins/datasource/influxdb/img/influxdb_logo.svg",
            "access": "proxy",
            "url": influx_url,
            "password": influx_password,
            "user": influx_url,
            "database": influx_database,
            "basicAuth": False,
            "isDefault": False,
            "jsonData": {"httpMode": "GET"},
            "readOnly": False,
        }
        self._ds_ids += 1

        return data

    async def add_datasource(self, info):
        address = info.get("address")
        database = info.get("database")

        graphana_url = self.graphana_datasource_url(address)

        influx_url = "http://" + address + ":" + str(8086)
        influx_user = influx_password = "umbra-influxdb"
        influx_database = database

        data = self.format_datasource(
            influx_url, influx_database, influx_user, influx_password
        )

        graphana_user = graphana_password = "umbra-graphana"
        await self.post(graphana_user, graphana_password, graphana_url, data)

    async def get_datasources(self, info):
        address = info.get("address")

        graphana_url = self.graphana_datasource_url(address)
        graphana_user = graphana_password = "umbra-graphana"
        reply = await self.get(graphana_user, graphana_password, graphana_url)
        return reply

    def format_dashboard(self, dashboard_template):
        dashboard = copy.deepcopy(dashboard_template)

        dashboard["id"] = None
        data = {"dashboard": dashboard, "folderId": 0, "overwrite": False}
        return data

    def format_dashboard_panels(self, dashboard_template, panels_template, environment):
        panels = copy.deepcopy(panels_template)
        dashboard = copy.deepcopy(dashboard_template)

        for panel in panels:
            title = panel.get("title")
            panel["title"] = title.format(environment=environment)
            panel["datasource"] = environment
            panel["id"] = self._dashboard_panel_ids
            panel["gridPos"]["y"] = self._dashboard_panel_ids
            self._dashboard_panel_ids += 1

        self._dashboard_panels.extend(panels)
        dashboard["panels"] = self._dashboard_panels
        dashboard["id"] = 1
        dashboard["version"] = self._dashboard_version

        data = {"dashboard": dashboard, "folderId": 0, "overwrite": False}
        return data

    async def add_dashboard(self, info):
        address = info.get("address")
        environment = info.get("database")

        graphana_user = graphana_password = "umbra-graphana"
        graphana_url = self.graphana_dashboad_url(address)

        if not self._dashboard_on:
            data = self.format_dashboard(dashboard_template)
            reply = await self.post(
                graphana_user, graphana_password, graphana_url, data
            )

            if reply.get("status") == "success":
                logger.info("Dashboard Created")
                self._dashboard_on = True
                self._dashboard_version += 1
            else:
                logger.info("Dashboard Not Created")
                self._dashboard_on = False

        if self._dashboard_on:
            if environment not in self._dashboards:

                data = self.format_dashboard_panels(
                    dashboard_template, panels_template, environment
                )

                reply = await self.post(
                    graphana_user, graphana_password, graphana_url, data
                )

                if reply.get("status") == "success":
                    logger.info(f"Environment {environment} dashboard panels created")
                    self._dashboards[environment] = True
                    self._dashboard_version += 1

                else:
                    logger.info(
                        f"Environment {environment} dashboard panels not created"
                    )
                    self._dashboards[environment] = False
            else:
                logger.info(
                    f"Environment {environment} dashboard panels not created - already existent"
                )

    async def get_dashboard(self, info, uid="umbra"):
        address = info.get("address")
        graphana_url = self.graphana_dashboad_url(address, uid=uid)
        graphana_user = graphana_password = "umbra-graphana"
        reply = await self.get(graphana_user, graphana_password, graphana_url)
        return reply


class Collector:
    def __init__(self, info):
        self.info = info
        self.address = None
        self.influx_client = None
        self.databases = {}
        self._is_connected = False
        self._gi = GraphanaInterface()
        self._lock = asyncio.Lock()
        self.set_address()
        self.connect()

    def set_address(self):
        address = self.info.get("address")
        host = address.split(":")[0]
        self.address = host

    def connect(self):
        host = self.address
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
        logger.debug(f"Databases in influx {dbs}")
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

    async def parse_message(self, message):
        data = []

        source = message["source"]
        environment = message["environment"]

        if environment not in self.databases:
            self.init_db(environment)
            logger.debug(f"New database: {environment}, {source}")

            await self.datasource(environment)
            logger.debug(f"New datasource: {environment}")

        self.databases[environment] = source

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

            tags = measurement.get("tags")
            tags["environment"] = environment

            frmt_measurement = {
                "measurement": measurement.get("name"),
                "tags": tags,
                "fields": frmt_fields,
            }

            logger.debug(
                f"Parsing measurement - database {environment} - measurement {measurement.get('name')}"
            )

            data.append(frmt_measurement)

        return data, environment

    async def datasource(self, database):
        async with self._lock:
            info = {
                "address": self.address,
                "database": database,
            }

            await self._gi.add_datasource(info)
            await self._gi.add_dashboard(info)

    async def collect(self, message):
        msg = json_format.MessageToDict(message, preserving_proto_field_name=True)

        logger.debug(f"Collected message")
        # logger.debug(f"{msg}")

        data, database = await self.parse_message(msg)
        ack, err = self.write(data, database)

        reply = Status(info=str(ack).encode("utf-8"), error=err)
        return reply
