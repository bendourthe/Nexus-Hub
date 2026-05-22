import express from "express";

const app = express();

function listUsers(req: any, res: any) {
  res.json([]);
}

function createUser(req: any, res: any) {
  res.json({ id: 1 });
}

app.get("/users", listUsers);
app.post("/users", createUser);
app.get("/health", (req: any, res: any) => res.send("ok"));
