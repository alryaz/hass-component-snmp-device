"""
Support for displaying collected data over SNMP.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.snmp/
"""
import asyncio
import logging
from datetime import timedelta
from typing import Optional, Dict, Any, Union, Tuple, List, TYPE_CHECKING, Type

from homeassistant.components.sensor import PLATFORM_SCHEMA, DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST, CONF_NAME, CONF_PORT, STATE_UNKNOWN, STATE_OFF,
    CONF_SCAN_INTERVAL, CONF_TIMEOUT,
    STATE_PROBLEM, STATE_IDLE, CONF_TYPE, EVENT_HOMEASSISTANT_START, STATE_OK)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import HomeAssistantType

from .const import DOMAIN, SUPPORTED_DEVICE_TYPES, SNMP_VERSIONS, CONF_VERSION, \
    CONF_COMMUNITY, DATA_DEVICE_CONFIGS, DEFAULT_SCAN_INTERVAL, SUPPLIES_ICONS, DEFAULT_SUPPLIES_ICON, \
    DATA_DEVICE_LISTENERS, DATA_DEVICE_ENTITIES
from .enums import CapacityLevelType, CapacityUnitType, PrinterDeviceStatus, PrinterActionStatus, SuppliesClass, \
    SuppliesType, CAPACITY_LEVEL_TYPE, PaperInputType, PrinterDetectedErrorState
from .schemas import DEVICE_SCHEMA

if TYPE_CHECKING:
    from .enums import _FriendlyEnum
    # noinspection PyProtectedMember
    from pysnmp.hlapi.transport import AbstractTransportTarget
    from pysnmp.hlapi import SnmpEngine, CommunityData, ContextData

REQUIREMENTS = ['pysnmp==4.4.12']

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPE_STATUS = 'status'
SENSOR_TYPE_MILEAGE = 'mileage'
SENSOR_TYPE_TONER = 'toner'
SENSOR_TYPE_PAPER_INPUT = 'paper_input'

STATE_MAPPING = {
    PrinterDeviceStatus.UNKNOWN: STATE_UNKNOWN,
    PrinterDeviceStatus.WARNING: STATE_PROBLEM,
    PrinterDeviceStatus.DOWN: STATE_OFF,
    PrinterActionStatus.UNKNOWN: STATE_UNKNOWN,
    PrinterActionStatus.IDLE: STATE_IDLE,
    #PrinterStatus.PRINTING: STATE_ON,
    #PrinterStatus.WARMUP: STATE_OPENING,
    PrinterActionStatus.OFFLINE: STATE_OFF,
}

INFO_KEY = 'info_key'
ENTITY = 'entity'
ATTR_ATTRIBUTES = 'attributes'

SENSOR_OID_DEFINITIONS = {
    "printer": {
    }
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(DEVICE_SCHEMA.schema)


def level_capacity(level: Union[CapacityLevelType, int], capacity: Union[CapacityLevelType, int]) -> Tuple[Union[str, int], Optional[str], Union[str, int]]:
    unit_of_measurement = None

    if isinstance(level, CapacityLevelType):
        level = level.friendly_name
    else:
        unit_of_measurement = 'sheets'

    if isinstance(capacity, CapacityLevelType):
        capacity = capacity.friendly_name

    # elif capacity > 0 and level >= 0:
    #     new_state = '{:.0f}'.format(level * 100 / capacity)
    #     unit_of_measurement = '%'

    return level, unit_of_measurement, capacity


def pysnmp_get(snmp_engine: 'SnmpEngine', community_obj: 'CommunityData', target_obj: 'AbstractTransportTarget',
               context_obj: 'ContextData', sub_keys):
    from pysnmp.hlapi import ObjectType, ObjectIdentity, getCmd
    #from pysnmp.proto.rfc1905 import endOfMibView

    return_data = {}
    var_binds = [
        ObjectType(ObjectIdentity(oid))
        for oid, converter in sub_keys.values()
    ]

    for (errorIndication,
         errorStatus,
         errorIndex,
         varBindTable) in getCmd(snmp_engine,
                                 community_obj,
                                 target_obj,
                                 context_obj,
                                 *var_binds,
                                 lexicographicalMode=False,
                                 lookupMib=False):
        if errorIndication:
            _LOGGER.error(errorIndication)
            break
        elif errorStatus:
            _LOGGER.error('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and var_binds[int(errorIndex) - 1][0] or '?'
            ))
        else:
            for (oid_obj, val_obj), (sub_key_name, (oid, converter)) in zip(varBindTable, sub_keys.items()):
                return_data[sub_key_name] = converter(val_obj)

    return return_data

