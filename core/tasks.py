from celery import shared_task
from django.core.mail import send_mail
from .models import User
from django.conf import settings


@shared_task
def send_activation_key_email(user_id):
    
    try:
        user = User.objects.get(id=user_id)
        print(f"!!! Попытка отправить письмо на {user.email} !!!")
        subject = 'Ваш ключ доступа к прокси'
        message = f'Привет! Твой ключ активации: {user.activation_key}\nИспользуй его в десктопном приложении.'
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return f"Email sent to {user.email}"
    except User.DoesNotExist:
        return "User not found"