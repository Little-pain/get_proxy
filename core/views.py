from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from core.tasks import send_activation_key_email

from .serializers import RegisterSerializer, UserProfileSerializer, ChangePasswordSerializer, ProxyDetailsSerializer

from .models import User

from .services import get_free_vm

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer, extend_schema_view


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Регистрация нового пользователя",
        description="Создает аккаунт и запускает асинхронную задачу Celery для отправки ключа на email.",
        responses={
            201: OpenApiResponse(
                description="Пользователь создан, письмо отправлено",
                response={"type": "object", "properties": {"message": {"type": "string"}}}
            ),
            400: OpenApiResponse(description="Ошибка валидации (например, такой email уже есть)")
        },
        tags=['Auth']
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_activation_key_email.delay(user.id)
        return Response(
            {"message": "Письмо с ключом отправлено на почту"},
            status=status.HTTP_201_CREATED
        )

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Получение данных профиля",
        description="Возвращает email и текущий ключ активации пользователя для личного кабинета.",
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="Неавторизованный доступ")
        },
        tags=['Profile']
    )
    def get_object(self):
        return self.request.user

class RefreshKeyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Обновление ключа активации",
        description="Аннулирует старый ключ, генерирует новый и отправляет его на почту пользователя через Celery.",
        responses={
            200: inline_serializer(
                name='RefreshKeyResponse',
                fields={'new_key': serializers.CharField()}
            ),
            401: OpenApiResponse(description="Пользователь не авторизован"),
            500: OpenApiResponse(description="Ошибка при генерации или отправке ключа")
        },
        tags=['Profile']
    )
    def post(self, request):
        user = request.user
        try:
            user.generate_new_key()
            send_activation_key_email.delay(user.id)
        except Exception as e:
            import traceback
            print(traceback.format_exc()) 
            return Response({"error": str(e)}, status=500)
        return Response({"new_key": user.activation_key}, status=200)

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        return self.request.user
    @extend_schema(
        summary="Смена пароля пользователя",
        description="Принимает старый и новый пароль. Проверяет корректность старого пароля перед обновлением.",
        responses={
            200: OpenApiResponse(description="Пароль успешно изменен"),
            400: OpenApiResponse(description="Ошибка валидации или неверный старый пароль"),
            401: OpenApiResponse(description="Пользователь не авторизован")
        },
        tags=['Profile']
    )
    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Неверный старый пароль."]}, status=status.HTTP_400_BAD_REQUEST)
            
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response({"status": "success", "message": "Пароль успешно изменен"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ActivateKeyView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary="Активация прокси по ключу",
        description="На данный момент момент не используется и является кодом на будущее, подробнее в README.md",

        responses={
            200: ProxyDetailsSerializer,
            400: OpenApiResponse(description="Неверный или использованный ключ"),
            503: OpenApiResponse(description="Все прокси-серверы сейчас заняты")
        },
        tags=['Desktop App API']
    )

    def post(self, request):

        vm = get_free_vm(request.user)

        if not vm:
            return Response({"error": "Все прокси заняты"}, status=503)

        return Response({
            "host": vm.host,
            "port": vm.port,
            "protocol": vm.protocol,
            "name": vm.name
        })
    
#Импорты декорируемых функций
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
    
)

@extend_schema_view(
    post=extend_schema(
        summary="Авторизация (Login)",
        description="Принимает email и пароль. Возвращает пару токенов: access (для запросов) и refresh (для обновления).",
        tags=["Auth"]
    )
)
class DecoratedTokenObtainPairView(TokenObtainPairView):
    pass

# Оформляем обновление токена
@extend_schema_view(
    post=extend_schema(
        summary="Обновление токена (Refresh)",
        description="Принимает refresh-токен и выдает новый access-токен.",
        tags=["Auth"]
    )
)
class DecoratedTokenRefreshView(TokenRefreshView):
    pass

# Оформляем выход (Blacklist)
@extend_schema_view(
    post=extend_schema(
        summary="Выход из системы (Logout)",
        description="Отправляет refresh-токен в черный список, деактивируя текущую сессию.",
        tags=["Auth"]
    )
)
class DecoratedTokenBlacklistView(TokenBlacklistView):
    pass