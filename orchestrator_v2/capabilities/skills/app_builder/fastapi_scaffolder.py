"""
FastAPI Scaffolder skill.

Generates FastAPI routers, endpoints, and Pydantic models.
"""

from pathlib import Path
from typing import Any

from .models import FastAPIScaffoldInput, FastAPIScaffoldOutput


class FastAPIScaffolder:
    """Skill for scaffolding FastAPI endpoints and routers."""

    def __init__(self):
        self.skill_id = "fastapi_scaffolder"
        self.description = "Scaffold FastAPI routers and endpoints with Pydantic models"

    def execute(self, input_data: FastAPIScaffoldInput) -> FastAPIScaffoldOutput:
        """Execute the FastAPI scaffolding."""
        output = FastAPIScaffoldOutput()
        repo_path = Path(input_data.repo_path)

        try:
            # Create API directory structure if needed
            self._ensure_api_structure(repo_path)

            # Create Pydantic models
            self._create_models(repo_path, input_data, output)

            # Create router with endpoints
            self._create_router(repo_path, input_data, output)

            # Create tests if requested
            if input_data.include_tests:
                self._create_tests(repo_path, input_data, output)

            # Update main app to register router
            self._register_router(repo_path, input_data, output)

            # Generate commit message
            output.commit_message = f"feat: add {input_data.endpoint_name} API endpoints"
            output.success = True

        except Exception as e:
            output.success = False
            output.errors.append(str(e))

        return output

    def _ensure_api_structure(self, repo_path: Path) -> None:
        """Ensure API directory structure exists."""
        directories = [
            "api",
            "api/routers",
            "api/models",
            "tests",
        ]

        for dir_name in directories:
            (repo_path / dir_name).mkdir(parents=True, exist_ok=True)

        # Create __init__.py files
        for dir_name in directories:
            init_file = repo_path / dir_name / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Package initialization."""\n')

    def _create_models(
        self,
        repo_path: Path,
        input_data: FastAPIScaffoldInput,
        output: FastAPIScaffoldOutput
    ) -> None:
        """Create Pydantic models for the endpoint."""

        # Convert endpoint name to class name
        class_name = ''.join(word.capitalize() for word in input_data.endpoint_name.split('_'))

        # Generate field definitions from resource_model
        fields = []
        for field_name, field_type in input_data.resource_model.items():
            if isinstance(field_type, dict):
                # Handle complex types
                type_str = field_type.get('type', 'str')
                default = field_type.get('default', '...')
                fields.append(f"    {field_name}: {type_str} = {default}")
            else:
                fields.append(f"    {field_name}: {field_type}")

        if not fields:
            # Default fields if none provided
            fields = [
                "    id: int",
                "    name: str",
                '    description: str | None = None',
                "    created_at: datetime = Field(default_factory=datetime.utcnow)",
            ]

        fields_str = "\n".join(fields)

        model_content = f'''"""
Pydantic models for {input_data.endpoint_name} API.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class {class_name}Base(BaseModel):
    """Base model for {class_name}."""
{fields_str}


class {class_name}Create(BaseModel):
    """Model for creating a new {class_name}."""
{fields_str.replace("    id: int", "").strip() or "    name: str"}


class {class_name}Update(BaseModel):
    """Model for updating a {class_name}."""
    name: str | None = None
    description: str | None = None


class {class_name}Response({class_name}Base):
    """Response model for {class_name}."""
    id: int

    class Config:
        from_attributes = True


class {class_name}ListResponse(BaseModel):
    """List response for {class_name}."""
    items: list[{class_name}Response]
    total: int
    page: int = 1
    page_size: int = 20
'''

        model_path = repo_path / "api" / "models" / f"{input_data.endpoint_name}.py"
        model_path.write_text(model_content)
        output.files_created.append(f"api/models/{input_data.endpoint_name}.py")

    def _create_router(
        self,
        repo_path: Path,
        input_data: FastAPIScaffoldInput,
        output: FastAPIScaffoldOutput
    ) -> None:
        """Create FastAPI router with endpoints."""

        class_name = ''.join(word.capitalize() for word in input_data.endpoint_name.split('_'))
        endpoint_path = f"/{input_data.endpoint_name}"

        # Build endpoint functions based on requested methods
        endpoints = []

        if "GET" in input_data.methods:
            endpoints.append(f'''
@router.get("", response_model={class_name}ListResponse)
async def list_{input_data.endpoint_name}(
    page: int = 1,
    page_size: int = 20,
) -> {class_name}ListResponse:
    """List all {input_data.endpoint_name}."""
    # TODO: Implement database query
    return {class_name}ListResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
    )


@router.get("/{{item_id}}", response_model={class_name}Response)
async def get_{input_data.endpoint_name.rstrip('s')}(
    item_id: int,
) -> {class_name}Response:
    """Get a single {input_data.endpoint_name.rstrip('s')} by ID."""
    # TODO: Implement database lookup
    raise HTTPException(status_code=404, detail="{class_name} not found")
''')
            output.endpoint_paths.append(f"GET {endpoint_path}")
            output.endpoint_paths.append(f"GET {endpoint_path}/{{item_id}}")

        if "POST" in input_data.methods:
            endpoints.append(f'''
@router.post("", response_model={class_name}Response, status_code=201)
async def create_{input_data.endpoint_name.rstrip('s')}(
    data: {class_name}Create,
) -> {class_name}Response:
    """Create a new {input_data.endpoint_name.rstrip('s')}."""
    # TODO: Implement database insert
    return {class_name}Response(
        id=1,
        name=data.name,
        description=getattr(data, 'description', None),
        created_at=datetime.utcnow(),
    )
