from web import reached


def alert(value):
    return "ALERT" if reached(value) else "OK"
