"""The Slide Local integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import logging
from SlideLocalAPI import SlideLocal

from . import hub
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["cover", "sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Slide Local from a config entry."""

    host = entry.data["host"]
    id = entry.data["id"]

    # Initialize Slide
    slide = SlideLocal(host, id)

    # Check if Slide is valid
    if not slide:
        # Log error
        _LOGGER.error("Could not connect to Slide", id, "at", host)
        return
    else:
        # Retreive current position
        mac = await slide.slide_get_key("mac")
        pos = await slide.slide_get_key("pos")
        # TO-DO validate MAC

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub.Hub(hass, entry.data["host"], entry.data["name"], entry.data["id"], mac, pos)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
