# tmux-tool — Persistent Terminal Sessions for Hermes Agent

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) tool that gives the agent full control over persistent tmux sessions — allowing it to run long-lived background processes, manage multiple parallel workspaces, and resume work across Hermes restarts.

> **The key difference from Hermes' built-in `process` tool:** tmux sessions survive Hermes restarts. Processes keep running even when Hermes is stopped, restarted, or the conversation ends.

---

## What it does

The agent can create named tmux sessions for different ongoing tasks — `pentest`, `monitoring`, `server`, `recon` — send commands to them, read their current output at any time, and kill them when done. Sessions persist independently of Hermes itself.

Think of it as giving the agent the same workflow a human uses with tmux: multiple named workspaces, each with their own processes, all running in the background while you do other things.

---

## Features

- **Persistent sessions** — survive Hermes restarts, conversation resets, and terminal disconnections
- **Multiple windows per session** — each session can have named windows for different tasks
- **Live output capture** — read the current terminal state of any session/window at any time
- **Raw key support** — send `Ctrl+C`, `Ctrl+D`, `Enter`, or any key sequence
- **Graceful degradation** — if tmux is not installed, the tool silently skips registration

---

## Installation

### 1. Install tmux

```bash
# Ubuntu/Debian
sudo apt install tmux

# Fedora
sudo dnf install tmux

# macOS
brew install tmux
```

### 2. Copy the tool file

```bash
cp tmux_tool.py ~/.hermes/hermes-agent/tools/tmux_tool.py
```

### 3. Register in `model_tools.py`

Open `~/.hermes/hermes-agent/model_tools.py` and add one line inside `_discover_tools()`:

```python
def _discover_tools():
    _modules = [
        # ... existing tools ...
        "tools.tmux_tool",   # <- add this
    ]
```

### 4. Add to `toolsets.py`

Open `~/.hermes/hermes-agent/toolsets.py` and add the toolset:

```python
_TOOLSET_MAP = {
    # ... existing toolsets ...
    "tmux": ["tmux"],
}
```

### 5. Enable in `config.yaml`

```yaml
platform_toolsets:
  cli:
  - terminal
  - file
  - web
  - tmux       # <- add this
  # ... rest of toolsets ...
```

### 6. Restart Hermes

```bash
hermes
```

---

## Actions

| Action | Description | Required params |
|--------|-------------|-----------------|
| `list` | List all active sessions and their windows | — |
| `new` | Create a new session (and optionally a window) | `session` |
| `send` | Send a command to a session/window (appends Enter) | `session`, `cmd` |
| `read` | Capture current terminal output | `session` |
| `send_raw` | Send raw keys without Enter (Ctrl+C, Ctrl+D, etc.) | `session`, `cmd` |
| `rename` | Rename the current window | `session`, `window` |
| `kill` | Kill a session or a specific window | `session` |

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action to perform (required) |
| `session` | string | Session name — use descriptive names: `pentest`, `monitoring`, `server` |
| `window` | string | Window name within the session (optional for most actions) |
| `cmd` | string | Command to send, or initial command when creating a session |
| `lines` | integer | Number of lines to capture with `read` (default: 50) |

---

## Usage examples

### Basic session management

```
# List active sessions
tmux(action="list")

# Create a session
tmux(action="new", session="pentest")

# Create a session with an initial command
tmux(action="new", session="monitoring", cmd="htop")

# Create a second window inside an existing session
tmux(action="new", session="pentest", window="exploit")

# Send a command
tmux(action="send", session="pentest", cmd="nmap -sV 192.168.1.0/24")

# Read output
tmux(action="read", session="pentest", lines=100)

# Send Ctrl+C to stop a process
tmux(action="send_raw", session="pentest", cmd="C-c")

# Kill a specific window
tmux(action="kill", session="pentest", window="recon")

# Kill an entire session
tmux(action="kill", session="pentest")
```

### Pentest workflow example

```
You: Set up a pentest workspace for 192.168.1.31

Agent:
- Creates session "recon" → runs nmap full scan in background
- Creates session "monitoring" → runs watch -n5 'netstat -an' in window 0, vmstat 2 in window 1
- Creates session "exploit" → ready for manual exploitation
- Creates session "loot" → tail -f any logs being written

Later:
- tmux(action="read", session="recon", lines=200)  → checks scan progress
- tmux(action="list")  → sees all 4 sessions still running
```

### Monitoring example

