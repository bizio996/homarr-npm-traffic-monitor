#!/usr/bin/env python3
"""Read-only Nginx Proxy Manager host and daily HTTP metrics collector."""
import json
import os
import re
import threading
import time
from datetime import datetime
from glob import glob
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

NPM_URL = os.environ.get('NPM_URL', 'http://nginx-proxy-manager:81').rstrip('/')
EMAIL = os.environ['NPM_EMAIL']
PASSWORD = os.environ['NPM_PASSWORD']
API_KEY = os.environ['COLLECTOR_KEY']
LOG_DIR = os.environ.get('LOG_DIR', '/npm-logs')
CACHE_SECONDS = int(os.environ.get('CACHE_SECONDS', '60'))
LISTEN = os.environ.get('LISTEN', '0.0.0.0')
PORT = int(os.environ.get('PORT', '8787'))

# NPM log format: [date] cache_status upstream_status response_status - METHOD scheme host "uri" ... [Length bytes]
PATTERN = re.compile(
    r'^\[(?P<stamp>[^\]]+)\]\s+\S+\s+\S+\s+(?P<status>\d{3})\s+-\s+'
    r'\S+\s+\S+\s+\S+\s+".*?"\s+\[Client [^\]]+\]\s+'
    r'\[Length (?P<bytes>\d+)\]'
)
FILE_PATTERN = re.compile(r'^proxy-host-(\d+)_access\.log$')
if hasattr(time, 'tzset'):
    time.tzset()
_lock = threading.Lock()
_cache = {'at': 0, 'value': None}


def api(path, payload=None, token=None):
    headers = {'Accept': 'application/json'}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = Request(NPM_URL + path, data=None if payload is None else json.dumps(payload).encode(), headers=headers)
    with urlopen(req, timeout=12) as response:
        return json.load(response)


def get_hosts():
    auth = api('/api/tokens', {'identity': EMAIL, 'secret': PASSWORD})
    token = auth['token']
    return api('/api/nginx/proxy-hosts', token=token)


def blank():
    return {'requests': 0, 'bytes': 0, 'http2xx': 0, 'http3xx': 0, 'http4xx': 0, 'http5xx': 0}


def daily_stats():
    result = {}
    # Access log date carries UTC offset; group by the same calendar date as the collector's TZ.
    today = datetime.now().astimezone().date()
    for path in glob(os.path.join(LOG_DIR, 'proxy-host-*_access.log*')):
        name = os.path.basename(path)
        match = FILE_PATTERN.fullmatch(name)
        if not match:
            continue
        host_id = int(match.group(1))
        metrics = result.setdefault(host_id, blank())
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as handle:
                for line in handle:
                    parsed = PATTERN.match(line)
                    if not parsed:
                        continue
                    try:
                        when = datetime.strptime(parsed['stamp'], '%d/%b/%Y:%H:%M:%S %z')
                    except ValueError:
                        continue
                    if when.astimezone().date() != today:
                        continue
                    status_code = int(parsed['status'])
                    metrics['requests'] += 1
                    metrics['bytes'] += int(parsed['bytes'])
                    bucket = status_code // 100
                    if bucket in (2, 3, 4, 5):
                        metrics[f'http{bucket}xx'] += 1
        except (OSError, PermissionError):
            continue
    return result


def snapshot():
    with _lock:
        if _cache['value'] is not None and time.monotonic() - _cache['at'] < CACHE_SECONDS:
            return _cache['value']
        hosts = get_hosts()
        if not isinstance(hosts, list):
            raise ValueError('NPM returned an unexpected hosts payload')
        stats = daily_stats()
        items = []
        total = blank()
        for host in hosts:
            values = stats.get(int(host['id']), blank())
            for k in total:
                total[k] += values[k]
            items.append({
                'id': host['id'],
                'domains': host.get('domain_names') or [],
                'forward': f"{host.get('forward_scheme', 'http')}://{host.get('forward_host', '?')}:{host.get('forward_port', '?')}",
                'enabled': bool(host.get('enabled')),
                'ssl': bool(host.get('certificate_id')),
                **values,
            })
        items.sort(key=lambda x: x['requests'], reverse=True)
        value = {'date': str(datetime.now().astimezone().date()),
                 'hostCount': len(items), 'enabledCount': sum(h['enabled'] for h in items),
                 'totals': total, 'hosts': items}
        _cache.update(at=time.monotonic(), value=value)
        return value


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != '/snapshot':
            self.reply(404, {'error': 'not found'})
            return
        if self.headers.get('X-API-Key') != API_KEY and self.headers.get('Authorization') != 'Bearer ' + API_KEY:
            self.reply(401, {'error': 'unauthorized'})
            return
        try:
            self.reply(200, snapshot())
        except (HTTPError, URLError, KeyError, ValueError, OSError) as exc:
            if isinstance(exc, HTTPError):
                print('Collector API error: HTTP', exc.code, 'at', exc.url.split('?')[0], flush=True)
            else:
                print('Collector error:', type(exc).__name__, str(exc), flush=True)
            self.reply(502, {'error': 'NPM or logs unavailable'})

    def reply(self, status, value):
        payload = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == '__main__':
    if len(API_KEY) < 24:
        raise SystemExit('COLLECTOR_KEY must be at least 24 characters')
    print(f'Listening on {LISTEN}:{PORT}', flush=True)
    ThreadingHTTPServer((LISTEN, PORT), Handler).serve_forever()
