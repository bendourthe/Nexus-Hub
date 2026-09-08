function receive(input: any): any {
    return input.value;
}

function handle(ctx: any, input: any): any {
    const value = receive(input);
    const route = ctx.serviceIds.lookup(value);
    if (!route) { return {error: "unknown service"}; }
    return ctx.requestRegistered(route, {redirects: false});
}
