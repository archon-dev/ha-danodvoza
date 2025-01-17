from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.components.sensor import ENTITY_ID_FORMAT
import os
import json

from .const import DOMAIN, CONF_ADDRESS
from .danodvoza_api import DanOdvozaApi
import logging
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Dan Odvoza sensors dynamically from a config entry."""


    address = entry.data[CONF_ADDRESS]
    session = async_get_clientsession(hass)


    api = DanOdvozaApi(address, session)

    # Initialize the update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="danodvoza_sensor",
        update_method=api.get_data,
        update_interval=timedelta(seconds=3600),  # Adjust as necessary
    )

    # Fetch initial data
    await coordinator.async_refresh()

    # Store coordinator for reference in sensor entities
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Corrected part: Directly iterate over keys of coordinator.data
    sensors = [
        DanOdvozaSensor(coordinator, entry.entry_id, measurement, address, hass)
        for measurement in coordinator.data.keys()
    ]
    async_add_entities(sensors)


class DanOdvozaSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id, measurement_name, address, hass):


        super().__init__(coordinator)

        # Store address as an instance variable
        self.address = address

        current_ids = hass.states.async_entity_ids()
        entity_id = generate_entity_id( ENTITY_ID_FORMAT, f"{DOMAIN}_{measurement_name.lower()}", current_ids )

        self._attr_unique_id = f"{address}-{entity_id}"
        self._attr_name = f"Dan Odvoza {measurement_name.replace('_', ' ')}"
        self.measurement_name = measurement_name
        self._last_known_state = None

        self._attr_device_class = SensorDeviceClass.DATE
        self._attr_icon = ("mdi:trash-can")

            
    @property
    def device_info(self):
        """Return device information for grouping sensors under a device."""
        _LOGGER.debug(f"Setting up device info {self.address} .")
        return {
            "identifiers": {(DOMAIN, self.address)},  # Use the stored meter_id
            "name": "Dan Odvoza",
            "manufacturer": "Dan Odvoza",
            "model": {self.address},  # Include meter_id in the model
            "sw_version": self.get_version(),
            "entry_type": DeviceEntryType.SERVICE,  # Use enum instead of string
        }
    @property
    def state(self):
        """Return the state of the sensor."""
        data = self.coordinator.data.get(self.measurement_name)
        if data is not None:
            try:
                # Store the current data as the last known good state
                self._last_known_state = data
                return self._last_known_state
            except ValueError:
                pass

        return None

    # Get the version from the manifest.json
    def get_version(self):
        manifest_path = os.path.join(os.path.dirname(__file__), 'manifest.json')
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        return manifest.get('version', 'Unknown')