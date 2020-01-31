"""SNMP Printer component"""
import asyncio
import logging
from datetime import timedelta
from typing import List, Tuple, Dict

from homeassistant import config_entries
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import CONF_HOST, CONF_BROADCAST_ADDRESS, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.helpers.typing import HomeAssistantType, ConfigType

from .const import DOMAIN, SNMP_VERSIONS, CONF_VERSION, CONF_COMMUNITY, DEFAULT_TIMEOUT, \
    DEFAULT_DISCOVERY_TIMEOUT, DEFAULT_PORT, DEFAULT_COMMUNITY, DEFAULT_VERSION, \
    DEFAULT_MAX_DEVICES, CONF_MAX_DEVICES, DEFAULT_BROADCAST_ADDRESS, DATA_DISCOVERY_CONFIG, \
    DATA_DEVICE_CONFIGS, SNMP_DISCOVERY
from .schemas import CONFIG_SCHEMA

_LOGGER = logging.getLogger(__name__)

SUPPORTED_COMPONENTS = [SENSOR_DOMAIN]

def discover_devices(protocol_version: int, community: str = DEFAULT_COMMUNITY, port: int = DEFAULT_PORT,
                     response_timeout: int = DEFAULT_DISCOVERY_TIMEOUT, max_responses: int = DEFAULT_MAX_DEVICES,
                     broadcast_address: str = DEFAULT_BROADCAST_ADDRESS) -> Dict[Tuple[str, int], str]:
    from pysnmp.proto import api
    if protocol_version not in api.protoModules:
        raise ValueError('"protocol_version" is invalid. Supported values: %s'
                         % ', '.join(map(str, api.protoModules.keys())))

    all_devices = dict()

    from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
    from pysnmp.carrier.asyncore.dgram import udp
    from pyasn1.codec.ber import encoder, decoder
    from time import time

    # Broadcast manager settings

    # Protocol version to use
    protocol = api.protoModules[protocol_version]

    # Build PDU
    request = protocol.GetRequestPDU()
    protocol.apiPDU.setDefaults(request)
    protocol.apiPDU.setVarBinds(request, (('1.3.6.1.2.1.1.1.0', protocol.Null('')),))

    # Build message
    message = protocol.Message()
    protocol.apiMessage.setDefaults(message)
    protocol.apiMessage.setCommunity(message, community)
    protocol.apiMessage.setPDU(message, request)

    started_at = time()
    last_found = None

    class StopWaiting(Exception):
        pass

    def callback_timer(now):
        if last_found is not None:
            if now - last_found > response_timeout:
                raise StopWaiting()
        elif now - started_at > response_timeout:
            raise StopWaiting()

    # noinspection PyUnusedLocal,PyUnusedLocal
    def callback_receive(_dispatcher, _domain, _address, _message, _request=request):
        global last_found
        while _message:
            response_message, _message = decoder.decode(_message, asn1Spec=protocol.Message())
            response = protocol.apiMessage.getPDU(response_message)
            # Match response to request
            if protocol.apiPDU.getRequestID(_request) == protocol.apiPDU.getRequestID(response):
                # Check for SNMP errors reported
                error_status = protocol.apiPDU.getErrorStatus(response)
                if error_status:
                    raise Exception('Protocol error:' + error_status.prettyPrint())
                else:
                    oid, val = next(iter(protocol.apiPDU.getVarBinds(response)))
                    _LOGGER.debug('Discovered "%s" on %s' % (val.prettyPrint(), _address))
                    all_devices[_address] = val.prettyPrint()
                    last_found = time()

                _dispatcher.jobFinished(1)

        return _message

    dispatcher = AsyncoreDispatcher()

    dispatcher.registerRecvCbFun(callback_receive)
    dispatcher.registerTimerCbFun(callback_timer)

    transport = udp.UdpSocketTransport().openClientMode().enableBroadcast()
    dispatcher.registerTransport(udp.domainName, transport)
    dispatcher.sendMessage(encoder.encode(message), udp.domainName, (broadcast_address, port))
    dispatcher.jobStarted(1, max_responses)

    # Dispatcher will finish as all jobs counter reaches zero
    try:
        dispatcher.runDispatcher()
    except StopWaiting:
        dispatcher.closeDispatcher()
    else:
        raise

    return all_devices


