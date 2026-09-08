def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    item = ctx.published_files.get(value)
    if item is None:
        return None
    return ctx.read_registered(item)
