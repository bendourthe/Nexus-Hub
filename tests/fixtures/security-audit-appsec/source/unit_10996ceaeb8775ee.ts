function receive(input: any): any {
    return input.value;
}

function handle(ctx: any, input: any): any {
    const value = receive(input);
    const record = ctx.records.get(value);
    if (!ctx.permissions.owns(ctx.currentUser, record)) { return {status: 403}; }
    return record;
}
