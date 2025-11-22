"""
React App Scaffolder skill.

Generates a complete React + Vite project structure with Kearney Design System styling.
"""

import json
from pathlib import Path
from typing import Any

from .models import AppScaffoldInput, AppScaffoldOutput


class ReactAppScaffolder:
    """Skill for scaffolding React applications with KDS styling."""

    def __init__(self):
        self.skill_id = "react_app_scaffolder"
        self.description = "Scaffold a React + Vite application with Kearney Design System"

    def execute(self, input_data: AppScaffoldInput) -> AppScaffoldOutput:
        """Execute the scaffolding operation."""
        output = AppScaffoldOutput()
        repo_path = Path(input_data.repo_path)

        try:
            # Create base directory structure
            self._create_directory_structure(repo_path, input_data)

            # Create configuration files
            self._create_config_files(repo_path, input_data, output)

            # Create source files
            self._create_source_files(repo_path, input_data, output)

            # Create initial pages
            for page in input_data.initial_pages:
                self._create_page(repo_path, page, output)

            # Create API client if requested
            if input_data.include_api_client:
                self._create_api_client(repo_path, input_data, output)

            # Create KDS styles
            self._create_kds_styles(repo_path, output)

            # Generate summary
            output.structure_summary = self._generate_summary(repo_path, input_data)
            output.commit_message = f"feat: scaffold {input_data.app_name} React app with KDS"
            output.success = True

        except Exception as e:
            output.success = False
            output.errors.append(str(e))

        return output

    def _create_directory_structure(self, repo_path: Path, input_data: AppScaffoldInput) -> None:
        """Create the base directory structure."""
        directories = [
            "src",
            "src/pages",
            "src/components",
            "src/api",
            "src/styles",
            "src/hooks",
            "src/utils",
            "public",
        ]

        for dir_name in directories:
            (repo_path / dir_name).mkdir(parents=True, exist_ok=True)

    def _create_config_files(self, repo_path: Path, input_data: AppScaffoldInput, output: AppScaffoldOutput) -> None:
        """Create project configuration files."""

        # package.json
        package_json = {
            "name": input_data.app_name.lower().replace(" ", "-"),
            "private": True,
            "version": "0.1.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.20.0",
                "axios": "^1.6.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.37",
                "@types/react-dom": "^18.2.15",
                "@typescript-eslint/eslint-plugin": "^6.10.0",
                "@typescript-eslint/parser": "^6.10.0",
                "@vitejs/plugin-react": "^4.2.0",
                "eslint": "^8.53.0",
                "eslint-plugin-react-hooks": "^4.6.0",
                "eslint-plugin-react-refresh": "^0.4.4",
                "typescript": "^5.2.2",
                "vite": "^5.0.0"
            }
        }

        package_path = repo_path / "package.json"
        package_path.write_text(json.dumps(package_json, indent=2))
        output.files_created.append("package.json")

        # vite.config.ts
        vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
