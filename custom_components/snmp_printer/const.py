"""Enumeration helpers for printer state attributes"""
from enum import IntEnum

__all__ = ["SENSOR_OID_DEFINITIONS", "SuppliesClass", "SuppliesType", "DEFAULT_SUPPLIES_ICON", "SUPPLIES_ICONS", "CapacityLevelType", "PrinterStatus", "DeviceStatus", "PaperInputType"]

from homeassistant.const import (
    
)

CAPACITY_LEVEL_TYPE = lambda x: CapacityLevelType(x) if int(x) < 0 else int(x)
SENSOR_OID_DEFINITIONS = {
    'info': ({
        'model': ('1.3.6.1.2.1.25.3.2.1.3.1', str, STATE_UNKNOWN),
        'device_id': ('1.3.6.1.2.1.25.3.2.1.4.1', str, STATE_UNKNOWN),
        'mileage': ('1.3.6.1.2.1.43.10.2.1.4.1.1',int, 0),
        'printer_status': ('1.3.6.1.2.1.25.3.5.1.1.1', PrinterStatus, PrinterStatus.UNKNOWN),
        'device_status': ('1.3.6.1.2.1.25.3.2.1.5.1', DeviceStatus, DeviceStatus.UNKNOWN)
    }, dict),
    'network_info': ({
        '_index': ('1.3.6.1.2.1.2.2.1.2', str),
        'phys_address': ('1.3.6.1.2.1.2.2.1.6', str),
    }, dict),
    
    'supplies': ({
        '_index': True,
        #'marker_index': ('1.3.6.1.2.1.43.11.1.1.2.1', int, STATE_UNKNOWN),
        'colorant_index': ('1.3.6.1.2.1.43.11.1.1.3.1', int, STATE_UNKNOWN),
        'description': ('1.3.6.1.2.1.43.11.1.1.6.1', str, STATE_UNKNOWN),
        'class': ('1.3.6.1.2.1.43.11.1.1.4.1', SuppliesClass, SuppliesClass.UNKNOWN),
        'type': ('1.3.6.1.2.1.43.11.1.1.5.1', SuppliesType, SuppliesType.UNKNOWN),
        'capacity': ('1.3.6.1.2.1.43.11.1.1.8.1', CAPACITY_LEVEL_TYPE, CapacityLevelType.UNKNOWN),
        'level': ('1.3.6.1.2.1.43.11.1.1.9.1', CAPACITY_LEVEL_TYPE, CapacityLevelType.UNKNOWN),
    }, dict),

    'colorants': ({
        '_index': True,
        #'marker_index': ('1.3.6.1.2.1.43.12.1.1.2', int),
        'color': ('1.3.6.1.2.1.43.12.1.1.4', str),
    }, dict),
    'paper_inputs': ({
        '_index': True,
        'type': ('1.3.6.1.2.1.43.8.2.1.2.1', PaperInputType),
        'capacity': ('1.3.6.1.2.1.43.8.2.1.9.1', int),
        'level': ('1.3.6.1.2.1.43.8.2.1.10.1', int),
        'model': ('1.3.6.1.2.1.43.8.2.1.18.1', str),
    }, list)
}

def key_tuple_to_tuple_keys(dict):
    return {
        tuple_value: key
        for (key, values) in dict.items()
        for tuple_value in values
    }

class SuppliesClass(IntEnum):
    OTHER = 1
    CONSUMABLE = 3
    RECEPTACLE = 4

class SuppliesType(IntEnum):
    OTHER = 1
    UNKNOWN = 2
    TONER = 3
    WASTETONER = 4
    INK = 5
    INKCARTRIDGE = 6
    INKRIBBON = 7
    WASTEINK = 8
    OPC = 9
    DEVELOPER = 10
    FUSEROIL = 11
    SOLIDWAX = 12
    RIBBONWAX = 13
    WASTEWAX = 14
    FUSER = 15
    CORONAWIRE = 16
    FUSEROILWICK = 17
    CLEANERUNIT = 18
    FUSERCLEANINGPAD = 19
    TRANSFERUNIT = 20
    TONERCARTRIDGE = 21
    FUSEROILER = 22
    WATER = 23
    WASTEWATER = 24
    GLUEWATERADDITIVE = 25
    WASTEPAPER = 26
    BINDINGSUPPLY = 27
    BANDINGSUPPLY = 28
    STITCHINGWIRE = 29
    SHRINKWRAP = 30
    PAPERWRAP = 31
    STAPLES = 32
    INSERTS = 33
    COVERS = 34

DEFAULT_SUPPLIES_ICON = 'mdi:puzzle'
SUPPLIES_ICONS = key_tuple_to_tuple_keys({
    DEFAULT_SUPPLIES_ICON: (SuppliesType.OTHER, SuppliesType.UNKNOWN),
    'mdi:delete': (SuppliesType.WASTEINK, SuppliesType.WASTEPAPER, SuppliesType.WASTETONER, SuppliesType.WASTEWATER, SuppliesType.WASTEWAX),
    'mdi:water': (SuppliesType.TONER, SuppliesType.TONERCARTRIDGE, SuppliesType.INK, SuppliesType.INKCARTRIDGE, SuppliesType.INKRIBBON, SuppliesType.FUSEROIL, SuppliesType.WATER),
    'mdi:cogs': (SuppliesType.DEVELOPER, SuppliesType.FUSEROILER, SuppliesType.CLEANERUNIT, SuppliesType.TRANSFERUNIT),
    'mdi:clip': (SuppliesType.STAPLES, SuppliesType.BANDINGSUPPLY, SuppliesType.BINDINGSUPPLY),
    'mdi:notebook': (SuppliesType.COVERS,),
    'mdi:book-open-variant': (SuppliesType.INSERTS,),
    'mdi:gift': (SuppliesType.PAPERWRAP, SuppliesType.SHRINKWRAP),
    'mdi:lightbulb': (SuppliesType.FUSER,),
})

class CapacityLevelType(IntEnum):
    UNTRACKED = -1
    UNKNOWN = -2
    AVAILABLE = -3

class PrinterStatus(IntEnum):
    OFFLINE = 0
    OTHER = 1
    UNKNOWN = 2
    IDLE = 3
    PRINTING = 4
    WARMUP = 5

class DeviceStatus(IntEnum):
    UNKNOWN = 1
    RUNNING = 2
    WARNING = 3
    TESTING = 4
    DOWN = 5

class PaperInputType(IntEnum):
    OTHER = 1
    UNKNOWN = 2
    SHEET_FEED_AUTO_REMOVABLE_TRAY = 3
    SHEET_FEED_AUTO_NON_REMOVABLE_TRAY = 4
    SHEET_FEED_MANUAL = 5
    CONTINUOUS_ROLL = 6
    CONTINUOUS_FAN_FOLD = 7