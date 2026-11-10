from web import total

BULK_QUANTITY = 10
BULK_DISCOUNT = 0.1


def discounted_total(quantity, unit_price):
    base = total(quantity, unit_price)
    if quantity >= BULK_QUANTITY:
        return base * (1 - BULK_DISCOUNT)
    return base
