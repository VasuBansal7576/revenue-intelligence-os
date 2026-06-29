# Production Deploy Handoff

Use `.env.production.example` as the source for `/etc/cdi/revenue-intelligence-os.env`.

```bash
sudo install -d -o cdi -g cdi /opt/revenue-intelligence-os /var/lib/cdi /etc/cdi
sudo install -m 640 .env.production.example /etc/cdi/revenue-intelligence-os.env
sudo install -m 644 deploy/systemd/cdi-api.service /etc/systemd/system/cdi-api.service
sudo install -m 644 deploy/systemd/cdi-web.service /etc/systemd/system/cdi-web.service
sudo systemctl daemon-reload
sudo systemctl enable --now cdi-api cdi-web
```

Build before starting web:

```bash
npm install
npm run build
```

Smoke gate:

```bash
API_BASE_URL=https://api.example.com \
WEB_BASE_URL=https://revenue.example.com \
EXPECTED_RUNTIME=live-provider-ready \
bash scripts/production-smoke.sh
```

Replace `revenue.example.com` and `api.revenue.example.com` in `deploy/nginx/revenue-intelligence-os.conf`, install TLS certificates, then reload nginx.
