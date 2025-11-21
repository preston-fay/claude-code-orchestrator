# Kearney Ready-Set-Go! UI

A React SPA for managing and visualizing Ready/Set/Go orchestration projects.

## Features

- **Project Management**: Create, list, and manage orchestration projects
- **RSG Visualization**: Visual representation of Ready/Set/Go macro stages
- **Phase Control**: Run individual phases and track progress
- **Checkpoint Tracking**: View checkpoint artifacts and status
- **Settings Configuration**: Configure API endpoint and user identity

## Tech Stack

- React 18 with TypeScript
- Vite for fast development
- React Router v6 for navigation
- Axios for API communication
- Kearney Design System (KDS) styling

## Prerequisites

- Node.js 18+
- npm or yarn
- Running Orchestrator API (default: http://localhost:8000)

## Getting Started

### Installation

```bash
cd rsg-ui
npm install
```

### Configuration

Copy the environment template:

```bash
cp .env.example .env.local
```

Edit `.env.local` to configure:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_DEFAULT_USER_ID=dev-user
VITE_DEFAULT_USER_EMAIL=dev@example.com
```

### Development

```bash
npm run dev
```

Opens at http://localhost:3000

The development server proxies `/api` requests to the orchestrator API at `http://localhost:8000`.

### Build

```bash
npm run build
```

Build output goes to `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
rsg-ui/
├── src/
│   ├── api/
│   │   ├── client.ts       # API client with auth headers
│   │   └── types.ts        # TypeScript interfaces
│   ├── components/
│   │   ├── Header.tsx      # App header with user info
│   │   ├── RsgStatus.tsx   # RSG 3-card visualization
│   │   └── SettingsPanel.tsx
│   ├── pages/
│   │   ├── ProjectListPage.tsx
│   │   └── ProjectDetailPage.tsx
│   ├── App.tsx             # Main app shell with routing
│   ├── main.tsx            # Entry point
│   └── index.css           # KDS-compliant styles
├── .env.example            # Environment template
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## API Integration

The UI communicates with the Orchestrator API using these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/projects` | GET | List all projects |
| `/projects` | POST | Create new project |
| `/projects/{id}` | GET | Get project details |
| `/projects/{id}/run-phase` | POST | Execute a phase |
| `/projects/{id}/checkpoints` | GET | List checkpoints |

### Authentication

In development mode, the UI sends authentication headers with each request:

- `X-User-Id`: User identifier
- `X-User-Email`: User email address

Configure these in Settings or via environment variables.

## RSG Visualization

The app displays the Ready/Set/Go workflow as three macro stages:

1. **Ready**: Planning, Architecture, Consensus phases
2. **Set**: Data Engineering, Development phases
3. **Go**: QA, Documentation, Deployment phases

Each stage shows its status (pending/active/completed) based on the current phase.

## Deployment to AWS Amplify

### Build Settings

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd rsg-ui
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: rsg-ui/dist
    files:
      - '**/*'
  cache:
    paths:
      - rsg-ui/node_modules/**/*
```

### Environment Variables

Set in Amplify Console:

- `VITE_API_BASE_URL`: Your App Runner API URL (e.g., `https://xxx.us-east-1.awsapprunner.com`)
- `VITE_DEFAULT_USER_ID`: Default user ID
- `VITE_DEFAULT_USER_EMAIL`: Default user email

## Kearney Design System

The UI follows Kearney Design System (KDS) guidelines:

- **Primary Color**: Purple (#7823DC)
- **Font Family**: Inter, Arial
- **No Green**: Success states use purple per brand guidelines
- **Charcoal**: Dark backgrounds (#1E1E1E)

All styles use CSS custom properties from `src/index.css`.

## Development Notes

### Adding New Pages

1. Create component in `src/pages/`
2. Add route in `src/App.tsx`
3. Use KDS color variables from CSS

### API Client

The API client in `src/api/client.ts` manages:
- Base URL configuration
- Authentication headers
- Response typing

### Local Storage

Settings are persisted in localStorage:
- `rsg_api_config`: API base URL and user identity

## License

Proprietary - Kearney