async def async_setup(hass: HomeAssistantType, config: ConfigType):
    if DOMAIN not in config:
        return True

    conf: List[Dict] = config[DOMAIN]

    devices_config = {}
    hass.data[DATA_DEVICE_CONFIGS] = devices_config

    for item_cfg in conf:
        host = item_cfg.get(CONF_HOST)
        port = item_cfg.get(CONF_PORT)
        if (host, port) in devices_config:
            _LOGGER.error('Duplicate entry for <host>:<port> pair (%s:%s). Please, '
                          'remove duplicate entry and try again.' % (host, port))
            continue

        item_cfg[CONF_SCAN_INTERVAL] = item_cfg[CONF_SCAN_INTERVAL].seconds

        devices_config[(
            item_cfg.get(CONF_HOST),
            item_cfg.get(CONF_PORT)
        )] = item_cfg
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data=item_cfg,
            )
        )

    return True

async def async_setup_entry(hass: HomeAssistantType, config_entry: config_entries.ConfigEntry, discovery_info=None):
    item_config = config_entry.data
    is_discovery = CONF_BROADCAST_ADDRESS in item_config

    hass_configs = hass.data.setdefault(DATA_DEVICE_CONFIGS, {})

    host = item_config.get(CONF_HOST)
    port = item_config.get(CONF_PORT)

    if config_entry.source == config_entries.SOURCE_IMPORT:
        item_config = hass_configs.get((host, port))
        if not item_config:
            _LOGGER.info('Removing entry %s after YAML configuration is purged.' % config_entry.entry_id)
            hass.async_create_task(
                hass.config_entries.async_remove(config_entry.entry_id)
            )
            return False

    elif (host, port) in hass.data[DATA_DEVICE_CONFIGS]:
        _LOGGER.error('Entry for %s already exists. Please, remove duplicate entry manually.'
                      % ('discovery' if is_discovery else 'device'))
        return False
    else:
        hass_configs[(host, port)] = item_config

    for component in SUPPORTED_COMPONENTS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(
                config_entry,
                component
            )
        )

    return True

async def async_unload_entry(hass: HomeAssistantType, config_entry: config_entries.ConfigEntry, discovery_info=None):
    host = config_entry.data[CONF_HOST]
    port = config_entry.data[CONF_PORT]

    _LOGGER.debug('Unloading entry for %s:%d', host, port)

    tasks = []
    for component in SUPPORTED_COMPONENTS:
        tasks.append(hass.async_create_task(
            hass.config_entries.async_forward_entry_unload(
                config_entry,
                component
            )
        ))

    await asyncio.wait(tasks)

    hass.data[DATA_DEVICE_CONFIGS].pop((host, port))

    return True

if __name__ == '__main__':
    logging.basicConfig()
    _LOGGER.setLevel(logging.DEBUG)
    import voluptuous as vol
    csc = lambda x: CONFIG_SCHEMA({DOMAIN: x})
    for data in [
        None,
        "discover_v1",
        "discover_v2c",
    ]:
        try:
            got = csc(data)
            print('pass valid', data, got)
        except (vol.Invalid, vol.MultipleInvalid) as e:
            raise Exception('Schema %s must be valid, got: %s' % (data, e))

    for data in [
        "discover_abcd"
    ]:
        try:
            got = csc(data)
            raise Exception('Schema %s must be invalid, got: %s' % (data, got))
        except (vol.Invalid, vol.MultipleInvalid) as e:
            print('pass invalid', data)

    print(discover_devices(SNMP_VERSIONS['1']))