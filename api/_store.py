"""Tiny Upstash Redis REST client used by the booking/reviews API routes.

Uses only the standard library (no extra pip installs needed on Vercel).
Requires two environment variables on the Vercel project:
  KV_REST_API_URL
  KV_REST_API_TOKEN
(the REST URL + token from an Upstash Redis database - see README.md)
"""
import json
import os
import time
import urllib.parse
import urllib.request


class StoreNotConfigured(Exception):
    pass


def _base():
    url = os.environ.get('KV_REST_API_URL')
    token = os.environ.get('KV_REST_API_TOKEN')
    if not url or not token:
        raise StoreNotConfigured('KV_REST_API_URL / KV_REST_API_TOKEN are not set on this deployment')
    return url.rstrip('/'), token


def _call(*parts):
    url, token = _base()
    path = '/'.join(urllib.parse.quote(str(p), safe='') for p in parts)
    req = urllib.request.Request(f'{url}/{path}', headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode())


def rpush(key, value):
    return _call('rpush', key, value)


def lrange(key, start=0, stop=-1):
    result = _call('lrange', key, start, stop)
    return result.get('result') or []


def acquire_lock(name, ttl_seconds=5, retries=15, delay=0.2):
    for _ in range(retries):
        res = _call('set', name, '1', 'NX', 'EX', ttl_seconds)
        if res.get('result') == 'OK':
            return True
        time.sleep(delay)
    return False


def release_lock(name):
    _call('del', name)
