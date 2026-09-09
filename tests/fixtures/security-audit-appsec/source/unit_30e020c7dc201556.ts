function receive(input: any): any {
    return input.value;
}

function handle(ctx: any, input: any): any {
    const value = receive(input);
    try { return ctx.service(value); }
    catch { return {error: "request could not be processed"}; }
}
