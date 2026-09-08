def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    return ctx.session_cookie(value, secure=True, httponly=True, samesite="Strict")
