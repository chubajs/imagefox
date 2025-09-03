#!/usr/bin/env python3
"""
Log monitoring dashboard for ImageFox.
Provides real-time insights into agent performance and errors.
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

# Log directory
LOG_DIR = Path("logs")
MAIN_LOG = LOG_DIR / "imagefox_agent.log"
CRON_LOG = LOG_DIR / "cron_imagefox_agent.log"

def parse_log_line(line: str) -> Dict:
    """Parse a log line into components."""
    # Format: 2025-09-03 16:17:23,566: WARNING: Message
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}): (\w+): (.+)$'
    match = re.match(pattern, line)
    if match:
        return {
            'timestamp': datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S,%f'),
            'level': match.group(2),
            'message': match.group(3)
        }
    return None

def analyze_logs(hours: int = 24) -> Dict:
    """Analyze logs from the last N hours."""
    if not MAIN_LOG.exists():
        return {"error": "No log file found"}
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    stats = {
        'time_range': f"Last {hours} hours",
        'total_lines': 0,
        'errors': 0,
        'warnings': 0,
        'info': 0,
        'debug': 0,
        'session_closed_errors': 0,
        'successful_images': 0,
        'failed_downloads': 0,
        'records_processed': 0,
        'projects_processed': set(),
        'cost_total': 0.0,
        'error_types': Counter(),
        'recent_errors': [],
        'processing_rate': 0
    }
    
    with open(MAIN_LOG, 'r') as f:
        for line in f:
            parsed = parse_log_line(line.strip())
            if not parsed:
                continue
                
            # Skip old entries
            if parsed['timestamp'] < cutoff_time:
                continue
                
            stats['total_lines'] += 1
            level = parsed['level']
            message = parsed['message']
            
            # Count by level
            if level == 'ERROR':
                stats['errors'] += 1
                # Extract error type
                if 'Session is closed' in message:
                    stats['session_closed_errors'] += 1
                    stats['error_types']['Session closed'] += 1
                elif 'Download failed' in message:
                    stats['failed_downloads'] += 1
                    stats['error_types']['Download failed'] += 1
                else:
                    stats['error_types']['Other'] += 1
                    
                # Keep last 5 errors
                if len(stats['recent_errors']) < 5:
                    stats['recent_errors'].append({
                        'time': parsed['timestamp'].strftime('%H:%M:%S'),
                        'message': message[:100]
                    })
                    
            elif level == 'WARNING':
                stats['warnings'] += 1
            elif level == 'INFO':
                stats['info'] += 1
                
                # Track successful operations
                if 'Successfully analyzed' in message:
                    match = re.search(r'Successfully analyzed (\d+)/(\d+) images', message)
                    if match:
                        stats['successful_images'] += int(match.group(1))
                        
                elif 'Processing record' in message:
                    stats['records_processed'] += 1
                    match = re.search(r'in project (\w+)', message)
                    if match:
                        stats['projects_processed'].add(match.group(1))
                        
                elif 'COST_TRACKING' in message:
                    match = re.search(r'cost: \$(\d+\.\d+)', message)
                    if match:
                        stats['cost_total'] += float(match.group(1))
                        
            elif level == 'DEBUG':
                stats['debug'] += 1
    
    # Calculate processing rate
    if stats['total_lines'] > 0 and hours > 0:
        stats['processing_rate'] = stats['records_processed'] / hours
        
    # Convert set to list for JSON serialization
    stats['projects_processed'] = list(stats['projects_processed'])
    
    return stats

def check_cron_status() -> Dict:
    """Check cron execution status."""
    if not CRON_LOG.exists():
        return {"status": "No cron log found"}
    
    with open(CRON_LOG, 'r') as f:
        lines = f.readlines()
        
    if not lines:
        return {"status": "Cron log empty"}
        
    last_line = lines[-1].strip()
    
    # Extract timestamp from cron log
    timestamp_match = re.match(r'^(\w+ \w+ +\d+ \d+:\d+:\d+ \w+ \d+):', last_line)
    if timestamp_match:
        last_run = timestamp_match.group(1)
        return {
            "status": "Active",
            "last_run": last_run,
            "message": last_line.split(': ', 1)[1] if ': ' in last_line else last_line
        }
    
    return {"status": "Unknown", "last_line": last_line}

def generate_report():
    """Generate a comprehensive monitoring report."""
    print("=" * 60)
    print("ImageFox Log Monitor Dashboard")
    print("=" * 60)
    
    # Check cron status
    print("\n📅 Cron Status:")
    cron_status = check_cron_status()
    for key, value in cron_status.items():
        print(f"  {key}: {value}")
    
    # Analyze recent logs
    print("\n📊 Log Analysis (Last 24 hours):")
    stats = analyze_logs(24)
    
    if 'error' in stats:
        print(f"  ❌ {stats['error']}")
        return
        
    print(f"  Time Range: {stats['time_range']}")
    print(f"  Total Log Lines: {stats['total_lines']:,}")
    print()
    print("  Log Levels:")
    print(f"    ℹ️  INFO: {stats['info']:,}")
    print(f"    ⚠️  WARNING: {stats['warnings']:,}")
    print(f"    ❌ ERROR: {stats['errors']:,}")
    print(f"    🐛 DEBUG: {stats['debug']:,}")
    
    print("\n  Processing Statistics:")
    print(f"    Records Processed: {stats['records_processed']}")
    print(f"    Projects Active: {', '.join(stats['projects_processed']) if stats['projects_processed'] else 'None'}")
    print(f"    Processing Rate: {stats['processing_rate']:.1f} records/hour")
    print(f"    Successful Images: {stats['successful_images']}")
    print(f"    Failed Downloads: {stats['failed_downloads']}")
    print(f"    Total Cost: ${stats['cost_total']:.4f}")
    
    print("\n  Error Analysis:")
    print(f"    Session Closed Errors: {stats['session_closed_errors']}")
    if stats['error_types']:
        print("    Error Types:")
        for error_type, count in stats['error_types'].most_common():
            print(f"      - {error_type}: {count}")
    
    if stats['recent_errors']:
        print("\n  Recent Errors (Last 5):")
        for error in stats['recent_errors']:
            print(f"    [{error['time']}] {error['message']}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if stats['session_closed_errors'] > 10:
        print("  ⚠️  High number of session errors - Consider enabling proxy support")
    if stats['processing_rate'] < 1:
        print("  ⚠️  Low processing rate - Check if agent is finding records")
    if stats['cost_total'] > 1.0:
        print("  ⚠️  High costs - Monitor API usage")
    if stats['errors'] > stats['info']:
        print("  ❌ More errors than info messages - Investigate issues")
    
    # Check log file size
    log_size = MAIN_LOG.stat().st_size / (1024 * 1024)  # MB
    if log_size > 10:
        print(f"  ⚠️  Log file is {log_size:.1f}MB - Consider rotation")
    
    print("\n" + "=" * 60)

def tail_logs(lines: int = 20):
    """Tail the main log file."""
    print(f"\n📜 Last {lines} log entries:")
    print("-" * 60)
    
    if not MAIN_LOG.exists():
        print("No log file found")
        return
        
    with open(MAIN_LOG, 'r') as f:
        all_lines = f.readlines()
        
    for line in all_lines[-lines:]:
        parsed = parse_log_line(line.strip())
        if parsed:
            time_str = parsed['timestamp'].strftime('%H:%M:%S')
            level = parsed['level']
            message = parsed['message'][:100]
            
            # Color code by level
            if level == 'ERROR':
                print(f"❌ [{time_str}] {message}")
            elif level == 'WARNING':
                print(f"⚠️  [{time_str}] {message}")
            elif level == 'INFO':
                print(f"ℹ️  [{time_str}] {message}")
            else:
                print(f"   [{time_str}] {message}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'tail':
        tail_logs(int(sys.argv[2]) if len(sys.argv) > 2 else 20)
    else:
        generate_report()
        
        # Show recent activity
        print("\n" + "=" * 60)
        tail_logs(10)