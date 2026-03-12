import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const SOURCEMAP_COMMENT = /\n\/\/# sourceMappingURL=.*\s*$/;
const TARGET_DIRS = ["node_modules/entities/lib/esm"];

function walk(dir) {
  const entries = readdirSync(dir);

  for (const entry of entries) {
    const path = join(dir, entry);
    const stats = statSync(path);

    if (stats.isDirectory()) {
      walk(path);
      continue;
    }

    if (!path.endsWith(".js")) {
      continue;
    }

    const code = readFileSync(path, "utf8");

    if (!SOURCEMAP_COMMENT.test(code)) {
      continue;
    }

    writeFileSync(path, code.replace(SOURCEMAP_COMMENT, ""), "utf8");
  }
}

for (const dir of TARGET_DIRS) {
  walk(fileURLToPath(new URL(`../${dir}`, import.meta.url)));
}
