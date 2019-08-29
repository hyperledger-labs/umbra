import logging
from umbra_orch.operator import Operator

logger = logging.getLogger(__name__)


class Manager:
    def __init__(self, loop, conf, exit_call):
        self.loop = loop
        self.conf = conf
        self.exit_call = exit_call
        self.operator = Operator(conf, loop, exit_call)
        self.callbacks = {
            "config": self.on_config,
            "built": self.on_built,
            "metrics": self.on_metrics,
            "events": self.on_events,
        }
        self.run_config = None
        self.run_config_info = None
        logger.info("Manager started")

    def callback(self):
        callback = "http://" + self.conf.host + ":" + self.conf.port + "/"
        return callback
    
    # must return list
    def workflow(self, data):
        data_type = data.get("type", None)
        if data_type in self.callbacks:
            call = self.callbacks.get(data_type)
            outputs = call(data)
            return outputs
        return []
    
    def on_config(self, data):
        logger.info("config")
        logger.info(data)
        self.run_config = data
        scenario = data.get("scenario")
        entrypoint = data.get("orchestration").get("entrypoint")

        data = {
            "type":"deploy",
            "request": "start",
            "continuous": False,
            "scenario": scenario,
            "callback": self.callback()
        }

        msg = {
            "to": entrypoint,
            "data": data,
        }
        return [msg]

    def on_built(self, data):
        logger.info("built")
        logger.info(data)
        self.run_config_info = data.get("data")
        scenario = self.run_config.get("scenario")
        self.operator.schedule(scenario, self.run_config_info)        
        
    def on_metrics(self, data):
        logger.info("metrics")
        logger.info(data)

    def on_events(self, data):
        logger.info("events")
        self.operator.events(data)      
        # logger.info(data)