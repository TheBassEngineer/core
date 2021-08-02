"""Test the decora_wifi Common components."""

from unittest.mock import patch

from homeassistant.components.decora_wifi.common import (
    DecoraWifiCommFailed,
    DecoraWifiLoginFailed,
    DecoraWifiPlatform,
)
from homeassistant.components.decora_wifi.const import LIGHT_DOMAIN

from tests.components.decora_wifi.common import (
    FakeDecoraWiFiResidence,
    FakeDecoraWiFiResidentialAccount,
    FakeDecoraWiFiSession,
)

USERNAME = "username@home-assisant.com"
PASSWORD = "test-password"
INCORRECT_PASSWORD = "incoreect-password"


def test_DecoraWifiPlatform_init():
    """Check DecoraWifiPlatform initialization and deletion."""
    instance = None

    with patch(
        "homeassistant.components.decora_wifi.common.DecoraWiFiSession.login",
        return_value=True,
    ) as mock_session_login, patch(
        "homeassistant.components.decora_wifi.common.DecoraWifiPlatform._apigetdevices"
    ) as mock_apigetdevices, patch(
        "homeassistant.components.decora_wifi.common.Person.logout"
    ) as mock_person_logout:
        # Check object setup
        instance = DecoraWifiPlatform(USERNAME, PASSWORD)
        assert isinstance(instance, DecoraWifiPlatform)
        mock_session_login.assert_called_once()
        mock_apigetdevices.assert_called_once()
        mock_session_login.reset_mock()
        mock_apigetdevices.reset_mock()
        # Check object reauth
        instance.reauth()
        mock_person_logout.assert_called_once()
        mock_session_login.assert_called_once()
        mock_person_logout.reset_mock()
        # Check object refresh devices
        instance.refresh_devices()
        mock_apigetdevices.assert_called_once()
        # Check object teardown
        instance = None
        mock_person_logout.assert_called_once()


def test_DecoraWifiPlatform_init_invalidpw():
    """Check DecoraWifiPlatform login failure throws correct exception, doesn't leave broken object."""
    instance = None
    exception = None

    with patch(
        "homeassistant.components.decora_wifi.common.DecoraWiFiSession.login",
        return_value=None,
    ) as mock_session_login, patch(
        "homeassistant.components.decora_wifi.common.DecoraWifiPlatform._apigetdevices"
    ) as mock_apigetdevices, patch(
        "homeassistant.components.decora_wifi.common.DecoraWifiPlatform.apilogout"
    ) as mock_apilogout:
        # Check exception thrown as expected
        try:
            DecoraWifiPlatform(USERNAME, PASSWORD)
        except Exception as ex:
            exception = ex
        assert isinstance(exception, DecoraWifiLoginFailed)
        mock_session_login.assert_called_once()
        mock_apigetdevices.assert_not_called()
        mock_apilogout.assert_not_called()
        assert instance is None


def test_DecoraWifiPlatform_init_nocomms():
    """Check DecoraWifiPlatform communication failure throws correct exception, doesn't leave broken object."""
    instance = None
    exception = None

    with patch(
        "homeassistant.components.decora_wifi.common.DecoraWiFiSession.login",
        side_effect=ValueError,
    ) as mock_session_login, patch(
        "homeassistant.components.decora_wifi.common.DecoraWifiPlatform._apigetdevices"
    ) as mock_apigetdevices, patch(
        "homeassistant.components.decora_wifi.common.DecoraWifiPlatform.apilogout"
    ) as mock_apilogout:
        # Check exception thrown as expected
        try:
            DecoraWifiPlatform(USERNAME, PASSWORD)
        except Exception as ex:
            exception = ex
        assert isinstance(exception, DecoraWifiCommFailed)
        mock_session_login.assert_called_once()
        mock_apigetdevices.assert_not_called()
        mock_apilogout.assert_not_called()
        assert instance is None


def test_DecoraWifiPlatform_getdevices():
    """Check DecoraWifiPlatform getdevices function."""
    instance = None

    with patch(
        "homeassistant.components.decora_wifi.common.DecoraWiFiSession",
        side_effect=FakeDecoraWiFiSession,
    ), patch(
        "homeassistant.components.decora_wifi.common.Residence",
        side_effect=FakeDecoraWiFiResidence,
    ), patch(
        "homeassistant.components.decora_wifi.common.ResidentialAccount",
        side_effect=FakeDecoraWiFiResidentialAccount,
    ), patch(
        "homeassistant.components.decora_wifi.common.DecoraWifiPlatform.apilogout"
    ) as mock_apilogout:
        # Setup platform object
        instance = DecoraWifiPlatform(USERNAME, PASSWORD)
        assert isinstance(instance, DecoraWifiPlatform)
        # Check that getdevices left platform object in expected state
        assert len(instance._iot_switches[LIGHT_DOMAIN]) == 6
        # Check object teardown
        instance = None
        mock_apilogout.assert_called_once()


async def test_async_setup_decora_wifi(hass):
    """Check async wrapper for platform setup."""

    with patch(
        "homeassistant.components.decora_wifi.common.DecoraWifiPlatform"
    ) as mock_platformsetup:
        await DecoraWifiPlatform.async_setup_decora_wifi(hass, USERNAME, PASSWORD)
        await hass.async_block_till_done()
        mock_platformsetup.assert_called_once()


def test_DecoraWifiPlatform_apigetdevices_commfailed():
    """Check DecoraWifiPlatform comm failure during initial getdevices."""
    instance = None
    exception = None

    with patch(
        "homeassistant.components.decora_wifi.common.DecoraWiFiSession",
        side_effect=FakeDecoraWiFiSession,
    ), patch(
        "homeassistant.components.decora_wifi.common.Residence",
        side_effect=FakeDecoraWiFiResidence,
    ), patch(
        "homeassistant.components.decora_wifi.common.ResidentialAccount",
        side_effect=ValueError,
    ), patch(
        "homeassistant.components.decora_wifi.common.DecoraWifiPlatform.apilogout"
    ):
        # Setup Object
        try:
            instance = DecoraWifiPlatform(USERNAME, PASSWORD)
        except DecoraWifiCommFailed as ex:
            exception = ex
        assert isinstance(exception, DecoraWifiCommFailed)
        # If the comm failure happens during initial setup, the constructor never completes and the platform object instance isn't created.
        assert not instance


def test_DecoraWifiPlatform_apilogout_commfailed():
    """Check DecoraWifiPlatform comm failure during deletion."""
    exception = None

    with patch(
        "homeassistant.components.decora_wifi.common.DecoraWiFiSession.login",
        return_value=True,
    ), patch(
        "homeassistant.components.decora_wifi.common.DecoraWifiPlatform._apigetdevices"
    ), patch(
        "homeassistant.components.decora_wifi.common.Person.logout",
        side_effect=DecoraWifiCommFailed,
    ) as mock_person_logout:
        # Setup Object
        try:
            instance = DecoraWifiPlatform(USERNAME, PASSWORD)
            instance.apilogout()
        except DecoraWifiCommFailed as ex:
            exception = ex
        assert isinstance(exception, DecoraWifiCommFailed)
        mock_person_logout.assert_called_once()
