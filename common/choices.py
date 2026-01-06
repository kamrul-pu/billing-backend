"""Common Choices for the app"""

from django.db.models import TextChoices


class Status(TextChoices):
    """
    Status Choices
    """

    ACTIVE = "ACTIVE", "Active"
    DRAFT = "DRAFT", "DRAFT"
    INACTIVE = "INACTIVE", "Inactive"
    REMOVED = "REMOVED", "Removed"
