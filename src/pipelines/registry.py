"""Pipeline registry - catalog of available pipelines."""

from typing import Dict, Callable, Any
from pathlib import Path


class PipelineRegistry:
    """Registry of available data pipelines."""

    def __init__(self):
        """Initialize pipeline registry."""
        self._pipelines: Dict[str, Dict[str, Any]] = {}
        self._register_builtin_pipelines()

    def _register_builtin_pipelines(self):
        """Register built-in pipelines."""
        from src.pipelines.demo_pipeline import run_demo_pipeline

        self.register(
            name="demo",
            func=run_demo_pipeline,
            description="Demo end-to-end pipeline: ingest → transform → train → evaluate",
            inputs=["None (uses sample data)"],
            outputs=["models/demo_model.pkl", "models/metrics.json"],
        )

    def register(
        self,
        name: str,
        func: Callable,
        description: str,
        inputs: list,
        outputs: list,
    ):
        """
        Register a pipeline.

        Args:
            name: Pipeline identifier
            func: Callable that executes the pipeline
            description: Human-readable description
            inputs: List of required inputs
            outputs: List of outputs produced
        """
        self._pipelines[name] = {
            "name": name,
            "func": func,
            "description": description,
            "inputs": inputs,
            "outputs": outputs,
        }

    def get(self, name: str) -> Dict[str, Any]:
        """
        Get pipeline by name.

        Args:
            name: Pipeline identifier

        Returns:
            Pipeline metadata dictionary

        Raises:
            KeyError: If pipeline not found
        """
        if name not in self._pipelines:
            raise KeyError(f"Pipeline '{name}' not found. Available: {self.list()}")
        return self._pipelines[name]

    def run(self, name: str, **kwargs) -> Any:
        """
        Run a registered pipeline.

        Args:
            name: Pipeline identifier
            **kwargs: Arguments to pass to pipeline function

        Returns:
            Pipeline results
        """
        pipeline = self.get(name)
        return pipeline["func"](**kwargs)

    def list(self) -> list:
        """Get list of available pipeline names."""
        return list(self._pipelines.keys())

    def describe(self, name: str = None) -> str:
        """
        Get description of pipeline(s).

        Args:
            name: Pipeline name (if None, describe all)

        Returns:
            Formatted description string
        """
        if name:
            pipeline = self.get(name)
            return self._format_pipeline_description(pipeline)
        else:
            descriptions = []
            for pipe_name in sorted(self._pipelines.keys()):
                pipeline = self._pipelines[pipe_name]
                descriptions.append(self._format_pipeline_description(pipeline))
            return "\n\n".join(descriptions)

    def _format_pipeline_description(self, pipeline: Dict[str, Any]) -> str:
        """Format a single pipeline description."""
        lines = [
            f"Pipeline: {pipeline['name']}",
            f"Description: {pipeline['description']}",
            f"Inputs: {', '.join(pipeline['inputs'])}",
            f"Outputs: {', '.join(pipeline['outputs'])}",
        ]
        return "\n".join(lines)


# Global registry instance
registry = PipelineRegistry()


# Convenience functions
def get_pipeline(name: str) -> Dict[str, Any]:
    """Get pipeline from global registry."""
    return registry.get(name)


def run_pipeline(name: str, **kwargs) -> Any:
    """Run pipeline from global registry."""
    return registry.run(name, **kwargs)


def list_pipelines() -> list:
    """List available pipelines."""
    return registry.list()


def describe_pipelines(name: str = None) -> str:
    """Describe available pipelines."""
    return registry.describe(name)


if __name__ == "__main__":
    # Demo: List and describe pipelines
    print("Available Pipelines:")
    print("=" * 60)
    print(describe_pipelines())
