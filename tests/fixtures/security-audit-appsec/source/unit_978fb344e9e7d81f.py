def receive(input):
    return input["value"]


def handle(ctx, input):
    value = receive(input)
    record = ctx.records.get(value)
    if record.owner_id != ctx.current_user.id:
        raise PermissionError("not permitted")
    return record
