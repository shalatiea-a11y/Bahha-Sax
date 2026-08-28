"""Simple per-IP rate limiting to stop scripted spam/abuse of the public
booking and review endpoints - the main realistic "hacker" risk for a site
with no login: a bot hammering /api/book to fill up every slot, or spamming
fake 1-star reviews.
"""
from _store import incr_with_expiry, StoreNotConfigured


def client_ip(handler):
    fwd = handler.headers.get('x-forwarded-for') or handler.headers.get('X-Forwarded-For')
    if fwd:
        return fwd.split(',')[0].strip()
    return handler.client_address[0] if handler.client_address else 'unknown'


def rate_limited(handler, action, limit, window_seconds):
    """Returns True if this IP should be BLOCKED (over the limit) for this action."""
    ip = client_ip(handler)
    key = f'ratelimit:{action}:{ip}'
    try:
        count = incr_with_expiry(key, window_seconds)
    except StoreNotConfigured:
        return False  # can't rate limit without the store; let the normal store checks handle it
    return count > limit


def is_honeypot_filled(body):
    """A hidden form field real visitors never see or fill; only bots that
    auto-fill every input trip it."""
    return bool((body.get('website') or '').strip())