def pysnmp_next(snmp_engine: 'SnmpEngine', community_obj: 'CommunityData', target_obj: 'AbstractTransportTarget',
                context_obj: 'ContextData', sub_keys, index_oid=None):
    from pysnmp.hlapi import ObjectType, ObjectIdentity, nextCmd
    from pysnmp.proto.rfc1905 import endOfMibView

    return_data = {}
    var_binds = [
        ObjectType(ObjectIdentity(oid))
        for oid, converter in sub_keys.values()
    ]
    index_converter = None
    if isinstance(index_oid, tuple):
        var_binds.insert(0, ObjectType(ObjectIdentity(index_oid[0])))
        index_converter = index_oid[1]

    for (error_indication,
         error_status,
         error_index,
         var_bind_table) in nextCmd(snmp_engine,
                                    community_obj,
                                    target_obj,
                                    context_obj,
                                    *var_binds,
                                    lexicographicMode=False,
                                    lookupMib=False):

        if error_indication:
            _LOGGER.error(error_indication)
            break
        elif error_status:
            _LOGGER.error('%s at %s' % (
                error_status.prettyPrint(),
                error_index and var_binds[int(error_index) - 1][0] or '?'
            ))
        else:
            current_index = None
            current_data = dict()
            var_bind_iter = iter(var_bind_table)

            if index_converter is not None:
                oid_obj, val_obj = next(var_bind_iter)
                if val_obj.isSameTypeWith(endOfMibView):
                    break
                current_index = index_converter(val_obj)

            for (oid_obj, val_obj), (sub_key_name, (oid, converter)) in zip(var_bind_iter, sub_keys.items()):
                if val_obj.isSameTypeWith(endOfMibView):
                    break

                if current_index is None:
                    current_index = converter(val_obj) if sub_key_name == '_index' else oid_obj[-1]

                current_data[sub_key_name] = converter(val_obj)

            return_data[current_index] = current_data

    return return_data


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the SNMP sensor."""
    from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget

    _LOGGER.debug('config: %s', config)

    device_type = config[CONF_TYPE]
    host = config[CONF_HOST]
    port = config[CONF_PORT]
    name = config.get(CONF_NAME) or device_type.capitalize()

    scan_interval = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    if isinstance(scan_interval, int):
        scan_interval = timedelta(seconds=scan_interval)

    community = config[CONF_COMMUNITY]
    timeout = config[CONF_TIMEOUT]
    snmp_version = SNMP_VERSIONS[config[CONF_VERSION]]

    try:
        engine = SnmpEngine()
        community_data = CommunityData(community, mpModel=snmp_version)
        transport_target = UdpTransportTarget((host, port), timeout=timeout, retries=0)

        sensor_class: Type[_SNMPSensor] = globals()[SUPPORTED_DEVICE_TYPES[device_type]]

        def create_entities():
            _LOGGER.debug('Creating entities with name %s, host %s, port %s' % (name, host, port))
            first_retrieved_data = sensor_class.retrieve_data(
                snmp_engine=engine,
                community_data=community_data,
                transport_target=transport_target
            )
            return sensor_class.create_sensors(
                host=host, port=port,
                base_name=name,
                sensor_types=None,
                received_data=first_retrieved_data
            )

        created_entities: List[_SNMPSensor] = await hass.async_add_executor_job(create_entities)
        added_entities: List[_SNMPSensor] = list()

        async def update_entities(*_):
            if not added_entities:
                _LOGGER.debug('Added entities for %s:%d is empty, not updating', host, port)
                return

            retrieved_data = sensor_class.retrieve_data(
                snmp_engine=engine,
                community_data=community_data,
                transport_target=transport_target
            )

            _LOGGER.debug('Received update data: %s', retrieved_data)

            tasks = []
            for entity in added_entities:
                if entity.update_sensor_attributes(retrieved_data):
                    _LOGGER.debug('Updating attributes for %s', entity)
                    tasks.append(entity.async_update_ha_state())
                else:
                    _LOGGER.debug('Skipping attribute update for %s', entity)
            if tasks:
                await asyncio.wait(tasks)

        hass.data.setdefault(DATA_DEVICE_LISTENERS, dict())
        hass.data[DATA_DEVICE_LISTENERS][(host, port)] = (update_entities, scan_interval, None)

        hass.data.setdefault(DATA_DEVICE_ENTITIES, dict())
        hass.data[DATA_DEVICE_ENTITIES][(host, port)] = added_entities

        async_add_entities(created_entities)

        return True

    except Exception as e:
        _LOGGER.warning('Device unavailable, retrying later')
        _LOGGER.exception('retry reason: %s' % str(e))

        raise PlatformNotReady

async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry, async_add_devices):
    _LOGGER.debug('Setting up entry %s for component %s' % (config_entry.entry_id, SENSOR_DOMAIN))
    host = config_entry.data[CONF_HOST]
    port = config_entry.data[CONF_PORT]
    config = hass.data[DATA_DEVICE_CONFIGS][(host, port)]

    return await async_setup_platform(
        hass=hass,
        config=config,
        async_add_entities=async_add_devices,
        discovery_info=None
    )

async def async_unload_entry(hass: HomeAssistantType, config_entry: ConfigEntry):
    device_listeners = hass.data.get(DATA_DEVICE_LISTENERS)
    host = config_entry.data[CONF_HOST]
    port = config_entry.data[CONF_PORT]
    _LOGGER.debug('Current device listeners: %s' % device_listeners)
    _LOGGER.debug('Unloading sensor entry for %s:%d', host, port)
    if device_listeners and (host, port) in device_listeners:
        device_listeners[(host, port)]()

    return True

class _SNMPSensor(RestoreEntity):
    """Representation of a SNMP sensor."""
    single_sensor_types: List[str] = NotImplemented
    multi_sensor_types: Dict[str, str] = NotImplemented
    update_oid_mapping = NotImplemented
    def __init__(self, host, port, sensor_type, base_name: str, entity_index: Optional[int] = None,
                 received_data: Optional[dict] = None):
        """Initialize the sensor."""
        self._host = host
        self._port = port
        self._sensor_type = sensor_type
        self._received_data = received_data
        self._entity_index = entity_index
        self._base_name = base_name

        self._icon = None
        self._last_data = None
        self._state = None
        self._attributes = None
        self._unit_of_measurement = None
        self._name = None

        if received_data is not None:
            self.update_sensor_attributes(received_data)

        _LOGGER.debug('Created %s with base_name %s' % (self, base_name))

    @classmethod
    def create_sensors(cls, host, port, base_name, sensor_types, received_data) -> List['_SNMPSensor']:
        new_entities = []

        # @TODO: respect `sensor_types` argument

        for sensor_type in cls.single_sensor_types:
            new_entities.append(cls(
                host=host, port=port,
                base_name=base_name,
                sensor_type=sensor_type,
                received_data=received_data,
            ))

        for sensor_type, data_key in cls.multi_sensor_types.items():
            this_data = received_data.get(data_key)
            if this_data:
                for index in this_data.keys():
                    new_entities.append(cls(
                        host=host, port=port,
                        base_name=base_name,
                        sensor_type=sensor_type,
                        entity_index=index,
                        received_data=received_data,
                    ))

        return new_entities

    @classmethod
    def retrieve_data(cls, snmp_engine: 'SnmpEngine', community_data: 'CommunityData',
                      transport_target: 'AbstractTransportTarget') -> Dict[str, Union[Dict[int, Dict[str, Any]], Dict[str, Any]]]:
        from pysnmp.hlapi import ContextData

        context_obj = ContextData()
        received_data = dict()
        for (key_name, index_oid), sub_keys in cls.update_oid_mapping.items():
            received_data[key_name] = (
                pysnmp_get(snmp_engine, community_data, transport_target, context_obj, sub_keys)
                if not index_oid else
                pysnmp_next(snmp_engine, community_data, transport_target, context_obj, sub_keys, index_oid)
            )

        if hasattr(cls, 'get_additional_info_keys'):
            sub_keys, base_info = cls.get_additional_info_keys(received_data)
            if sub_keys:
                new_data = pysnmp_get(snmp_engine, community_data, transport_target, context_obj, sub_keys)
                if base_info:
                    base_info.update(new_data)
                    received_data['additional_info'] = base_info
                else:
                    received_data['additional_info'] = new_data
            else:
                received_data['additional_info'] = base_info if base_info else dict()

        return received_data

    def update_sensor_attributes(self, new_data: dict) -> bool:
        raise NotImplementedError

    async def async_will_remove_from_hass(self) -> None:
        key = (self._host, self._port)
        entities = self.hass.data[DATA_DEVICE_ENTITIES][key]
        entities.remove(self)
        listener = self.hass.data[DATA_DEVICE_LISTENERS][key]
        if not entities and listener[2] is not None:
            _LOGGER.debug('Stopping update checker for %s:%d', *key)
            # noinspection PyTypeChecker
            listener[2]()
            self.hass.data[DATA_DEVICE_LISTENERS][key] = (listener[0], listener[1], None)

    async def async_added_to_hass(self) -> None:
        _LOGGER.debug('Added %s to HomeAssistant', self)
        key = (self._host, self._port)
        self.hass.data[DATA_DEVICE_ENTITIES][key].append(self)
        listener = self.hass.data[DATA_DEVICE_LISTENERS][key]
        if listener[2] is None:
            _LOGGER.debug('Starting update checker for %s:%d', *key)
            # noinspection PyTypeChecker
            tracker_stop = async_track_time_interval(self.hass, listener[0], interval=listener[1])
            self.hass.data[DATA_DEVICE_LISTENERS][key] = (listener[0], listener[1], tracker_stop)

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
        return self._base_name + ' ' + self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def unique_id(self) -> Optional[str]:
        """Return a unique ID."""
        unique_id_parts = [
            DOMAIN,
            self._host,
            self._port,
            SENSOR_DOMAIN,
            self._sensor_type,
        ]
        if self._entity_index is not None:
            unique_id_parts.append(self._entity_index)

        return '_'.join(map(str, unique_id_parts))

    @property
    def device_info_sw_version(self) -> Optional[str]:
        if self._last_data and 'additional_info' in self._last_data:
            return self._last_data['additional_info'].get('sw_version')

    @property
    def device_info_model(self) -> Optional[str]:
        if self._last_data and 'additional_info' in self._last_data:
            return self._last_data['additional_info'].get('model')

    @property
    def device_info_manufacturer(self) -> Optional[str]:
        if self._last_data and 'additional_info' in self._last_data:
            return self._last_data['additional_info'].get('manufacturer')

    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        """Return device specific attributes."""
        device_info = {
            "identifiers": {(DOMAIN, self._host + ':' + str(self._port))},
            "name": self._base_name,
            "model": self.device_info_model,
            "manufacturer": self.device_info_manufacturer,
            "sw_version": self.device_info_sw_version,
        }

        network_info: Optional[Dict[str, Dict[str, Any]]] = self._last_data.get('network_info')
        if network_info:
            device_info["connections"] = {
                (CONNECTION_NETWORK_MAC, network_info[interface]['phys_address'])
                for interface in sorted(network_info.keys())
            }

        return device_info

    @property
    def should_poll(self) -> bool:
        """Disable sensor polling."""
        return False

class SNMPPrinterSensor(_SNMPSensor):
    """Representation of a printer SNMP sensor."""
    single_sensor_types = [SENSOR_TYPE_STATUS, SENSOR_TYPE_MILEAGE]
    multi_sensor_types = {SENSOR_TYPE_TONER: 'supplies', SENSOR_TYPE_PAPER_INPUT: 'paper_inputs'}
    update_oid_mapping = {
        ('info',                False): {
            'model':            ('1.3.6.1.2.1.25.3.2.1.3.1', str),
            #'device_id':        ('1.3.6.1.2.1.25.3.2.1.4.1', str),
            'mileage':          ('1.3.6.1.2.1.43.10.2.1.4.1.1', int),
            'printer_status':   ('1.3.6.1.2.1.25.3.5.1.1.1', PrinterActionStatus),
            'device_status':    ('1.3.6.1.2.1.25.3.2.1.5.1', PrinterDeviceStatus),
            'error_state':      ('1.3.6.1.2.1.25.3.5.1.2.1', PrinterDetectedErrorState.decode),
            'description':      ('1.3.6.1.2.1.1.1.0', str),
        },
        ('network_info',        ('1.3.6.1.2.1.2.2.1.2', str)): {
            'type':             ('1.3.6.1.2.1.2.2.1.1', str),
            'phys_address':     ('1.3.6.1.2.1.2.2.1.6', lambda x: ':'.join(['%02x' % octet for octet in x.asNumbers()])),
        },
        ('supplies',            True): {
            'marker_index':     ('1.3.6.1.2.1.43.11.1.1.2.1', int),
            'colorant_index':   ('1.3.6.1.2.1.43.11.1.1.3.1', int),
            'description':      ('1.3.6.1.2.1.43.11.1.1.6.1', str),
            'class':            ('1.3.6.1.2.1.43.11.1.1.4.1', SuppliesClass),
            'type':             ('1.3.6.1.2.1.43.11.1.1.5.1', SuppliesType),
            'capacity':         ('1.3.6.1.2.1.43.11.1.1.8.1', CAPACITY_LEVEL_TYPE),
            'level':            ('1.3.6.1.2.1.43.11.1.1.9.1', CAPACITY_LEVEL_TYPE),
        },
        ('colorants',           True): {
            'marker_index':     ('1.3.6.1.2.1.43.12.1.1.2.1', int),
            'color':            ('1.3.6.1.2.1.43.12.1.1.4.1', str),
            'tonality':         ('1.3.6.1.2.1.43.12.1.1.5.1', int),
        },
        ('paper_inputs',        True): {
            'type':             ('1.3.6.1.2.1.43.8.2.1.2.1', PaperInputType),
            'unit':             ('1.3.6.1.2.1.43.8.2.1.8.1', CapacityUnitType),
            'capacity':         ('1.3.6.1.2.1.43.8.2.1.9.1', CAPACITY_LEVEL_TYPE),
            'level':            ('1.3.6.1.2.1.43.8.2.1.10.1', CAPACITY_LEVEL_TYPE),
            'media':            ('1.3.6.1.2.1.43.8.2.1.12.1', lambda x: bytes(x).decode('utf-8')),
            'serial':           ('1.3.6.1.2.1.43.8.2.1.17.1', str),
            'model':            ('1.3.6.1.2.1.43.8.2.1.18.1', str),
        },
    }

    @classmethod
    def get_additional_info_keys(cls, retrieved_data):
        sub_keys = dict()
        base_info = dict()

        if 'info' in retrieved_data:
            description = retrieved_data['info'].get('description')
            if description:
                lower_description = description.lower()
                if 'panasonic' in lower_description:
                    base_info['manufacturer'] = 'Panasonic'
                    if 'kx-mb' in lower_description:
                        base_info['model'] = description[10:]
                        sub_keys['sw_version'] = ('1.3.6.1.4.1.258.405.1.1.1.4.0', lambda s: str(s).strip())
                elif 'kyocera' in lower_description:
                    base_info['manufacturer'] = 'Kyocera'
                    sub_keys['sw_version'] = ('1.3.6.1.4.1.1347.43.5.4.1.5.1.1', str)
                    sub_keys['model'] = ('1.3.6.1.4.1.1347.43.5.1.1.1.1', str)
        return sub_keys, base_info

    def update_sensor_attributes(self, new_data):
        self._last_data = new_data

        new_icon = self._icon
        new_state = self._state
        new_attributes = self._attributes
        new_unit = self._unit_of_measurement
        new_name = self._name
        if self._sensor_type == SENSOR_TYPE_STATUS:
            new_name = 'Status'
            sensor_data = new_data['info']
            error_state = sensor_data['error_state']

            new_state = STATE_PROBLEM if error_state else sensor_data['printer_status'].friendly_name
            new_icon = 'mdi:printer-alert' if error_state else 'mdi:printer-check'
            new_attributes = {
                'device_status': sensor_data['device_status'].friendly_name,
                'error_state': [e.friendly_name for e in error_state] if error_state else None,
            }

        elif self._sensor_type == SENSOR_TYPE_MILEAGE:
            new_name = 'Mileage'
            sensor_data = new_data['info']
            new_state = sensor_data['mileage']
            new_icon = 'mdi:counter'
            new_unit = 'sheets'

        elif self._sensor_type == SENSOR_TYPE_PAPER_INPUT:
            new_icon = 'mdi:tray-full'
            sensor_data = new_data['paper_inputs'].get(self._entity_index)
            if sensor_data:
                new_name = sensor_data['model']
                new_state, new_unit, capacity = level_capacity(sensor_data['level'], sensor_data['capacity'])
                new_attributes = {
                    'capacity': capacity,
                    'type': sensor_data['type'].friendly_name,
                    'model': sensor_data['model'],
                }
            else:
                new_state = STATE_UNKNOWN

        elif self._sensor_type == SENSOR_TYPE_TONER:
            sensor_data = new_data['supplies'].get(self._entity_index)
            if sensor_data:
                new_name = sensor_data['description']
                new_icon = SUPPLIES_ICONS.get(sensor_data['type'], DEFAULT_SUPPLIES_ICON)
                new_state, new_unit, capacity = level_capacity(sensor_data['level'], sensor_data['capacity'])
                new_attributes = {
                    'capacity': capacity,
                    'type': sensor_data['type'].friendly_name,
                    'model': sensor_data['description'],
                }

                if sensor_data['colorant_index'] > 0:
                    colorants = new_data.get('colorants')
                    if colorants:
                        colorant = colorants.get(sensor_data['colorant_index'])
                        if colorant:
                            new_attributes['color'] = colorant['color']
                            new_name = colorant['color'].capitalize() + ' ' + new_name

        needs_update = False
        for new_value, attribute in [
            (new_state, '_state'),
            (new_unit, '_unit_of_measurement'),
            (new_attributes, '_attributes'),
            (new_name, '_name'),
            (new_icon, '_icon'),
        ]:
            if new_value != getattr(self, attribute):
                needs_update = True
                setattr(self, attribute, new_value)

        return needs_update

    @property
    def device_info_model(self) -> Optional[str]:
        additional_info_model = self._last_data['additional_info'].get('model')
        if additional_info_model:
            return additional_info_model

        return self._last_data['info'].get('model') or None

    @property
    def device_info_manufacturer(self) -> Optional[str]:
        additional_info_manufacturer = self._last_data['additional_info'].get('manufacturer')
        if additional_info_manufacturer:
            return additional_info_manufacturer

        info = self._last_data.get('info')
        if info:
            description = info.get('description')
            if description:
                stripped_description = str(description).strip()
                if stripped_description:
                    return stripped_description.split(' ')[0]
        return None


class SNMPComputerSensor(_SNMPSensor):
    single_sensor_types = [SENSOR_TYPE_STATUS]
    multi_sensor_types = {}
    update_oid_mapping = {
        ('info', False): {
            'description':  ('1.3.6.1.2.1.1.1.0', str),
            'uptime':       ('1.3.6.1.2.1.1.3.0', str),
            'name':         ('1.3.6.1.2.1.1.5.0', str),
        },
    }

    def update_sensor_attributes(self, new_data):
        self._last_data = new_data

        new_unit = self._unit_of_measurement
        if self._sensor_type == SENSOR_TYPE_STATUS:
            new_name = 'Status'
            new_state = STATE_OK  # @TODO: more attributes to yield state

            new_icon = 'mdi:desktop-tower'
            new_attributes = {
                'uptime': new_data['info']['uptime'],
            }
        else:
            _LOGGER.error('Unsupported sensor type: %s' % self._sensor_type)
            return False

        needs_update = False
        for new_value, attribute in [
            (new_state, '_state'),
            (new_unit, '_unit_of_measurement'),
            (new_attributes, '_attributes'),
            (new_name, '_name'),
            (new_icon, '_icon'),
        ]:
            if new_value != getattr(self, attribute):
                needs_update = True
                setattr(self, attribute, new_value)

        return needs_update

    @classmethod
    def get_additional_info_keys(cls, retrieved_data):
        sub_keys = dict()
        base_info = dict()
        description = retrieved_data['info'].get('description')
        if description:
            lower_description = description.lower()
            if 'linux' in lower_description or 'unix' in lower_description:
                parts = description.split(' ')
                base_info['model'] = parts[0]
                #base_info['hostname'] = parts[1]
                base_info['sw_version'] = parts[2]
            elif 'windows' in lower_description:
                parts = description.split('\n')
                base_info['model'] = 'Windows'
                base_info['sw_version'] = parts[2][9:] # 'Software: (value)'
        return sub_keys, base_info