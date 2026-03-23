"""
Base repository for all repositories in the application.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

ModelType = TypeVar('ModelType')


class BaseRepository(ABC, Generic[ModelType]):
    """
    Abstract base repository that provides common database operations.
    """
    
    def __init__(self, model: ModelType):
        self.model = model
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get a single record by ID."""
        try:
            return self.model.objects.get(id=id)
        except self.model.DoesNotExist:
            return None
    
    def get_all(self) -> List[ModelType]:
        """Get all records."""
        return list(self.model.objects.all())
    
    def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        return self.model.objects.create(**kwargs)
    
    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """Update a record by ID."""
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            instance.save()
            return instance
        return None
    
    def delete(self, id: int) -> bool:
        """Delete a record by ID."""
        instance = self.get_by_id(id)
        if instance:
            instance.delete()
            return True
        return False
    
    def filter(self, **kwargs) -> List[ModelType]:
        """Filter records by given criteria."""
        return list(self.model.objects.filter(**kwargs))
    
    def get_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> tuple:
        """Get or create a record."""
        return self.model.objects.get_or_create(defaults=defaults or {}, **kwargs)
    
    def count(self, **kwargs) -> int:
        """Count records matching criteria."""
        return self.model.objects.filter(**kwargs).count()
    
    def exists(self, **kwargs) -> bool:
        """Check if records exist matching criteria."""
        return self.model.objects.filter(**kwargs).exists()
