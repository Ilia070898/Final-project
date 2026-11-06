# პროექტის პარამეტრები: აპები, middleware, შაბლონები, მონაცემთა ბაზა და ავტორიზაცია.
import os
from pathlib import Path

# პროექტის მთავარი საქაღალდე; SQLite ფაილის გზაც აქედან იწყება.
BASE_DIR = Path(__file__).resolve().parent.parent
# ლოკალურად დეტალური შეცდომები ჩანს. საჯარო სერვერზე DEBUG უნდა იყოს გამორთული.
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
# Django-ს ხელმოწერების საიდუმლო გასაღები. გარემოს ცვლადი ცვლის ლოკალურ მნიშვნელობას.
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY", "development-only-restaurant-change-before-deploy"
)
if not DEBUG and SECRET_KEY.startswith("development-only"):
    raise RuntimeError("Set DJANGO_SECRET_KEY for deployment")
# დომენები და მისამართები, რომლებზეც Django მოთხოვნას მიიღებს.
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(
    ","
)
# ჩართული აპები: ავტორიზაცია, სესიები, შეტყობინებები, სტატიკური ფაილები და menu.
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "menu",
]
# ყოველი მოთხოვნის საერთო დამუშავება: უსაფრთხოება, სესია, მომხმარებელი და CSRF დაცვა.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
# მისამართების მთავარი ფაილი.
ROOT_URLCONF = "config.urls"
# Django შაბლონების პარამეტრები. APP_DIRS აპების templates საქაღალდეებში ეძებს.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
# WSGI სერვერისთვის აპლიკაციის შესასვლელი.
WSGI_APPLICATION = "config.wsgi.application"
# SQLite ბაზა ინახავს მომხმარებლებსა და სესიებს; კერძები გარე API-შია.
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}
# ინტერფეისის ენა და თარიღის/დროის რეგიონული პარამეტრები.
LANGUAGE_CODE = "ka"
TIME_ZONE = "Asia/Tbilisi"
USE_I18N = True
USE_TZ = True
# ბრაუზერისთვის CSS-ის მისამართის პრეფიქსი.
STATIC_URL = "static/"
# collectstatic ბრძანების დანიშნულების საქაღალდე ჰოსტინგისთვის.
STATIC_ROOT = BASE_DIR / "staticfiles"
# ავტომატური პირველადი გასაღების ნაგულისხმევი ტიპი.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# IT Step API-ის საწყისი მისამართი; გარემოს ცვლადით შეიძლება შეიცვალოს.
API_BASE_URL = os.getenv(
    "RESTAURANT_API_URL", "https://restaurant.stepprojects.ge/api"
).rstrip("/")
# ქსელის პასუხის ლოდინის ზღვარი წამებში.
API_TIMEOUT = 12
# სესიის cookie ბრაუზერის სკრიპტებისთვის წაუკითხავია.
SESSION_COOKIE_HTTPONLY = True
# Lax ზღუდავს სესიის cookie-ს ზოგიერთ უცხო საიტიდან მოთხოვნაში.
SESSION_COOKIE_SAMESITE = "Lax"
# DEBUG=0 რეჟიმში ეს cookie-ები მხოლოდ HTTPS-ით იგზავნება.
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# შესვლის გვერდის სახელი; ქვემოთაა შესვლა/გამოსვლის შემდეგ გადასასვლელი გვერდები.
LOGIN_URL = "menu:login"
LOGIN_REDIRECT_URL = "menu:catalog"
LOGOUT_REDIRECT_URL = "menu:catalog"
# Django-ს მზა შემოწმებები: მსგავსება, მინიმალური სიგრძე, გავრცელებული ან მხოლოდ ციფრული პაროლი.
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
