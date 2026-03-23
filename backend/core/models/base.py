"""
Base model for all models in the application.
"""
from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model that provides common fields for all models.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
