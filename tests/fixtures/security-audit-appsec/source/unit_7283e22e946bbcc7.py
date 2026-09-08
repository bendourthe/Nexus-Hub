def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    return ctx.transport.get(value)
