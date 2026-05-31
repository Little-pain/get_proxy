import pytest
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_BROKER_URL='memory://')
class TestAuth(TestCase):
    
    def test_register_success(self):
        """Проверка успешной регистрации"""
        url = reverse('register')
        data = {
            "email": "tester@test.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == 201

    def test_login_get_token(self):
        """Проверка получения JWT токена по email"""
        email = "login@test.com"
        password = "Password123!"
        user = User.objects.create_user(email=email, password=password)
        user.is_active = True
        user.save()

        url = reverse('token_obtain_pair')
        data = {"email": email, "password": password}
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_register_duplicate_email(self):
        """Проверка ошибки при дублировании email"""
        email = "dup@test.com"
        User.objects.create_user(email=email, password="Password123!")
        
        url = reverse('register')
        data = {
            "email": email,
            "password": "Password123!",
            "password_confirm": "Password123!",
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == 400

@pytest.mark.django_db
class TestProtectedEndpoints(TestCase):

    @classmethod
    def setUpClass(cls):
        """Создаем юзера один раз для всего класса"""
        super().setUpClass()
        cls.email = "test_user@proxy.com"
        cls.password = "SuperSecret123!"
        cls.user = User.objects.create_user(
            email=cls.email, 
            password=cls.password, 
            is_active=True
        )

    def get_access_token(self):
        """Хелпер для получения токена"""
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {"email": self.email, "password": self.password}, format='json')
        return response.data['access']

    def test_profile_endpoint_protection(self):
        """Тест защиты /api/profile/"""
        url = reverse('profile')
        
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        token = self.get_access_token()
        response = self.client.get(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_refresh_key_endpoint_protection(self):
        """Тест защиты /api/refresh-key/ с изоляцией Celery"""
        url = reverse('refresh-key')
        
        response = self.client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        token = self.get_access_token()
        
        with patch('core.views.send_activation_key_email.delay'):
            response = self.client.post(
                url, 
                HTTP_AUTHORIZATION=f'Bearer {token}'
            )
            
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
