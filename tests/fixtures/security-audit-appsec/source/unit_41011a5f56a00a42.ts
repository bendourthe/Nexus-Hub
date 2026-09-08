function receive(input: any): any {
    return input.value;
}

function handle(ctx: any, input: any): any {
    const value = receive(input);
    return ctx.objectRestorer.restore(value, {allowConstructors: true});
}
