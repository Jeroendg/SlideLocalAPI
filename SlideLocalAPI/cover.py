"""Platform for cover integration"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.cover import (ATTR_POSITION, SUPPORT_CLOSE, SUPPORT_OPEN, SUPPORT_SET_POSITION, SUPPORT_STOP, DEVICE_CLASS_CURTAIN, PLATFORM_SCHEMA, STATE_CLOSED, STATE_CLOSING, STATE_OPEN, STATE_OPENING, CoverEntity)
from homeassistant.const import ATTR_ID, CONF_NAME, CONF_HOST, CONF_ID, CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback, DiscoveryInfoType
from homeassistant.helpers.typing import ConfigType

from .const import (ATTR_TOUCHGO, ATTR_CALIB_TIME, DOMAIN, OFFSET)

_LOGGER = logging.getLogger(__name__)

# Define configuration schema
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_ID): cv.string,
    vol.Required(CONF_MAC): cv.string,
})

async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities
) -> None:
    """Add cover from hub."""
    hub = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(LocalSlide(curtain) for curtain in hub.curtains)

class LocalSlide(CoverEntity):
    """Representation of a Slide"""
    _attr_has_entity_name = True
    should_poll = True
    supported_features = SUPPORT_SET_POSITION | SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP

    def __init__(self, cover) -> None:
        """Initialize Slide"""
        self._cover = cover
        self._attr_unique_id = f"{self._cover.curtain_id}_cover"
        self._attr_name = self._cover.name
        self._calibration_time = None
        self._online = False
        self._position = self._cover.position
        self._state = None
        self._touchgo = False
        self._device_id = self._cover.curtain_id

    @property
    def device_info(self) -> device_info:
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._cover.curtain_id)},
            # If desired, the name for the device could be different to the entity
            "name": self.name,
            "manufacturer": self._cover.hub.manufacturer,
        }

    @property
    def name(self) -> str:
        """Return the display name of this cover."""
        return self._attr_name

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        return self._state == STATE_OPENING

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        return self._state == STATE_CLOSING

    @property
    def is_closed(self):
        """Return None if status is unknown, True if closed, else False."""
        if self._state is None:
            return None
        return self._state == STATE_CLOSED

    @property
    def available(self) -> bool:
        """Return False if state is not available."""
        return self._cover.online and self._cover.hub.online

    @property
    def assumed_state(self):
        """Let HASS know the integration is assumed state."""
        return True

    @property
    def device_class(self):
        """Return the device class of the cover."""
        return DEVICE_CLASS_CURTAIN

    @property
    def current_cover_position(self):
        """Return the current position of cover."""
        return self._position

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        self._state = STATE_OPENING
        await self._cover.set_position(100)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        self._state = STATE_CLOSING
        await self._cover.set_position(0)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self._cover.stop()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set a new cover position"""
        position = kwargs[ATTR_POSITION]
        await self._cover.set_position(position)

    async def async_calibrate(self):
        """Calibrate the cover."""
        await self._cover.calibrate()

    async def async_update(self):
        """Update the cover information"""
        slide = await self._cover.get_info()

        self._online = self._cover.online
        self._touchgo = self._cover._touchgo
        self._position = self._cover._current_position
        self._calibration_time = self._cover._calibration_time
        self._state = self._cover._state
