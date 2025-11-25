import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
import homeassistant.helpers.config_validation as cv
from .const import DOMAIN, LOGGER, CONF_IP_ADDRESS
import aiohttp
import async_timeout

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
    }
)

class VentilationSystemConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ventilation system."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._async_abort_entries_match({CONF_IP_ADDRESS: user_input[CONF_HOST]})

            # Here you can add any connection validation if needed
            try:
                async with async_timeout.timeout(10):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"http://{user_input[CONF_HOST]}/status.xml") as response:
                            if response.status == 200:
                                text = await response.text()
                pass
            except Exception as err:
                errors["base"] = "cannot_connect"
                LOGGER.debug("Cannot connect: %s", err)
            else:
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data={CONF_IP_ADDRESS: user_input[CONF_HOST]},
                )

        data_schema = self.add_suggested_values_to_schema(DATA_SCHEMA, user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

class VentilationSystemOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        default_host = (
            self.config_entry.data.get(CONF_HOST)
            or self.config_entry.data.get(CONF_IP_ADDRESS)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=default_host, description={}): str
            })
        )
