from django.contrib import admin
from .models import User, VirtualMachine

admin.site.register(User)
admin.site.register(VirtualMachine)