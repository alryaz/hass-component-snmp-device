# SNMP Device Integration
_Add printer-related sensors for SNMP-supporting devices._

## Configuration
### Using GUI (__with autodiscovery!__)
To add devices via HomeAssistant's user interface, navigate to _Integrations_ submenu of _Settings_, and
search for _SNMP Device_. Follow the wizard to set up your device.

### Using YAML via platform
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

### Using YAML via domain
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
