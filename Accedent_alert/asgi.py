import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import Alert_system.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Accedent_alert.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            Alert_system.routing.websocket_urlpatterns
        )
    ),
})
