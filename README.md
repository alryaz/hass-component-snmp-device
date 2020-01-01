# hass-snmp-printer-sensor

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

_Add printer-related sensors for SNMP-supporting devices._

## Installation
1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `snmp_printer`.
4. Download _all_ the files from the `custom_components/snmp_printer/` directory (folder) in this repository. 
5. Place the files you downloaded in the new directory (folder) you created.
6. Add new sensor based on the following configuration example:
```yaml
- platform: snmp_printer
  # Prefix name for added sensors
  name: Test Printer
  # Printer host (required)
  host: test-printer.lan
  # Printer SNMP port (optional, default: 161)
  port: 161
  # Printer SNMP community (optional, default: 'public')
  community: public
  # Printer SNMP version (optional, default: '2c')
  version: '1'
  # Timeout to get values (optional, default: '1')
  timeout: 1
```
7. Restart HomeAssistant

## Quirks
- Sensors are not retained over HomeAssistant restarts (although their data is), and will be inexistent if the printer is offline at boot

## Roadmap
- Port more options to configure SNMP requests
- Better entity name generation
- Better offline printer handling