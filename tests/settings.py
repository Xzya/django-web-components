from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

INSTALLED_APPS = ["django_web_components"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "builtins": ["django_web_components.templatetags.components"],
        },
    },
]
