# hass-component-snmp-device

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

_Add device-related sensors for SNMP-supporting devices with ease._

## Installation
1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `snmp_device`.
1. Download _all_ the files from the `custom_components/snmp_device/` directory (folder) in this repository. 
1. Place the files you downloaded in the new directory (folder) you created.

### GUI configuration (__with autodiscovery!__)
To add devices via HomeAssistant's user interface, navigate to _Integrations_ submenu of _Settings_, and
search for _SNMP Device_. Follow the wizard to set up your device.

### YAML configuration via platform
```yaml
sensor:
- platform: snmp_device
  # Prefix name for added sensors (optional)
  name: Test Printer
  # Device host (required)
  host: test-printer.lan
  # Device type (required, available: 'printer', 'computer')
  type: 'printer'
  # SNMP port (optional, default: 161)
  port: 161
  # SNMP community (optional, default: 'public')
  community: public
  # SNMP version (optional, default: '2c')
  version: '1'
  # Timeout to get values (optional, default: '1')
  timeout: 1
```

### YAML configuration via domain
```yaml
snmp_device:
  # Prefix name for added sensors (optional)
  name: Test Printer
  # Device host (required)
  host: test-printer.lan
  # Device type (required, available: 'printer', 'computer')
  type: 'printer'
  # SNMP port (optional, default: 161)
  port: 161
  # SNMP community (optional, default: 'public')
  community: public
  # SNMP version (optional, default: '2c')
  version: '1'
  # Timeout to get values (optional, default: '1')
  timeout: 1
```

## Supported device types
- `printer`: supports the following sensors: _Status_, _Mileage_, _Paper Inputs_ (a separate sensor for each), and _Supplies_ (a separate sensor for each)
- `computer`: supports the following sensors: _Status_

## Roadmap
- Port more options to configure SNMP requests
- Better offline printer handling
