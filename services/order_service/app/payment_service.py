import stripe
from .settings import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(amount: float, order_id: int):
    
    payment_intent = stripe.PaymentIntent.create(
        amount=int(round(amount * 100)),
        currency="inr",
        metadata={
            "order_id": str(order_id)
        },
        automatic_payment_methods={
            "enabled": True,
            "allow_redirects": "never"
        }
    )

    return payment_intent