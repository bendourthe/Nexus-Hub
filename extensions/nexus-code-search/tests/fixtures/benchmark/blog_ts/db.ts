// Shared database + cache clients for the blog service. Imported nearly
// everywhere, so this is one of the hottest files in the codebase.
import { Pool } from "pg";
import { createClient } from "redis";

const DATABASE_URL = process.env.DATABASE_URL;
const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";

export const pool = new Pool({ connectionString: DATABASE_URL });
export const cache = createClient({ url: REDIS_URL });

export async function query(sql: string, params: unknown[] = []) {
  const client = await pool.connect();
  try {
    const result = await client.query(sql, params);
    return result.rows;
  } finally {
    client.release();
  }
}

export async function cached(key: string, loader: () => Promise<unknown>) {
  const hit = await cache.get(key);
  if (hit) {
    return JSON.parse(hit);
  }
  const value = await loader();
  await cache.set(key, JSON.stringify(value));
  return value;
}
