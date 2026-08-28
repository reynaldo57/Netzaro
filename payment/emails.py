"""Correos transaccionales de la app de pagos."""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order):
    """Envía el correo de confirmación de compra para una orden ya pagada.

    Tolera fallos: si el SMTP no responde, se registra el error pero no se
    propaga, para no romper el webhook/redirección de la pasarela de pago.
    """
    email = order.email or (order.user.email if order.user_id and order.user else None)
    if not email:
        return

    items = list(order.orderitem_set.select_related('product'))
    site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    message = render_to_string('order_confirmation_email.html', {
        'order': order,
        'items': items,
        'site_url': site_url,
    })

    try:
        send_mail(
            f"Confirmación de tu compra en ANTARES (Orden #{order.id})",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "No se pudo enviar la confirmación de compra de la orden %s", order.id
        )
