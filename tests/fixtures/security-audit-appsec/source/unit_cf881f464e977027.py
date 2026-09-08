def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    return ctx.process(value, shell=True)
