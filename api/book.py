import json
import os
import sys
import time
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler

sys.path.append(os.path.dirname(__file__))
from _store import lrange, rpush, acquire_lock, release_lock, StoreNotConfigured  # noqa: E402
from _biz import slot_list, overlaps, is_past_slot  # noqa: E402
from _notify import send_owner_email  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length) or b'{}')
            date = (body.get('date') or '').strip()
            time_str = (body.get('time') or '').strip()
            duration = int(body.get('duration', 30))
            service = (body.get('service') or '').strip()
            service_name = (body.get('serviceName') or service).strip()[:60]
            name = (body.get('name') or '').strip()[:80]
            phone = (body.get('phone') or '').strip()[:30]

            if not (date and time_str and service and name and phone):
                self._send(400, {'error': 'missing_fields'})
                return

            day = datetime.strptime(date, '%Y-%m-%d')
            if time_str not in slot_list(day, duration):
                self._send(400, {'error': 'invalid_slot'})
                return
            if is_past_slot(day, time_str):
                self._send(409, {'error': 'slot_in_past'})
                return

            try:
                got_lock = acquire_lock('bookings_lock')
            except StoreNotConfigured:
                self._send(503, {'error': 'store_not_configured'})
                return

            if not got_lock:
                self._send(409, {'error': 'busy_try_again'})
                return

            try:
                raw = lrange('bookings')
                todays = [b for b in (json.loads(r) for r in raw) if b['date'] == date]
                if any(overlaps(time_str, duration, b['time'], b['duration']) for b in todays):
                    self._send(409, {'error': 'slot_taken'})
                    return
                booking = {
                    'id': str(uuid.uuid4()),
                    'service': service,
                    'service_name': service_name,
                    'date': date,
                    'time': time_str,
                    'duration': duration,
                    'name': name,
                    'phone': phone,
                    'created_at': int(time.time()),
                }
                rpush('bookings', json.dumps(booking))
                try:
                    send_owner_email(
                        subject=f'Ny bokning: {service_name} {date} {time_str}',
                        body=(
                            f'Ny bokning på Bahaa Sax:\n\n'
                            f'Tjänst: {service_name}\n'
                            f'Datum: {date}\n'
                            f'Tid: {time_str}\n'
                            f'Kund: {name}\n'
                            f'Telefon: {phone}\n'
                        ),
                    )
                except Exception:
                    pass
                self._send(200, {'ok': True, 'booking': booking})
            finally:
                release_lock('bookings_lock')
        except Exception as e:
            self._send(500, {'error': str(e)})

    def _send(self, code, payload):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())
