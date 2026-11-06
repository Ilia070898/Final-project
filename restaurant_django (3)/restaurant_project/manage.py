#!/usr/bin/env python
# Django-ს სტანდარტული ბრძანებების გამშვები: runserver, migrate, test, check.
import os
import sys

# პირდაპირ გაშვებისას ვასრულებთ ქვემოთ მოცემულ ბლოკს.
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    # sys.argv შეიცავს ტერმინალიდან მიღებულ ბრძანებასა და არგუმენტებს.
    execute_from_command_line(sys.argv)
