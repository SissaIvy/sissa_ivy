import json, re
from datetime import datetime
from pathlib import Path

# Synthetic samples modeled after cogsec_probe_linux main() output
SAMPLE_NORMAL = {
    'host': 'alpha',
    'timestamp': '2025-09-15T12:34:56Z',
    'os': 'linux',
    'cpu': 12.34,
    'mem': 45.67,
    'disk': 78.9,
    'net_in': 1024,
    'net_out': 2048,
    'firewall': {'manager': 'ufw', 'enabled': True},
    'controls': {'av_services': ['clamd','falcon-sensor']},
    'listening_ports': [22,443,8080]
}

# Edge case: missing firewall tool, no AV services, no listening ports, zero network, high cpu/mem=0
SAMPLE_EDGE = {
    'host': 'beta',
    'timestamp': '2025-09-15T00:00:00Z',
    'os': 'linux',
    'cpu': 0.0,
    'mem': 0.0,
    'disk': 0.0,
    'net_in': 0,
    'net_out': 0,
    'firewall': {'manager': None, 'enabled': None},
    'controls': {'av_services': []},
    'listening_ports': []
}

REQUIRED_TOP_LEVEL = {'host','timestamp','os','cpu','mem','disk','net_in','net_out','firewall','controls','listening_ports'}

def validate_record(rec: dict):
    # Presence
    missing = REQUIRED_TOP_LEVEL - rec.keys()
    assert not missing, f"Missing keys: {missing}"

    # Types & ranges
    assert isinstance(rec['host'], str) and rec['host'], 'host must be non-empty str'

    # Timestamp basic ISO8601Z check
    assert isinstance(rec['timestamp'], str) and rec['timestamp'].endswith('Z'), 'timestamp must end with Z'
    # Loose parse (allow fractional seconds)
    ts_core = rec['timestamp'][:-1]
    fmt_variants = ['%Y-%m-%dT%H:%M:%S','%Y-%m-%dT%H:%M:%S.%f']
    parsed = None
    for fmt in fmt_variants:
        try:
            parsed = datetime.strptime(ts_core, fmt)
            break
        except ValueError:
            pass
    assert parsed is not None, 'timestamp not ISO8601 seconds or fractional'

    assert rec['os'] == 'linux', 'os must be linux'

    for k in ['cpu','mem','disk']:
        assert isinstance(rec[k], (int,float)), f"{k} must be number"
        assert 0.0 <= float(rec[k]) <= 100.0, f"{k} percent out of range"

    for k in ['net_in','net_out']:
        assert isinstance(rec[k], int) and rec[k] >= 0, f"{k} must be non-negative int"

    fw = rec['firewall']
    assert isinstance(fw, dict) and 'manager' in fw and 'enabled' in fw
    assert (fw['manager'] is None) or isinstance(fw['manager'], str)
    assert (fw['enabled'] in (True, False, None)), 'enabled must be tri-state'

    ctrls = rec['controls']
    assert isinstance(ctrls, dict) and 'av_services' in ctrls
    assert isinstance(ctrls['av_services'], list)
    for svc in ctrls['av_services']:
        assert isinstance(svc, str) and svc, 'av service names must be non-empty strings'

    ports = rec['listening_ports']
    assert isinstance(ports, list)
    for p in ports:
        assert isinstance(p, int) and 0 < p < 65536, 'port out of range'


def test_normal_sample_valid():
    validate_record(SAMPLE_NORMAL)


def test_edge_sample_valid():
    validate_record(SAMPLE_EDGE)


def test_percent_bounds_enforced():
    bad = dict(SAMPLE_NORMAL)
    bad['cpu'] = 150
    try:
        validate_record(bad)
    except AssertionError as e:
        assert 'cpu percent out of range' in str(e)
    else:
        assert False, 'Expected assertion for cpu > 100'
