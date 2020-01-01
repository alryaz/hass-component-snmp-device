_Add printer-related sensors for SNMP-supporting devices._

# Usage
Add new sensor based on the following configuration example:
```
- platform: snmp_printer
  # Prefix name for added sensors (optional)
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

