import pytest
from django.core import mail
from core.tasks import send_activation_key_email
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_send_activation_key_email_task():
    # 1. Создаем пользователя
    user = User.objects.create_user(email="test@task.com", password="password")
    
    # 2. Генерируем ключ (как это происходит в реальности в views.py)
    user.generate_new_key() 
    
    # 3. Вызываем функцию таски напрямую
    send_activation_key_email(user.id)
    
    # 4. Проверяем, что письмо в очереди
    assert len(mail.outbox) == 1
    sent_email = mail.outbox[0]
    
    # 5. Дебаг-вывод
    print(f"\n--- ПРОВЕРКА ОТПРАВКИ ПИСЬМА ---")
    print(f"Тема: {sent_email.subject}")
    print(f"Тело: {sent_email.body}")
    print(f"Ключ пользователя в базе: {user.activation_key}")
    print(f"---------------------------------")
    
    assert sent_email.to == [user.email]
    assert "ключ" in sent_email.subject.lower()
    
    assert user.activation_key is not None
    assert user.activation_key in sent_email.body
    assert "None" not in sent_email.body