# tmux-config

tmux config plus a small `tmux-sessionizer` toolkit. Rose Pine theme to match
[neovim-config](https://github.com/blakekrpec/neovim-config) and the workstation
starship prompt.

## Setup

Setup is handled by the [**workstation**](https://github.com/blakekrpec/workstation)
repo, not by this one. Its `tmux` role installs `tmux` and `fzf`, clones this
repo to `~/.config/tmux`, clones the plugins at pinned commits, links `bin/*`
into `~/.local/bin`, and seeds the sessionizer config:

```bash
~/workstation/bootstrap.sh --only base,tmux
```

There is no install script here on purpose — same split as neovim-config:
this repo is config, workstation is machine setup.

tmux >= 3.1 reads `~/.config/tmux/tmux.conf` natively; no `~/.tmux.conf` is
needed. Requires tmux >= 3.3 (`allow-passthrough`). Ubuntu 24.04 ships 3.4.

## Layout

| Path | Purpose |
|---|---|
| `tmux.conf` | Main config. Plugins are loaded directly from `plugins/` (gitignored), no TPM |
| `bin/tmux-sessionizer` | fzf project picker; creates/switches to a session per directory |
| `bin/tmux-quit-session` | Kill the current session, switching to the last one (or the picker) first |
| `bin/tmux-sessionizer-cleanup` | Interactive: pick and kill sessions whose project dir is gone |
| `bin/tmux-missing-dir-cleanup` | Non-interactive: kill detached sessions whose dir is gone |
| `bin/tmux-nvim-cleanup` | Close nvim in detached sessions idle longer than `--timeout` minutes |
| `tmux-sessionizer.conf.example` | Seed for `~/.config/tmux-sessionizer/tmux-sessionizer.conf` (per machine) |
| `tests/` | `python3 tests/test_tmux_sessionizer_cleanup.py` (uses a fake tmux) |

The cleanup scripts all support `--dry-run` (or `--list`) and only act on
detached sessions. None are scheduled; run them by hand.

## Plugins

| Plugin | Pinned in |
|---|---|
| [tmux-resurrect](https://github.com/tmux-plugins/tmux-resurrect) | `tmux_plugins` in workstation `group_vars/all.yml` |
| [tmux-continuum](https://github.com/tmux-plugins/tmux-continuum) | same — autosaves every 15 min, restores on server start |

To bump: change the commit in workstation, then `./bootstrap.sh --only tmux`.
To add one: add an entry there and an `if-shell … run-shell` line at the bottom
of `tmux.conf`.

## Key bindings

Prefix is `Ctrl+a`.

| Keys | Action |
|---|---|
| `Alt+h/j/k/l` | Move between panes (no prefix) |
| `Alt+Shift+h/j/k/l` | Resize pane by 5 (no prefix) |
| `prefix \|` / `prefix -` | Split horizontal / vertical |
| `prefix t` | New window |
| `prefix c` | Copy mode (vi keys; `v` select, `y` copy) |
| `prefix f` | Sessionizer popup |
| `prefix p` | Last session |
| `prefix q` | Quit session (confirm), switching elsewhere first |
| `prefix K` | Kill session (confirm) |
| `prefix r` | Reload config |

Pane navigation is intentionally **not** shared with Neovim: `Ctrl+h/j/k/l`
moves between nvim splits, `Alt+h/j/k/l` moves between tmux panes. No
vim-tmux-navigator on either side, so neither config depends on the other.
(Ctrl+Shift was the first choice, but gnome-terminal/VTE sends the same byte
for `Ctrl+H` and `Ctrl+Shift+H`, so tmux can't distinguish them.)

## Sessionizer

`prefix f` lists the immediate children of every `TS_SEARCH_PATHS` entry, plus
running sessions. Picking a directory creates a session named
`<parent>_<dir>` with a three-pane layout. If the directory (or `~`) has a
`.tmux-sessionizer` file, it is sourced into the new session.

Per-machine config lives at `~/.config/tmux-sessionizer/tmux-sessionizer.conf`;
see the comment header in `bin/tmux-sessionizer` for every option.

## Credits

Started from a friend's (Cody's) tmux setup; `tmux-sessionizer` descends from
ThePrimeagen's script of the same name.
