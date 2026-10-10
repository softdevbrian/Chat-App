from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that permits users to log in
    using either their username OR their email address with their password.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')
        if not username or not password:
            return None

        try:
            # Query by case-insensitive username or case-insensitive email
            user = User.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username)
            ).first()

            if user and user.check_password(password):
                return user
        except Exception:
            return None

        return None
