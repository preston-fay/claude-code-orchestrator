/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_ORCHESTRATOR_API_URL: string;
  readonly VITE_DEFAULT_USER_ID: string;
  readonly VITE_DEFAULT_USER_EMAIL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
