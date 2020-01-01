# hass-snmp-printer-sensor

[![GitHub Release][releases-shield]][releases] [![GitHub Activity][commits-shield]][commits] 
[![hacs][hacsbadge]](hacs) 
![Project Maintenance][maintenance-shield] 

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
  name: Test Printer
  host: test-printer.lan
  community: public
  version: '2c'
  timeout: 1
```
7. Restart HomeAssistant

## Roadmap
- Port more options to configure SNMP requests
- Better entity name generation
- Better offline printer handling