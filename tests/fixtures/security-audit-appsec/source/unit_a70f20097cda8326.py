def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    document = ctx.json_codec.decode(value)
    return ctx.schema.validate(document)
