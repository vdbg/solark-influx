

import asyncio
from datetime import datetime, timedelta, timezone
import logging
import platform
import sys
import time


import logging
from config import Config
from influx import InfluxConnector
from solark import SolarkConnector
from datetime import datetime

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

SUPPORTED_PYTHON_MAJOR = 3
SUPPORTED_PYTHON_MINOR = 11

if sys.version_info < (SUPPORTED_PYTHON_MAJOR, SUPPORTED_PYTHON_MINOR):
    raise Exception(
        f"Python version {SUPPORTED_PYTHON_MAJOR}.{SUPPORTED_PYTHON_MINOR} or later required. Current version: {platform.python_version()}."
    )

try:
    config = Config("config.toml", "solark_influx").load()
    main_conf = config["main"]
    logging.getLogger().setLevel(logging.getLevelName(main_conf["log_verbosity"]))
    sleep_time_seconds = main_conf["loop_minutes"] * 60
    logging.debug(f"CONFIG: {config}")

    solarkConnector = SolarkConnector(config["solark"])
    influxConnector = InfluxConnector(config["influx"])

    while True:
        try:
            measurement = influxConnector.measurement
            to_time_utc = datetime.now(timezone.utc)
            from_time_utc = influxConnector.get_last_recorded_time_utc(
                solarkConnector.max_days, to_time_utc, measurement
            )

            while from_time_utc <= to_time_utc:
                logging.info(f"Querying Sol-Ark for {from_time_utc}...")
                ret = solarkConnector.get_data(from_time_utc, measurement)
                if ret:
                    influxConnector.add_samples(ret)
                from_time_utc += timedelta(days=1)
        except Exception as e:
            logging.exception(e)

        if not sleep_time_seconds:
            exit(0)

        time.sleep(sleep_time_seconds)

except Exception as e:
    logging.exception(e)
    exit(1)