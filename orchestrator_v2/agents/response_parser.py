"""
Response parser for Orchestrator v2 agents.

Parses LLM responses into structured data for agent consumption.
Handles JSON extraction, validation, and error recovery.
"""

import json
import logging
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class PlanResponse(BaseModel):
    """Parsed response from a planning prompt."""
    analysis: str = ""
    steps: list[dict[str, Any]] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    validation_criteria: list[str] = Field(default_factory=list)
    raw_response: str = ""


class ArtifactData(BaseModel):
    """A single artifact from execution."""
    filename: str
    content: str
    artifact_type: str = "file"


class ActResponse(BaseModel):
    """Parsed response from an execution prompt."""
    execution_summary: str = ""
    artifacts: list[ArtifactData] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    success: bool = True
    error_message: str | None = None
    raw_response: str = ""


class ResponseParser:
    """Parser for LLM responses.
    
    Extracts structured data from LLM text responses,
    handling various formats and edge cases.
    """
    
    def parse_plan_response(self, response_text: str) -> PlanResponse:
        """Parse a planning response from the LLM.
        
        Args:
            response_text: Raw LLM response text.
            
        Returns:
            Parsed PlanResponse.
        """
        # Try to extract JSON from the response
        json_data = self._extract_json(response_text)
        
        if json_data:
            try:
                return PlanResponse(
                    analysis=json_data.get("analysis", ""),
                    steps=json_data.get("steps", []),
                    outputs=json_data.get("outputs", []),
                    dependencies=json_data.get("dependencies", []),
                    validation_criteria=json_data.get("validation_criteria", []),
                    raw_response=response_text,
                )
            except ValidationError as e:
                logger.warning(f"Validation error parsing plan response: {e}")
        
        # Fallback: Try to parse structured text
        return self._parse_plan_from_text(response_text)
    
    def parse_act_response(self, response_text: str) -> ActResponse:
        """Parse an execution response from the LLM.
        
        Args:
            response_text: Raw LLM response text.
            
        Returns:
            Parsed ActResponse.
        """
        # Try to extract JSON from the response
        json_data = self._extract_json(response_text)
        
        if json_data:
            try:
                artifacts = []
                for a in json_data.get("artifacts", []):
                    if isinstance(a, dict) and "filename" in a and "content" in a:
                        artifacts.append(ArtifactData(
                            filename=a["filename"],
                            content=a["content"],
                            artifact_type=a.get("artifact_type", "file"),
                        ))
                
                return ActResponse(
                    execution_summary=json_data.get("execution_summary", ""),
                    artifacts=artifacts,
                    recommendations=json_data.get("recommendations", []),
                    success=json_data.get("success", True),
                    error_message=json_data.get("error_message"),
                    raw_response=response_text,
                )
            except ValidationError as e:
                logger.warning(f"Validation error parsing act response: {e}")
        
        # Fallback: Try to extract artifacts from markdown
        return self._parse_act_from_text(response_text)
    
    def _extract_json(self, text: str) -> dict[str, Any] | None:
        """Extract JSON object from text.
        
        Handles JSON in code blocks and raw JSON.
        
        Args:
            text: Text potentially containing JSON.
            
        Returns:
            Parsed JSON dict or None.
        """
        # Try to find JSON in code blocks first
        json_block_pattern = r"```(?:json)?\s*\n?({[\s\S]*?})\s*\n?```"
        matches = re.findall(json_block_pattern, text)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Try to find raw JSON object
        json_pattern = r"({[\s\S]*?})(?:\s*$|\s*```|\s*\n\n)"
        matches = re.findall(json_pattern, text)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Try to parse the entire text as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _parse_plan_from_text(self, text: str) -> PlanResponse:
        """Parse plan from unstructured text.
        
        Args:
            text: Raw text response.
            
        Returns:
            PlanResponse with extracted data.
        """
        response = PlanResponse(raw_response=text)
        
        # Extract numbered steps
        step_pattern = r"^\d+\.\s*(.+)$"
        steps = re.findall(step_pattern, text, re.MULTILINE)
        response.steps = [
            {"step_id": f"step_{i+1}", "description": step, "estimated_tokens": 500}
            for i, step in enumerate(steps)
        ]
        
        # Extract bullet points as potential outputs
        bullet_pattern = r"^[-*]\s*(.+)$"
        bullets = re.findall(bullet_pattern, text, re.MULTILINE)
        
        # Try to categorize bullets
        for bullet in bullets:
            lower = bullet.lower()
            if any(ext in lower for ext in [".md", ".py", ".json", ".yaml", "file", "document"]):
                response.outputs.append(bullet)
            elif "depend" in lower or "require" in lower or "need" in lower:
                response.dependencies.append(bullet)
        
        # Use first paragraph as analysis
        paragraphs = text.split("\n\n")
        if paragraphs:
            response.analysis = paragraphs[0].strip()
        
        return response
    
    def _parse_act_from_text(self, text: str) -> ActResponse:
        """Parse execution response from unstructured text.
        
        Args:
            text: Raw text response.
            
        Returns:
            ActResponse with extracted data.
        """
        response = ActResponse(raw_response=text)
        
        # Try to extract code blocks as artifacts
        code_block_pattern = r"```(\w+)?\s*\n([\s\S]*?)```"
        matches = re.findall(code_block_pattern, text)
        
        for i, (lang, content) in enumerate(matches):
            if lang and lang.lower() != "json":  # Skip JSON blocks (those are metadata)
                ext = self._lang_to_extension(lang)
                response.artifacts.append(ArtifactData(
                    filename=f"artifact_{i+1}.{ext}",
                    content=content.strip(),
                    artifact_type="code",
                ))
        
        # Try to extract markdown sections as document artifacts
        section_pattern = r"^# ([^\n]+)\n([\s\S]*?)(?=^# |\Z)"
        sections = re.findall(section_pattern, text, re.MULTILINE)
        
        for title, content in sections:
            if len(content.strip()) > 100:  # Only substantial sections
                filename = self._title_to_filename(title)
                if not any(a.filename == filename for a in response.artifacts):
                    response.artifacts.append(ArtifactData(
                        filename=filename,
                        content=f"# {title}\n{content.strip()}",
                        artifact_type="document",
                    ))
        
        # Use first paragraph as summary
        paragraphs = text.split("\n\n")
        if paragraphs:
            response.execution_summary = paragraphs[0].strip()[:500]
        
        response.success = True
        return response
    
    def _lang_to_extension(self, lang: str) -> str:
        """Convert language identifier to file extension.
        
        Args:
            lang: Language identifier.
            
        Returns:
            File extension.
        """
        mapping = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "markdown": "md",
            "yaml": "yaml",
            "yml": "yaml",
            "json": "json",
            "sql": "sql",
            "bash": "sh",
            "shell": "sh",
        }
        return mapping.get(lang.lower(), lang.lower())
    
    def _title_to_filename(self, title: str) -> str:
        """Convert section title to filename.
        
        Args:
            title: Section title.
            
        Returns:
            Sanitized filename.
        """
        # Remove special characters and convert to snake_case
        clean = re.sub(r"[^\w\s-]", "", title.lower())
        clean = re.sub(r"[\s-]+", "_", clean)
        return f"{clean}.md"


# Singleton instance
_parser: ResponseParser | None = None


def get_response_parser() -> ResponseParser:
    """Get the global response parser instance."""
    global _parser
    if _parser is None:
        _parser = ResponseParser()
    return _parser
