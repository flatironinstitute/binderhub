from .base import BaseHandler
from prometheus_client import REGISTRY, generate_latest, CONTENT_TYPE_LATEST
from tornado import web
import ipaddress


class MetricsHandler(BaseHandler):
    async def get(self):
        allowed = self.settings.get('allowed_metrics_ips', set())
        if allowed:
            ip = ipaddress.ip_address(self.request.remote_ip)
            if not any(ip in a for a in allowed):
                raise web.HTTPError(403)
        self.set_header("Content-Type", CONTENT_TYPE_LATEST)
        self.write(generate_latest(REGISTRY))
