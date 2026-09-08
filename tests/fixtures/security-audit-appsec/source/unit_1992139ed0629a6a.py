def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    try:
        return ctx.service(value)
    except Exception as error:
        return {"error": str(error), "debug": True}
