import { randomBytes } from "node:crypto";

interface WebviewDocumentOptions {
  body: string;
  styles: string;
  script: string;
  nonce?: string;
  cspDirectives?: readonly string[];
}

export function renderWebviewDocument({
  body,
  styles,
  script,
  nonce = createNonce(),
  cspDirectives = []
}: WebviewDocumentOptions): string {
  const csp = [
    "default-src 'none'",
    ...cspDirectives,
    `style-src 'nonce-${nonce}'`,
    `script-src 'nonce-${nonce}'`
  ].join("; ");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="${csp};">
  <style nonce="${nonce}">${styles}</style>
</head>
<body>
  ${body}
  <script nonce="${nonce}">
    ${script}
  </script>
</body>
</html>`;
}

function createNonce(): string {
  return randomBytes(16).toString("base64url");
}
