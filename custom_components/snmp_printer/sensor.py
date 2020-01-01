"""
Support for displaying collected printer status data over SNMP.
"""
import logging
import asyncio
from datetime import timedelta

import voluptuous as vol
from pysnmp.hlapi import (
    SnmpEngine, CommunityData, ContextData, UdpTransportTarget,
    ObjectIdentity, ObjectType, nextCmd, getCmd
)
from enum import IntEnum

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval, async_call_later
from homeassistant.const import (
    CONF_HOST, CONF_NAME, CONF_PORT, CONF_UNIT_OF_MEASUREMENT, STATE_UNKNOWN, STATE_OFF,
    CONF_VALUE_TEMPLATE, CONF_SCAN_INTERVAL, CONF_TIMEOUT
)

from .const import *

REQUIREMENTS = ['pysnmp==4.4.4']

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)

CONF_COMMUNITY = 'community'
CONF_VERSION = 'version'
CONF_ACCEPT_ERRORS = 'accept_errors'
CONF_DEFAULT_VALUE = 'default_value'

DEFAULT_COMMUNITY = 'public'
DEFAULT_PORT = '161'
DEFAULT_VERSION = '2c'
DEFAULT_TIMEOUT = 1

SNMP_VERSIONS = {
    '1': 0,
    '2c': 1,
}

SENSOR_TYPE_STATUS = 'status'
SENSOR_TYPE_TONER = 'toner'
SENSOR_TYPE_MILEAGE = 'mileage'
SENSOR_TYPE_PAPER_INPUT = 'paper_input'

CAPACITY_LEVEL_TYPE = lambda x: CapacityLevelType(x) if int(x) < 0 else int(x)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_COMMUNITY, default=DEFAULT_COMMUNITY): cv.string,
    vol.Optional(CONF_VERSION, default=DEFAULT_VERSION): vol.In(SNMP_VERSIONS),
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.socket_timeout,
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the SNMP sensor."""
    from pysnmp.hlapi import (
        getCmd, CommunityData, SnmpEngine, UdpTransportTarget, ContextData,
        ObjectType, ObjectIdentity)

    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    community = config.get(CONF_COMMUNITY)
    version = config.get(CONF_VERSION)
    timeout = config.get(CONF_TIMEOUT)
    scan_interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)

    default_name = 'SNMP Printer {}'.format(host)
    name = config.get(CONF_NAME, default_name)

        
    try:
        data_source = SNMPPrinterData(
            hass = hass,
            name = name,
            host = host,
            port = port,
            community = community,
            timeout = timeout,
            version = version,
            async_add_entities = async_add_entities
        )
        
        await data_source.update_data()

        async_track_time_interval(hass, data_source.update_data, scan_interval)

    except:
        _LOGGER.warning('Device unavailable, retrying later')

        raise PlatformNotReady


class SNMPPrinterSensor(Entity):
    """Representation of a SNMP sensor."""

    def __init__(self, hass, name, sensor_type, unit_of_measurement, icon = 'mdi:printer', entity_index = 0):
        """Initialize the sensor."""
        self.hass = hass
        self._name = name
        self._type = sensor_type
        self._entity_index = entity_index
        self._state = None
        self._icon = icon
        self._unit_of_measurement = unit_of_measurement
        self._attributes = None
    
    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Return device icon."""
        return self._icon

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def should_poll(self):
        """Disable sensor polling."""
        return False

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement


