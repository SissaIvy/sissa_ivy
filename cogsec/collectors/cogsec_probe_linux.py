#!/usr/bin/env python3
import os, json, time, subprocess, shutil, datetime

def cpu_percent(interval=0.2):
    def read():
        with open('/proc/stat','r') as f:
            parts = f.readline().split()[1:8]
        vals = list(map(int, parts))
        idle = vals[3] + vals[4]
        total = sum(vals)
        return idle, total
    i1,t1 = read(); time.sleep(interval); i2,t2 = read()
    dt = t2 - t1; di = i2 - i1
    return round((1 - (di / dt if dt > 0 else 1)) * 100.0, 2)

def mem_percent():
    info = {}
    with open('/proc/meminfo') as f:
        for line in f:
            k,v = line.split(':',1)
            info[k.strip()] = int(v.strip().split()[0])  # kB
    total = info.get('MemTotal',1)
    avail = info.get('MemAvailable', info.get('MemFree',0))
    used = total - avail
    return round(used/total*100.0, 2)

def disk_max_percent():
    skip = {'tmpfs','devtmpfs','overlay','squashfs','proc','sysfs','cgroup','cgroup2','debugfs',
            'tracefs','ramfs','autofs','devpts','fusectl','mqueue','hugetlbfs','pstore','configfs'}
    mounts = set()
    with open('/proc/mounts') as f:
        for line in f:
            fs = line.split()[2]
            mp = line.split()[1]
            if fs in skip: continue
            mounts.add(mp)
    maxpct = 0.0
    for mp in mounts:
        try:
            st = os.statvfs(mp)
            total = st.f_frsize * st.f_blocks
            free  = st.f_frsize * st.f_bavail
            used  = total - free
            if total > 0:
                pct = round(used/total*100.0, 2)
                if pct > maxpct: maxpct = pct
        except Exception:
            pass
    return maxpct

def firewall_status():
    def run(cmd):
        try:
            return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True, timeout=3).strip()
        except Exception:
            return ""
    if shutil.which('ufw'):
        return {'manager':'ufw','enabled': 'Status: active' in run('ufw status')}
    if shutil.which('firewall-cmd'):
        return {'manager':'firewalld','enabled': run('firewall-cmd --state') == 'running'}
    if shutil.which('nft'):
        out = run('nft list ruleset | wc -l')
        try: return {'manager':'nftables','enabled': int(out) > 0}
        except: return {'manager':'nftables','enabled': None}
    if shutil.which('iptables'):
        out = run('iptables -S | wc -l')
        try: return {'manager':'iptables','enabled': int(out) > 0}
        except: return {'manager':'iptables','enabled': None}
    return {'manager': None, 'enabled': None}

def av_status():
    services = ['falcon-sensor','xagt','ds_agent','sav-protect','cylance','symcfgd','wsdaemon','mfevtps','clamd','clamav-daemon']
    active=[]
    if shutil.which('systemctl'):
        for s in services:
            try:
                r = subprocess.run(['systemctl','is-active',s], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2)
                if r.returncode==0 and r.stdout.strip()=='active': active.append(s)
            except: pass
    else:
        for s in services:
            try:
                r = subprocess.run(['service',s,'status'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2)
                if 'running' in r.stdout.lower(): active.append(s)
            except: pass
    return sorted(set(active))

def listening_ports():
    if not shutil.which('ss'): return []
    try:
        out = subprocess.check_output(['ss','-lntup'], stderr=subprocess.DEVNULL, text=True, timeout=3)
    except Exception:
        return []
    ports=set()
    for ln in out.strip().splitlines()[1:]:
        try:
            local = ln.split()[3]
            port  = local.rsplit(':',1)[-1]
            if port.isdigit(): ports.add(int(port))
        except: pass
    return sorted(ports)

def net_bytes(interval=0.2):
    def read():
        rx=tx=0
        with open('/proc/net/dev') as f:
            for ln in f:
                if ':' not in ln: continue
                _, data = ln.split(':',1)
                vals = data.split()
                rx += int(vals[0]); tx += int(vals[8])
        return rx, tx
    r1,t1 = read(); time.sleep(interval); r2,t2 = read()
    return max(r2-r1,0), max(t2-t1,0)

def main():
    now = datetime.datetime.utcnow().isoformat()+'Z'
    host = os.uname().nodename.split('.')[0].lower()
    rec = {
        'host': host, 'timestamp': now, 'os': 'linux',
        'cpu': cpu_percent(), 'mem': mem_percent(), 'disk': disk_max_percent()
    }
    rx,tx = net_bytes(); rec['net_in']=rx; rec['net_out']=tx
    rec['firewall'] = firewall_status()
    rec['controls'] = {'av_services': av_status()}
    rec['listening_ports'] = listening_ports()
    print(json.dumps(rec))

if __name__ == '__main__':
    main()
