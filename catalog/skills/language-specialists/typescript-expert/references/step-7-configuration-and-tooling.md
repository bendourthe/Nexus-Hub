### Step 7: Configuration and Tooling

**tsconfig Strict Flags**:

A production-grade tsconfig should enable every strictness flag available. Each flag catches a distinct class of bugs. Here is a recommended configuration with explanations.

```jsonc
{
  "compilerOptions": {
    // Strict family (all enabled by "strict": true)
    "strict": true,

    // Additional strictness beyond the "strict" umbrella
    "noUncheckedIndexedAccess": true,    // arr[0] is T | undefined, not T
    "exactOptionalPropertyTypes": true,  // { x?: string } does not accept undefined assignment
    "noPropertyAccessFromIndexSignature": true, // force bracket notation for index signatures
    "noFallthroughCasesInSwitch": true,  // switch cases must break or return

    // Module resolution
    "module": "ESNext",
    "moduleResolution": "bundler",       // modern resolution for Vite, esbuild, etc.
    "resolveJsonModule": true,
    "esModuleInterop": true,
    "isolatedModules": true,             // required for esbuild, swc, and similar transpilers

    // Output
    "target": "ES2022",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "dist",

    // Path aliases
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@utils/*": ["src/utils/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx"],
  "exclude": ["node_modules", "dist"]
}
```

**Path Aliases**:

Path aliases replace long relative imports with clean, absolute-looking paths. You must configure them in both tsconfig (for the compiler) and your bundler (for runtime resolution).

```typescript
// Without path aliases
import { Button } from "../../../components/ui/Button";
import { formatDate } from "../../../../utils/date";

// With path aliases
import { Button } from "@components/ui/Button";
import { formatDate } from "@utils/date";
```

```typescript
// Vite configuration for path aliases
// vite.config.ts
import { defineConfig } from "vite";
import path from "path";

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "@components": path.resolve(__dirname, "src/components"),
      "@utils": path.resolve(__dirname, "src/utils"),
    },
  },
});
```

**Declaration Files**:

Declaration files (`.d.ts`) describe the types of JavaScript code that has no TypeScript source. Use them for untyped third-party modules, global ambient declarations, and when publishing a library.

```typescript
// Declare types for an untyped module
// types/untyped-lib.d.ts
declare module "untyped-lib" {
  export function doSomething(input: string): number;
  export interface Config {
    verbose: boolean;
    output: string;
  }
  export default function init(config: Config): void;
}

// Declare global ambient types available everywhere
// types/global.d.ts
declare global {
  // Extend NodeJS process.env with known variables
  namespace NodeJS {
    interface ProcessEnv {
      NODE_ENV: "development" | "production" | "test";
      DATABASE_URL: string;
      API_KEY: string;
    }
  }
}

export {}; // Makes this file a module so `declare global` works

// Type-only imports and exports (erased at runtime)
import type { User } from "./models";
export type { User };

// Import type inline (TypeScript 4.5+)
function processUser(user: import("./models").User): void {
  // ...
}
```

**Project References**:

Project references split a large codebase into smaller TypeScript projects that can be compiled independently. This improves editor responsiveness and build times through incremental compilation.

```jsonc
// Root tsconfig.json
{
  "files": [],
  "references": [
    { "path": "packages/shared" },
    { "path": "packages/client" },
    { "path": "packages/server" }
  ]
}

// packages/shared/tsconfig.json
{
  "compilerOptions": {
    "composite": true,       // required for project references
    "declaration": true,     // required for composite projects
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src/**/*.ts"]
}

// packages/client/tsconfig.json
{
  "compilerOptions": {
    "composite": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "references": [
    { "path": "../shared" }  // client depends on shared
  ],
  "include": ["src/**/*.ts", "src/**/*.tsx"]
}
```

```bash
# Build all referenced projects in dependency order
tsc --build

# Build incrementally (only changed projects)
tsc --build --incremental

# Clean all build outputs
tsc --build --clean
```
