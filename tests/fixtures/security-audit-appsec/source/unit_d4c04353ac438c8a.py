def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    return {"value": value, "secure": False, "httponly": False, "samesite": "None"}
