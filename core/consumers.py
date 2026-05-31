import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer

from asgiref.sync import async_to_sync

from .models import VirtualMachine

class ProxyStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        user = self.scope.get("user")

        if getattr(user, 'is_anonymous', True):
            await self.send(text_data=json.dumps({
                "status": "error",
                "message": "Не передан токен или он невалиден. Подключение установлено, но данных не будет."
            }))
            return

        safe_email = user.email.replace('@', '_').replace('.', '_')
        self.group_name = f"user_{safe_email}"
        
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        proxy_data = await self.get_user_proxy(user)
        
        await self.send(text_data=json.dumps({
            'status': 'connected' if proxy_data else 'waiting',
            'proxy': proxy_data,
            'message': None if proxy_data else 'Прокси еще не назначена.'
        }))

    @database_sync_to_async
    def get_user_proxy(self, user):
        vm = VirtualMachine.objects.filter(current_user=user, is_active=True).first()
        if vm:
            return {
                'host': vm.host,
                'port': vm.port,
                'protocol': vm.protocol
            }
        return None

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)




def notify_user_desktop(user_email, status, payload=None):
    allowed_statuses = ['connected', 'disconnected', 'no_free_vms', 'error']
    if status not in allowed_statuses:
        raise ValueError(f"Недопустимый статус: {status}")

    channel_layer = get_channel_layer()
    group_name = f"user_{user_email.replace('@', '_').replace('.', '_')}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "proxy_update",
            "message": {
                "status": status,
                "data": payload
            }
        }
    )