from django.utils import timezone
from django.db import transaction
from .models import VirtualMachine

def get_free_vm(user):
    with transaction.atomic():
        vm = VirtualMachine.objects.filter(current_user__isnull=True, is_active=True).first()
        
        if not vm:
            return None
        
        vm.current_user = user
        vm.last_used_at = timezone.now()
        vm.save()
        
        return vm