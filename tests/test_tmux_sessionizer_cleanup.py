#!/usr/bin/env python3
"""Run with python3 tests/test_tmux_sessionizer_cleanup.py; uses fake tmux."""

import os
from pathlib import Path
import subprocess
import tempfile


SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "tmux-sessionizer-cleanup"


def main():
    with tempfile.TemporaryDirectory(prefix="sessionizer-cleanup-test-") as directory:
        base = Path(directory)
        root = base / "projects"
        root.mkdir()
        (root / "exists").mkdir()
        (root / "has.dots").mkdir()
        (root / "has spaces").mkdir()
        config = base / "config" / "tmux-sessionizer"
        config.mkdir(parents=True)
        (config / "tmux-sessionizer.conf").write_text(
            f'TS_SEARCH_PATHS=("{root}")\nTS_MAX_DEPTH=1\n'
        )
        state = base / "sessions"
        original = (
            f"$1\t1\tprojects_exists\t0\t{base}\n"
            f"$2\t2\tprojects_gone\t0\t{base}\n"
            f"$3\t3\tprojects_also-gone\t1\t{base}\n"
            f"$4\t4\tprojects_has_dots\t0\t{base}\n"
            f"$5\t5\tmanual\t0\t{base}\n"
            f"$6\t6\tmanual-missing\t0\t{base / 'deleted directory'}\n"
            f"$7\t7\tprojects_has spaces\t0\t{base}\n"
        )
        state.write_text(original)
        killed = base / "killed"
        bin_dir = base / "bin"
        bin_dir.mkdir()
        commands = {
            "tmux": """#!/usr/bin/env bash
case $1 in
    list-sessions) cat "$TEST_STATE" ;;
    display-message) printf '%s\\n' '$2' ;;
    kill-session) printf '%s\\n' "$3" >> "$TEST_KILLED" ;;
    *) exit 2 ;;
esac
""",
            "fzf": """#!/usr/bin/env bash
if [[ ${TEST_CANCEL:-} == yes ]]; then exit 130; fi
if [[ ${TEST_ERROR:-} == yes ]]; then exit 2; fi
if [[ -n ${TEST_RECOVER:-} ]]; then mkdir -p "$TEST_RECOVER"; fi
if [[ ${TEST_CHANGED:-} == yes ]]; then
    sed -i 's/projects_gone/projects_replaced/' "$TEST_STATE"
fi
grep -E 'projects_(gone|also-gone)'
""",
        }
        for name, content in commands.items():
            command = bin_dir / name
            command.write_text(content)
            command.chmod(0o755)
        env = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "XDG_CONFIG_HOME": str(base / "config"),
            "TEST_STATE": str(state),
            "TEST_KILLED": str(killed),
            "HOME": str(base),
            "TMUX_PANE": "",
        }

        def run(*args, answer="", extra=None):
            return subprocess.run(
                ["bash", str(SCRIPT), *args],
                cwd=base,
                env={**env, **(extra or {})},
                input=answer,
                capture_output=True,
                text=True,
            )

        listing = run("--list")
        assert listing.returncode == 0, listing.stderr
        assert "projects_gone" in listing.stdout
        assert "projects_also-gone" in listing.stdout
        assert "manual-missing" in listing.stdout
        for valid in ("projects_exists", "projects_has_dots", "projects_has spaces"):
            assert valid not in listing.stdout, listing.stdout
        assert "\tmanual\t" not in listing.stdout
        assert not killed.exists()

        assert run(answer="no\n").returncode == 0
        assert run(extra={"TEST_CANCEL": "yes"}).returncode == 0
        assert run(extra={"TEST_ERROR": "yes"}).returncode == 2
        assert not killed.exists()

        result = run(answer="delete\n")
        assert result.returncode == 0, result.stderr
        assert killed.read_text().splitlines() == ["$2", "$3"]
        killed.unlink()

        result = run(answer="delete\n", extra={"TMUX_PANE": "%1"})
        assert result.returncode == 0, result.stderr
        assert killed.read_text().splitlines() == ["$3", "$2"]
        killed.unlink()

        result = run(answer="delete\n", extra={"TEST_RECOVER": str(root / "gone")})
        assert result.returncode == 0, result.stderr
        assert killed.read_text().splitlines() == ["$3"]
        (root / "gone").rmdir()
        killed.unlink()

        result = run(answer="delete\n", extra={"TEST_CHANGED": "yes"})
        assert result.returncode == 0, result.stderr
        assert killed.read_text().splitlines() == ["$3"]
        killed.unlink()
        state.write_text(original)

        (config / "tmux-sessionizer.conf").write_text(
            f'TS_SEARCH_PATHS=("{root}:1")\nTS_EXTRA_SEARCH_PATHS=()\n'
        )
        assert "projects_gone" in run("--list").stdout
        (config / "tmux-sessionizer.conf").unlink()
        result = run("--list")
        assert result.returncode == 0, result.stderr
        assert "projects_exists" not in result.stdout
        assert "manual-missing" in result.stdout
        print("All cleanup checks passed; no real tmux sessions were touched.")


if __name__ == "__main__":
    main()
