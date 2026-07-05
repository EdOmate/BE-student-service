from django.conf import settings


def setup_django():
    if settings.configured:
        return

    settings.configure(
        SECRET_KEY="dummy-secret-key",
        PASSWORD_HASHERS=[
            "django.contrib.auth.hashers.PBKDF2PasswordHasher",
            "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
            "django.contrib.auth.hashers.Argon2PasswordHasher",
            "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
        ],
    )

