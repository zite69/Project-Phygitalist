#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
#from shop.patch import PatchedModuleFinder

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
    #sys.meta_path.insert(0, PatchedModuleFinder())
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
