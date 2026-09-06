// HTTP route handlers for posts and comments, mounted by the Express server.
import { Router } from "express";

import { cached, query } from "./db";

const router = Router();

router.get("/posts", async (req, res) => {
  const posts = await cached("posts:all", () =>
    query("SELECT id, title, slug FROM posts ORDER BY created_at DESC"),
  );
  res.json(posts);
});

router.get("/posts/:slug", async (req, res) => {
  const rows = await query("SELECT * FROM posts WHERE slug = $1", [
    req.params.slug,
  ]);
  res.json(rows[0] ?? null);
});

router.post("/posts", requireAuth, async (req, res) => {
  const { title, body } = req.body;
  const rows = await query(
    "INSERT INTO posts(title, body) VALUES($1, $2) RETURNING id",
    [title, body],
  );
  res.status(201).json({ id: rows[0].id });
});

router.post("/posts/:id/comments", async (req, res) => {
  await query("INSERT INTO comments(post_id, body) VALUES($1, $2)", [
    req.params.id,
    req.body.body,
  ]);
  res.status(201).end();
});

export default router;
