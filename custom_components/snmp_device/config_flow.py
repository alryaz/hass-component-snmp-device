"""Config flow for the SNMP Printer component."""
import logging
from collections import OrderedDict
from typing import Optional, TYPE_CHECKING, Type

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PORT, CONF_HOST, \
    CONF_TIMEOUT, CONF_SCAN_INTERVAL, CONF_NAME, CONF_TYPE
from homeassistant.helpers import ConfigType

from .const import DOMAIN, DEFAULT_VERSION, SNMP_VERSIONS, CONF_COMMUNITY, CONF_VERSION, DEFAULT_COMMUNITY, \
    DEFAULT_PORT, DEFAULT_TIMEOUT, DEFAULT_SCAN_INTERVAL, DEVICE_TYPE_PRINTER, DEVICE_TYPE_COMPUTER, \
    SUPPORTED_DEVICE_TYPES, DATA_DEVICE_CONFIGS

CONF_POLLING = "polling"

_LOGGER = logging.getLogger(__name__)

SKIP_DISCOVERY = "skip_discovery"

@config_entries.HANDLERS.register(DOMAIN)
class SNMPPrinterFlowHandler(config_entries.ConfigFlow):
    """Config flow for SNMP Printers."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    type_matchers = {
        DEVICE_TYPE_COMPUTER: (False, [
            'linux',
            'windows',
        ]),
        DEVICE_TYPE_PRINTER: (True, [
            'print',
        ]),
    }

    def __init__(self):
        """Initialize."""
        self._initial_config = None
        self._discovered_devices = None
        self._device_type_options = {
            device_type: device_type.capitalize()
            for device_type in SUPPORTED_DEVICE_TYPES
        }

    @classmethod
    def _determine_device_from_sys_description(cls, description: str) -> Optional[str]:
        lower_description = description.lower()
        for device_type, (rich_name, matchers) in cls.type_matchers.items():
            if any(x in lower_description for x in matchers):
                return device_type

        return None

    async def async_step_user(self, user_input=None, skip_discovery=False):
        """Handle a flow initialized by the user."""
        if not user_input:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required(CONF_COMMUNITY, default=DEFAULT_COMMUNITY): str,
                    vol.Required(CONF_VERSION, default=DEFAULT_VERSION): vol.In(SNMP_VERSIONS),
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Optional(SKIP_DISCOVERY, default=False): bool,
                }),
            )

        self._initial_config = {
            CONF_COMMUNITY: user_input.get(CONF_COMMUNITY),
            CONF_VERSION: user_input.get(CONF_VERSION),
            CONF_PORT: user_input.get(CONF_PORT)
        }

        if not user_input.get(SKIP_DISCOVERY):
            return await self.async_step_discovered_select()

        return await self.async_step_device()

    async def async_step_discovered_select(self, user_input=None):
        i_c = self._initial_config
        if user_input is None:
            from . import discover_devices
            all_devices = discover_devices(
                protocol_version=SNMP_VERSIONS[i_c[CONF_VERSION]],
                community=i_c[CONF_COMMUNITY],
                port=i_c[CONF_PORT],
            )

            if all_devices:
                self._discovered_devices = all_devices

                configured_num = 0

                configured_devices = self.hass.data.get(DATA_DEVICE_CONFIGS)
                discovered_choices = dict()
                for (host, port), description in all_devices.items():
                    if self._check_entity_exists(host, port):
                        configured_num += 1
                        continue

                    device_type = self._determine_device_from_sys_description(description)
                    if not device_type or self.type_matchers[device_type][0] is True:
                        discovered_choices[host] = description + ' (' + str(host) + ')'
                    else:
                        discovered_choices[host] = device_type.capitalize() + ' (' + str(host) + ')'

                if discovered_choices:
                    return self.async_show_form(
                        step_id="discovered_select",
                        data_schema=vol.Schema({
                            vol.Optional(CONF_HOST): vol.In(discovered_choices),
                        }),
                        description_placeholders={
                            "discovered_num": len(self._discovered_devices),
                            "configured_num": configured_num,
                        }
                    )
        else:
            host = user_input.get(CONF_HOST)
            if host:
                sys_description = self._discovered_devices[(host, i_c[CONF_PORT])]
                device_type = self._determine_device_from_sys_description(sys_description)
                i_c[CONF_HOST] = host
                i_c[CONF_TYPE] = device_type
                i_c[CONF_NAME] = (
                    sys_description
                    if (not device_type or self.type_matchers[device_type][0] is True) else
                    device_type.capitalize()
                )

        return await self.async_step_device()

    async def async_step_device(self, user_input=None):
        i_c = self._initial_config
        if not user_input:
            schema = OrderedDict()
            schema[vol.Required(CONF_TYPE, default=i_c.get(CONF_TYPE))] = vol.In(self._device_type_options)
            schema[vol.Optional(CONF_NAME, default=i_c.get(CONF_NAME))] = str
            schema[vol.Required(CONF_HOST, default=i_c.get(CONF_HOST))] = str
            schema[vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT)] = int
            schema[vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL.seconds)] = int

            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema(schema)
            )

        if self._check_entity_exists(user_input[CONF_HOST], i_c[CONF_PORT]):
            return self.async_abort(reason='already_configured')

        from pysnmp.hlapi import SnmpEngine, UdpTransportTarget, ContextData, CommunityData
        from importlib import import_module
        if TYPE_CHECKING:
            from .sensor import _SNMPSensor

        host = user_input[CONF_HOST]
        port = self._initial_config[CONF_PORT]
        device_type = user_input[CONF_TYPE]

        module_object = import_module('.sensor', package='.'.join(__name__.split('.')[:-1]))
        target_class: Type['_SNMPSensor'] = getattr(module_object, SUPPORTED_DEVICE_TYPES[device_type])

        snmp_engine = SnmpEngine()
        community_data = CommunityData(
            self._initial_config[CONF_COMMUNITY],
            mpModel=SNMP_VERSIONS[self._initial_config[CONF_VERSION]]
        )
        transport_target = UdpTransportTarget((host, port))

        try:

            retrieved_data = target_class.retrieve_data(snmp_engine, community_data, transport_target)
            _LOGGER.debug('Retrieved data during configuration: %s', retrieved_data)

            i_c.update({
                CONF_NAME: user_input.get(CONF_NAME) or device_type.capitalize(),
                CONF_TYPE: device_type,
                CONF_HOST: host,
                CONF_TIMEOUT: user_input[CONF_TIMEOUT],
                CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL]
            })

            _LOGGER.debug('Final initial config %s' % i_c)

        except Exception as e:
            _LOGGER.exception('Error while connecting to device')
            return self.async_abort(reason='connection_failed')

        return self._async_final_create_entry(
            title=i_c[CONF_NAME],
            data=i_c,
        )

    def _check_entity_exists(self, host, port):
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data[CONF_HOST] == host and entry.data[CONF_PORT] == port:
                return True
        return False

    def _async_final_create_entry(self, title, data):
        """Return a set of the configured hosts."""
        _LOGGER.debug('afce %s %s', title, data)
        if self._check_entity_exists(data[CONF_HOST], data[CONF_PORT]):
            return self.async_abort(reason='already_configured')
        
        return self.async_create_entry(
            title=title,
            data=data
        )

    async def async_step_import(self, config: ConfigType):
        """Import a config entry from configuration.yaml."""
        _LOGGER.debug('Import entry: %s' % config)
        return self._async_final_create_entry(
            title=(config.get(CONF_NAME) or config[CONF_HOST]) + ' (yaml)',
            data={
                CONF_HOST: config[CONF_HOST],
                CONF_PORT: config[CONF_PORT],
            }
        )