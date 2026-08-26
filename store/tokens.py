from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Incluir email_verified hace que el token deje de ser válido
        # en cuanto se usa una vez, evitando que se reutilice.
        return f"{user.pk}{timestamp}{user.email}{user.profile.email_verified}"


email_verification_token = EmailVerificationTokenGenerator()
