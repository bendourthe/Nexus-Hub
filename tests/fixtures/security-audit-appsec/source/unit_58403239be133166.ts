function receive(input: any): any {
    return input.value;
}

function handle(ctx: any, input: any): any {
    const value = receive(input);
    try { return ctx.service(value); }
    catch (error) { return {error: String(error), debug: true}; }
}
