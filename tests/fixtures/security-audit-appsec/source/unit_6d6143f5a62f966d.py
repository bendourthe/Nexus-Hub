def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    return ctx.records.get(value)
