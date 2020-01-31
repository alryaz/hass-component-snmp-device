import voluptuous as vol
from homeassistant.const import CONF_TIMEOUT, CONF_HOST, CONF_PORT, CONF_NAME, \
    CONF_SCAN_INTERVAL, CONF_TYPE
from homeassistant.helpers import config_validation as cv

from custom_components.snmp_printer.const import CONF_VERSION, DEFAULT_VERSION, SNMP_VERSIONS, DEFAULT_PORT, \
    CONF_COMMUNITY, \
    DEFAULT_COMMUNITY, DEFAULT_TIMEOUT, DOMAIN, DEFAULT_SCAN_INTERVAL, SUPPORTED_DEVICE_TYPES

SNMP_DISCOVERY_OPTIONS = {
    'discover_v' + version: version
    for version in SNMP_VERSIONS
}

DEVICE_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_TYPE): vol.In(SUPPORTED_DEVICE_TYPES),
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_COMMUNITY, default=DEFAULT_COMMUNITY): cv.string,
    vol.Optional(CONF_VERSION, default=DEFAULT_VERSION): vol.In(SNMP_VERSIONS),
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.socket_timeout,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
})


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.All(cv.ensure_list,[DEVICE_SCHEMA]),
}, extra=vol.ALLOW_EXTRA)