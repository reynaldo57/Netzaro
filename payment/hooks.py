from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from django.conf import settings
import time
from .models import Order


@receiver(valid_ipn_received)
def paypal_payment_received(sender, **kwargs):
    #Add a ten seconds pause for paypal to send IPN data
    time.sleep(10)
    # Grab the info that paypal sends
    paypal_obj = sender
    #Grab the invoice
    my_Invoice = str(paypal_obj.invoice)

    #Match the paypal invoice to the Order invoice
    #Look Up The Order
    my_Order = Order.objects.get(invoice=my_Invoice)

    #Record the Order was paid
    my_Order.paid = True

    #Save the order
    my_Order.save