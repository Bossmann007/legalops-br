# Deploy — Maffini Dashboard

Single-user dashboard for Dra. Maylin. Default mode: **no login, loopback-only**
(`127.0.0.1`). The per-command **approval gate** (confirm modal + server-side 403)
is always on and is independent of login auth — nothing runs without authorization.

## Install (systemd)

1. Copy the app to `/opt/maffini-dashboard` (or edit `WorkingDirectory`/`User`
   in the unit to match your path/account).
2. Create `/opt/maffini-dashboard/.env` from `.env.example`, then `chmod 600 .env`.
   Leave `MAFFINI_AUTH_USER` unset for default no-login mode.
3. Install and start the unit:

   ```bash
   sudo cp deploy/maffini-dashboard.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now maffini-dashboard
   sudo systemctl status maffini-dashboard
   ```

The boot log prints the active mode, e.g.:

```
Maffini Dashboard listening on http://127.0.0.1:4318
auth: disabled (loopback-only)
```

## Boot guard

If `MAFFINI_AUTH_USER` is unset/empty **and** `MAFFINI_HOST` is **not** loopback
(`127.0.0.1`, `::1`, `localhost`, `127.0.0.0/8`), the server **refuses to start**.
This makes it impossible to expose an auth-less dashboard on a LAN/WAN interface.

## LAN / remote access (optional)

Loopback-only means the dashboard is reachable only from Dra. Maylin's own machine.
To reach it from other devices you **must enable login auth first**:

1. Set `MAFFINI_AUTH_USER` and `MAFFINI_AUTH_PASS_HASH` (scrypt) in `.env`.
   Generate the hash:

   ```bash
   node -e "console.log(require('./server/lib/auth').hashPassword('senha-forte'))"
   ```

2. Keep the Node app bound to `127.0.0.1` and put a TLS reverse proxy in front
   (Caddy gives automatic HTTPS):

   ```caddyfile
   maffini.example.com {
       reverse_proxy 127.0.0.1:4318
   }
   ```

Never expose the raw Node port to a LAN/WAN, and never run LAN access without
`MAFFINI_AUTH_USER` set — the boot guard only protects loopback binds.
