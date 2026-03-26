# Smart Garbage Disposal System
**York University k2i Academy STEM Challenge — Top 3 Finalist, 2024**

An AI-powered waste management system that uses a HuskyLens AI camera to classify waste in real time and automatically opens the correct bin compartment (Recyclable, Compost, or Landfill) via a Micro:bit-controlled servo mechanism.

---

## How It Works

```
[ Object placed in front of bin ]
          │
          ▼
  [ HuskyLens AI Camera ]
  Identifies waste category
  (Recyclable / Compost / Landfill)
          │
          ▼
  [ Python Backend — main.py ]
  Debounces detection across N frames
  to filter false positives
          │
          ▼
  [ Micro:bit (MicroPython) ]
  Receives serial command
  Actuates the correct servo
          │
          ▼
  [ Correct bin compartment opens ]
  Closes automatically after timeout
```

---

## Hardware

| Component | Purpose |
|---|---|
| [HuskyLens AI Camera](https://www.dfrobot.com/product-1922.html) | Real-time object classification |
| [BBC Micro:bit v2](https://microbit.org/) | GPIO controller for servos |
| 3× Servo Motors (SG90 or similar) | Opens/closes bin compartments |
| USB cables | Serial communication between host and Micro:bit |

**Wiring — Servos to Micro:bit edge connector:**
| Servo | Pin | Category |
|---|---|---|
| Servo 1 | Pin 0 | Recyclable |
| Servo 2 | Pin 1 | Compost |
| Servo 3 | Pin 2 | Landfill |

---

## Software Setup

### 1. Clone the repo
```bash
git clone https://github.com/your-username/smart-garbage-disposal.git
cd smart-garbage-disposal
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Flash the Micro:bit
Open `microbit/main.py` in the [Micro:bit Python Editor](https://python.microbit.org/) and flash it to your Micro:bit.

### 4. Configure ports
Edit `config.py` to match your system:
```python
MICROBIT_PORT    = "/dev/ttyUSB0"   # Windows: "COM3"
HUSKY_LENS_PORT  = "/dev/ttyUSB1"   # Windows: "COM4"
HUSKY_MODE       = "UART"           # or "I2C" if connected via GPIO
```

### 5. Train HuskyLens
In HuskyLens **Object Classification** mode, train:
- **Class 1** → Recyclable items (bottles, cans, paper)
- **Class 2** → Compost items (food scraps, organic material)
- **Class 3** → Landfill items (general/non-sortable waste)

### 6. Run
```bash
# Real hardware
python main.py

# Simulation mode (no hardware needed)
python main.py --mock

# Verbose output
python main.py --mock --verbose
```

---

## Project Structure

```
smart-garbage-disposal/
├── main.py                     # Entry point — main detection loop
├── config.py                   # Hardware ports, timing, class ID mappings
├── requirements.txt
│
├── src/
│   ├── husky_lens.py           # HuskyLens camera interface (UART/I2C)
│   ├── classifier.py           # Class ID → waste category + debounce logic
│   └── microbit_controller.py  # Serial command interface for Micro:bit
│
├── microbit/
│   └── main.py                 # MicroPython firmware — flash this to Micro:bit
│
└── tests/
    └── test_classifier.py      # Unit tests for classification logic
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Serial Protocol

The host Python backend and Micro:bit communicate over USB serial using newline-terminated ASCII commands:

| Direction | Command | Meaning |
|---|---|---|
| Host → Micro:bit | `PING` | Health check |
| Host → Micro:bit | `OPEN:RECYCLABLE` | Open recyclable compartment |
| Host → Micro:bit | `OPEN:COMPOST` | Open compost compartment |
| Host → Micro:bit | `OPEN:LANDFILL` | Open landfill compartment |
| Micro:bit → Host | `ACK:RECYCLABLE` | Compartment opened successfully |
| Micro:bit → Host | `ERR:UNKNOWN_CATEGORY:X` | Unrecognised category received |

---

## Team

Built at the York University k2i Academy STEM Challenge 2024 by a cross-functional team of four. Placed **Top 3 overall** out of all competing teams.

---

## License

MIT
