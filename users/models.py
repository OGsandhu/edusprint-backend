from django.contrib.auth.models import AbstractUser
from django.db import models
from typing import ClassVar
from django.db.models.manager import Manager

class CustomUser(AbstractUser):
    objects: ClassVar[Manager]
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('client', 'Client'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
