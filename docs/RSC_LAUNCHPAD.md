# RSC Launchpad

The RSC Launchpad is the new homepage for the Ready-Set-Code platform, providing a streamlined experience for starting new projects and accessing recent work.

## Overview

The Launchpad replaces the previous Project List as the default landing page (`/`), while the Project List remains accessible at `/projects`.

## Features

### Quick Actions

- **Start New Project**: Opens a pre-filled modal for creating a new project
- Quick access to template catalog for rapid project initialization

### Template Catalog

Visual grid of available project templates, each showing:

- **Icon**: Visual identifier for the template type
- **Title**: Display name of the template
- **Description**: Brief explanation of what the template builds
- **Capabilities**: Purple chips showing included capabilities (e.g., `data pipeline`, `analytics forecasting`)
- **Best For**: Use cases and scenarios where this template excels
- **Start Project Button**: One-click project creation with pre-filled settings

### Recent Projects

- Displays up to 6 most recent projects sorted by creation date
- Each project card shows:
  - Project name
  - Current status
  - Current phase
  - Creation date
- Click to navigate directly to project detail
- "View all projects" link to access full project list

## Navigation

| Route | Page | Description |
|-------|------|-------------|
| `/` | LaunchpadPage | New homepage with template catalog |
| `/projects` | ProjectListPage | Full project list with table view |
| `/projects/:id` | ProjectDetailPage | Project detail with RSG status |
| `/projects/:id/dashboard` | ProjectDashboardPage | Project metrics dashboard |
| `/projects/:id/features` | ProjectFeaturesPage | Feature management |
| `/projects/:id/app-build` | ProjectAppBuildPage | App build status |

## Project Creation Flow

1. **From Launchpad**:
   - Click "Start Project" on a template card
   - Modal opens with pre-filled values:
     - Project name: `{Template Title} (Month Year)`
     - Brief: Template's suggested brief
     - Capabilities: Template's default capabilities
   - Optionally enable "Auto-create GitHub repo"
   - Click "Create Project"

2. **From Project List**:
   - Click "New Project"
   - Select a template from the card grid
   - Fill in project details
   - Click "Create Project"

## Auto GitHub Repository

When creating a project, you can enable automatic GitHub repository creation:

- Toggle "Automatically create a GitHub repo for this project"
- Requires `GITHUB_PAT` environment variable to be set
- Creates a private repository with:
  - README.md
  - docs/PRD.md
  - docs/architecture.md
  - .gitignore
- Repository URL is stored in `app_repo_url` field

## Configuration

### Environment Variables

```bash
# Required for auto-repo creation
GITHUB_PAT=your-github-personal-access-token
```

### API Endpoints

The Launchpad uses these API endpoints:

- `GET /projects` - List all projects
- `GET /project-templates` - List template catalog
- `POST /projects` - Create new project

## Styling

The Launchpad uses the Kearney Design System (KDS) tokens:

- **Primary color**: Purple (`#7823DC`)
- **Grid layout**: 3 columns on desktop, responsive on smaller screens
- **Template cards**: Hover effects with purple borders
- **Capability chips**: Violet background with purple text

## Best Practices

1. **Template Selection**: Choose the template that best matches your project's primary goal
2. **Project Brief**: Customize the suggested brief to add specific requirements
3. **Capabilities**: Review and adjust capabilities before creation
4. **GitHub Integration**: Enable auto-repo for production projects requiring version control

## Related Documentation

- [RSC Template Catalog](RSC_TEMPLATE_CATALOG.md)
- [RSC Orchestration Profiles](RSC_ORCHESTRATION_PROFILES.md)
- [RSC User Guide](RSC_USER_GUIDE.md)
