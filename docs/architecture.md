# TelePort2PI — Architecture

## Overview

TelePort2PI is a three-layer system: a Telegram interface, a Python bot service, and a local Ollama AI runtime.

```
┌─────────────────────────────────────────────────────┐
│                   User Device                        │
│              (Phone / PC / Tablet)                   │
│                 Telegram App                         │
└──────────────────────┬──────────────────────────────┘
                       │  HTTPS (Telegram API)
                       ▼
┌─────────────────────────────────────────────────────┐
│               Telegram Bot API                       │
│         (Cloud relay — no AI here)                   │
└──────────────────────┬──────────────────────────────┘
                       │  Long-polling
                       ▼
┌─────────────────────────────────────────────────────┐
│              Raspberry Pi 5 (8GB)                    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │           bot/bot.py  (Main Service)         │    │
│  │                                              │    │
│  │  • Auth guard (ALLOWED_USER_IDS)             │    │
│  │  • Rate limiter                              │    │
│  │  • Per-user conversation history             │    │
│  │  • Message routing                           │    │
│  └────────────────┬────────────────────────────┘    │
│                   │                                  │
│  ┌────────────────▼────────────────────────────┐    │
│  │         bot/commands.py  (Commands)          │    │
│  │  /start /help /reset /status                 │    │
│  │  /model /models /setmodel                    │    │
│  │  /summarize /translate /code /explain        │    │
│  └────────────────┬────────────────────────────┘    │
│                   │                                  │
│  ┌────────────────▼────────────────────────────┐    │
│  │       bot/ollama_client.py  (AI Layer)       │    │
│  │  REST → http://localhost:11434               │    │
│  └────────────────┬────────────────────────────┘    │
│                   │                                  │
│  ┌────────────────▼────────────────────────────┐    │
│  │              Ollama Runtime                  │    │
│  │        LLaMA / Mistral / Phi / etc.          │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Data Flow (normal chat message)

1. User types a message in Telegram
2. Telegram Bot API delivers it to `bot.py` via long-polling
3. `bot.py` checks auth + rate limit
4. Conversation history + new message are assembled into a `messages` list
5. `ollama_client.py` POSTs to `http://localhost:11434/api/chat`
6. Ollama runs inference locally and returns the response
7. Response is sent back to the user via Telegram

## Key Design Decisions

### No external AI calls
All inference happens on-device. Nothing is sent to OpenAI, Anthropic, or any cloud service.

### Long-polling vs Webhooks
The bot uses Telegram long-polling (no inbound port required). This means the Pi only makes outbound connections — no port forwarding needed on your router.

### Per-user session isolation
Each Telegram user ID gets its own `context.user_data` dict, holding:
- `history` — rolling conversation turns
- `model` — their currently selected model

### Stateless Ollama client
`OllamaClient` holds no conversation state itself. State is managed by `bot.py` and passed in with each request, making it easy to test and extend.

## File Reference

| File | Purpose |
|------|---------|
| `bot/bot.py` | Entry point, message handler, auth, rate limiting |
| `bot/commands.py` | All `/command` handlers |
| `bot/ollama_client.py` | REST client for Ollama API |
| `config/config.example.py` | Configuration template |

## Security Model

- **User whitelist** — `ALLOWED_USER_IDS` in config restricts access
- **Rate limiting** — prevents abuse (configurable requests/minute)
- **No open ports** — long-polling means zero inbound exposure
- **Local-only AI** — prompts and responses never leave the Pi

## Scaling Notes

The Raspberry Pi 5 (8GB) can comfortably run 7B parameter models (LLaMA 3.2, Mistral 7B). Larger models (13B+) will be slow. For best performance:
- Use quantized models (Q4_K_M or Q5_K_M)
- Keep `MAX_HISTORY_TURNS` low (5–10)
- Use an SSD over microSD for model storage