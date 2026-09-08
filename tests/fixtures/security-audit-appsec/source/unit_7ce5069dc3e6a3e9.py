def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    return ctx.query("SELECT value FROM records WHERE label = ?", (value,))
