import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .danodvoza_api import DanOdvozaApi
from .const import DOMAIN, CONF_ADDRESS

class SimbioFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = DanOdvozaApi(user_input[CONF_ADDRESS], session)
            valid = await api.validate_address()
            if valid:
                return self.async_create_entry(title="Dan Odvoza", data=user_input)
            else:
                errors["base"] = "invalid_data"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ADDRESS): str,
            }),
            errors=errors,
        )
