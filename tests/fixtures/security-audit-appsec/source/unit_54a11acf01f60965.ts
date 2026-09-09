function receive(input: any): any {
    return input.value;
}

function handle(ctx: any, input: any): any {
    const value = receive(input);
    const action = ctx.actions.get(value);
    if (!action) { throw new Error("unsupported action"); }
    return ctx.processArgs(action, {shell: false});
}
