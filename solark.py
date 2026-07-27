from zoneinfo import ZoneInfo

from pysolark import SolArkClient, SolArkSeriesCollection, SolArkTokenExpiredError
import logging
from datetime import datetime, date

from reactivex import catch

class SolarkConnector:
    def __init__(self, solark_conf: dict) -> None:
        self.username: str = solark_conf["username"]
        self.password: str = solark_conf["password"]
        plant_id: int = solark_conf["plant_id"]
        if plant_id <= 0:
            raise Exception(f"Invalid plant_id {plant_id}. Must be a positive integer.")
        self.max_days: int = solark_conf["max_days"]
        if self.max_days <= 0:
            raise Exception(f"Invalid max_days {self.max_days}. Must be a positive integer.")
        self.client = SolArkClient(username=self.username, password=self.password)
        self.client.login()
        self.plant = self.client.get_plant(plant_id)

    def __get_data(self, day: str, measurement: str, retry: bool) -> SolArkSeriesCollection:
        try:
            if measurement == "plant_energy":
                return self.client.get_plant_energy(self.plant.plant_id, period="day", date=day)
            if measurement == "plant_power":
                return self.client.get_plant_power(self.plant.plant_id, period="day", date=day)
        except SolArkTokenExpiredError as e:
            if retry:
                logging.warning(f"Sol-Ark token expired, re-logging in and retrying...")
                self.client.login()
                return self.__get_data(day, measurement, False)
            
            raise Exception(f"Sol-Ark token expired and retry failed: {e}")
        raise Exception(f"Invalid measurement {measurement}. Must be either 'plant_energy' or 'plant_power'.")

    def get_data(self, day: date, measurement: str) -> list[dict]:
        try:
            day_str = day.strftime("%Y-%m-%d")
            series_collection: SolArkSeriesCollection = self.__get_data(day_str, measurement, True)
            if not series_collection:
                logging.error(f"No data returned from Sol-Ark for {day_str} using {measurement}.")
                return []
            
            logging.info(f"Successfully downloaded {measurement} for {day_str}")
            # NOTES: 
            # 1. the Sol-Ark API returns a time of day, e.g. "00:15" for quarter past midnight. Therefore, we need to combine that
            # with the date to get a full timestamp for InfluxDB
            # 2. the Sol-Ark API returns local time, while InfluxDB expects UTC time, so we need to convert the local time to UTC. 
            # This is done by using the date and time of day to create a datetime object, and then converting that to UTC.
            self.plant.timezone
            # dict of time, and all fields and values for that time. Because we want to import all fields for a given time at once
            results = {}
            for s in series_collection.series:
                if not s.label:
                    logging.warning(f"Series label is missing for series with unit {s.unit}!")
                    continue
                for r in s.records:
                    result = results.get(r.time, {})
                    if not result:
                        # r.time is time of day, e.g. "00:15" for quarter midnight
                        result_datetime = datetime.fromisoformat(f"{day_str} {r.time}")
                        if self.plant.timezone and self.plant.timezone.code:
                            result_datetime = result_datetime.replace(tzinfo=ZoneInfo(self.plant.timezone.code))
                            result_datetime = result_datetime.astimezone(ZoneInfo("UTC"))

                        result = {
                            "measurement": measurement,
                            "tags": {"plant_id": self.plant.plant_id, "plant_name": self.plant.name},
                            "fields": {},
                            "time": result_datetime
                        }
                        results[r.time] = result

                    result["fields"][s.label] = r.value

            return list(results.values())
        except Exception as e:
            raise Exception(f"get_{measurement} failed: {e}")    



    
