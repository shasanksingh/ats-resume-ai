import { defineConfig, globalIgnores } from "eslint/config";
import eslintJs from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const baseDirectory = dirname(fileURLToPath(import.meta.url));
const compat = new FlatCompat({
  baseDirectory,
  recommendedConfig: eslintJs.configs.recommended,
  allConfig: eslintJs.configs.all
});

export default defineConfig([
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  globalIgnores([".next/**", ".next-*/**", "node_modules/**", "next-env.d.ts"])
]);
