# Android Claude Controller — Getting Started Guide

> Control any Android device through natural language, powered by Claude or DeepSeek AI.
> Works on Termux (Android), Kali Linux, or any system with ADB.

---

## Table of Contents

1. [What is ACC?](#what-is-acc)
2. [How It Works](#how-it-works)
3. [Requirements](#requirements)
4. [Installation](#installation)
   - [On Termux (Android)](#on-termux-android)
   - [On Linux Desktop](#on-linux-desktop)
5. [API Key Setup](#api-key-setup)
   - [Anthropic (Claude)](#anthropic-claude)
   - [DeepSeek](#deepseek)
   - [Provider Auto-Detection](#provider-auto-detection)
6. [Connecting Your Android Device](#connecting-your-android-device)
   - [USB Debugging](#usb-debugging)
   - [Wireless Debugging (TCP/IP)](#wireless-debugging-tcpip)
7. [Quick Start](#quick-start)
8. [CLI Reference](#cli-reference)
   - [`acc goal` — Single-shot execution](#acc-goal)
   - [`acc chat` — Interactive session](#acc-chat)
   - [`acc device` — Device management](#acc-device)
   - [`acc screenshot` — Quick capture](#acc-screenshot)
   - [`acc ui-dump` — UI inspection](#acc-ui-dump)
   - [`acc config` — Configuration](#acc-config)
   - [`acc web` — Web server](#acc-web)
9. [Django Web Interface](#django-web-interface)
10. [Configuration Reference](#configuration-reference)
11. [How the Agent Works](#how-the-agent-works)
    - [Vision Modes](#vision-modes)
    - [The Observe-Plan-Execute-Verify Loop](#the-observe-plan-execute-verify-loop)
    - [Safety System](#safety-system)
12. [All 19 Tools (Reference)](#all-19-tools-reference)
13. [Project Architecture](#project-architecture)
14. [Troubleshooting](#troubleshooting)
15. [Termux-Specific Notes](#termux-specific-notes)

---

## What is ACC?

**Android Claude Controller (ACC)** lets you control your Android phone or tablet by typing natural language instructions. You describe what you want—"open Chrome and search for weather" or "take a screenshot of my home screen"—and an AI agent observes the screen, decides what actions to take, and executes them through ADB.

You can use either **Anthropic Claude** or **DeepSeek** as the AI backend. Claude offers stronger reasoning and vision capabilities; DeepSeek is significantly cheaper.

### What You Can Do

- Open apps, navigate UIs, fill forms, type text
- Take screenshots and have the AI analyze them
- Manage files, install/uninstall apps
- Execute shell commands on the device
- Read/write system settings
- Automate repetitive tasks (e.g., "scroll through my gallery and tell me which photos are blurry")
- Test Android apps through natural language

---

## How It Works

```
You: "open the calculator and type 2+2"
  │
  ▼
┌─────────────────────────────────────────┐
│  Agent Loop (observe → plan → execute)  │
│                                          │
│  1. OBSERVE: Take UI dump/screenshot    │
│  2. PLAN:    Send to Claude/DeepSeek    │
│  3. EXECUTE: Run ADB commands           │
│  4. VERIFY:  Check if UI changed        │
│                                          │
│  Repeat until goal achieved or max steps │
└─────────────────────────────────────────┘
  │
  ▼
ADB (Android Debug Bridge) → Your Phone
```

The AI never sees raw ADB output directly. Instead, it sees:
- **UI hierarchy dumps** (structured text of all visible elements with coordinates)
- **Screenshots** (JPEG images for visual understanding)

It calls **19 predefined tools** (functions) that map to safe ADB operations. The system validates every action before executing it.

---

## Requirements

### Hardware
- An Android device (phone/tablet) with **USB Debugging enabled**
- A computer or Android device running Termux

### Software
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.11+ | 3.12+ |
| ADB | Platform tools 33+ | Platform tools 34+ |
| Android | 7.0+ (API 24) | 10+ (API 29) |

### API Key (one of)
- **Anthropic API key** (claude.ai) for Claude
- **DeepSeek API key** (platform.deepseek.com) for DeepSeek

---

## Installation

### On Termux (Android)

```bash
# 1. Install Termux from F-Droid (NOT Google Play — Play Store version is outdated)
#    https://f-droid.org/packages/com.termux/

# 2. Update packages
pkg update && pkg upgrade

# 3. Install prerequisites
pkg install python python-pip android-tools git

# 4. Grant Termux storage access
termux-setup-storage

# 5. Clone and install ACC
cd ~
git clone https://github.com/tai/android-claude-controller
cd android-claude-controller

# Install with core dependencies
pip install -e .

# Or with web UI dependencies
pip install -e ".[web]"

# 6. Set your API key
echo 'export ANTHROPIC_API_KEY=sk-ant-your-key' >> ~/.bashrc
# OR for DeepSeek:
echo 'export DEEPSEEK_API_KEY=sk-your-deepseek-key' >> ~/.bashrc
source ~/.bashrc

# 7. Verify
acc --version
acc device list
```

### On Linux Desktop

```bash
# 1. Install ADB
# Debian/Ubuntu/Kali:
sudo apt install android-sdk-platform-tools adb

# Arch:
sudo pacman -S android-tools

# 2. Clone and install
git clone https://github.com/tai/android-claude-controller
cd android-claude-controller
pip install -e ".[dev,web]"

# 3. Create .env file
cp .env.example .env
# Edit .env with your API key
nano .env

# 4. Verify
acc --version
```

---

## API Key Setup

### Anthropic (Claude)

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account and generate an API key
3. Set the environment variable:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
   ```
4. Add to `~/.bashrc` or `~/.zshrc` for persistence

**Recommended model:** `claude-sonnet-4-5-20250929` (best speed/cost/capability balance for device control)

### DeepSeek

1. Go to [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)
2. Create an account and generate an API key
3. Set the environment variable:
   ```bash
   export DEEPSEEK_API_KEY=sk-your-deepseek-key-here
   ```

**Default model:** `deepseek-chat`

**Cost comparison:**
| Provider | Input (per 1M tokens) | Output (per 1M tokens) | Screenshot cost |
|----------|----------------------|------------------------|-----------------|
| Claude Sonnet 4.5 | ~$3.00 | ~$15.00 | ~$0.003/image |
| DeepSeek Chat | ~$0.27 | ~$1.10 | ~$0.0003/image |

DeepSeek is roughly **10x cheaper** but Claude has stronger vision understanding.

### Provider Auto-Detection

ACC automatically detects which provider to use:

1. If `ACC_PROVIDER` is set to `"anthropic"` or `"deepseek"`, that provider is used
2. If `ACC_PROVIDER` is set to `"auto"` (default), ACC checks:
   - Has `ANTHROPIC_API_KEY`? → Use Anthropic
   - Has `DEEPSEEK_API_KEY`? → Use DeepSeek
   - Neither? → Error: set an API key

```bash
# Force a specific provider regardless of which keys are set
export ACC_PROVIDER=deepseek
```

---

## Connecting Your Android Device

### USB Debugging

1. **Enable Developer Options:**
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times
   - Enter your PIN when prompted

2. **Enable USB Debugging:**
   - Settings → Developer Options
   - Toggle ON "USB Debugging"
   - Confirm the dialog

3. **Connect via USB:**
   ```bash
   # Plug in your phone, then:
   adb devices
   # Should show:  RFCN305XXXX   device
   ```

4. **Trust the computer:**
   - A dialog will appear on your phone: "Allow USB debugging?"
   - Check "Always allow from this computer"
   - Tap "Allow"

### Wireless Debugging (TCP/IP)

```bash
# 1. Connect via USB first, then:
adb tcpip 5555

# 2. Find your phone's IP address
#    Settings → About Phone → Status → IP address
#    Or: adb shell ip addr show wlan0

# 3. Connect wirelessly
adb connect 192.168.1.100:5555

# 4. Unplug USB — stays connected
adb devices
# Should show:  192.168.1.100:5555   device
```

**For Android 11+ with Wireless Debugging tile:**
- Settings → Developer Options → Wireless Debugging
- Tap "Pair device with pairing code"
- Use `adb pair <ip>:<pairing-port> <code>`
- Then `adb connect <ip>:<connect-port>`

---

## Quick Start

```bash
# 1. Check your device is connected
acc device list

# 2. Run your first goal
acc goal "open settings and show me the wifi page"

# 3. Start an interactive chat session
acc chat

# 4. Take a quick screenshot
acc screenshot -o my_screen.png

# 5. Inspect the current UI
acc ui-dump
```

### Example Session

```
$ acc goal "open Chrome and search for weather"

╭──── Android Claude Controller ───────────────────────────────╮
│ Device: Pixel 7 (Android 14)  Mode: auto  Step: 1/20         │
╰──────────────────────────────────────────────────────────────╯

  🔍 Observing device...
     Mode: text (UI dump) │ Foreground: com.android.launcher

  🧠 Claude: I can see the home screen. Let me launch Chrome.
     ▸ app_launch(package="com.android.chrome")
  ✅ Launched successfully.

  🔍 Observing... Chrome is now in foreground.
  🧠 Claude: Chrome is open. I'll tap the address bar.
     ▸ ui_dump_hierarchy()
  ✅ Found address bar at (540, 120)
     ▸ input_tap(x=540, y=120)
  ✅ Tapped.

  🔍 Observing... Address bar is focused.
  🧠 Claude: URL bar focused. Typing search.
     ▸ input_type(text="weather")
  ✅ Text typed.
     ▸ input_keyevent(keycode="ENTER")
  ✅ Enter pressed.

  🧠 Claude: ▸ task_complete(success=true)
  🎉 Goal achieved in 4 steps!
     Chrome is showing search results for "weather".
```

---

## CLI Reference

### `acc goal`

Execute a single goal against a connected Android device.

```bash
acc goal "your goal description" [OPTIONS]

# Options:
#   -d, --device SERIAL    Target device serial (required if multiple connected)
#   -m, --mode MODE        Observation mode: auto, vision, text (default: auto)
#   -s, --max-steps N      Max agent steps before giving up (default: 20)
#   --safe / --unsafe      Enable/disable safety confirmations
#   -v, --verbose          Show debug logging

# Examples:
acc goal "take a screenshot and save it"
acc goal "open Instagram and go to my profile" -m vision
acc goal "uninstall the app called TestApp" --safe
acc goal "check my battery and tell me the level" -m text -s 5
```

### `acc chat`

Start an interactive chat session. Type goals continuously — the agent remembers context across turns.

```bash
acc chat [OPTIONS]

# Options:
#   -d, --device SERIAL    Target device serial
#   -m, --mode MODE        Observation mode (default: auto)
#   --resume SESSION_ID    Resume a previous session

# Chat commands (type these during a chat session):
#   /help          Show help
#   /screenshot    Toggle to vision mode
#   /text          Switch to text-only mode
#   /auto          Switch to auto (hybrid) mode
#   /device        Show device info
#   /sessions      List saved sessions
#   /save          Save current session
#   /exit          Exit chat
```

### `acc device`

Manage connected Android devices.

```bash
acc device list              # Show all connected devices
acc device info [SERIAL]     # Detailed info about a device
acc device scan              # Scan network for wireless ADB devices
```

### `acc screenshot`

Quick screenshot capture.

```bash
acc screenshot -o screenshot.png
acc screenshot -d RFCN305XXXX -o ~/Pictures/phone.png
```

### `acc ui-dump`

Inspect the current UI hierarchy (text representation of all visible elements).

```bash
acc ui-dump                           # Print compact UI dump
acc ui-dump -f "Settings"             # Filter elements containing "Settings"
acc ui-dump -o full_hierarchy.xml     # Save full XML to file
```

### `acc config`

View and change configuration.

```bash
acc config show               # Show all current settings and their sources
acc config set max_steps 30   # Change a setting
acc config init               # Interactive first-time setup wizard
acc config path               # Show config file location
```

### `acc web`

Run the Django web interface.

```bash
acc web serve                 # Start at http://127.0.0.1:8000
acc web serve -p 9000         # On a different port
acc web migrate               # Run database migrations
```

---

## Django Web Interface

The web UI provides a browser-based interface for controlling your device.

### Starting the Web Server

```bash
# Install web dependencies
pip install -e ".[web]"

# Run migrations (first time only)
acc web migrate

# Create an admin user (optional)
python web/manage.py createsuperuser

# Start the server
acc web serve

# Open http://127.0.0.1:8000
```

### Web Features

- **Dashboard:** See connected devices and active sessions at a glance
- **Device Management:** View device details and session history per device
- **Session Chat:** Chat with the AI agent in your browser
- **Live Polling:** Messages appear automatically (1.5s polling interval)
- **Safety Approvals:** Dangerous actions trigger confirmation dialogs in the UI
- **Admin Panel:** Full Django admin at `/admin/` for managing models

### The Chat Interface

1. Create a new session — select device and mode
2. Type your goal in the chat input (e.g., "take a screenshot of the home screen")
3. Watch as the agent observes, plans, and executes step by step
4. If a dangerous action is requested, an approval card appears — click Approve or Deny
5. The session persists — come back later to review or resume

---

## Configuration Reference

All settings can be set via:
1. **Environment variables** (highest priority) — `ACC_SETTING_NAME`
2. **`.env` file** in the project directory
3. **`~/.config/acc/config.toml`** — written by `acc config set`
4. **Defaults** (built-in)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ANTHROPIC_API_KEY` | string | — | Anthropic API key (env only) |
| `DEEPSEEK_API_KEY` | string | — | DeepSeek API key (env only) |
| `ACC_PROVIDER` | string | `auto` | Provider: `anthropic`, `deepseek`, `auto` |
| `ACC_MODEL` | string | varies | Override the default model |
| `ACC_MAX_STEPS` | int | `20` | Max steps per goal before giving up |
| `ACC_DEFAULT_MODE` | string | `auto` | Observation mode: `auto`, `vision`, `text` |
| `ACC_SAFE_MODE` | bool | `true` | Require confirmation for dangerous actions |
| `ACC_SCREENSHOT_QUALITY` | int | `70` | JPEG quality (1-100) for screenshots sent to AI |
| `ACC_MAX_SCREENSHOT_DIMENSION` | int | `1280` | Max width/height of screenshots (pixels) |
| `ACC_TOOL_TIMEOUT_SECONDS` | int | `15` | Max time for a single tool execution |
| `ACC_SHELL_TIMEOUT_SECONDS` | int | `10` | Max time for shell commands |
| `ACC_MAX_UI_ELEMENTS` | int | `80` | Max UI elements in text dumps |
| `ACC_DEBUG` | bool | `false` | Enable Django debug mode |
| `ACC_SECRET_KEY` | string | — | Django secret key (web UI only) |
| `ACC_HOSTS` | string | `localhost,127.0.0.1` | Allowed Django hosts |

### Example `.env` File

```bash
# Use DeepSeek for lower cost
ACC_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key

# Conservative settings for battery saving on Termux
ACC_MAX_STEPS=10
ACC_DEFAULT_MODE=text
ACC_SCREENSHOT_QUALITY=50
```

---

## How the Agent Works

### Vision Modes

The agent has three observation modes:

| Mode | What the AI Sees | Best For | Token Cost |
|------|-----------------|----------|------------|
| **text** | UI hierarchy XML (element names, text, coordinates) | Settings, forms, lists, text-heavy apps | Low (~200 tokens) |
| **vision** | Screenshot (JPEG image) | Images, maps, games, visual content | High (~2000 tokens) |
| **auto** | Starts with text, escalates to vision | General use — best of both | Adaptive |

**In auto mode**, the agent:
1. Begins with cheap text-based UI dumps
2. Switches to screenshots if 3+ consecutive actions produce no UI change
3. Also switches to vision when screenshots are explicitly needed

### The Observe-Plan-Execute-Verify Loop

```
┌──────────────────────────────────────────────────┐
│                   AGENT LOOP                      │
│                                                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │ OBSERVE  │───▶│   PLAN   │───▶│ EXECUTE  │   │
│  │          │    │          │    │          │   │
│  │ Screenshot   │ AI model │    │ ADB tool │   │
│  │ or UI dump   │ decides  │    │ call     │   │
│  └──────────┘    └──────────┘    └──────────┘   │
│        ▲                              │          │
│        │         ┌──────────┐         │          │
│        └─────────│ VERIFY   │◀────────┘          │
│                  │          │                     │
│                  │ Check if │                     │
│                  │ UI changed                     │
│                  └──────────┘                     │
│                                                   │
│  Loop until: task_complete called OR max steps    │
└──────────────────────────────────────────────────┘
```

### Safety System

Every tool call is classified into one of four risk levels:

| Level | Examples | Behavior |
|-------|----------|----------|
| **SAFE** | Screenshots, UI dumps, tapping, typing | Executed immediately |
| **LOW** | Launching apps, writing files | Confirmed in safe mode |
| **MEDIUM** | Shell commands, modifying settings | Always confirmed |
| **HIGH** | Uninstalling apps, clearing data, dangerous shell | Always confirmed with warning |

Dangerous shell patterns detected automatically:
- `rm -rf` (recursive delete)
- `dd if=` (raw disk operations)
- `mkfs` (filesystem formatting)
- `reboot` (device restart)
- Writing to `/system/`, `/vendor/`, `/data/data/`

**Safe mode** (`--safe` or `ACC_SAFE_MODE=true`) enables confirmation prompts for all LOW+ risk actions.
**Unsafe mode** (`--unsafe` or `ACC_SAFE_MODE=false`) skips all confirmations — use with care.

---

## All 19 Tools (Reference)

These are the functions the AI can call. Each maps to a concrete ADB operation.

### Observation Tools (3)

| Tool | Description | Parameters |
|------|-------------|------------|
| `screen_screenshot` | Take a JPEG screenshot; returns base64 image | — |
| `ui_dump_hierarchy` | Dump current UI as structured text with coordinates | `max_elements` (int, optional) |
| `app_current` | Get foreground app's package + activity name | — |

### Input Tools (6)

| Tool | Description | Parameters |
|------|-------------|------------|
| `input_tap` | Tap at coordinates | `x`, `y` (int, pixels from top-left) |
| `input_long_press` | Long press at coordinates | `x`, `y` (int), `duration_ms` (int, optional) |
| `input_swipe` | Swipe gesture | `x1`, `y1`, `x2`, `y2` (int), `duration_ms` (int, optional) |
| `input_type` | Type text into focused field | `text` (string) |
| `input_keyevent` | Press hardware/system key | `keycode` (string: HOME, BACK, ENTER, etc.) |
| `wait` | Pause for UI to settle | `seconds` (float, optional, default 1.0) |

### App Management Tools (3)

| Tool | Description | Parameters |
|------|-------------|------------|
| `app_list` | List installed packages | `filter` (string, optional), `include_system` (bool) |
| `app_launch` | Launch an app by package name | `package` (string), `activity` (string, optional) |
| `app_control` | Force stop, clear data, or uninstall | `action` (force_stop/clear_data/uninstall), `package` (string) |

### System Tools (6)

| Tool | Description | Parameters |
|------|-------------|------------|
| `shell_exec` | Execute arbitrary shell command | `command` (string), `timeout_sec` (int, optional) |
| `file_read` | Read text from a file on device | `path` (string), `max_lines` (int, optional) |
| `file_write` | Write text to a file on device | `path` (string), `content` (string), `append` (bool) |
| `file_list` | List directory contents | `path` (string) |
| `device_info` | Get model, version, battery, storage | — |
| `system_setting` | Get/set/list Android settings | `action` (get/set/list), `namespace` (global/secure/system), `key`, `value` |

### Terminal Tool (1)

| Tool | Description | Parameters |
|------|-------------|------------|
| `task_complete` | Signal goal achieved/failed | `success` (bool), `summary` (string) |

---

## Project Architecture

```
android-claude-controller/
│
├── acc_core/                    # Core Python package
│   ├── adb/                     # ADB device abstraction (8 modules)
│   │   ├── client.py            #   Connection management
│   │   ├── device.py            #   Device info, properties
│   │   ├── screen.py            #   Screenshot capture
│   │   ├── input.py             #   Touch, keys, gestures
│   │   ├── ui.py                #   UI Automator XML
│   │   ├── app.py               #   App management
│   │   ├── shell.py             #   Shell execution
│   │   └── files.py             #   File operations
│   │
│   ├── providers/               # LLM provider abstraction
│   │   ├── base.py              #   Abstract provider interface
│   │   ├── factory.py           #   Auto-detect and create provider
│   │   ├── anthropic.py         #   Anthropic Claude provider
│   │   └── deepseek.py          #   DeepSeek provider (OpenAI-compatible)
│   │
│   ├── claude/                  # Claude-specific (prompts, history, tool defs)
│   │   ├── tools.py             #   All 19 tool schemas
│   │   ├── prompts.py           #   System prompt
│   │   ├── history.py           #   Conversation management
│   │   └── client.py            #   Legacy Claude client (kept for compat)
│   │
│   ├── agent/                   # Agent loop
│   │   ├── loop.py              #   Observe → plan → execute → verify
│   │   ├── executor.py          #   Tool call → ADB dispatch
│   │   ├── safety.py            #   Risk classification
│   │   └── callbacks.py         #   Abstract progress callbacks
│   │
│   ├── utils/                   # Utilities
│   │   ├── image.py             #   Image compression/encoding
│   │   ├── text.py              #   Token estimation, XML truncation
│   │   └── logging.py           #   Logging setup
│   │
│   ├── config.py                # Configuration management
│   └── exceptions.py            # Exception hierarchy
│
├── cli/                         # CLI application (Click + Rich)
│   ├── main.py                  #   Entry point, command group
│   ├── goal.py                  #   `acc goal` command
│   ├── chat.py                  #   `acc chat` interactive TUI
│   ├── device_cmd.py            #   `acc device` group
│   ├── screenshot.py            #   `acc screenshot`
│   ├── ui_dump.py               #   `acc ui-dump`
│   ├── config_cmd.py            #   `acc config` group
│   ├── web.py                   #   `acc web` group
│   ├── display.py               #   Rich layout helpers
│   └── session_store.py         #   JSON session persistence
│
├── web/                         # Django web application
│   ├── manage.py
│   ├── web/                     #   Django project
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py / asgi.py
│   └── controller/              #   Main Django app
│       ├── models.py            #     Device, Session, Message, Screenshot
│       ├── views.py             #     Views + API endpoints
│       ├── urls.py              #     URL routing
│       ├── admin.py             #     Django admin
│       ├── forms.py             #     Session creation form
│       ├── tasks.py             #     Celery agent runner
│       ├── callbacks.py         #     DjangoRedisCallbacks
│       └── templates/           #     HTML templates (7 files)
│
├── tests/                       # Test suite
│   ├── test_adb/                #   ADB module tests
│   ├── test_claude/             #   Claude integration tests
│   ├── test_agent/              #   Agent loop tests
│   ├── test_cli/                #   CLI tests
│   └── test_web/                #   Django model tests
│
├── docs/                        # Documentation
│   └── GETTING_STARTED.md       #   This file
│
├── pyproject.toml               # Package metadata + dependencies
├── .env.example                 # Environment template
└── .gitignore
```

### Key Design Decisions

**SQLite for Django** — Termux cannot easily run PostgreSQL. SQLite works without configuration and is perfect for single-user device control.

**No WebSockets by default** — The web UI uses 1.5-second polling instead of Django Channels. This avoids the Daphne+Redis+ASGI stack overhead on Termux. Channels can be added later if needed.

**JPEG quality 70, max 1280px** — Screenshots are compressed before sending to the AI. This balances visual clarity against token cost. A 1080×2400 screenshot compresses to ~150KB / ~2000 tokens.

**UI dump truncation to 80 elements** — Raw `uiautomator dump` output can be hundreds of KB. ACC parses the XML, ranks elements by importance (has text, clickable, focused, visible), and returns only the top 80.

**Subprocess ADB (not async)** — ADB commands are fast blocking calls. Using async subprocess adds complexity without benefit. Each ADB call runs in a thread pool via `asyncio.to_thread()`.

---

## Troubleshooting

### "No ADB devices found"

```bash
# Check ADB server is running
adb start-server

# Check device is connected
adb devices

# If "unauthorized" — unlock phone and accept the USB debugging dialog
# If "offline" — reconnect USB, or run:
adb kill-server && adb start-server

# On Termux, ensure android-tools is installed:
pkg install android-tools
```

### "ANTHROPIC_API_KEY not set"

```bash
# Check your key is exported
echo $ANTHROPIC_API_KEY

# If empty, export it
export ANTHROPIC_API_KEY=sk-ant-...
# Or for DeepSeek:
export DEEPSEEK_API_KEY=sk-...

# Add to your shell profile for persistence
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
source ~/.bashrc
```

### "Permission denied" in Termux

```bash
# ADB requires Termux to access USB
# On Android, you need to either:
# 1. Use wireless ADB (connect to localhost if both on same device)
# 2. Or run Termux with USB permissions (requires root)
```

### Screenshots are slow

```bash
# Reduce screenshot quality
acc config set screenshot_quality 40

# Reduce max dimension
acc config set max_screenshot_dimension 720

# Use text mode to avoid screenshots entirely
acc chat -m text
```

### DeepSeek tool calls fail or return bad JSON

DeepSeek's tool calling is less reliable than Claude's for complex multi-step operations. Try:
```bash
# Use simpler goals with DeepSeek
acc goal "take a screenshot"  # Good — single step
acc goal "open settings"       # Good — straightforward

# For complex navigation, use Claude instead
ACC_PROVIDER=anthropic acc goal "navigate to wifi settings and forget network XYZ"
```

### "Context too large" errors

This happens when the conversation history grows too large:
```bash
# Reduce max steps
acc config set max_steps 10

# Use text mode (much smaller than screenshots)
acc chat -m text

# Start a fresh session instead of resuming
```

### Django fails to start

```bash
# Check Django is installed
pip install "Django>=4.2,<5.2"

# Run migrations
acc web migrate

# Check for port conflicts
acc web serve -p 8080
```

---

## Termux-Specific Notes

### Performance
- Termux runs on phone CPU — agent loops are light (just API calls + ADB commands), so performance is fine
- The Django server on Termux works for local-only use. Don't expose it to the network without proper security
- Screenshot compression uses Pillow — first import may be slow on older devices

### Running ADB Locally
If you're running ACC on the same phone you want to control:
```bash
# Connect ADB to localhost
adb connect localhost:5555
# Or use wireless debugging on Android 11+
```

### Battery Considerations
- Vision mode (screenshots) uses more CPU and network
- Text mode is much lighter on battery
- Consider `ACC_MAX_STEPS=10` for quick tasks
- Use DeepSeek for lower-cost, lighter API calls

### Storage
- Session files: `~/.config/acc/sessions/` — JSON files, ~100KB each with screenshots
- Screenshots: `~/.config/acc/screenshots/` — JPEG files, ~50-150KB each
- Cache: `~/.cache/acc/` — temporary files
- Django DB: `db.sqlite3` in project directory
- Clean up old sessions periodically: `rm -rf ~/.config/acc/sessions/*.json`

### Security
- **Never** share your API key
- The Django admin uses Django's auth system — create a strong password
- Don't expose the web server to the internet without HTTPS
- ADB gives full device control — only connect trusted devices
- Safety mode is ON by default — keep it that way unless you know what you're doing

---

## Getting Help

- **GitHub Issues:** [github.com/tai/android-claude-controller/issues](https://github.com/tai/android-claude-controller)
- **View config:** `acc config show`
- **Check version:** `acc --version`
- **Enable debug logging:** `acc -v goal "test"`