```
You: Monitor the system while we work

Agent:
- tmux(action="new", session="monitoring", window="htop",    cmd="htop")
- tmux(action="new", session="monitoring", window="disk",    cmd="watch -n5 'df -h'")
- tmux(action="new", session="monitoring", window="network", cmd="watch -n2 'ss -tulnp'")
```

---

## How it differs from the built-in `process` tool

| Feature | `process` tool | `tmux` tool |
|---------|----------------|-------------|
| Survives Hermes restart | ❌ | ✅ |
| Multiple named workspaces | ❌ | ✅ |
| Multiple windows per workspace | ❌ | ✅ |
| Read output at any time | ✅ (polling) | ✅ (capture-pane) |
| Send interactive input | ✅ | ✅ |
| Human can attach and watch | ❌ | ✅ (`tmux attach -t session`) |
| Processes survive conversation reset | ❌ | ✅ |

---

## Attach to a session yourself

While the agent has sessions running, you can attach to any of them from your own terminal:

```bash
# List sessions
tmux ls

# Attach to a session
tmux attach -t pentest

# Detach without killing (Ctrl+B then D)
```

This lets you watch exactly what the agent is doing in real time, or take manual control of a session.

---

## Requirements

- Python 3.8+
- tmux installed on the system running the terminal backend
- [Hermes Agent](https://github.com/NousResearch/hermes-agent)

---

## License

MIT

---

## Credits

Built for [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [Nous Research](https://nousresearch.com).  
Inspired by how humans actually use tmux.

---

---

# tmux-tool — Sesiones de Terminal Persistentes para Hermes Agent

Una herramienta para [Hermes Agent](https://github.com/NousResearch/hermes-agent) que da al agente control total sobre sesiones tmux persistentes — permitiéndole ejecutar procesos de larga duración en segundo plano, gestionar múltiples espacios de trabajo en paralelo, y retomar el trabajo entre reinicios de Hermes.

> **La diferencia clave con el tool `process` integrado de Hermes:** las sesiones tmux sobreviven a los reinicios de Hermes. Los procesos siguen corriendo aunque Hermes se detenga, se reinicie, o la conversación termine.

---

## Qué hace

El agente puede crear sesiones tmux con nombres descriptivos para distintas tareas en curso — `pentest`, `monitoring`, `servidor`, `recon` — enviarles comandos, leer su output actual en cualquier momento, y matarlas cuando ya no las necesite. Las sesiones son completamente independientes de Hermes.

Es darle al agente el mismo flujo de trabajo que usa un humano con tmux: múltiples espacios de trabajo con nombre, cada uno con sus propios procesos, todos corriendo en segundo plano mientras se hace otra cosa.

---

## Características

- **Sesiones persistentes** — sobreviven reinicios de Hermes, resets de conversación y desconexiones de terminal
- **Múltiples ventanas por sesión** — cada sesión puede tener ventanas con nombre para distintas tareas
- **Captura de output en vivo** — lee el estado actual del terminal de cualquier sesión/ventana en cualquier momento
- **Soporte de teclas especiales** — envía `Ctrl+C`, `Ctrl+D`, `Enter` o cualquier secuencia de teclas
- **Degradación silenciosa** — si tmux no está instalado, el tool no se registra sin errores

---

## Instalación

### 1. Instalar tmux

```bash
# Ubuntu/Debian
sudo apt install tmux

# Fedora
sudo dnf install tmux

# macOS
brew install tmux
```

### 2. Copiar el fichero del tool

```bash
cp tmux_tool.py ~/.hermes/hermes-agent/tools/tmux_tool.py
```

### 3. Registrar en `model_tools.py`

Abre `~/.hermes/hermes-agent/model_tools.py` y añade una línea dentro de `_discover_tools()`:

```python
def _discover_tools():
    _modules = [
        # ... tools existentes ...
        "tools.tmux_tool",   # <- añadir esto
    ]
```

### 4. Añadir a `toolsets.py`

Abre `~/.hermes/hermes-agent/toolsets.py` y añade el toolset:

```python
_TOOLSET_MAP = {
    # ... toolsets existentes ...
    "tmux": ["tmux"],
}
```

### 5. Habilitar en `config.yaml`

```yaml
platform_toolsets:
  cli:
  - terminal
  - file
  - web
  - tmux       # <- añadir esto
  # ... resto de toolsets ...
```

### 6. Reiniciar Hermes

```bash
hermes
```

---

## Acciones

| Acción | Descripción | Parámetros requeridos |
|--------|-------------|----------------------|
| `list` | Listar todas las sesiones activas y sus ventanas | — |
| `new` | Crear una nueva sesión (y opcionalmente una ventana) | `session` |
| `send` | Enviar un comando a una sesión/ventana (añade Enter) | `session`, `cmd` |
| `read` | Capturar el output actual del terminal | `session` |
| `send_raw` | Enviar teclas sin Enter (Ctrl+C, Ctrl+D, etc.) | `session`, `cmd` |
| `rename` | Renombrar la ventana actual | `session`, `window` |
| `kill` | Matar una sesión o una ventana específica | `session` |

### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `action` | string | Acción a realizar (requerido) |
| `session` | string | Nombre de sesión — usar nombres descriptivos: `pentest`, `monitoring`, `servidor` |
| `window` | string | Nombre de ventana dentro de la sesión (opcional para la mayoría de acciones) |
| `cmd` | string | Comando a enviar, o comando inicial al crear una sesión |
| `lines` | integer | Número de líneas a capturar con `read` (por defecto: 50) |

---

## Ejemplos de uso

### Gestión básica de sesiones

```
# Listar sesiones activas
tmux(action="list")

# Crear una sesión
tmux(action="new", session="pentest")

# Crear una sesión con comando inicial
tmux(action="new", session="monitoring", cmd="htop")

# Crear una segunda ventana dentro de una sesión existente
tmux(action="new", session="pentest", window="exploit")

# Enviar un comando
tmux(action="send", session="pentest", cmd="nmap -sV 192.168.1.0/24")

# Leer output
tmux(action="read", session="pentest", lines=100)

# Enviar Ctrl+C para parar un proceso
tmux(action="send_raw", session="pentest", cmd="C-c")

# Matar una ventana específica
tmux(action="kill", session="pentest", window="recon")

# Matar una sesión entera
tmux(action="kill", session="pentest")
```

### Ejemplo de flujo de pentest

```
Tú: Prepara un espacio de trabajo de pentest para 192.168.1.31

Agente:
- Crea sesión "recon"      → lanza nmap en background
- Crea sesión "monitoring" → htop en ventana 0, vmstat 2 en ventana 1
- Crea sesión "exploit"    → lista para explotación manual
- Crea sesión "loot"       → tail -f de logs relevantes

Más tarde:
- tmux(action="read", session="recon", lines=200)  → comprueba progreso del scan
- tmux(action="list")  → ve las 4 sesiones todavía corriendo
```

### Ejemplo de monitoring

```
Tú: Monitoriza el sistema mientras trabajamos

Agente:
- tmux(action="new", session="monitoring", window="htop",    cmd="htop")
- tmux(action="new", session="monitoring", window="disco",   cmd="watch -n5 'df -h'")
- tmux(action="new", session="monitoring", window="red",     cmd="watch -n2 'ss -tulnp'")
```

---

## Diferencias con el tool `process` integrado

| Característica | Tool `process` | Tool `tmux` |
|----------------|----------------|-------------|
| Sobrevive reinicio de Hermes | ❌ | ✅ |
| Múltiples espacios de trabajo con nombre | ❌ | ✅ |
| Múltiples ventanas por espacio de trabajo | ❌ | ✅ |
| Leer output en cualquier momento | ✅ (polling) | ✅ (capture-pane) |
| Enviar input interactivo | ✅ | ✅ |
| El humano puede conectarse y ver | ❌ | ✅ (`tmux attach -t sesión`) |
| Procesos sobreviven reset de conversación | ❌ | ✅ |

---

## Conectarte tú a una sesión

Mientras el agente tiene sesiones corriendo, puedes conectarte a cualquiera desde tu propio terminal:

```bash
# Listar sesiones
tmux ls

# Conectarse a una sesión
tmux attach -t pentest

# Desconectarse sin matar (Ctrl+B luego D)
```

Esto te permite ver exactamente lo que está haciendo el agente en tiempo real, o tomar control manual de una sesión.

---

## Requisitos

- Python 3.8+
- tmux instalado en el sistema donde corre el backend de terminal
- [Hermes Agent](https://github.com/NousResearch/hermes-agent)

---

## Licencia

MIT

---

## Créditos

Construido para [Hermes Agent](https://github.com/NousResearch/hermes-agent) por [Nous Research](https://nousresearch.com).  
Inspirado en cómo los humanos usamos tmux de verdad.
