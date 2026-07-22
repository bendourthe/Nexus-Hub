// Express application entry point: wires middleware and mounts the routers.
import cors from "cors";
import express from "express";
import helmet from "helmet";
import morgan from "morgan";
import rateLimit from "express-rate-limit";

import { cache, pool } from "./db";
import routes from "./routes";

const PORT = process.env.PORT || "3000";
const SESSION_SECRET = process.env.SESSION_SECRET;

const app = express();

app.use(helmet());
app.use(cors());
app.use(morgan("combined"));
app.use(rateLimit({ windowMs: 60000, max: 120 }));
app.use(express.json());

app.get("/health", async (req, res) => {
  await pool.query("SELECT 1");
  res.json({ ok: true });
});

app.use("/api", routes);

export function start() {
  return app.listen(Number(PORT), () => {
    console.log(`blog listening on ${PORT}`);
  });
}

export { app };
