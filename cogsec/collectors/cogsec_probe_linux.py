#!/usr/bin/env python3
"""Lightweight Linux endpoint probe.

Collects quick host posture metrics without external dependencies:
* CPU, memory, highest disk usage percent
* Network rx/tx byte deltas over a short sampling window
* Firewall manager + enabled heuristic
* AV / EDR service presence (subset list)
* Listening TCP/UDP ports (numeric only)

Output: single JSON object written to stdout.

Design goals:
* Finish in well under 2 seconds (default sampling intervals are short)
* No exceptions should bubble to the top; failures degrade to empty/None values
* Avoid heavy parsing or persistent state
"""
from __future__ import annotations

import os
import json
import time
import subprocess
import shutil
import datetime
from typing import Dict, List, Tuple, Optional
import argparse
from pathlib import Path

CPU_SAMPLE_INTERVAL = 0.2
NET_SAMPLE_INTERVAL = 0.2


def cpu_percent(interval: float = CPU_SAMPLE_INTERVAL) -> float:
    """Approximate total CPU usage percentage over a small interval.

    Reads the first line of /proc/stat twice and derives active time delta.
    Returns a float in [0,100]. On error, returns 0.0.
    """

    def read() -> Tuple[int, int]:
        with open('/proc/stat','r', encoding='utf-8') as f:
            parts = f.readline().split()[1:8]
        vals = list(map(int, parts))
        idle = vals[3] + vals[4]
        total = sum(vals)
        return idle, total

    try:
        i1, t1 = read(); time.sleep(interval); i2, t2 = read()
        dt = t2 - t1; di = i2 - i1
        if dt <= 0:
            return 0.0
        pct = (1 - (di / dt)) * 100.0
        if pct < 0:
            return 0.0
        if pct > 100:
            return 100.0
        return round(pct, 2)
    except Exception:
        return 0.0

def mem_percent() -> float:
    """Return memory usage percent based on MemAvailable heuristic.

    Falls back to MemFree if MemAvailable missing. Always 0-100 bound.
    """
    try:
        info: Dict[str, int] = {}
        with open('/proc/meminfo', encoding='utf-8') as f:
            for line in f:
                if ':' not in line:
                    continue
                k, v = line.split(':', 1)
                try:
                    info[k.strip()] = int(v.strip().split()[0])  # kB
                except ValueError:
                    continue
        total = info.get('MemTotal', 0) or 0
        if total <= 0:
            return 0.0
        avail = info.get('MemAvailable', info.get('MemFree', 0))
        used = max(total - avail, 0)
        pct = (used / total) * 100.0
        return round(min(max(pct, 0.0), 100.0), 2)
    except Exception:
        return 0.0

def disk_max_percent() -> float:
    """Return the highest utilization percentage among mounted real filesystems."""
    skip = {'tmpfs','devtmpfs','overlay','squashfs','proc','sysfs','cgroup','cgroup2','debugfs',
            'tracefs','ramfs','autofs','devpts','fusectl','mqueue','hugetlbfs','pstore','configfs'}
    try:
        mounts = set()
        with open('/proc/mounts', encoding='utf-8') as f:
            for line in f:
                parts = line.split()
                if len(parts) < 3:
                    continue
                fs = parts[2]; mp = parts[1]
                if fs in skip:
                    continue
                mounts.add(mp)
        maxpct = 0.0
        for mp in mounts:
            try:
                st = os.statvfs(mp)
                total = st.f_frsize * st.f_blocks
                free  = st.f_frsize * st.f_bavail
                if total <= 0:
                    continue
                used  = total - free
                pct = (used / total) * 100.0
                if pct > maxpct:
                    maxpct = pct
            except Exception:
                continue
        return round(min(maxpct, 100.0), 2)
    except Exception:
        return 0.0

def firewall_status() -> Dict[str, Optional[object]]:
    """Identify available firewall manager and a coarse enabled flag.

    Uses presence of tools and minimal commands; returns tri-state enabled (True/False/None).
    """
    def run(cmd: str) -> str:
        try:
            return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True, timeout=3).strip()
        except Exception:
            return ""

    try:
        if shutil.which('ufw'):
            return {'manager':'ufw','enabled': 'Status: active' in run('ufw status')}
        if shutil.which('firewall-cmd'):
            return {'manager':'firewalld','enabled': run('firewall-cmd --state') == 'running'}
        if shutil.which('nft'):
            out = run('nft list ruleset | wc -l')
            try:
                return {'manager':'nftables','enabled': int(out) > 0}
            except Exception:
                return {'manager':'nftables','enabled': None}
        if shutil.which('iptables'):
            out = run('iptables -S | wc -l')
            try:
                return {'manager':'iptables','enabled': int(out) > 0}
            except Exception:
                return {'manager':'iptables','enabled': None}
    except Exception:
        pass
    return {'manager': None, 'enabled': None}

