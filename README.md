# Bahaa Sax — booking website

Real booking site for Bahaa Sax barbershop (Halmstad, Sweden). Static frontend
(`index.html`) + three small Python serverless API routes in `api/` for
availability, booking and reviews, all backed by one shared Redis database so
every visitor sees the same live data (bookings, slot conflicts, reviews).

## One-time setup (about 5 minutes, no coding needed)

### 1. Deploy to Vercel
1. Go to **vercel.com** and sign up / log in (use "Continue with GitHub").
2. Click **Add New → Project**, pick this **bahaa-sax** repo, click **Deploy**.
   No build settings needed — Vercel detects `index.html` and the `api/*.py`
   functions automatically.
3. You'll get a live URL like `https://bahaa-sax.vercel.app`. It will work,
   but bookings/reviews won't save yet until step 2.

### 2. Add the shared database (Upstash Redis, free)
1. In your Vercel project, open the **Storage** tab.
2. Click **Browse Marketplace**, choose **Upstash** → **Redis**, create a
   free database and connect it to this project.
3. Vercel will show you a REST URL and REST token for the new database
   (or find them on upstash.com under your database → REST API).
4. Go to your Vercel project → **Settings → Environment Variables** and add:
   - `KV_REST_API_URL` = the REST URL
   - `KV_REST_API_TOKEN` = the REST token
5. Go to **Deployments**, click the latest one → **Redeploy**.

That's it — bookings and reviews now save for real and everyone who opens the
link sees the same data.

### 3. Give the owner a bookings list (works even without WhatsApp)
The WhatsApp button on the confirmation screen is just a convenience — the
booking itself is always saved and the slot is always blocked for others,
whether or not the customer has WhatsApp or taps that button. So the owner
needs one place to see every booking, not just the ones a customer happened
to notify him about. That's what `agenda.html` is for.

1. In Vercel → **Settings → Environment Variables**, add:
   - `OWNER_KEY` = a private password only the owner knows (pick your own, or
     use a random one — this protects the page since it shows real customer
     names/phone numbers).
2. Redeploy.
3. Give the owner this link (with the key baked in, so he just bookmarks it):
   `https://bahha-sax.vercel.app/agenda.html?key=YOUR_OWNER_KEY`
4. He opens it once, it remembers the key on that device from then on, and
   shows every upcoming booking grouped by day — regardless of WhatsApp.

### 4. Automatic email notification (works even without WhatsApp)
The WhatsApp button only fires if the customer has WhatsApp and taps it — not
everyone does. This adds a real, automatic email to the owner on every single
booking, sent server-side, with no dependency on the customer at all.

1. On the Gmail account that should send/receive these (can be the owner's
   own address), turn on **2-Step Verification** if it isn't already
   (Google Account → Security).
2. Still under Security, open **App passwords**, create one for "Mail", and
   copy the 16-character password it gives you.
3. In Vercel → **Settings → Environment Variables**, add:
   - `GMAIL_ADDRESS` = that Gmail address
   - `GMAIL_APP_PASSWORD` = the 16-character app password from step 2
   - `OWNER_NOTIFY_EMAIL` = where the notification should land (optional -
     defaults to `GMAIL_ADDRESS` itself if omitted)
4. Redeploy.

From then on, every successful booking sends a real email automatically -
service, date, time, customer name and phone. If these env vars aren't set,
booking still works fine, it just skips the email silently.

## Changing business details later
- **Opening hours / slot length**: edit the `HOURS` dict in `api/_biz.py`,
  and the matching `HOURS` array near the top of the `<script>` in
  `index.html` (both must stay in sync — one drives real slot availability,
  the other drives the hours shown on the page).
- **Services & prices**: edit the `SERVICES` array in `index.html`.
- **WhatsApp number for booking notifications**: `OWNER_WHATSAPP` constant in
  `index.html` (international format, no `+` or spaces, e.g. `46701234567`).
- **Address / phone / email / Instagram**: search `index.html` for the
  "hours" section and footer.

## How booking notifications work right now
When someone finishes booking, the confirmation screen shows a **"Notify
Bahaa on WhatsApp"** button that opens a pre-filled WhatsApp message to his
number — the customer taps send. This works immediately with no extra setup.
A fully automatic Google Calendar entry (no tap needed) is possible later but
requires a Google Cloud OAuth app and more backend work — ask if you want
that built next.
