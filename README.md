<div align="center">

# 🔬 sigvet_master_app

**The Official Sigvet Device Installer & Diagnostic Suite**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%2F%20Debian-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE)

> A production-grade, GUI-based application for **installing, diagnosing, and benchmarking Sigvet devices** on Linux/Debian systems. Wraps hardware control, benchmarking utilities, and device management into a single, polished touchscreen-ready interface.

</div>

---

## ✨ Key Features

| Category | Capability |
|---|---|
| 🖥️ **Hardware Control** | Interactive XY-stage control, hardware monitoring, device erasing & backup via GUI |
| 🧪 **Benchmarking Suite** | CPU (Geekbench + Stress-NG), Memory (Memtester), Disk I/O (FIO), Network & Wi-Fi reliability |
| 📊 **Profile Evaluation** | Compares results against `device_profiles.yaml` baselines; auto-grades Pass/Fail |
| 📄 **Report Generation** | Exports results as **PDF**, JSON, HTML, and TXT into `reports/` |
| 📦 **Debian Packaging** | One-command `.deb` build via `build_deb.py` for seamless device installation |
| 🔌 **Connectivity** | Twilio notifications, Google API integration, serial port management |
| ⌨️ **Touchscreen UI** | On-screen keyboard, phone numpad, animated splash, and full dark-themed GUI |

---

## 📂 Project Structure

```
sigvet_master_app/
│
├── main.py                         # 🚀 Application entry point
├── build_deb.py                    # 📦 Debian package builder
├── requirements.txt                # 🐍 Python dependencies
├── config.yaml                     # ⚙️  Top-level runtime configuration
├── template_test.py                # 🧩 Template for adding new benchmark tests
│
├── core/                           # 🧠 Application core logic
│   ├── benchmark_base.py           #    Abstract base class for all tests
│   ├── config_loader.py            #    YAML/JSON config parsing
│   ├── config.py                   #    Runtime configuration object
│   ├── drive_handler.py            #    Storage device detection & management
│   ├── env_parser.py               #    Environment variable resolution
│   ├── evaluator.py                #    Scoring & Pass/Fail evaluation engine
│   ├── loader.py                   #    Dynamic test module discovery & loading
│   ├── pdf_generator.py            #    PDF report generation (ReportLab)
│   └── worker.py                   #    Background threading / task runner
│
├── display/                        # 🖼️  GUI components (PyQt6)
│   ├── window.py                   #    Main application window & routing
│   ├── hardware_control.py         #    Hardware control panel UI
│   ├── xy_stage.py                 #    Interactive XY-stage controller
│   ├── components.py               #    Reusable UI widgets & cards
│   ├── device_selector.py          #    Device profile selection screen
│   ├── db_editor.py                #    Database / config editor UI
│   ├── menu.py                     #    Navigation menu
│   ├── splash.py                   #    Animated splash screen
│   ├── animated_stack.py           #    Page-transition animation stack
│   ├── keyboard.py                 #    On-screen full keyboard
│   ├── phone_numpad.py             #    On-screen numeric keypad
│   ├── row_widget.py               #    Test-progress row widget
│   ├── erase.py                    #    Device erase workflow UI
│   ├── backup.py                   #    Device backup workflow UI
│   └── styles.py                   #    Global stylesheet & theme tokens
│
├── tests/                          # 🧪 Benchmark test modules
│   ├── geekbench.py                #    Geekbench CPU benchmark wrapper
│   ├── fio_speed.py                #    FIO disk I/O benchmark
│   ├── memtest.py                  #    Memtester RAM reliability test
│   ├── network_speed.py            #    Network speed test (speedtest-cli)
│   ├── disk_io.py                  #    Custom disk read/write profiler
│   └── wifi_reliability.py         #    Wi-Fi stability & packet-loss test
│
├── config/                         # 📋 Device profiles & thresholds
│   ├── device_profiles.yaml        #    Hardware baseline specs per device model
│   ├── benchmark_values.yaml       #    Pass/Fail thresholds for each test metric
│   └── settings.json               #    App preferences (excluded from git)
│
├── utils/                          # 🛠️  Shared utilities
│   ├── notifier.py                 #    Twilio / notification dispatcher
│   └── geekbench/                  #    Geekbench binary cache (excluded from git)
│
└── reports/                        # 📁 Generated reports (excluded from git)
```

---

## 🛠️ Prerequisites

**Runtime requirements:**

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | Required |
| OS | Linux (Debian/Ubuntu) | Recommended for full feature parity |
| `fio` | Latest | Disk I/O benchmarking |
| `stress-ng` | Latest | CPU stress testing |
| `memtester` | Latest | RAM reliability testing |
| Geekbench | 5 or 6 | Fetched automatically on first run |

Install system dependencies:
```bash
sudo apt-get update && sudo apt-get install -y fio stress-ng memtester
```

---

## 🚀 Installation & Setup

### Option 1 — Install via `.deb` Package (Recommended for Device Deployment)

This is the **primary intended workflow** for deploying the app on a Sigvet device.

```bash
# Build the package from source
python build_deb.py

# Install on the target device
sudo dpkg -i sv-setup-v2.deb
sudo apt-get install -f          # Resolve any missing system dependencies
```

The installed application will be available system-wide and can be launched from the application menu or terminal.

---

### Option 2 — Run from Source (Development)

**1. Clone the repository:**
```bash
git clone https://github.com/sigvet/sigvet_master_app.git
cd sigvet_master_app
```

**2. Set up a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**4. Run the application:**
```bash
python main.py
```

---

## ⚙️ Configuration

Edit files inside `config/` to customize behavior:

| File | Purpose |
|---|---|
| `config/device_profiles.yaml` | Define expected hardware specs (CPU cores, RAM, storage, network) per Sigvet device model |
| `config/benchmark_values.yaml` | Set Pass/Fail thresholds for each benchmark metric |
| `config/settings.json` | Local app preferences — **not committed to git** |
| `config.yaml` | Top-level runtime config (ports, API keys, feature flags) — **review before committing** |

---

## 🧩 Adding Custom Benchmark Tests

`sigvet_master_app` is designed to be easily extensible:

1. Copy `template_test.py` from the project root into the `tests/` folder.
2. Rename it to describe your test (e.g., `gpu_stress.py`).
3. Inherit from `BenchmarkBase` (`core/benchmark_base.py`) and implement:
   - `run()` — executes the benchmark logic
   - `evaluate()` — scores the result and returns Pass/Fail
4. The loader (`core/loader.py`) will **automatically discover** and register your test in the GUI on next launch.

---

## 📦 Building the Debian Package

```bash
# From the project root:
python build_deb.py
```

The script will:
- Bundle all Python sources and dependencies
- Create a self-contained `.deb` installer
- Output the package to the project root

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "feat: describe your change"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request against `main`

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## 📬 Contact

For internal Sigvet team support, raise an issue in the repository or contact the platform engineering team directly.

---

<div align="center">
<sub>Built with by Abhishek S @ sigtuple</sub>
</div>
