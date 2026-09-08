def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    try:
        return ctx.service(value)
    except Exception:
        return {"error": "request could not be processed"}
