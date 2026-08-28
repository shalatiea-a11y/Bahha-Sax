import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.append(os.path.dirname(__file__))
from _store import lrange, StoreNotConfigured  # noqa: E402
from _biz import slot_list, overlaps, is_past_slot  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            date_str = (qs.get('date') or [None])[0]
            duration = int((qs.get('duration') or ['30'])[0])
            if not date_str:
                self._send(400, {'error': 'date_required'})
                return
            day = datetime.strptime(date_str, '%Y-%m-%d')
            all_slots = slot_list(day, duration)

            try:
                raw = lrange('bookings')
                todays = [b for b in (json.loads(r) for r in raw) if b['date'] == date_str]
            except StoreNotConfigured:
                self._send(200, {'slots': [{'time': s, 'busy': is_past_slot(day, s)} for s in all_slots], 'warning': 'store_not_configured'})
                return

            result = [
                {
                    'time': s,
                    'busy': is_past_slot(day, s) or any(overlaps(s, duration, b['time'], b['duration']) for b in todays),
                }
                for s in all_slots
            ]
            self._send(200, {'slots': result})
        except Exception as e:
            self._send(400, {'error': str(e)})

    def _send(self, code, payload):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())
