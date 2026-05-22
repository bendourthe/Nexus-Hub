import { Router } from "express";

const router = Router();

function getItem(req: any, res: any) {
  res.json({ id: req.params.id });
}

function deleteItem(req: any, res: any) {
  res.status(204).end();
}

router.get("/:id", getItem);
router.delete("/:id", deleteItem);
router.put("/:id", deleteItem);

export default router;
