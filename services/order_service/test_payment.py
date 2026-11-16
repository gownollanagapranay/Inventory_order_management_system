import stripe
from app.settings import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

PAYMENT_INTENT_ID = "pi_3UXbQ4BL7s51PFTL1mBDcqsl"

payment_intent = stripe.PaymentIntent.confirm(
    PAYMENT_INTENT_ID,
    payment_method="pm_card_visa"
)

print("Payment Intent ID:", payment_intent.id)
print("Payment Status:", payment_intent.status)
print("Amount:", payment_intent.amount)
print("Currency:", payment_intent.currency)