"""Project-level routing for Django Channels."""

from dashboard import routing as dashboard_routing

websocket_urlpatterns = list(dashboard_routing.websocket_urlpatterns)
