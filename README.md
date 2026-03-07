# sissa_ivy

# 🧩 Summary of the Repository: **sissa_ivy**  
### *AI Senior Information Systems Service Analyst (#SISSA)*

## 🔍 **What This Project Is**
A lightweight, cross‑platform endpoint‑health and security‑posture collection toolkit.  
It provides **native probes for Windows and Linux** that gather system health, security status, and configuration data **without requiring a heavy agent**.

---

# 🖥️ Windows Probe  
### **Get-CogSecEndpointState.ps1**

- Uses **WMI/CIM**, **registry**, **performance counters**, and **Microsoft Defender cmdlets**.  
- Produces **one JSON record per run**.  
- Can also append a **CSV line** matching the `cogsec_workflow.py` health schema.  
- Example usage includes a **Scheduled Task running every 5 minutes**.

---

# 🐧 Linux Probe  
### **cogsec_probe_linux.py**

- Reads from `/proc`, package/firewall status, listening ports, and AV services.  
- Outputs a **JSON record** to stdout.  
- Designed to run via **systemd service + timer** (e.g., every 5 minutes).  
- Can write output to `/opt/cogsec/state.json`.

---

# 🔄 Integration  
Both probes can be executed or monitored by **Cribl Edge** as Exec sources, allowing their JSON output to be forwarded into existing pipelines.

---

# 📁 Repository Structure  
- **collectors/** – Windows & Linux probe scripts  
- **normalize_terminology.py** – Script for terminology normalization  
- **LICENSE** – Apache‑2.0  
- **README.md** – Documentation  
- **Languages:** Python (76.9%), PowerShell (23.1%)

---

# 👤 Contributor  
- **SissaIvy (Hakeem Moore)** – Sole listed contributor

---

If you want, I can also break this down into:

- A more concise executive summary  
- A technical architecture overview  
- A security‑focused analysis  
- A suggested roadmap or improvements  

Just tell me which direction you want to explore next.
Native endpoint probes for Windows and Linux that collect basic health and security posture
without relying on a heavyweight agent. The probes emit a compact JSON record and, for Windows,
optionally append a CSV line that matches the `cogsec_workflow.py` health schema.

## Collectors

### Windows: `Get-CogSecEndpointState.ps1`

* Queries WMI/CIM, registry, performance counters and Defender cmdlets.
* Outputs one JSON record per run and can append a health CSV line.
* Example scheduled task (every 5 minutes):

```powershell
$script = "C:\cogsec\Get-CogSecEndpointState.ps1"
$csv    = "C:\cogsec\health_metrics.csv"
$log    = "C:\cogsec\state.json"
schtasks /Create /SC MINUTE /MO 5 /TN "CogSec Probe" `
  /TR "powershell -NoProfile -ExecutionPolicy Bypass -File `"$script`" -CsvPath `"$csv`" -JsonPath `"$log`"" `
  /RU "SYSTEM" /RL HIGHEST /F
```

### Linux: `cogsec_probe_linux.py`

* Reads `/proc`, package/firewall status, listening ports and AV services.
* Prints a JSON record to stdout; make it executable and schedule via systemd:

```ini
# /etc/systemd/system/cogsec-probe.service
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/cogsec/collectors/cogsec_probe_linux.py | tee /opt/cogsec/state.json

# /etc/systemd/system/cogsec-probe.timer
[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Unit=cogsec-probe.service
```

Enable the timer with `systemctl enable --now cogsec-probe.timer`.

Both probes can be executed or monitored by **Cribl Edge** as Exec sources to forward
the JSON output into existing pipelines.
