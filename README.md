# sissa_ivy

Native endpoint probes for Windows and Linux that collect basic health and security posture
without relying on a heavyweight agent. The probes emit a compact JSON record and, for Windows,
optionally append a CSV line that matches the `cogsec_workflow.py` health schema.

## Collectors

### Windows: `probe_windows.ps1`

* Queries WMI/CIM, registry, performance counters and Defender cmdlets.
* Outputs one JSON record per run and can append a health CSV line.
* Example scheduled task (every 5 minutes):

```powershell
$script = "C:\cogsec\windows\probe_windows.ps1"
$csv    = "C:\cogsec\health_metrics.csv"
$log    = "C:\cogsec\state.json"
schtasks /Create /SC MINUTE /MO 5 /TN "CogSec Probe" `
  /TR "powershell -NoProfile -ExecutionPolicy Bypass -File `"$script`" -CsvPath `"$csv`" -JsonPath `"$log`"" `
  /RU "SYSTEM" /RL HIGHEST /F
```

### Linux: `probe_linux.py`

* Reads `/proc`, package/firewall status, listening ports and AV services.
* Prints a JSON record to stdout; make it executable and schedule via systemd:

```ini
# /etc/systemd/system/cogsec-probe.service
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/cogsec/collectors/linux/probe_linux.py | tee /opt/cogsec/state.json

# /etc/systemd/system/cogsec-probe.timer
[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Unit=cogsec-probe.service
```

Enable the timer with `systemctl enable --now cogsec-probe.timer`.

Both probes can be executed or monitored by **Cribl Edge** as Exec sources to forward
the JSON output into existing pipelines.
