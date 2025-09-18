#!/usr/bin/env python3
"""
Real-time Security Dashboard for SISSA Ivy
Visualizes endpoint security metrics from enhanced probes
"""

import json
import time
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import sys

try:
    import flask
    from flask import Flask, render_template, jsonify, request
    import plotly
    import plotly.graph_objs as go
    import plotly.express as px
    from plotly.utils import PlotlyJSONEncoder
except ImportError:
    print("Required packages not installed. Install with:")
    print("pip install flask plotly pandas")
    sys.exit(1)

app = Flask(__name__)

class SecurityMetricsCollector:
    """Collects and aggregates security metrics from probes"""
    
    def __init__(self, probe_paths: Dict[str, str]):
        self.probe_paths = probe_paths
        self.metrics_history: List[Dict] = []
        self.alerts: List[Dict] = []
        self.collection_interval = 60  # seconds
        self.running = False
        
        # Alert thresholds
        self.thresholds = {
            'failed_logins_warning': 10,
            'failed_logins_critical': 50,
            'file_changes_warning': 1,
            'usb_devices_warning': 1,
            'cpu_warning': 80,
            'memory_warning': 85,
            'disk_warning': 90
        }
    
    def collect_probe_data(self, probe_type: str, probe_path: str) -> Optional[Dict]:
        """Execute probe and return metrics"""
        try:
            if probe_type == 'linux':
                result = subprocess.run(
                    ['python3', probe_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            elif probe_type == 'windows':
                result = subprocess.run(
                    ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', probe_path],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
            else:
                return None
                
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            print(f"Error collecting {probe_type} probe data: {e}")
        return None
    
    def analyze_security_metrics(self, metrics: Dict) -> List[Dict]:
        """Analyze metrics and generate alerts"""
        alerts = []
        timestamp = datetime.now().isoformat()
        
        # Failed login analysis
        if 'security' in metrics and 'failed_logins' in metrics['security']:
            failed_count = metrics['security']['failed_logins'].get('count_24h', 0)
            if failed_count >= self.thresholds['failed_logins_critical']:
                alerts.append({
                    'timestamp': timestamp,
                    'severity': 'critical',
                    'type': 'authentication',
                    'message': f"Critical: {failed_count} failed login attempts detected",
                    'host': metrics.get('host', 'unknown'),
                    'value': failed_count
                })
            elif failed_count >= self.thresholds['failed_logins_warning']:
                alerts.append({
                    'timestamp': timestamp,
                    'severity': 'warning',
                    'type': 'authentication',
                    'message': f"Warning: {failed_count} failed login attempts detected",
                    'host': metrics.get('host', 'unknown'),
                    'value': failed_count
                })
        
        # File integrity analysis
        if 'security' in metrics and 'file_integrity' in metrics['security']:
            modified_files = len(metrics['security']['file_integrity'].get('modified_files', []))
            missing_files = len(metrics['security']['file_integrity'].get('missing_files', []))
            
            if modified_files > 0:
                alerts.append({
                    'timestamp': timestamp,
                    'severity': 'warning' if modified_files < 3 else 'critical',
                    'type': 'integrity',
                    'message': f"{modified_files} critical system files modified recently",
                    'host': metrics.get('host', 'unknown'),
                    'value': modified_files
                })
            
            if missing_files > 0:
                alerts.append({
                    'timestamp': timestamp,
                    'severity': 'critical',
                    'type': 'integrity',
                    'message': f"{missing_files} critical system files are missing",
                    'host': metrics.get('host', 'unknown'),
                    'value': missing_files
                })
        
        # USB device analysis
        if 'security' in metrics and 'usb_devices' in metrics['security']:
            usb_devices = len(metrics['security']['usb_devices'].get('connected_devices', []))
            authorized_only = metrics['security']['usb_devices'].get('authorized_only', True)
            
            if not authorized_only:
                alerts.append({
                    'timestamp': timestamp,
                    'severity': 'critical',
                    'type': 'device',
                    'message': "Unauthorized USB devices detected",
                    'host': metrics.get('host', 'unknown'),
                    'value': usb_devices
                })
            elif usb_devices > 0:
                alerts.append({
                    'timestamp': timestamp,
                    'severity': 'info',
                    'type': 'device',
                    'message': f"{usb_devices} USB devices connected",
                    'host': metrics.get('host', 'unknown'),
                    'value': usb_devices
                })
        
        # System resource analysis
        cpu = metrics.get('cpu', 0)
        memory = metrics.get('mem', 0)
        disk = metrics.get('disk', 0)
        
        if cpu >= self.thresholds['cpu_warning']:
            alerts.append({
                'timestamp': timestamp,
                'severity': 'warning',
                'type': 'performance',
                'message': f"High CPU usage: {cpu}%",
                'host': metrics.get('host', 'unknown'),
                'value': cpu
            })
        
        if memory >= self.thresholds['memory_warning']:
            alerts.append({
                'timestamp': timestamp,
                'severity': 'warning',
                'type': 'performance',
                'message': f"High memory usage: {memory}%",
                'host': metrics.get('host', 'unknown'),
                'value': memory
            })
        
        if disk >= self.thresholds['disk_warning']:
            alerts.append({
                'timestamp': timestamp,
                'severity': 'critical' if disk >= 95 else 'warning',
                'type': 'performance',
                'message': f"High disk usage: {disk}%",
                'host': metrics.get('host', 'unknown'),
                'value': disk
            })
        
        return alerts
    
    def collect_metrics(self):
        """Main metrics collection loop"""
        while self.running:
            try:
                all_metrics = []
                
                for probe_type, probe_path in self.probe_paths.items():
                    if Path(probe_path).exists():
                        metrics = self.collect_probe_data(probe_type, probe_path)
                        if metrics:
                            metrics['probe_type'] = probe_type
                            metrics['collection_time'] = datetime.now().isoformat()
                            all_metrics.append(metrics)
                            
                            # Analyze for alerts
                            new_alerts = self.analyze_security_metrics(metrics)
                            self.alerts.extend(new_alerts)
                
                # Store metrics history (keep last 1000 entries)
                self.metrics_history.extend(all_metrics)
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                # Keep only alerts from last 24 hours
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.alerts = [
                    alert for alert in self.alerts
                    if datetime.fromisoformat(alert['timestamp']) > cutoff_time
                ]
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                print(f"Error in metrics collection: {e}")
                time.sleep(5)
    
    def start_collection(self):
        """Start background metrics collection"""
        self.running = True
        self.collection_thread = threading.Thread(target=self.collect_metrics)
        self.collection_thread.daemon = True
        self.collection_thread.start()
    
    def stop_collection(self):
        """Stop background metrics collection"""
        self.running = False
        if hasattr(self, 'collection_thread'):
            self.collection_thread.join()
    
    def get_latest_metrics(self) -> List[Dict]:
        """Get the most recent metrics for each host"""
        latest = {}
        for metric in reversed(self.metrics_history):
            host = metric.get('host', 'unknown')
            if host not in latest:
                latest[host] = metric
        return list(latest.values())
    
    def get_security_summary(self) -> Dict:
        """Generate security summary statistics"""
        latest_metrics = self.get_latest_metrics()
        
        summary = {
            'total_hosts': len(latest_metrics),
            'total_alerts': len(self.alerts),
            'critical_alerts': len([a for a in self.alerts if a['severity'] == 'critical']),
            'warning_alerts': len([a for a in self.alerts if a['severity'] == 'warning']),
            'failed_logins_total': 0,
            'usb_devices_total': 0,
            'file_changes_total': 0,
            'avg_cpu': 0,
            'avg_memory': 0,
            'avg_disk': 0
        }
        
        if latest_metrics:
            cpu_total = sum(m.get('cpu', 0) for m in latest_metrics)
            memory_total = sum(m.get('mem', 0) for m in latest_metrics)
            disk_total = sum(m.get('disk', 0) for m in latest_metrics)
            
            summary['avg_cpu'] = round(cpu_total / len(latest_metrics), 1)
            summary['avg_memory'] = round(memory_total / len(latest_metrics), 1)
            summary['avg_disk'] = round(disk_total / len(latest_metrics), 1)
            
            for metric in latest_metrics:
                if 'security' in metric:
                    sec = metric['security']
                    if 'failed_logins' in sec:
                        summary['failed_logins_total'] += sec['failed_logins'].get('count_24h', 0)
                    if 'usb_devices' in sec:
                        summary['usb_devices_total'] += len(sec['usb_devices'].get('connected_devices', []))
                    if 'file_integrity' in sec:
                        summary['file_changes_total'] += len(sec['file_integrity'].get('modified_files', []))
        
        return summary

# Global metrics collector
collector = None

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for latest metrics"""
    if collector:
        return jsonify(collector.get_latest_metrics())
    return jsonify([])

@app.route('/api/summary')
def api_summary():
    """API endpoint for security summary"""
    if collector:
        return jsonify(collector.get_security_summary())
    return jsonify({})

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for recent alerts"""
    if collector:
        return jsonify(collector.alerts[-50:])  # Last 50 alerts
    return jsonify([])

@app.route('/api/trends')
def api_trends():
    """API endpoint for trend data"""
    if not collector:
        return jsonify({})
    
    # Get last 24 hours of data
    cutoff_time = datetime.now() - timedelta(hours=24)
    recent_metrics = [
        m for m in collector.metrics_history
        if datetime.fromisoformat(m['collection_time']) > cutoff_time
    ]
    
    # Group by hour for trending
    trends = {}
    for metric in recent_metrics:
        hour = datetime.fromisoformat(metric['collection_time']).strftime('%Y-%m-%d %H:00')
        if hour not in trends:
            trends[hour] = {
                'timestamp': hour,
                'failed_logins': 0,
                'cpu_avg': [],
                'memory_avg': [],
                'disk_avg': [],
                'usb_events': 0
            }
        
        trends[hour]['cpu_avg'].append(metric.get('cpu', 0))
        trends[hour]['memory_avg'].append(metric.get('mem', 0))
        trends[hour]['disk_avg'].append(metric.get('disk', 0))
        
        if 'security' in metric:
            sec = metric['security']
            if 'failed_logins' in sec:
                trends[hour]['failed_logins'] += sec['failed_logins'].get('count_24h', 0)
            if 'usb_devices' in sec:
                trends[hour]['usb_events'] += sec['usb_devices'].get('recent_events', 0)
    
    # Calculate averages
    for hour_data in trends.values():
        if hour_data['cpu_avg']:
            hour_data['cpu_avg'] = sum(hour_data['cpu_avg']) / len(hour_data['cpu_avg'])
        if hour_data['memory_avg']:
            hour_data['memory_avg'] = sum(hour_data['memory_avg']) / len(hour_data['memory_avg'])
        if hour_data['disk_avg']:
            hour_data['disk_avg'] = sum(hour_data['disk_avg']) / len(hour_data['disk_avg'])
    
    return jsonify(list(trends.values()))

def main():
    parser = argparse.ArgumentParser(description='SISSA Ivy Security Dashboard')
    parser.add_argument('--linux-probe', default='cogsec/collectors/cogsec_probe_linux.py',
                       help='Path to Linux probe script')
    parser.add_argument('--windows-probe', default='cogsec/collectors/Get-CogSecEndpointState.ps1',
                       help='Path to Windows probe script')
    parser.add_argument('--port', type=int, default=5000, help='Dashboard port')
    parser.add_argument('--host', default='0.0.0.0', help='Dashboard host')
    parser.add_argument('--interval', type=int, default=60, help='Collection interval in seconds')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Initialize metrics collector
    global collector
    probe_paths = {}
    
    if Path(args.linux_probe).exists():
        probe_paths['linux'] = args.linux_probe
        print(f"✓ Linux probe found: {args.linux_probe}")
    
    if Path(args.windows_probe).exists():
        probe_paths['windows'] = args.windows_probe
        print(f"✓ Windows probe found: {args.windows_probe}")
    
    if not probe_paths:
        print("Error: No probe scripts found!")
        sys.exit(1)
    
    collector = SecurityMetricsCollector(probe_paths)
    collector.collection_interval = args.interval
    
    # Start metrics collection
    print("Starting security metrics collection...")
    collector.start_collection()
    
    try:
        print(f"Starting dashboard on http://{args.host}:{args.port}")
        app.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        collector.stop_collection()

if __name__ == '__main__':
    main()