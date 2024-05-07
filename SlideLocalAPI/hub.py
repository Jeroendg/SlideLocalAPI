from __future__ import annotations

import asyncio
import logging
from typing import Any

from SlideLocalAPI import SlideLocal
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.cover import (ATTR_POSITION, SUPPORT_CLOSE, SUPPORT_OPEN, SUPPORT_SET_POSITION, SUPPORT_STOP, DEVICE_CLASS_CURTAIN, PLATFORM_SCHEMA, STATE_CLOSED, STATE_CLOSING, STATE_OPEN, STATE_OPENING, CoverEntity)
from homeassistant.const import ATTR_ID, CONF_NAME, CONF_HOST, CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback, DiscoveryInfoType
from homeassistant.helpers.typing import ConfigType

from .const import (ATTR_TOUCHGO, ATTR_CALIB_TIME, DOMAIN, OFFSET)

_LOGGER = logging.getLogger(__name__)

class Hub:
    """Hub for a Slide device."""

    manufacturer = "Slide"

    def __init__(self, hass: HomeAssistant, host: str, name: str, id: str, mac: str, pos: str) -> None:
        """Init for the Slide device hub."""
        _LOGGER.info("Setting up Slide hub entity %s(%s) at %s(%s) - %s", name, id, host, mac, pos)
        self._host = host
        self._hass = hass
        self._name = name
        self._id = mac
        self._device_id = id
        # self._attr_unique_id = f"{mac}_hub"
        self.curtains = [
            Curtain(f"{self._id}_1", self._name, pos, self)
        ]
        self.online = True

    @property
    def hub_id(self) -> str:
        """Return ID for the Slide device hub."""
        return self._id

    async def test_connection(self) -> bool:
        """Test connectivity to the Slide device."""
        # TO DO: replace with real function, remove asyncio import
        await asyncio.sleep(1)
        return True

class Curtain:
    """Curtain class for the Slide hub."""

    def __init__(self, id: str, name: str, pos: str, hub: Hub) -> None:
        """Init for the Slide curtain"""
        self._id = id
        self.hub = hub
        self._cover = SlideLocal(hub._host, hub._id)
        self.name = name
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        self._current_position = self.parse_to_cover(pos)
        self._target_position = self._current_position
        self.board_rev = "0"
        self._online = False
        self._touchgo = False
        self._calibration_time = 0
        self._moving = False

        if self.parse_to_api(self._current_position) > 1 - OFFSET:
            self._state = STATE_CLOSED
        else:
            self._state = STATE_OPEN

    @property
    def curtain_id(self) -> str:
        """Return ID for the Slide curtain."""
        return self._id

    @property
    def position(self):
        """Return position for the Slide curtain."""
        return self._current_position

    async def set_position(self, set_position: int) -> None:
        """Set a new cover position"""
        self._target_position = set_position
        self._moving = True

        #Convert
        api_position = self.parse_to_api(set_position)

        _LOGGER.info("Setting Slide %s to POS: %s (%s)", self._id, api_position, set_position)
        await self._cover.slide_set_pos(api_position)

    async def get_info(self) -> None:
        """Get Slide inormation."""
        slide = await self._cover.slide_get_info()
        self.parsedata(slide)

    async def calibrate(self) -> None:
        """Calibrate the cover."""
        await self._cover.slide_calibrate()

    def online(self) -> bool:
        """Cover state"""
        return self._online

    def parsedata(self, slide):
        """Parse data received from the API"""
        try:
            if slide is None:
                _LOGGER.error("Slide '%s' returned no data (offline?)", self._id)

            # Check if API response has valid position
            # To Do validate all entries
            if "pos" in slide:
                # Get the previous position
                old_api_position = self.parse_to_api(self._current_position)

                # Set the properties
                self._online = True
                self._touchgo = slide["touch_go"]
                api_position = max(0, min(1, slide["pos"]))
                self._current_position = self.parse_to_cover(api_position)
                new_api_position = self.parse_to_api(self._current_position)
                self._calibration_time = slide["calib_time"]
                _LOGGER.info("Slide %s POS INFO - OLD_API: %s - NEW_API: %s - API: %s - CUR: %s", self._id, old_api_position, new_api_position, api_position, self._current_position)

                # Determine cover state based on position
                if abs(self._target_position - self._current_position) > (OFFSET * 100) and self._moving:
                    if self._target_position > self._current_position:
                        self._state = STATE_OPENING
                    else:
                        self._state = STATE_CLOSING
                else:
                    if new_api_position > 1 - OFFSET:
                        self._state = STATE_CLOSED
                    elif new_api_position == old_api_position and new_api_position <= 1 - OFFSET:
                        self._state = STATE_OPEN
                    elif new_api_position < old_api_position:
                        self._state = STATE_OPENING
                    else:
                        self._state = STATE_CLOSING

                if old_api_position == new_api_position:
                    self._moving = False
            else:
                # Log invalid data error
                _LOGGER.error("Slide '%s' has invalid data %s", self._id, str(slide))
        except Exception as e:
            self._online = False
            # Log all other erros
            _LOGGER.error("Error parsing data for Slide '%s': %s - %s", self._id, str(e), slide)

    def parse_to_api(self, position: int) -> float:
        """Parse cover position for use in API."""
        position = position / 100
        position = 1 - position

        if position < OFFSET:
            position = 0
        elif position > 1 - OFFSET:
            position = 1

        return round(position, 2)

    def parse_to_cover(self, position: float) -> int:
        """Parse API position for cover."""
        position = 1 - position

        if position < OFFSET:
            position = 0
        elif position > 1 - OFFSET:
            position = 100
        else:
            position = position * 100

        return round(position, 0)
