"""Interfaces with the myLeviton API for Decora Smart WiFi products."""

import logging

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_TRANSITION,
    SUPPORT_BRIGHTNESS,
    SUPPORT_TRANSITION,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .common import DecoraWifiEntity, DecoraWifiPlatform
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Decora Wifi lights based on a config entry."""
    # Retrieve the platform session from the reference stored in data.
    session: DecoraWifiPlatform = hass.data[DOMAIN][entry.entry_id]

    if session:
        lights = session.lights

    entities = []
    if lights:
        entities.extend([DecoraWifiLight(light) for light in lights])
    async_add_entities(entities, True)


class DecoraWifiLight(DecoraWifiEntity, LightEntity):
    """Representation of a Decora WiFi switch."""

    @property
    def unique_id(self):
        """Return the unique id of the switch."""
        return self._unique_id

    @property
    def supported_features(self):
        """Return supported features."""
        if self._switch.canSetLevel:
            return SUPPORT_BRIGHTNESS | SUPPORT_TRANSITION
        return 0

    @property
    def name(self):
        """Return the display name of this switch."""
        return self._switch.name

    @property
    def brightness(self):
        """Return the brightness of the dimmer switch."""
        return int(self._switch.brightness * 255 / 100)

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._switch.power == "ON"

    def turn_on(self, **kwargs):
        """Instruct the switch to turn on & adjust brightness."""
        attribs = {"power": "ON"}

        if ATTR_BRIGHTNESS in kwargs:
            maxlevel = self._switch.data.get("maxLevel", 100)
            minlevel = self._switch.data.get("minLevel", 100)
            brightness = int(kwargs[ATTR_BRIGHTNESS] * maxlevel / 255)
            brightness = max(brightness, minlevel)
            attribs["brightness"] = brightness

        if ATTR_TRANSITION in kwargs:
            transition = int(kwargs[ATTR_TRANSITION])
            attribs["fadeOnTime"] = attribs["fadeOffTime"] = transition

        try:
            self._switch.update_attributes(attribs)
        except ValueError:
            _LOGGER.error("Failed to turn on myLeviton switch")

    def turn_off(self, **kwargs):
        """Instruct the switch to turn off."""
        attribs = {"power": "OFF"}

        try:
            self._switch.update_attributes(attribs)
        except ValueError:
            _LOGGER.error("Failed to turn off myLeviton switch")

    def update(self):
        """Fetch new state data for this switch."""
        try:
            self._switch.refresh()
        except ValueError:
            _LOGGER.error("Failed to update myLeviton switch data")
