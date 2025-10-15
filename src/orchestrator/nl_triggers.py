"""Natural language trigger routing for orchestrator commands."""

from typing import List, Tuple, Optional
from .state import is_busy


# Trigger phrase mappings
TRIGGER_MAP = {
    # New project triggers
    "new project": ["intake", "new"],
    "create new project": ["intake", "new"],
    "start a new project": ["intake", "new"],
    "begin project intake": ["intake", "new"],
    "start new project": ["intake", "new"],
    "create project": ["intake", "new"],

    # Type-specific shortcuts
    "new web project": ["intake", "new", "--type", "webapp"],
    "new webapp": ["intake", "new", "--type", "webapp"],
    "new analytics project": ["intake", "new", "--type", "analytics"],
    "new ml project": ["intake", "new", "--type", "ml"],
    "new library": ["intake", "new", "--type", "library"],
    "new service": ["intake", "new", "--type", "service"],

    # Hygiene triggers
    "tidy repo": ["run", "repo-hygiene"],
    "cleanup repository": ["run", "repo-hygiene"],
    "hygiene check": ["run", "repo-hygiene"],
    "clean up repo": ["run", "repo-hygiene"],
    "repo cleanup": ["run", "repo-hygiene"],
    "cleanliness report": ["run", "repo-hygiene"],
    "repo health": ["run", "repo-hygiene"],
    "check repo health": ["run", "repo-hygiene"],
    "weekly hygiene": ["run", "repo-hygiene"],
    "show cleanliness": ["run", "repo-hygiene"],

    # Release triggers
    "prepare release": ["release", "prepare"],
    "new release": ["release", "prepare"],
    "cut release": ["release", "cut"],
    "ship release": ["release", "cut"],
    "create release": ["release", "cut"],
    "verify release": ["release", "verify"],
    "check release": ["release", "verify"],
    "rollback release": ["release", "rollback"],
    "undo release": ["release", "rollback"],
}

# Type keywords that can be detected in natural language
TYPE_KEYWORDS = {
    "web": "webapp",
    "webapp": "webapp",
    "website": "webapp",
    "api": "service",
    "service": "service",
    "microservice": "service",
    "analytics": "analytics",
    "ml": "ml",
    "machine learning": "ml",
    "data science": "ml",
    "library": "library",
    "package": "library",
}


def route_nl_command(
    text: str,
    busy: Optional[bool] = None,
    default_type: Optional[str] = None
) -> Tuple[List[str], Optional[str]]:
    """
    Route natural language command to orchestrator CLI argv.

    Args:
        text: Natural language input (e.g., "new project", "create new web project")
        busy: Whether orchestrator is currently busy (if None, will check state)
        default_type: Default project type if not specified in text

    Returns:
        Tuple of (command_argv, message)
        - command_argv: List of CLI arguments (e.g., ["intake", "new", "--type", "webapp"])
        - message: Optional message to show user (e.g., busy warning)

    Examples:
        >>> route_nl_command("new project")
        (["intake", "new"], None)

        >>> route_nl_command("create new web project")
        (["intake", "new", "--type", "webapp"], None)

        >>> route_nl_command("new project", busy=True)
        ([], "Orchestrator is currently running. Finish current workflow or run: orchestrator run --abort")
    """
    # Check busy state
    if busy is None:
        busy = is_busy()

    if busy:
        return (
            [],
            "Orchestrator is currently running a workflow. "
            "Please finish the current workflow or run: orchestrator run --abort"
        )

    # Normalize text
    text_lower = text.lower().strip()

    # Check for matches
    matched_command = None
    is_exact_match = False

    # First check exact phrase matches
    for phrase, command in TRIGGER_MAP.items():
        if text_lower == phrase:
            matched_command = command.copy()
            is_exact_match = True
            break

    # If no exact match, check for phrase as prefix (e.g., "new project analytics")
    if not matched_command:
        for phrase, command in TRIGGER_MAP.items():
            if text_lower.startswith(phrase + " "):
                matched_command = command.copy()
                is_exact_match = False
                break

    # If we found a match, check for type keywords
    if matched_command:
        # Check for type keywords in the text
        detected_type = None
        for keyword, mapped_type in TYPE_KEYWORDS.items():
            if keyword in text_lower:
                detected_type = mapped_type
                break

        # Add type argument if detected
        if detected_type and "--type" not in matched_command:
            matched_command.extend(["--type", detected_type])
        # Only apply default_type for non-exact matches (with extra text)
        elif not is_exact_match and default_type and "--type" not in matched_command:
            matched_command.extend(["--type", default_type])

        return (matched_command, None)

    # No match found
    return ([], None)


def describe_triggers() -> str:
    """Get human-readable description of available triggers."""
    lines = ["Available Natural Language Triggers:", ""]

    # Group by command
    triggers_by_cmd = {}
    for phrase, cmd in TRIGGER_MAP.items():
        cmd_str = " ".join(cmd)
        triggers_by_cmd.setdefault(cmd_str, []).append(phrase)

    for cmd_str, phrases in sorted(triggers_by_cmd.items()):
        lines.append(f"  Command: orchestrator {cmd_str}")
        for phrase in phrases:
            lines.append(f"    - \"{phrase}\"")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    # Demo usage
    print(describe_triggers())
    print("\n" + "=" * 60)
    print("Examples:")
    print("=" * 60)

    test_cases = [
        "new project",
        "create new web project",
        "start a new project",
        "new analytics project",
        "something else",
    ]

    for test in test_cases:
        cmd, msg = route_nl_command(test, busy=False)
        if cmd:
            print(f"\n  '{test}'")
            print(f"    → orchestrator {' '.join(cmd)}")
        else:
            print(f"\n  '{test}'")
            print(f"    → No trigger matched")
            if msg:
                print(f"    Note: {msg}")
