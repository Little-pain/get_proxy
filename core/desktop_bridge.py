import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import VirtualMachine, User 

class DesktopBridgeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Принимаем соединение сразу. Авторизация будет по ключу в методе receive.
        await self.accept()
        self.user_id = None
        self.group_name = None

    async def disconnect(self, close_code):
        # Если юзер был авторизован, удаляем его из группы прослушивания
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "activate_key":
            code = data.get("code")
            
            # Делаем всю магию с БД
            result = await self.activate_logic(code)
            
            # Если ключ подошел, запоминаем юзера и кидаем его в группу для пуш-уведомлений
            if result.get("success"):
                self.user_id = result["user_id"]
                self.group_name = f"user_{self.user_id}"
                await self.channel_layer.group_add(self.group_name, self.channel_name)
            
            # Отдаем ответ десктопу
            await self.send(text_data=json.dumps(result))

    # --- МЕТОД ДЛЯ ПРИЕМА ПРИНУДИТЕЛЬНЫХ СООБЩЕНИЙ ОТ СЕРВЕРА (Celery/Admin) ---
    async def proxy_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "status_change",
            "data": event["message"]
        }))

    # --- ЛОГИКА РАБОТЫ С БД ---
    @database_sync_to_async
    def activate_logic(self, code):
        try:
            # 1. Ищем юзера по ключу активации
            user = User.objects.filter(activation_key=code).first()
            if not user:
                return {"type": "activation_result", "success": False, "error": "Неверный ключ активации"}
            
            # 2. Проверяем, есть ли уже активная виртуалка у этого юзера (защита от двойного коннекта)
            vm = VirtualMachine.objects.filter(current_user=user, is_active=True).first()
            
            # 3. Если нет, ищем свободную
            if not vm:
                vm = VirtualMachine.objects.filter(current_user__isnull=True, is_active=True).first()
                if not vm:
                    return {"type": "activation_result", "success": False, "error": "Все прокси заняты"}
                
                # Привязываем виртуалку к юзеру
                vm.current_user = user
                vm.last_used_at = timezone.now()
                vm.save()

            # 4. Возвращаем успех
            return {
                "type": "activation_result", 
                "success": True, 
                "user_id": user.id,
                "proxy_data": {
                    "host": vm.host, 
                    "port": vm.port, 
                    "protocol": vm.protocol,
                    "name": vm.name
                }
            }
        except Exception as e:
            return {"type": "activation_result", "success": False, "error": str(e)}