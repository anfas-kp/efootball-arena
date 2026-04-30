from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role support."""

    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('captain', 'Team Captain'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='captain')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser

    @property
    def is_captain(self):
        return self.role == 'captain'
