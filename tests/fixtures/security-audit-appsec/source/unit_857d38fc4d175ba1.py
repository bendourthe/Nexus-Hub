def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    return ctx.read_text(ctx.root / value)
