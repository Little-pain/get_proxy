import uuid
import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings

class UserManager(BaseUserManager):
    """
    Кастомный менеджер пользователей, где email является уникальным идентификатором.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """
    Модель пользователя согласно ТЗ.
    Вход осуществляется по Email.
    """
    username = None
    email = models.EmailField(unique=True)

    # Ключ активации
    activation_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    activation_key_expires = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def generate_new_key(self):
        """Генерирует криптографически стойкий уникальный ключ"""
        self.activation_key = secrets.token_urlsafe(64)
        self.save()

    def __str__(self):
        return self.email

class VirtualMachine(models.Model):
    """
    Модель прокси-сервера согласно ТЗ.
    """
    PROTOCOL_CHOICES = [
        ('socks5', 'SOCKS5'),
        ('http', 'HTTP'),
        ('https', 'HTTPS'),
    ]

    name = models.CharField(max_length=100)
    host = models.GenericIPAddressField()
    port = models.PositiveIntegerField()
    protocol = models.CharField(max_length=10, choices=PROTOCOL_CHOICES, default='http')
    is_active = models.BooleanField(default=True)



    # ПОЛЯ НА БУДУЩЕЕ если мало ли прокси будут требовать сами по себе авторизации.
    proxy_user = models.CharField(max_length=100, null=True, blank=True)
    proxy_pass = models.CharField(max_length=100, null=True, blank=True)


    current_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vms'
    )
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"