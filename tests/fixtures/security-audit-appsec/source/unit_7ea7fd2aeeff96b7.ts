function receive(input: any): any {
    return input.value;
}

function handle(ctx: any, input: any): any {
    const value = receive(input);
    return ctx.sessionCookie(value, {secure: true, httpOnly: true, sameSite: "Strict"});
}
