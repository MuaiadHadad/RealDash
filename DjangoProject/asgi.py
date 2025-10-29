"""ASGI entrypoint configured for HTTP and WebSocket protocols."""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject.settings')

django_application = get_asgi_application()

try:
	from DjangoProject import routing as project_routing
except ImportError as exc:  # pragma: no cover
	raise ImportError('Unable to load DjangoProject.routing module') from exc


application = ProtocolTypeRouter({
	'http': django_application,
	'websocket': AuthMiddlewareStack(
		URLRouter(project_routing.websocket_urlpatterns)
	),
})
