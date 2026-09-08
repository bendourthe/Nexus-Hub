def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    return ctx.pickle_adapter.loads(value)
