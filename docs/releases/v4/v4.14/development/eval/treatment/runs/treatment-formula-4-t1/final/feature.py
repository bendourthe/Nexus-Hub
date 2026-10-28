from web import total

BULK_QUANTITY = 10


def discounted_total(quantity, unit_price):
    base = total(quantity, unit_price)
    if quantity >= BULK_QUANTITY:
        return base * 9 / 10
    return base