class SNMPPrinterData(object):

    def __init__(self, hass, name, host, port, timeout, community, version, async_add_entities, entities = None):
        """Initialize data object"""
        self.name = name
        self.hass = hass
        self.host = host
        self.port = port
        self.timeout = timeout
        self.community = community
        self.snmp_version = version
        self.entities = entities or {}

        self.__data = {}
        self.__async_add_entities = async_add_entities
        self.__last_update_failed = False

    def __getattribute__(self, name):
        """Return object attributes based on OID attribute definitions"""
        if name in SENSOR_OID_DEFINITIONS:
            return self.__data.get(name, SENSOR_OID_DEFINITIONS[name][2] if len(SENSOR_OID_DEFINITIONS[name]) >= 3 else None)
        else:
            return super().__getattribute__(name)

    async def add_missing_entities(self, dont_add_to_hass = False):
        if dont_add_to_hass:
            _LOGGER.debug('missing entities addition, not adding to homeassistant')
        else:
            _LOGGER.debug('missing entities addition, addint to homeassistant afterwards')

        new_entities = {}
        if SENSOR_TYPE_STATUS not in self.entities:
            new_entities[SENSOR_TYPE_STATUS] = SNMPPrinterSensor(
                hass = self.hass,
                name = '{} Status'.format(self.name),
                sensor_type = SENSOR_TYPE_STATUS,
                unit_of_measurement = None
            )
            new_entities[SENSOR_TYPE_STATUS]._state = STATE_OFF

        if SENSOR_TYPE_MILEAGE not in self.entities:
            new_entities[SENSOR_TYPE_MILEAGE] = SNMPPrinterSensor(
                hass = self.hass,
                name = '{} Mileage'.format(self.name),
                sensor_type = SENSOR_TYPE_MILEAGE,
                unit_of_measurement = 'sheets',
                icon = 'mdi:counter'
            )
        
        if self.paper_inputs:
            for index, paper_input in self.paper_inputs.items():
                paper_input_index = SENSOR_TYPE_PAPER_INPUT + '_' + str(index)

                if paper_input_index not in self.entities:
                    item_name = '{} {}'.format(self.name, paper_input['model'])
                    new_entities[paper_input_index] = SNMPPrinterSensor(
                        hass = self.hass,
                        name = item_name,
                        sensor_type = SENSOR_TYPE_PAPER_INPUT,
                        unit_of_measurement = 'sheets',
                        entity_index = index,
                        icon = 'mdi:file'
                    )
        
        if self.supplies:
            for index, supply in self.supplies.items():
                supply_entity_index = SENSOR_TYPE_TONER + '_' + str(index)
                
                if supply_entity_index not in self.entities:
                    item_name = supply['description']
                    if supply['colorant_index'] > 0:
                        item_name = '{} {} {}'.format(
                            item_name,
                            self.colorants[supply['colorant_index']]['color'].capitalize(),
                            supply['type'].name.capitalize()   
                        )
                        
                    new_entities[supply_entity_index] = SNMPPrinterSensor(
                        hass = self.hass,
                        name = '{} {}'.format(self.name, item_name),
                        sensor_type = SENSOR_TYPE_TONER,
                        unit_of_measurement = '%',
                        entity_index = index,
                        icon = SUPPLIES_ICONS.get(supply['type'], DEFAULT_SUPPLIES_ICON)
                    )

        if new_entities:
            self.entities.update(new_entities)
            
            missing_entities_string = ', '.join([dev.name for dev in new_entities.values()])

            if not dont_add_to_hass and new_entities:
                _LOGGER.debug('adding missing entities to homeassistant: %s', missing_entities_string)
                self.__async_add_entities(new_entities.values())

            else:
                _LOGGER.debug('adding missing entities to local definition only: %s', missing_entities_string)

        else:
            _LOGGER.debug('no new missing entities added')

    async def update_data(self, *_, dont_update_hass = False):
        _LOGGER.debug('begin data update, %s', 'no hass update scheduled' if dont_update_hass else 'updating homeassistant afterwards')
        try:
            new_data = {}

            for attribute in SENSOR_OID_DEFINITIONS.keys():
                new_data[attribute] = self.get_oid_value(*SENSOR_OID_DEFINITIONS[attribute])
        
            _LOGGER.debug('Updated data: %s', ', '.join([
                ('%s = %s' % (attribute, value))
                for (attribute, value) in new_data.items()
            ]))

            self.__data = new_data
            self.__last_update_failed = False
        except Exception:
            _LOGGER.warning('Could not update device, but will retry soon')
            self.__last_update_failed = True

        await self.add_missing_entities(dont_add_to_hass=dont_update_hass)
        await self.update_devices(dont_update_hass=dont_update_hass)
    
    async def update_devices(self, dont_update_hass = False):
        _LOGGER.debug('update_devices, %s', 'no hass update scheduled' if dont_update_hass else 'updating homeassistant afterwards')
        if not self.entities:
            return
        
        tasks = []
        for dev in self.entities.values():
            needs_update = False
            new_state = None
            new_attributes = None

            if dev._type == SENSOR_TYPE_STATUS:
                if self.__last_update_failed:
                    printer_status = PrinterStatus.UNKNOWN
                    device_status = DeviceStatus.DOWN
                else:
                    printer_status = self.info['printer_status']
                    device_status = self.info['device_status']
                
                if device_status in (DeviceStatus.WARNING, DeviceStatus.DOWN):
                    printer_status = device_status
                    dev._icon = 'mdi:printer-alert'
                else:
                    dev._icon = 'mdi:printer'

                new_state = printer_status.name.lower()
                new_attributes = {
                    'model': self.info['model'],
                    'printerStatus': printer_status,
                    'device_status': device_status,
                }

            elif dev._type == SENSOR_TYPE_TONER:
                supply = self.supplies[dev._entity_index]

                capacity = supply['capacity']
                level = supply['level']
                if capacity > 0:
                    new_state = '{:.0f}'.format(level * 100 / capacity)
                    dev._unit_of_measurement = '%'
                else:
                    capacity = capacity.name.lower()
                    level = level.name.lower()
                    new_state = level
                    dev._unit_of_measurement = None

                new_attributes = {
                    'current_level': level,
                    'max_capacity': capacity,
                    'type': supply['type'].name.lower(),
                    'model': supply['description'],
                }
                if supply['colorant_index'] > 0:
                    new_attributes['color'] = self.colorants[supply['colorant_index']]['color']

            elif dev._type == SENSOR_TYPE_MILEAGE:
                new_state = self.info['mileage']

            elif dev._type == SENSOR_TYPE_PAPER_INPUT:
                paper_input = self.paper_inputs[dev._entity_index]

                capacity = paper_input['capacity']
                level = paper_input['level']
                
                if level >= 0 and capacity > 0:
                    new_state = '{:.0f}'.format(level * 100 / capacity)
                    dev._unit_of_measurement = '%'

                else:
                    if capacity < 0:
                        capacity = CapacityLevelType(capacity).name.lower()

                    if level < 0:
                        level = CapacityLevelType(level).name.lower()
                        dev._unit_of_measurement = None
                    else:
                        dev._unit_of_measurement = 'sheets'

                new_state = level
                new_attributes = {
                    'current_level': level,
                    'max_capacity': capacity,
                    'type': paper_input['type'].name.lower(),
                    'model': paper_input['model'],
                }

            else:
                raise Exception('Impossible sensor type detected')
            
            if needs_update or new_state != dev._state or new_attributes != dev._attributes:
                _LOGGER.debug('entity %s needs update', dev.name)
                dev._state = new_state
                dev._attributes = new_attributes

                if not dont_update_hass and dev.entity_id is not None:
                    tasks.append(dev.async_update_ha_state())
        
        if tasks:
            _LOGGER.debug('%d update tasks scheduled', len(tasks))
            await asyncio.wait(tasks)

    def get_snmp_request_args(self):
        return [
            SnmpEngine(),
            CommunityData(self.community, mpModel=SNMP_VERSIONS[self.snmp_version]),
            UdpTransportTarget((self.host, self.port), timeout=self.timeout, retries=0),
            ContextData(),
        ]
    
    def get_oid_value(self, oids, type=str, default_value=None):
        """Request SNMP value (tree) by OID"""
        definitions = None
        has_index = False
        if isinstance(oids, str):
            oids = [oids]

        elif isinstance(oids, dict):
            definitions = oids
            has_index = ('_index' in definitions)
            oids = [definition[0] for definition in oids.values() if isinstance(definition, tuple)]
        
        if type == list or type == dict and has_index:
            iterator = nextCmd(*self.get_snmp_request_args(),
                                *[ObjectType(ObjectIdentity(oid)) for oid in oids],
                                lookupMib=False,
                                lexicographicMode=False)
        else:
            iterator = getCmd(*self.get_snmp_request_args(),
                                *[ObjectType(ObjectIdentity(oid)) for oid in oids],
                                lookupMib=False,
                                lexicographicMode=False)

        
        values = {} if has_index or type == dict else []
        for (errorIndication,
            errorStatus,
            errorIndex,
            varBinds) in iterator:

            if errorIndication:
                raise Exception(errorIndication)

            elif errorStatus:
                raise Exception('%s at %s', errorStatus.prettyPrint(),
                                    errorIndex and varBinds[int(errorIndex) - 1][0] or '?')

            else:
                if type == list or type == dict and has_index:
                    new_value = {}
                    new_index = None
                    for varBind in varBinds:
                        for (attribute, definition) in definitions.items():
                            bind_oid = varBind[0].prettyPrint()

                            if attribute == '_index' and definition == True:
                                new_index = varBind[0][-1]
                            elif bind_oid.startswith(definition[0]):
                                bind_value = definition[1](varBind[1])

                                if attribute == '_index':
                                    new_index = bind_value
                                else:
                                    new_value[attribute] = bind_value
                    
                    if has_index:
                        values[new_index] = new_value
                    else:
                        values.append(new_value)
                elif type == dict:
                    for varBind in varBinds:
                        for (attribute, definition) in definitions.items():
                            bind_oid = varBind[0].prettyPrint()
                            
                            if bind_oid == definition[0]:
                                values[attribute] = definition[1](varBind[1])
                else:
                    return type(varBinds[0][1])
        
        return values
