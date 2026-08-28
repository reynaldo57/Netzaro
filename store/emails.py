"""Correos de notificación de la app store."""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_teacher_decision_email(user, approved):
    """Notifica al usuario el resultado de su solicitud para ser profesor.

    Tolera fallos de envío: registra el error pero no lo propaga, para que la
    acción del administrador en el panel no quede bloqueada por el SMTP.
    """
    if not user or not user.email:
        return

    subject = (
        "Tu solicitud para ser profesor en ANTARES fue aprobada"
        if approved
        else "Actualización sobre tu solicitud para ser profesor en ANTARES"
    )
    site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    message = render_to_string('teacher_application_email.html', {
        'user': user,
        'approved': approved,
        'site_url': site_url,
    })

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "No se pudo enviar el correo de decisión de profesor a %s", user.email
        )
