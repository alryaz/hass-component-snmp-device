"""Enumeration helpers for printer state attributes"""
__all__ = [
    "DOMAIN",
    "DATA_DISCOVERY_CONFIG",
    "DATA_DEVICE_CONFIGS",
    "DATA_DEVICE_LISTENERS",
    "SNMP_DISCOVERY",
    "SUPPORTED_DEVICE_TYPES",
    "DEVICE_TYPE_COMPUTER",
    "DEVICE_TYPE_PRINTER",
    "DATA_DEVICE_ENTITIES",

    "SNMP_VERSIONS",
    "CONF_COMMUNITY",
    "CONF_VERSION",
    "CONF_ACCEPT_ERRORS",
    "CONF_DEFAULT_VALUE",
    "CONF_MAX_DEVICES",
    "CONF_DISCOVERY_INTERVAL",
    "CONF_DISCOVERY_TIMEOUT",
    "DEFAULT_COMMUNITY",
    "DEFAULT_VERSION",
    "DEFAULT_ACCEPT_ERRORS",
    "DEFAULT_PORT",
    "DEFAULT_TIMEOUT",
    "DEFAULT_DISCOVERY_TIMEOUT",
    "DEFAULT_BROADCAST_ADDRESS",
    "DEFAULT_MAX_DEVICES",
    "DEFAULT_SUPPLIES_ICON",
    "DEFAULT_SCAN_INTERVAL",
    "SUPPLIES_ICONS",
]

from datetime import timedelta

from pysnmp.proto.api import protoVersion1, protoVersion2c
from .enums import SuppliesType

DOMAIN = "snmp_device"
DATA_DISCOVERY_CONFIG = DOMAIN + "_discovery_config"
DATA_DEVICE_CONFIGS = DOMAIN + "_device_configs"
DATA_DEVICE_LISTENERS = DOMAIN + "_device_listeners"
DATA_DEVICE_ENTITIES = DOMAIN + "_device_entities"

PLATFORM_CREATED_ENTITIES = "created_entities"
PLATFORM_ADDED_ENTITIES = "added_entities"
PLATFORM_LISTENER = "listener"

SNMP_DISCOVERY = DOMAIN + "_discovery_{}_{}"

DEVICE_TYPE_PRINTER = 'printer'
DEVICE_TYPE_COMPUTER = 'computer'

SUPPORTED_DEVICE_TYPES = {
    DEVICE_TYPE_PRINTER: 'SNMPPrinterSensor',
    DEVICE_TYPE_COMPUTER: 'SNMPComputerSensor',
}

SNMP_VERSIONS = {
    '1': protoVersion1,
    '2c': protoVersion2c,
}

CONF_COMMUNITY = 'community'
CONF_VERSION = 'version'
CONF_ACCEPT_ERRORS = 'accept_errors'
CONF_DEFAULT_VALUE = 'default_value'
CONF_MAX_DEVICES = 'max_devices'
CONF_DISCOVERY_INTERVAL = 'discovery_interval'
CONF_DISCOVERY_TIMEOUT = 'discovery_timeout'

DEFAULT_ACCEPT_ERRORS = True
DEFAULT_COMMUNITY = 'public'
DEFAULT_PORT: str = '161'
DEFAULT_VERSION = '2c'
DEFAULT_TIMEOUT = 1
DEFAULT_DISCOVERY_TIMEOUT = 2
DEFAULT_MAX_DEVICES = 10
DEFAULT_BROADCAST_ADDRESS = "255.255.255.255"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

def key_tuple_to_tuple_keys(input_dict):
    return {
        tuple_value: key
        for (key, values) in input_dict.items()
        for tuple_value in values
    }

DEFAULT_SUPPLIES_ICON = 'mdi:puzzle'
SUPPLIES_ICONS = key_tuple_to_tuple_keys({
    DEFAULT_SUPPLIES_ICON: (SuppliesType.OTHER, SuppliesType.UNKNOWN),
    'mdi:delete': (SuppliesType.WASTE_INK, SuppliesType.WASTE_PAPER, SuppliesType.WASTE_TONER,
                   SuppliesType.WASTE_WATER, SuppliesType.WASTE_WAX),
    'mdi:water': (SuppliesType.TONER, SuppliesType.TONER_CARTRIDGE, SuppliesType.INK, SuppliesType.INK_CARTRIDGE,
                  SuppliesType.INK_RIBBON, SuppliesType.FUSER_OIL, SuppliesType.WATER),
    'mdi:cogs': (SuppliesType.DEVELOPER, SuppliesType.FUSER_OILER, SuppliesType.CLEANER_UNIT,
                 SuppliesType.TRANSFER_UNIT),
    'mdi:clip': (SuppliesType.STAPLES, SuppliesType.BANDING_SUPPLY, SuppliesType.BINDING_SUPPLY),
    'mdi:notebook': (SuppliesType.COVERS,),
    'mdi:book-open-variant': (SuppliesType.INSERTS,),
    'mdi:gift': (SuppliesType.PAPER_WRAP, SuppliesType.SHRINK_WRAP),
    'mdi:lightbulb': (SuppliesType.FUSER,),
})