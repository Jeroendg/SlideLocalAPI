"""Config flow for Slide Local."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant

from .const import DOMAIN

import re

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({vol.Required("name"): str, vol.Required("host"): str, vol.Required("id"): str})

async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    regex_ipv4 = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    regex_id = "^[A-Za-z0-9]{8}$"

    if not re.match(regex_ipv4, data["host"]):
        raise InvalidHost

    if not re.match(regex_id, data["id"]):
        raise InvalidID

    return {"title": data["name"]}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidID:
                errors["base"] = "invalid_id"
            except InvalidHost:
                errors["base"] = "invalid_host"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidID(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid ID."""

class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid IP."""
