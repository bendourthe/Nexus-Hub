import cors from "cors";
import express from "express";
import morgan from "morgan";

const app = express();

const API_KEY = process.env.API_KEY;
const MODE = process.env.NODE_ENV || "dev";

app.use(cors());
app.use(morgan("dev"));
app.use(rateLimit({ max: 100 }));

app.get("/users/:id", (req, res) => res.json(users.find_one(req.params.id)));
app.post("/users", createUser);

export default app;
