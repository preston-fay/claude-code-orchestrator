/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_ORCHESTRATOR_API_URL: string;
  // add other VITE_... vars here if you ever need them
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
