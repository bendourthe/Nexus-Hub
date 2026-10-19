// The pinned @types/node predates the built-in SQLite module; currentModel.ts
// checks the loaded module's shape at runtime instead of trusting typings.
declare module "node:sqlite";
