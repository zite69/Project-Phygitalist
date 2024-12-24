from django.core.files.storage import FileSystemStorage
from django.conf import settings

protected_storage = FileSystemStorage(location=settings.PROTECTED_ROOT)

class ProtectedStorage(FileSystemStorage):
    """
    Custom storage that points to `protected/` folder
    and optionally uses `/protected/` as the base URL.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('location', settings.PROTECTED_ROOT)
        # If you *want* the .url property to generate /protected/... links:
        kwargs.setdefault('base_url', settings.PROTECTED_URL)
        super().__init__(*args, **kwargs)
