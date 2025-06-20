# 🛰️ Python Gateway

A lightweight Python Gateway that listens for incoming traffic on a specified IPs and ports and forwards them to specified IPs and ports according to configuration

---

## ⚙️ Features

- 📄 Logs to file or prints to terminal
- 🧩 Configurable via `config.ini`
- 🧵 Threaded handling for tunnels
- 📡 Routes all traffic on a from/to specified ports

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/luissequeira94/Gateway.git
cd Gateway
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Edit the config.ini file:
```bash
[tunnel_1]
# IP address for the gateway to listen on. '0.0.0.0' means listen on all available interfaces.
listen_ip = 0.0.0.0
# Port number for the gateway to listen on for this tunnel.
listen_port = 8000
# Destination IP address to which traffic will be forwarded.
forward_ip = 127.0.0.1
# Destination port number to which traffic will be forwarded.
forward_port = 8080
# Path to the log file for this specific tunnel.
log_file = tunnel_1.log

# You can add more tunnels by creating new sections like [tunnel_2], [tunnel_3], etc.
# Make sure each tunnel has unique listen_port if listening on the same IP.
```

## 🌐 Execution

```bash
python Gateway.py
```

Example Logs
```bash
2025-06-20 18:28:48,945 - tunnel_1 - INFO - Initializing tunnel: Listen on 0.0.0.0:8000, Forward to 127.0.0.1:8080
2025-06-20 18:30:49,327 - tunnel_1 - INFO - [127.0.0.1:8080] New client connected from ('127.0.0.1', 28184)
2025-06-20 18:30:49,328 - tunnel_1 - INFO - [127.0.0.1:8080] Connected to destination 127.0.0.1:8080
2025-06-20 18:30:49,338 - tunnel_1 - INFO - [127.0.0.1:8080] Client -> Destination: No more data. Connection closed.

```

## 📁 Project Structure
```bash
.
├── Gateway.py          # Main application
├── config.ini          # Configuration file
└── tunnel_$.txt        # Log file (created at runtime if needed)
```

## 📜 License
MIT License. See LICENSE file for details.

## 🤝 Contributing
Pull requests are welcome.  
For major changes, please open an issue first to discuss what you would like to change.

## Buy Me a Coffee
Like this content? Wanna help me and keep the cadence? Buy me a Coffee! - https://coff.ee/novabyt3
Thank you!! <3 
