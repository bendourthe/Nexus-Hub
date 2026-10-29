from web import total

DISCOUNT_THRESHOLD = 10


def discounted_total(quantity, unit_price):
    base = total(quantity, unit_price)
    if quantity >= DISCOUNT_THRESHOLD:
        return base * 0.9
    return base
