function receive(input: any): any {
    return input.value;
}

function handle(ctx: any, input: any): any {
    const value = receive(input);
    const document = ctx.jsonCodec.parse(value);
    return ctx.schema.check(document);
}
