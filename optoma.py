"""
Support for Optoma projector.

For more details about this component, please refer to github documentation
"""
import logging

import voluptuous as vol

from homeassistant.components.media_player import (
    MediaPlayerDevice, MEDIA_PLAYER_SCHEMA, PLATFORM_SCHEMA)
from homeassistant.components.media_player.const import (
    DOMAIN, SUPPORT_SELECT_SOURCE, SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON)
from homeassistant.const import (
    ATTR_ENTITY_ID, CONF_NAME, CONF_PORT, STATE_OFF,
    STATE_ON)
import homeassistant.helpers.config_validation as cv

""""REQUIREMENTS = ['optoma-projector==0.1.0']"""

_LOGGER = logging.getLogger(__name__)

DATA_OPTOMA = 'optoma'
DEFAULT_NAME = 'Optoma Projector'

SUPPORT_OPTOMA = SUPPORT_TURN_ON | SUPPORT_TURN_OFF | SUPPORT_SELECT_SOURCE 

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PORT): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
    """Set up the Optoma media player platform."""

    if DATA_OPTOMA not in hass.data:
        hass.data[DATA_OPTOMA] = []

    name = config.get(CONF_NAME)
    port = config.get(CONF_PORT)
    _LOGGER.info("Name for the optoma Projector is: %s", name)

    optoma = OptomaProjector(name, port)

    hass.data[DATA_OPTOMA].append(optoma)
    async_add_entities([optoma], update_before_add=True)

    async def async_service_handler(service):
        """Handle for services."""
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [device for device in hass.data[DATA_OPTOMA]
                       if device.entity_id in entity_ids]
        else:
            devices = hass.data[DATA_OPTOMA]
        for device in devices:
            device.async_schedule_update_ha_state(True)


class OptomaProjector(MediaPlayerDevice):
    """Representation of Epson Projector Device."""

    def __init__(self, name, port):
        """Initialize entity to control Epson projector."""
        import pyoptoma as optoma
        from pyoptoma import SOURCE_LIST

        self._name = name
        self._projector = optoma.Projector(port)
        self._source_list = list(SOURCE_LIST.values())
        self._source = None
        self._state = None
        _LOGGER.debug("init of the Optoma projector")
        self._projector.powered_off(self._on_state_changed)
        self._projector.powering_on(self._on_state_changed)

    async def async_update(self):
        """Update state of device."""
        from pyoptoma import (POWER, SOURCE, SOURCE_LIST, BUSY)
        is_turned_on = await self._projector.get_property(POWER)
        _LOGGER.debug("Project turn on/off status: %s", is_turned_on)
        if is_turned_on == 'on':
            self._state = STATE_ON
            source = await self._projector.get_property(SOURCE)
            self._source = SOURCE_LIST.get(source)
        elif is_turned_on == BUSY:
            self._state = STATE_ON
        else:
            self._state = STATE_OFF

    def _on_state_changed(self):
        """Handle state changes."""
        _LOGGER.debug("Updating due to notification")
        self.async_update()
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_OPTOMA

    async def async_turn_on(self):
        """Turn on optoma."""
        from pyoptoma import TURN_ON
        result = self._projector.send_command(TURN_ON)
        if result == 'OK':
           self._state = STATE_ON 

    async def async_turn_off(self):
        """Turn off optoma."""
        from pyoptoma import TURN_OFF
        result = self._projector.send_command(TURN_OFF)
        if result == 'OK':
           self._state = STATE_OFF

    @property
    def source_list(self):
        """List of available input sources."""
        return self._source_list

    @property
    def source(self):
        """Get current input sources."""
        return self._source

    async def async_select_source(self, source):
        """Select input source."""
        _LOGGER.info("optoma, setting source to: %s", source)
        self._projector.send_command(source)

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attributes = {}
    
    @property
    def should_poll(self):
        """Return that projector do not require polling."""
        return True

