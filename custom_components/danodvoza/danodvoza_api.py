from datetime import datetime, timedelta, date
import json
import aiohttp
import logging
from dateutil import parser

from .const import SETUP_ADDRESS_ARRAY

_LOGGER = logging.getLogger(__name__)

class DanOdvozaApi:

    def __init__(self, address, session):
        self.address = address
        self.cache = None
        self.cache_date = None
        self.cacheOK = False
        self.last_data = None
        self.first_load = None


    async def validate_address(self):
        """Validate the token by using the getMeterReadings method."""
        try:
            validate = await self.get_data()
            return validate is not None
        except Exception as e:
            _LOGGER.error(f"Error during address validation: {e}")
            return False


    async def get_address_readings(self):
        url = 'https://www.simbio.si/sl/moj-dan-odvoza-odpadkov'
        headers = {"accept": "application/json"}
        data = { "query": self.address }
        try:
            async with self.session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug(data)
                    return data
                else:
                    _LOGGER.error(f"HTTP error {response.status} when getting address readings.")
                    return None
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error making API call: {e}")
            return None


    async def get_data(self):
        """Get or update cache."""

        # Update only at each hour or on empty last_data
        current_minute = datetime.now().minute
        if self.last_data is None or current_minute in [0]:

            #Update Cache
            cache = await self.get_cache()

            sensor_return = {}

            if cache is None:
                _LOGGER.debug("Data not received! Returning empty data.")

            else:
                sensor_return.update(self.sensors_output(cache.get('data'), json.loads(SETUP_ADDRESS_ARRAY)))

            self.last_data = sensor_return
            return sensor_return
        else:
            _LOGGER.debug("Not time to update, returning last good data.")
            return self.last_data


    async def get_cache(self):
        """Update cache from API if necessary"""
        if self.cache is None or self.cache_date != datetime.today().date():
            _LOGGER.debug("Cache has no pre-stored data. Refreshing from API...")

            # Connect to API asynchronously
            address_readings = await self.get_address_readings()


            if address_readings is None:
                _LOGGER.error("No data received! Check user settings.")
                return None


            self.cache = {}
            # Ensure the results are lists or have a length before attempting to access them
            if (isinstance(address_readings, list) and address_readings):
                self.cache.update({"data": address_readings })
            else:
                #return empty list
                self.cache.update({"data": [] })
                _LOGGER.debug("Searched address list is empty. Possible wrong address. Will continue with empty list.")

        else:
            _LOGGER.debug("Cache has stored data. Will use self.cache.")
        return self.cache


    def sensors_output(self, data, setup):
        """Organize sensors and calculate values."""
        sensor_output = {}

        if not data:
            #return 0 instead od unavailable
            for item in json.loads(SETUP_ADDRESS_ARRAY):
                sensor_output[item["sensor"]] = "0.0"

        else:
            for block in data:
                next_mko = block.get("next_mko", "")
                next_emb = block.get("next_emb", "")
                next_bio = block.get("next_emb", "")


                sensor_output['next_mko'] = next_mko
                sensor_output['next_emb'] = next_emb
                sensor_output['next_bio'] = next_bio

        return sensor_output
        
        