'''
        (repo_path / "vite.config.ts").write_text(vite_config)
        output.files_created.append("vite.config.ts")

        # tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True
            },
            "include": ["src"],
            "references": [{"path": "./tsconfig.node.json"}]
        }
        (repo_path / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))
        output.files_created.append("tsconfig.json")

        # tsconfig.node.json
        tsconfig_node = {
            "compilerOptions": {
                "composite": True,
                "skipLibCheck": True,
                "module": "ESNext",
                "moduleResolution": "bundler",
                "allowSyntheticDefaultImports": True
            },
            "include": ["vite.config.ts"]
        }
        (repo_path / "tsconfig.node.json").write_text(json.dumps(tsconfig_node, indent=2))
        output.files_created.append("tsconfig.node.json")

        # index.html
        index_html = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{input_data.app_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''
        (repo_path / "index.html").write_text(index_html)
        output.files_created.append("index.html")

    def _create_source_files(self, repo_path: Path, input_data: AppScaffoldInput, output: AppScaffoldOutput) -> None:
        """Create main source files."""

        # main.tsx
        main_tsx = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './styles/index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
'''
        (repo_path / "src" / "main.tsx").write_text(main_tsx)
        output.files_created.append("src/main.tsx")

        # App.tsx with routing
        routes = "\n".join([
            f'        <Route path="/{page.lower()}" element={{<{page}Page />}} />'
            for page in input_data.initial_pages
        ])

        imports = "\n".join([
            f"import {page}Page from './pages/{page}Page'"
            for page in input_data.initial_pages
        ])

        app_tsx = f'''import {{ Routes, Route, Link }} from 'react-router-dom'
{imports}

function App() {{
  return (
    <div className="app">
      <header className="app-header">
        <nav className="nav-links">
          <Link to="/" className="nav-link">Home</Link>
{chr(10).join([f'          <Link to="/{page.lower()}" className="nav-link">{page}</Link>' for page in input_data.initial_pages if page != "Home"])}
        </nav>
        <h1>{input_data.app_name}</h1>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={{<HomePage />}} />
{routes}
        </Routes>
      </main>

      <footer className="app-footer">
        <p>Built with RSC App Builder</p>
      </footer>
    </div>
  )
}}

export default App
'''
        (repo_path / "src" / "App.tsx").write_text(app_tsx)
        output.files_created.append("src/App.tsx")

    def _create_page(self, repo_path: Path, page_name: str, output: AppScaffoldOutput) -> None:
        """Create a page component."""

        page_content = f'''import React from 'react'

interface {page_name}PageProps {{
  // Add props here
}}

const {page_name}Page: React.FC<{page_name}PageProps> = () => {{
  return (
    <div className="page {page_name.lower()}-page">
      <h2>{page_name}</h2>
      <p>Welcome to the {page_name} page.</p>
    </div>
  )
}}

export default {page_name}Page
'''

        page_path = repo_path / "src" / "pages" / f"{page_name}Page.tsx"
        page_path.write_text(page_content)
        output.files_created.append(f"src/pages/{page_name}Page.tsx")

    def _create_api_client(self, repo_path: Path, input_data: AppScaffoldInput, output: AppScaffoldOutput) -> None:
        """Create API client with Axios."""

        api_client = f'''import axios from 'axios'

const API_BASE_URL = '{input_data.api_base_url}'

export const apiClient = axios.create({{
  baseURL: API_BASE_URL,
  headers: {{
    'Content-Type': 'application/json',
  }},
}})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {{
    // Add auth token if available
    const token = localStorage.getItem('authToken')
    if (token) {{
      config.headers.Authorization = `Bearer ${{token}}`
    }}
    return config
  }},
  (error) => Promise.reject(error)
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {{
    if (error.response?.status === 401) {{
      // Handle unauthorized
      localStorage.removeItem('authToken')
    }}
    return Promise.reject(error)
  }}
)

// Generic API functions
export async function fetchData<T>(endpoint: string): Promise<T> {{
  const response = await apiClient.get<T>(endpoint)
  return response.data
}}

export async function postData<T, D>(endpoint: string, data: D): Promise<T> {{
  const response = await apiClient.post<T>(endpoint, data)
  return response.data
}}

export async function putData<T, D>(endpoint: string, data: D): Promise<T> {{
  const response = await apiClient.put<T>(endpoint, data)
  return response.data
}}

export async function deleteData<T>(endpoint: string): Promise<T> {{
  const response = await apiClient.delete<T>(endpoint)
  return response.data
}}
'''

        (repo_path / "src" / "api" / "client.ts").write_text(api_client)
        output.files_created.append("src/api/client.ts")

        # Types file
        types_content = '''// API response types

export interface ApiResponse<T> {
  data: T
  message?: string
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

// Add your domain types here
'''
        (repo_path / "src" / "api" / "types.ts").write_text(types_content)
        output.files_created.append("src/api/types.ts")

    def _create_kds_styles(self, repo_path: Path, output: AppScaffoldOutput) -> None:
        """Create Kearney Design System styles."""

        kds_styles = '''/* Kearney Design System - RSC App Builder */

:root {
  /* Primary colors - Kearney Purple */
  --kds-primary: #6B2D7B;
  --kds-primary-light: #8B4D9B;
  --kds-primary-dark: #4B1D5B;

  /* Secondary colors */
  --kds-secondary: #2C3E50;
  --kds-secondary-light: #34495E;

  /* Neutral colors */
  --kds-background: #F5F5F5;
  --kds-surface: #FFFFFF;
  --kds-text: #333333;
  --kds-text-secondary: #666666;
  --kds-border: #E0E0E0;

  /* Accent colors */
  --kds-accent: #9B59B6;
  --kds-info: #3498DB;
  --kds-warning: #F39C12;
  --kds-error: #E74C3C;
  --kds-success: #27AE60;

  /* Typography */
  --kds-font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --kds-font-size-sm: 0.875rem;
  --kds-font-size-md: 1rem;
  --kds-font-size-lg: 1.25rem;
  --kds-font-size-xl: 1.5rem;
  --kds-font-size-2xl: 2rem;

  /* Spacing */
  --kds-spacing-xs: 0.25rem;
  --kds-spacing-sm: 0.5rem;
  --kds-spacing-md: 1rem;
  --kds-spacing-lg: 1.5rem;
  --kds-spacing-xl: 2rem;

  /* Border radius */
  --kds-radius-sm: 4px;
  --kds-radius-md: 8px;
  --kds-radius-lg: 12px;

  /* Shadows */
  --kds-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --kds-shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --kds-shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}

/* Reset and base styles */
*, *::before, *::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: var(--kds-font-family);
  font-size: var(--kds-font-size-md);
  color: var(--kds-text);
  background-color: var(--kds-background);
  line-height: 1.5;
}

/* App layout */
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: var(--kds-primary);
  color: white;
  padding: var(--kds-spacing-md) var(--kds-spacing-xl);
  box-shadow: var(--kds-shadow-md);
}

.app-header h1 {
  margin: var(--kds-spacing-sm) 0 0;
  font-size: var(--kds-font-size-xl);
  font-weight: 600;
}

.nav-links {
  display: flex;
  gap: var(--kds-spacing-lg);
}

.nav-link {
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  font-size: var(--kds-font-size-sm);
  font-weight: 500;
  transition: color 0.2s ease;
}

.nav-link:hover {
  color: white;
}

.app-main {
  flex: 1;
  padding: var(--kds-spacing-xl);
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background: var(--kds-secondary);
  color: white;
  padding: var(--kds-spacing-md);
  text-align: center;
  font-size: var(--kds-font-size-sm);
}

/* Page styles */
.page {
  background: var(--kds-surface);
  border-radius: var(--kds-radius-lg);
  padding: var(--kds-spacing-xl);
  box-shadow: var(--kds-shadow-sm);
}

.page h2 {
  color: var(--kds-primary);
  margin-top: 0;
  font-size: var(--kds-font-size-2xl);
}

/* Button styles */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--kds-spacing-sm) var(--kds-spacing-md);
  border-radius: var(--kds-radius-md);
  font-size: var(--kds-font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn-primary {
  background: var(--kds-primary);
  color: white;
}

.btn-primary:hover {
  background: var(--kds-primary-dark);
}

.btn-secondary {
  background: var(--kds-secondary);
  color: white;
}

.btn-secondary:hover {
  background: var(--kds-secondary-light);
}

/* Form styles */
.form-group {
  margin-bottom: var(--kds-spacing-md);
}

.form-label {
  display: block;
  margin-bottom: var(--kds-spacing-xs);
  font-size: var(--kds-font-size-sm);
  font-weight: 500;
  color: var(--kds-text-secondary);
}

.form-input {
  width: 100%;
  padding: var(--kds-spacing-sm) var(--kds-spacing-md);
  border: 1px solid var(--kds-border);
  border-radius: var(--kds-radius-md);
  font-size: var(--kds-font-size-md);
  transition: border-color 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--kds-primary);
  box-shadow: 0 0 0 3px rgba(107, 45, 123, 0.1);
}

/* Card styles */
.card {
  background: var(--kds-surface);
  border-radius: var(--kds-radius-lg);
  padding: var(--kds-spacing-lg);
  box-shadow: var(--kds-shadow-sm);
  border: 1px solid var(--kds-border);
}

.card-title {
  font-size: var(--kds-font-size-lg);
  font-weight: 600;
  margin-bottom: var(--kds-spacing-md);
  color: var(--kds-text);
}

/* Table styles */
.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: var(--kds-spacing-sm) var(--kds-spacing-md);
  text-align: left;
  border-bottom: 1px solid var(--kds-border);
}

.table th {
  background: var(--kds-background);
  font-weight: 600;
  color: var(--kds-text-secondary);
  font-size: var(--kds-font-size-sm);
}

/* Utility classes */
.text-primary { color: var(--kds-primary); }
.text-secondary { color: var(--kds-text-secondary); }
.text-center { text-align: center; }
.mt-md { margin-top: var(--kds-spacing-md); }
.mb-md { margin-bottom: var(--kds-spacing-md); }
.p-md { padding: var(--kds-spacing-md); }
'''

        (repo_path / "src" / "styles" / "index.css").write_text(kds_styles)
        output.files_created.append("src/styles/index.css")

    def _generate_summary(self, repo_path: Path, input_data: AppScaffoldInput) -> str:
        """Generate a summary of the scaffolded structure."""
        return f"""React App Scaffolded: {input_data.app_name}

Directory Structure:
{repo_path}/
  ├── src/
  │   ├── pages/       - Page components
  │   ├── components/  - Reusable components
  │   ├── api/         - API client and types
  │   ├── styles/      - KDS stylesheets
  │   ├── hooks/       - Custom React hooks
  │   ├── utils/       - Utility functions
  │   ├── App.tsx      - Main app with routing
  │   └── main.tsx     - Entry point
  ├── public/          - Static assets
  ├── package.json     - Dependencies
  ├── vite.config.ts   - Vite configuration
  └── tsconfig.json    - TypeScript config

Initial Pages: {', '.join(input_data.initial_pages)}
Style: Kearney Design System (purple accent, charcoal panels)
API Client: {'Configured' if input_data.include_api_client else 'Not included'}

To start development:
  cd {repo_path}
  npm install
  npm run dev
"""
