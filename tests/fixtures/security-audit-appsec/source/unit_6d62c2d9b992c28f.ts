function receive(input: any): any {
    return input.value;
}

function handle(ctx: any, input: any): any {
    const value = receive(input);
    return ctx.execute("SELECT value FROM records WHERE label = " + value);
}
