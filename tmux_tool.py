import json
import os
import subprocess
import shutil
from tools.registry import registry


# ── UTILIDADES INTERNAS ──────────────────────────────────────────────────────

def _run(cmd: list) -> tuple[int, str, str]:
    """Ejecuta un comando tmux y devuelve (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _session_exists(session: str) -> bool:
    rc, _, _ = _run(["tmux", "has-session", "-t", session])
    return rc == 0


def _window_id(session: str, window: str) -> str:
    """Devuelve el target tmux en formato session:window."""
    return f"{session}:{window}"


# ── HANDLERS ─────────────────────────────────────────────────────────────────

def tmux_tool(
    action: str,
    session: str = None,
    window: str = None,
    cmd: str = None,
    lines: int = 50,
    **kw
) -> str:

    # ── list ──────────────────────────────────────────────────────────────────
    if action == "list":
        rc, out, err = _run([
            "tmux", "list-sessions",
            "-F", "#{session_name} | windows:#{session_windows} | created:#{session_created_string}"
        ])
        if rc != 0:
            return json.dumps({"sessions": [], "note": "No active tmux sessions"})

        sessions = []
        for line in out.splitlines():
            parts = line.split(" | ")
            sess_name = parts[0].strip()

            # listar ventanas de cada sesión
            rc2, wins, _ = _run([
                "tmux", "list-windows", "-t", sess_name,
                "-F", "#{window_index}:#{window_name} [#{window_activity_flag}]"
            ])
            windows = wins.splitlines() if rc2 == 0 else []
            sessions.append({
                "session": sess_name,
                "info": " | ".join(parts[1:]),
                "windows": windows
            })

        return json.dumps({"sessions": sessions, "count": len(sessions)}, ensure_ascii=False)

    # ── new ───────────────────────────────────────────────────────────────────
    if action == "new":
        if not session:
            return json.dumps({"error": "session name required", "ok": False})

        if _session_exists(session):
            # sesión ya existe — crear nueva ventana si se especifica
            if window:
                rc, _, err = _run(["tmux", "new-window", "-t", session, "-n", window])
                if rc != 0:
                    return json.dumps({"error": err, "ok": False})
                return json.dumps({"ok": True, "action": "window_created",
                                   "session": session, "window": window})
            return json.dumps({"ok": True, "action": "session_exists",
                               "session": session, "note": "Session already running"})

        # crear sesión nueva (detached)
        win_name = window or "main"
        rc, _, err = _run(["tmux", "new-session", "-d", "-s", session, "-n", win_name])
        if rc != 0:
            return json.dumps({"error": err, "ok": False})

        # si hay comando inicial, enviarlo
        if cmd:
            _run(["tmux", "send-keys", "-t", _window_id(session, win_name), cmd, "Enter"])

        return json.dumps({"ok": True, "action": "session_created",
                           "session": session, "window": win_name})

    # ── send ──────────────────────────────────────────────────────────────────
    if action == "send":
        if not session or not cmd:
            return json.dumps({"error": "session and cmd required", "ok": False})

        if not _session_exists(session):
            return json.dumps({"error": f"Session '{session}' does not exist. Create it first with action=new.", "ok": False})

        target = _window_id(session, window) if window else session
        rc, _, err = _run(["tmux", "send-keys", "-t", target, cmd, "Enter"])
        if rc != 0:
            return json.dumps({"error": err, "ok": False})

        return json.dumps({"ok": True, "action": "sent", "session": session,
                           "window": window, "cmd": cmd})

    # ── read ──────────────────────────────────────────────────────────────────
    if action == "read":
        if not session:
            return json.dumps({"error": "session required", "ok": False})

        if not _session_exists(session):
            return json.dumps({"error": f"Session '{session}' does not exist.", "ok": False})

        target = _window_id(session, window) if window else session
        rc, out, err = _run(["tmux", "capture-pane", "-t", target,
                              "-p", "-e",          # incluir colores escapados
                              f"-S -{lines}"])     # últimas N líneas

        if rc != 0:
            # intentar sin flag -e si falla
            rc, out, err = _run(["tmux", "capture-pane", "-t", target,
                                  "-p", f"-S -{lines}"])

        if rc != 0:
            return json.dumps({"error": err, "ok": False})

        # limpiar secuencias de escape ANSI
        import re
        clean = re.sub(r'\x1b\[[0-9;]*[mGKHF]', '', out)
        clean = re.sub(r'\x1b\[[0-9;]*[A-Z]', '', clean)

        return json.dumps({
            "ok": True,
            "session": session,
            "window": window,
            "output": clean,
            "lines": len(clean.splitlines())
        }, ensure_ascii=False)

    # ── send_raw (sin Enter — para enviar Ctrl+C, Ctrl+D, etc.) ─────────────
    if action == "send_raw":
        if not session or not cmd:
            return json.dumps({"error": "session and cmd required", "ok": False})

        if not _session_exists(session):
            return json.dumps({"error": f"Session '{session}' does not exist.", "ok": False})

        target = _window_id(session, window) if window else session
        # cmd puede ser "C-c", "C-d", "q", "Enter", etc.
        rc, _, err = _run(["tmux", "send-keys", "-t", target, cmd])
        if rc != 0:
            return json.dumps({"error": err, "ok": False})

        return json.dumps({"ok": True, "action": "raw_sent", "key": cmd})

    # ── rename ────────────────────────────────────────────────────────────────
    if action == "rename":
        if not session or not window:
            return json.dumps({"error": "session and window (new name) required", "ok": False})

        rc, _, err = _run(["tmux", "rename-window", "-t", session, window])
        if rc != 0:
            return json.dumps({"error": err, "ok": False})
        return json.dumps({"ok": True, "action": "renamed", "session": session, "window": window})

    # ── kill ──────────────────────────────────────────────────────────────────
    if action == "kill":
        if not session:
            return json.dumps({"error": "session required", "ok": False})

        if window:
            # matar solo la ventana
            rc, _, err = _run(["tmux", "kill-window", "-t", _window_id(session, window)])
            if rc != 0:
                return json.dumps({"error": err, "ok": False})
            return json.dumps({"ok": True, "action": "window_killed",
                               "session": session, "window": window})
        else:
            # matar sesión entera
            rc, _, err = _run(["tmux", "kill-session", "-t", session])
            if rc != 0:
                return json.dumps({"error": err, "ok": False})
            return json.dumps({"ok": True, "action": "session_killed", "session": session})

    # ── acción desconocida ────────────────────────────────────────────────────
    return json.dumps({
        "error": f"Unknown action: '{action}'",
        "valid_actions": ["list", "new", "send", "read", "send_raw", "rename", "kill"],
        "ok": False
    })


# ── SCHEMA ───────────────────────────────────────────────────────────────────

TMUX_SCHEMA = {
        "name": "tmux",
        "description": (
            "Manage persistent terminal sessions via tmux. Sessions survive Hermes "
            "restarts — use this for long-running processes, background tasks, "
            "monitoring, or any work that needs to persist between conversations. "
            "Think of it as your own workspace: create named sessions for different "
            "ongoing tasks (pentest, monitoring, server), send commands to them, "
            "and read their output at any time. "
            "Actions: "
            "'list' — show all active sessions and windows. "
            "'new' — create a session (and optionally a window inside it). "
            "'send' — send a command to a session/window (appends Enter). "
            "'read' — capture current terminal output from a session/window. "
            "'send_raw' — send raw keys without Enter (use for Ctrl+C='C-c', Ctrl+D='C-d', etc). "
            "'kill' — kill a session or a specific window. "
            "Always 'list' first to see what sessions already exist. "
            "Use descriptive session names: 'pentest', 'monitoring', 'server', 'recon'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "new", "send", "read", "send_raw", "rename", "kill"],
                    "description": "Action to perform"
                },
                "session": {
                    "type": "string",
                    "description": "Session name (e.g. 'pentest', 'monitoring', 'server')"
                },
                "window": {
                    "type": "string",
                    "description": "Window name within the session. Optional for most actions."
                },
                "cmd": {
                    "type": "string",
                    "description": "Command to send (for action=send/send_raw) or initial command (for action=new)"
                },
                "lines": {
                    "type": "integer",
                    "description": "Number of lines to capture from terminal output (action=read). Default: 50",
                    "default": 50
                },
            },
            "required": ["action"],
        },

}


# ── CHECK Y REGISTRO ─────────────────────────────────────────────────────────

def _check_tmux() -> bool:
    return shutil.which("tmux") is not None


registry.register(
    name="tmux",
    toolset="tmux",
    schema=TMUX_SCHEMA,
    handler=lambda args, **kw: tmux_tool(**args, **kw),
    check_fn=_check_tmux,
    requires_env=[],
)
