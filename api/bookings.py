import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.append(os.path.dirname(__file__))
from _store import lrange, StoreNotConfigured  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            key = (qs.get('key') or [''])[0]
            expected = os.environ.get('OWNER_KEY')
            if not expected or key != expected:
                self._send(403, {'error': 'forbidden'})
                return

            raw = lrange('bookings')
            bookings = [json.loads(b) for b in raw]
            today = time.strftime('%Y-%m-%d')
            upcoming = [b for b in bookings if b['date'] >= today]
            upcoming.sort(key=lambda b: (b['date'], b['time']))
            self._send(200, {'bookings': upcoming})
        except StoreNotConfigured:
            self._send(200, {'bookings': [], 'warning': 'store_not_configured'})
        except Exception as e:
            self._send(500, {'error': str(e)})

    def _send(self, code, payload):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())
