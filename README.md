# TelePort2PI

**TelePort2PI** is an open-source project that connects a Telegram bot to locally running AI models on a Raspberry Pi using Ollama.

It allows you to access your personal AI assistant from anywhere through Telegram while keeping all AI processing local.

---

## Features

* Run AI models locally using Ollama
* Access AI through a Telegram bot
* Works on Raspberry Pi 5
* Multi-model support
* Private and self-hosted
* Open-source and extensible

---

## Why TelePort2PI?

Most AI assistants depend on cloud APIs. TelePort2PI allows you to run AI locally and access it remotely through Telegram.

Benefits:

* No API costs
* Full privacy
* Customizable models
* Lightweight hardware requirements

---

## How It Works

User sends a message to a Telegram bot.

```
User → Telegram Bot → TelePort2PI → Ollama → AI Model → Response → Telegram
```

TelePort2PI acts as the bridge between Telegram and the local AI model.

---

## System Architecture

Components:

* Telegram Bot
* TelePort2PI Service
* Ollama API
* Local LLM Model

All AI inference runs locally on the Raspberry Pi.

---

## Requirements

Hardware:

* Raspberry Pi 5 (8GB recommended)

Software:

* Python 3.10+
* Ollama
* Telegram Bot Token

---

## Installation

### 1 Install Ollama

```
curl -fsSL https://ollama.com/install.sh | sh
```

Pull a model:

```
ollama pull mistral
```

---

### 2 Clone Repository

```
git clone https://github.com/YOUR_USERNAME/teleport2pi.git
cd teleport2pi
```

---

### 3 Install Dependencies

```
pip install -r requirements.txt
```

---

### 4 Configure Telegram Bot

Create a bot using Telegram BotFather.

Add your bot token in:

```
config/config.py
```

---

### 5 Run TelePort2PI

```
python teleport2pi.py
```

---

## Example Usage

Send a message to your Telegram bot:

```
Explain black holes in simple terms
```

The AI model running on your Raspberry Pi will generate a response.

---

## Roadmap

Planned features:

* Multi-user support
* Conversation memory
* Voice messages
* File summarization
* Smart home integration
* Model switching

---

## Contributing

Contributions are welcome.

You can help by:

* reporting issues
* improving documentation
* adding features
* optimizing performance

Fork the repository and submit a pull request.

---

## License

MIT License

---

## Vision

TelePort2PI aims to make personal AI servers simple, private, and accessible using affordable hardware like Raspberry Pi.

Run your own AI. Access it anywhere.

---

## Author

Created as an open-source project to explore local AI systems and edge computing.
