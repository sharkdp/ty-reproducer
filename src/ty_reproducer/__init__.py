import os
import shutil
import subprocess
import sys
from pathlib import Path

import click

PROMPT = """We are developing a Python type checker called 'ty'.

A user has reported a bug at https://github.com/astral-sh/ty/issues/{issue_number}.

Our goal is to reproduce that bug locally.

* Read the content of that GitHub issue.
* Create Python files as appropriate based on the content of the users report.
  If no specific file name is given, use `main.py`. Create multiple Python files if imports
  between files seem to be important.
* Install necessary 3rd-party dependencies using `uv add <package-name>`.
* Run `uv run ty check` in the current folder and check if we can reproduce the error.
  Activating virtual envs or similar is not required.
* If not, modify the files / dependencies and see if you can reproduce it after the edit.
"""


@click.command()
@click.argument("issue_number", type=int)
@click.option("--force", "-f", is_flag=True)
def main(issue_number, force):
    folder_name = f"issue_{issue_number}"
    folder = Path(folder_name)

    if force:
        shutil.rmtree(folder)
    elif folder.exists():
        print(f"Folder '{folder.resolve()}' already exists. Use '-f' to overwrite.")
        sys.exit(1)

    folder.mkdir()

    subprocess.run(
        ["uv", "init", "--no-workspace", "--bare", "--name", folder_name],
        cwd=folder,
        check=True,
    )
    print(f"Created new uv project in folder '{folder.resolve()}'")

    prompt_file = folder / "PROMPT.md"
    prompt_file.write_text(PROMPT.replace("{issue_number}", str(issue_number)))

    # Try to find claude on PATH first, fallback to ~/.claude/local/claude
    claude_path = shutil.which("claude")
    if claude_path is None:
        claude_path = str(Path.home() / ".claude" / "local" / "claude")

    # Remove our VIRTUAL_ENV from the environment, so that nested "uv run" calls by Claude won't pick it up
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)

    subprocess.run(
        [
            claude_path,
            "--allowedTools",
            "WebFetch(domain:github.com),Bash(uv add:*),Bash(uv run ty check:*)",
            "--permission-mode",
            "acceptEdits",
            "Read the instructions in @PROMPT.md",
        ],
        cwd=folder,
        check=True,
        env=env,
    )


if __name__ == "__main__":
    main()
