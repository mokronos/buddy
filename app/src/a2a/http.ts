import { z, type ZodType } from "zod";

export async function readJson<T>(response: Response, schema: ZodType<T>): Promise<T> {
  const text = await response.text();
  if (!response.ok) {
    throw new Error(text || `Request failed with HTTP ${response.status}`);
  }

  let parsed: unknown;
  try {
    parsed = text.length > 0 ? JSON.parse(text) : null;
  } catch {
    throw new Error("Invalid JSON response");
  }

  const result = schema.safeParse(parsed);
  if (!result.success) {
    throw new Error(`Invalid API response: ${z.prettifyError(result.error)}`);
  }

  return result.data;
}
