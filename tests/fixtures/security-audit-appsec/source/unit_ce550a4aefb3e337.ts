function receive(input: any): any {
    return input.value;
}

function handle(ctx: any, input: any): any {
    const value = receive(input);
    const item = ctx.catalog.lookup(value);
    return item ? ctx.readRegistered(item) : null;
}
