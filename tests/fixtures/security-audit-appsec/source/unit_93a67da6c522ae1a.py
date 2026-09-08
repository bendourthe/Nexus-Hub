def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    route = ctx.local_service_ids.get(value)
    if route is None:
        raise ValueError("unknown service")
    return ctx.request_registered(route, redirects=False)