''')
            output.endpoint_paths.append(f"POST {endpoint_path}")

        if "PUT" in input_data.methods:
            endpoints.append(f'''
@router.put("/{{item_id}}", response_model={class_name}Response)
async def update_{input_data.endpoint_name.rstrip('s')}(
    item_id: int,
    data: {class_name}Update,
) -> {class_name}Response:
    """Update a {input_data.endpoint_name.rstrip('s')}."""
    # TODO: Implement database update
    raise HTTPException(status_code=404, detail="{class_name} not found")
''')
            output.endpoint_paths.append(f"PUT {endpoint_path}/{{item_id}}")

        if "DELETE" in input_data.methods:
            endpoints.append(f'''
@router.delete("/{{item_id}}", status_code=204)
async def delete_{input_data.endpoint_name.rstrip('s')}(
    item_id: int,
) -> None:
    """Delete a {input_data.endpoint_name.rstrip('s')}."""
    # TODO: Implement database delete
    raise HTTPException(status_code=404, detail="{class_name} not found")
''')
            output.endpoint_paths.append(f"DELETE {endpoint_path}/{{item_id}}")

        endpoints_str = "\n".join(endpoints)

        router_content = f'''"""
FastAPI router for {input_data.endpoint_name} endpoints.

{input_data.summary}
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException

from ..models.{input_data.endpoint_name} import (
    {class_name}Create,
    {class_name}Update,
    {class_name}Response,
    {class_name}ListResponse,
)

router = APIRouter(
    prefix="/{input_data.endpoint_name}",
    tags=["{input_data.endpoint_name}"],
)

{endpoints_str}
'''

        router_path = repo_path / "api" / "routers" / f"{input_data.endpoint_name}.py"
        router_path.write_text(router_content)
        output.files_created.append(f"api/routers/{input_data.endpoint_name}.py")

    def _create_tests(
        self,
        repo_path: Path,
        input_data: FastAPIScaffoldInput,
        output: FastAPIScaffoldOutput
    ) -> None:
        """Create test files for the endpoints."""

        class_name = ''.join(word.capitalize() for word in input_data.endpoint_name.split('_'))

        test_content = f'''"""
Tests for {input_data.endpoint_name} API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class Test{class_name}Endpoints:
    """Tests for {input_data.endpoint_name} endpoints."""

    def test_list_{input_data.endpoint_name}(self, client: TestClient):
        """Test listing {input_data.endpoint_name}."""
        response = client.get("/{input_data.endpoint_name}")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_{input_data.endpoint_name.rstrip('s')}_not_found(self, client: TestClient):
        """Test getting non-existent {input_data.endpoint_name.rstrip('s')}."""
        response = client.get("/{input_data.endpoint_name}/999")
        assert response.status_code == 404

    def test_create_{input_data.endpoint_name.rstrip('s')}(self, client: TestClient):
        """Test creating a {input_data.endpoint_name.rstrip('s')}."""
        response = client.post(
            "/{input_data.endpoint_name}",
            json={{"name": "Test {class_name}"}},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test {class_name}"
        assert "id" in data


@pytest.fixture
def client():
    """Create test client."""
    # TODO: Import your FastAPI app
    # from api.main import app
    # return TestClient(app)
    pytest.skip("Test client not configured")
'''

        test_path = repo_path / "tests" / f"test_{input_data.endpoint_name}.py"
        test_path.write_text(test_content)
        output.files_created.append(f"tests/test_{input_data.endpoint_name}.py")

    def _register_router(
        self,
        repo_path: Path,
        input_data: FastAPIScaffoldInput,
        output: FastAPIScaffoldOutput
    ) -> None:
        """Register the router with the main FastAPI app."""

        main_path = repo_path / "api" / "main.py"

        # Create main.py if it doesn't exist
        if not main_path.exists():
            main_content = f'''"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.{input_data.endpoint_name} import router as {input_data.endpoint_name}_router

app = FastAPI(
    title="App API",
    description="API built with RSC App Builder",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router({input_data.endpoint_name}_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {{"status": "healthy"}}
'''
            main_path.write_text(main_content)
            output.files_created.append("api/main.py")
            output.router_registered = True
        else:
            # Update existing main.py
            content = main_path.read_text()

            # Add import if not present
            import_stmt = f"from .routers.{input_data.endpoint_name} import router as {input_data.endpoint_name}_router"
            if import_stmt not in content:
                # Add import after other router imports
                import_pattern = r'(from \.routers\.\w+ import router as \w+_router\n)(?!from \.routers)'
                if 'from .routers' in content:
                    import re
                    content = re.sub(import_pattern, f'\\1{import_stmt}\n', content)
                else:
                    # Add after fastapi import
                    content = content.replace(
                        'from fastapi import FastAPI',
                        f'from fastapi import FastAPI\n\n{import_stmt}'
                    )

            # Register router if not present
            register_stmt = f"app.include_router({input_data.endpoint_name}_router)"
            if register_stmt not in content:
                # Add after other include_router calls
                if 'app.include_router' in content:
                    content = content.replace(
                        'app.include_router',
                        f'{register_stmt}\napp.include_router',
                        1
                    )
                else:
                    # Add before health check
                    content = content.replace(
                        '@app.get("/health")',
                        f'# Register routers\n{register_stmt}\n\n\n@app.get("/health")'
                    )

            main_path.write_text(content)
            output.files_modified.append("api/main.py") if "api/main.py" not in output.files_created else None
            output.router_registered = True
