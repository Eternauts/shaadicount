# ShaadiCount

Voice-first wedding RSVPs that keep the catering count honest.

[![Watch the 10 second intro](docs/intro-poster.jpg)](samples/intro_video.mp4)

**[Watch the intro video](samples/intro_video.mp4)** (10 seconds)

Built at Festive Hacks x WeAreDevelopers Conference India, 25 Nov 2026.

## Problem

How can an Indian wedding host stop losing lakhs to catering over-orders or shortages when elders won't fill RSVP forms and guests bring unannounced +1s?

## Hear it work

Two real recordings, run through the live pipeline:

| Recording | Saaras heard | Saved as |
| --- | --- | --- |
| [Tamil voice note](samples/sample_tamil.ogg) | நம்ம family-ம்மா மொத்தம் சேர்த்து 7 பேர் இருக்காங்க, நம்ம எல்லாருமே vegetarian தான். | 7 guests, veg |
| [Hinglish voice note](samples/sample_hinglish.ogg) | हम शर्मा परिवार से हैं मैं और शर्मा uncle total 3 लोग हैं आ रहे हैं हम सब pure vegetarian हैं। | 3 guests, veg |

## Demo stage

Open `/demo`. It has a guest chat for voice notes and text, a live view of what the backend did
for each reply, and the plate count with the current Flagsmith flags.

1. **Tamil voice RSVP**: send the Tamil voice note and hear the reply in Tamil.
2. **Surprise +1**: a colleague's extra friends are blocked by Flagsmith, close family's are allowed.
3. **Approval and lock**: the caterer buffer is breached, and NudgeBee asks for approval.

The chat is a simulation that calls the same API as the invitation page at `/invite/1`.
WhatsApp is not connected: our test messages did not go through, so it is not part of the demo.
The couple, the households and the date are made up.

## Sponsor tools

- **Sarvam AI**: voice RSVPs in Hinglish and regional languages (Saaras), structured extraction (Sarvam LLM), spoken confirmations (Bulbul).
- **Flagsmith**: per-segment +1 rules, RSVP prompt A/B variant, catering lock kill switch. Flags are evaluated in memory, so a dropped connection cannot change a decision.
- **NudgeBee**: approval-gated catering workflow and incident investigation on the Kubernetes deployment.

## Run locally

| Variable | Used for |
| --- | --- |
| `SARVAM_API_KEY` | Speech to text, extraction, text to speech |
| `FLAGSMITH_SERVER_ENVIRONMENT_KEY` | Reading flags on the server |
| `FLAGSMITH_CLIENT_ENVIRONMENT_KEY` | Public environment key |
| `FLAGSMITH_ENVIRONMENT_API_KEY` | Optional. Which environment the Admin API changes. Defaults to the client key |
| `FLAGSMITH_ADMIN_TOKEN` | Changing flags through the Admin API |
| `CATERER_BUFFER_PLATES`, `COST_PER_PLATE_INR` | Optional, default 400 and 1500 |

```bash
cp .env.example .env   # fill in keys
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make run               # http://localhost:8000/api/status
```

## Run on kind

```bash
make deploy            # build, load into kind, create secret from .env, apply manifests
make forward           # http://localhost:8000
```

## AI assistance disclosure

AI coding assistants were used during this hackathon: Claude (scaffolding, planning and code review). All code was reviewed and is understood by the team.

The intro video is AI-generated.
