from influxdb_client.client.influxdb_client import InfluxDBClient
from  influxdb_client.client.flux_table import TableList
import logging
from datetime import datetime, timedelta

class InfluxConnector:
    def __init__(self, influx_conf: dict):
        self.bucket: str = influx_conf["bucket"]
        self.token: str = influx_conf["token"]
        self.org: str = influx_conf["org"]
        self.url: str = influx_conf["url"]
        self.measurement: str = influx_conf["measurement"]
        self.no_op: bool = influx_conf["no_op"]
        logging.debug(f"Influx conf: url={self.url};bucket={self.bucket};org={self.org};no-op={self.no_op}")

    def get_last_recorded_time_utc(self, max_days: int, to_time: datetime, measurement: str) -> datetime:
        if self.no_op:
            logging.warning("No-op mode, returning 1 day prior.")
            return to_time - timedelta(days=1)
        
        query = f'from(bucket: "{self.bucket}") |> range(start: -{max_days}d) |> filter(fn: (r) => r._measurement == "{measurement}") |> last()'
        result = self.__run_query(query)
        results = list(result)

        if len(results) == 0:
            logging.info(f"Found no records dated less than {max_days} days(s) in influx bucket {self.bucket} measurement {measurement}.")
            return to_time - timedelta(days=max_days)

        fluxtable = results[-1]
        fluxrecord = fluxtable.records[-1]
        fluxtime = fluxrecord.get_time()

        return fluxtime

    def __get_client(self) -> InfluxDBClient:
        return InfluxDBClient(url=self.url, token=self.token, org=self.org, debug=False)

    def add_samples(self, records) -> None:
        if not records:
            return
        logging.info(f"Importing {len(records)} record(s) to influx")
        logging.debug(records)
        if self.no_op:
            logging.warning("No-op mode, records not imported.")
            return
        with self.__get_client() as client:
            with client.write_api() as write_api:
                write_api.write(bucket=self.bucket, record=records)


    def __run_query(self, query: str) -> TableList:
        logging.debug(f"Running influx query: {query}")
        with self.__get_client() as client:
            query_api = client.query_api()
            return query_api.query(query)