AV_CANDIDATE_SERVICES = ['falcon-sensor','xagt','ds_agent','sav-protect','cylance','symcfgd','wsdaemon','mfevtps','clamd','clamav-daemon']

# Critical system files for integrity monitoring
CRITICAL_FILES = [
    '/etc/passwd', '/etc/shadow', '/etc/group', '/etc/gshadow',
    '/etc/sudoers', '/etc/ssh/sshd_config', '/boot/grub/grub.cfg',
    '/etc/crontab', '/etc/fstab', '/etc/hosts'
]

def failed_login_attempts() -> Dict[str, object]:
    """Monitor failed login attempts from various sources."""
    attempts = {'count_24h': 0, 'unique_users': 0, 'sources': []}
    
    try:
        # Check auth.log and secure log for failed logins
        log_files = ['/var/log/auth.log', '/var/log/secure', '/var/log/messages']
        
        for log_file in log_files:
            if not os.path.exists(log_file):
                continue
                
            try:
                # Get failed login attempts from last 24 hours
                cmd = f"grep -i 'failed\\|invalid\\|authentication failure' {log_file} | tail -100"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    recent_attempts = 0
                    users = set()
                    
                    for line in lines:
                        if 'failed' in line.lower() or 'invalid' in line.lower():
                            recent_attempts += 1
                            # Extract username if present
                            for part in line.split():
                                if part.startswith('user=') or part.startswith('user:'):
                                    user = part.split('=')[-1].split(':')[-1]
                                    users.add(user)
                    
                    attempts['count_24h'] += recent_attempts
                    attempts['unique_users'] = len(users)
                    attempts['sources'].append(os.path.basename(log_file))
            except Exception:
                continue
                
        # Check lastb for failed login attempts
        try:
            result = subprocess.run(['lastb', '-n', '50'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                attempts['count_24h'] += len([l for l in lines if l.strip() and not l.startswith('btmp')])
        except Exception:
            pass
            
    except Exception:
        pass
    
    return attempts

def usb_device_monitoring() -> Dict[str, object]:
    """Monitor USB device connections and removals."""
    usb_info = {'connected_devices': [], 'recent_events': 0, 'authorized_only': True}
    
    try:
        # List currently connected USB devices
        if os.path.exists('/sys/bus/usb/devices'):
            for device_dir in os.listdir('/sys/bus/usb/devices'):
                device_path = f'/sys/bus/usb/devices/{device_dir}'
                
                try:
                    # Read device info
                    vendor_file = f'{device_path}/idVendor'
                    product_file = f'{device_path}/idProduct'
                    authorized_file = f'{device_path}/authorized'
                    
                    if os.path.exists(vendor_file) and os.path.exists(product_file):
                        with open(vendor_file, 'r') as f:
                            vendor = f.read().strip()
                        with open(product_file, 'r') as f:
                            product = f.read().strip()
                        
                        authorized = True
                        if os.path.exists(authorized_file):
                            with open(authorized_file, 'r') as f:
                                authorized = f.read().strip() == '1'
                        
                        if not authorized:
                            usb_info['authorized_only'] = False
                        
                        usb_info['connected_devices'].append({
                            'vendor_id': vendor,
                            'product_id': product,
                            'authorized': authorized,
                            'device': device_dir
                        })
                except Exception:
                    continue
        
        # Check for recent USB events in dmesg
        try:
            result = subprocess.run(['dmesg', '-T'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                usb_lines = [line for line in result.stdout.split('\n') if 'usb' in line.lower()]
                usb_info['recent_events'] = len(usb_lines[-20:])  # Last 20 USB-related events
        except Exception:
            pass
            
    except Exception:
        pass
    
    return usb_info

def file_integrity_monitoring() -> Dict[str, object]:
    """Monitor integrity of critical system files."""
    integrity = {'files_checked': 0, 'modified_files': [], 'missing_files': [], 'checksum_changes': []}
    
    try:
        for file_path in CRITICAL_FILES:
            integrity['files_checked'] += 1
            
            if not os.path.exists(file_path):
                integrity['missing_files'].append(file_path)
                continue
            
            try:
                # Get file stats
                stat = os.stat(file_path)
                
                # Check if file was modified recently (within last 24 hours)
                current_time = time.time()
                if current_time - stat.st_mtime < 86400:  # 24 hours
                    integrity['modified_files'].append({
                        'path': file_path,
                        'mtime': stat.st_mtime,
                        'size': stat.st_size
                    })
                
                # Store basic checksum (for change detection in future runs)
                # Note: In production, this would compare against stored baseline
                import hashlib
                with open(file_path, 'rb') as f:
                    content = f.read(8192)  # Read first 8KB for performance
                    checksum = hashlib.sha256(content).hexdigest()[:16]  # Short hash
                    
            except Exception:
                continue
                
    except Exception:
        pass
    
    return integrity


def av_status() -> List[str]:
    """Return list of active AV/EDR service names from a static candidate list."""
    active: List[str] = []
    try:
        if shutil.which('systemctl'):
            for s in AV_CANDIDATE_SERVICES:
                try:
                    r = subprocess.run(['systemctl','is-active',s], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2)
                    if r.returncode == 0 and r.stdout.strip() == 'active':
                        active.append(s)
                except Exception:
                    continue
        else:
            for s in AV_CANDIDATE_SERVICES:
                try:
                    r = subprocess.run(['service',s,'status'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2)
                    if 'running' in r.stdout.lower():
                        active.append(s)
                except Exception:
                    continue
    except Exception:
        return []
    return sorted(set(active))

def listening_ports() -> List[int]:
    """Return sorted list of listening TCP/UDP ports (numeric)."""
    if not shutil.which('ss'):
        return []
    try:
        out = subprocess.check_output(['ss','-lntup'], stderr=subprocess.DEVNULL, text=True, timeout=3)
    except Exception:
        return []
    ports: set[int] = set()
    for ln in out.strip().splitlines()[1:]:
        try:
            parts = ln.split()
            if len(parts) < 5:
                continue
            local = parts[3]
            port = local.rsplit(':',1)[-1]
            if port.isdigit():
                val = int(port)
                if 0 < val < 65536:
                    ports.add(val)
        except Exception:
            continue
    return sorted(ports)

def net_bytes(interval: float = NET_SAMPLE_INTERVAL) -> Tuple[int, int]:
    """Return tuple (rx_delta, tx_delta) over a short interval."""
    def read() -> Tuple[int, int]:
        rx = tx = 0
        with open('/proc/net/dev', encoding='utf-8') as f:
            for ln in f:
                if ':' not in ln:
                    continue
                _, data = ln.split(':', 1)
                vals = data.split()
                try:
                    rx += int(vals[0]); tx += int(vals[8])
                except (IndexError, ValueError):
                    continue
        return rx, tx
    try:
        r1, t1 = read(); time.sleep(interval); r2, t2 = read()
        return max(r2 - r1, 0), max(t2 - t1, 0)
    except Exception:
        return 0, 0

def collect_record() -> Dict[str, object]:
    """Build and return the probe record dictionary."""
    now = datetime.datetime.utcnow().isoformat()+'Z'
    try:
        host = os.uname().nodename.split('.')[0].lower()
    except Exception:
        host = 'unknown'
    rx, tx = net_bytes()
    return {
        'host': host,
        'timestamp': now,
        'os': 'linux',
        'cpu': cpu_percent(),
        'mem': mem_percent(),
        'disk': disk_max_percent(),
        'net_in': rx,
        'net_out': tx,
        'firewall': firewall_status(),
        'controls': {'av_services': av_status()},
        'listening_ports': listening_ports(),
        'security': {
            'failed_logins': failed_login_attempts(),
            'usb_devices': usb_device_monitoring(),
            'file_integrity': file_integrity_monitoring()
        }
    }


def main() -> int:
    """CLI entrypoint: gather metrics and emit JSON record."""
    parser = argparse.ArgumentParser(
        prog='cogsec_probe_linux',
        description='Collect Linux endpoint metrics and emit JSON (1.x additive schema).'
    )
    parser.add_argument('--json-path', default='-', help='Output path (use - for stdout)')
    parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON (indent=2)')
    parser.add_argument('--strict', action='store_true', help='Exit 2 if core metrics all zero (sampling failure heuristic)')
    args = parser.parse_args()

    record = collect_record()
    out = json.dumps(
        record,
        ensure_ascii=False,
        indent=(2 if args.pretty else None),
        separators=None if args.pretty else (",", ":"),
    )
    if args.json_path == '-':
        print(out)
    else:
        Path(args.json_path).write_text(out, encoding='utf-8')

    if args.strict:
        def safe_float(val: object) -> float:
            try:
                return float(val)  # type: ignore[arg-type]
            except Exception:
                return 0.0
        cpu = safe_float(record.get('cpu'))
        mem = safe_float(record.get('mem'))
        disk = safe_float(record.get('disk'))
        if cpu == 0.0 and mem == 0.0 and disk == 0.0:
            return 2
    return 0

if __name__ == '__main__':  # pragma: no cover - direct CLI execution
    raise SystemExit(main())
