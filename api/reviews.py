import json
import os
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler

sys.path.append(os.path.dirname(__file__))
from _store import lrange, rpush, StoreNotConfigured  # noqa: E402
from _ratelimit import rate_limited, is_honeypot_filled  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            raw = lrange('reviews')
            reviews = [json.loads(r) for r in raw]
            reviews.sort(key=lambda r: r['created_at'], reverse=True)
            self._send(200, {'reviews': reviews})
        except StoreNotConfigured:
            self._send(200, {'reviews': [], 'warning': 'store_not_configured'})
        except Exception as e:
            self._send(500, {'error': str(e)})

    def do_POST(self):
        try:
            if rate_limited(self, 'review', limit=5, window_seconds=3600):
                self._send(429, {'error': 'rate_limited'})
                return

            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length) or b'{}')

            if is_honeypot_filled(body):
                self._send(200, {'ok': True})
                return

            name = (body.get('name') or '').strip()[:60]
            stars = int(body.get('stars', 0))
            text = (body.get('text') or '').strip()[:500]
            if not name or stars < 1 or stars > 5:
                self._send(400, {'error': 'invalid'})
                return
            review = {
                'id': str(uuid.uuid4()),
                'name': name,
                'stars': stars,
                'text': text,
                'created_at': int(time.time()),
            }
            rpush('reviews', json.dumps(review))
            self._send(200, {'ok': True, 'review': review})
        except StoreNotConfigured:
            self._send(503, {'error': 'store_not_configured'})
        except Exception as e:
            self._send(500, {'error': str(e)})

    def _send(self, code, payload):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())
