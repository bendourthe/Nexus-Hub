def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    action = ctx.allowed_actions.get(value)
    if action is None:
        raise ValueError("unsupported action")
    return ctx.process_args(action, shell=False)
