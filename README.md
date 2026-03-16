# TelePort2PI

TelePort2PI is an open-source bridge that connects a Telegram bot with locally running AI models on a Raspberry Pi using Ollama.

It allows you to access your personal AI assistant from anywhere through Telegram while keeping all AI processing on your own hardware.

---

# Project Goal

The goal of TelePort2PI is to make it easy to run a **private AI assistant** on a Raspberry Pi and interact with it remotely using Telegram.

Instead of sending your prompts to cloud AI services, the AI runs locally on your device.

---

# Features

* Access AI through Telegram
* Run AI models locally using Ollama
* Designed for Raspberry Pi
* Multi-model support
* Lightweight architecture
* Open-source and extensible

---

# Why TelePort2PI?

Most AI assistants rely on cloud APIs.

TelePort2PI provides:

* Full privacy
* No API cost
* Local AI execution
* Full control over models

---

# How It Works

User sends a message to a Telegram bot.

```
User → Telegram → TelePort2PI → Ollama → AI Model → Response → Telegram
```

TelePort2PI acts as a bridge between Telegram and the local AI model.

---

# Hardware Requirements

Recommended:

* Raspberry Pi 5 (8GB RAM)
* 64GB storage
* Internet connection

---

# Software Requirements

* Python 3.10+
* Ollama
* Telegram Bot Token

---

# Installation

## 1 Install Ollama

```
curl -fsSL https://ollama.com/install.sh | sh
```

Pull a model:

```
ollama pull mistral
```

---

## 2 Clone Repository

```
git clone https://github.com/a-sunny/teleport2pi.git
cd teleport2pi
```

---

## 3 Install Dependencies

```
pip install -r requirements.txt
```

---

## 4 Create Telegram Bot

Use Telegram **BotFather** to create a bot and obtain a bot token.

Add your token inside:

```
config/config.py
```

---

## 5 Run TelePort2PI

```
python teleport2pi.py
```

---

# Example Usage

Send a message to your Telegram bot:

```
Explain quantum computing simply
```

The AI model running on your Raspberry Pi will generate a response and send it back through Telegram.

---

# Roadmap

Planned features:

* Multi-user support
* Conversation memory
* File summarization
* Voice messages
* Model switching
* Smart home integration

---

# Contributing

Contributions are welcome.

You can help by:

* reporting issues
* improving documentation
* adding features
* optimizing performance

Fork the repository and submit a pull request.

---

# License

MIT License

---

# Author

Created by **Sunny**
https://github.com/a-sunny

---

# Vision

TelePort2PI aims to make personal AI servers simple, private, and accessible using affordable hardware like Raspberry Pi.

Run your own AI. Access it anywhere.
