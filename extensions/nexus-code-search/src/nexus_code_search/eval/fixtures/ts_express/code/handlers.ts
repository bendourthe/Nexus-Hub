import express from "express";

const app = express();

function listUsers(req: any, res: any) {
  res.json([]);
}

function getUser(req: any, res: any) {
  res.json({ id: req.params.id });
}

function createUser(req: any, res: any) {
  res.json({ created: true });
}

app.get("/users", listUsers);
app.get("/users/:id", getUser);
app.post("/users", createUser);

export { listUsers, getUser, createUser };
