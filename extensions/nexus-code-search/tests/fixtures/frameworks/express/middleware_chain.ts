import express from "express";

const app = express();

function authMiddleware(req: any, res: any, next: any) {
  next();
}

function loggerMiddleware(req: any, res: any, next: any) {
  next();
}

function adminHandler(req: any, res: any) {
  res.json({ admin: true });
}

app.use(loggerMiddleware);
app.post("/admin", authMiddleware, adminHandler);
app.all("/wildcard/*", authMiddleware, loggerMiddleware, adminHandler);
