# ShaadiCount

Voice-first wedding RSVPs that keep the catering count honest.

Built at Festive Hacks x WeAreDevelopers Conference India, 25 Nov 2026.

## Problem

How can an Indian wedding host stop losing lakhs to catering over-orders or shortages when elders won't fill RSVP forms and guests bring unannounced +1s?

## Sponsor tools

- **Sarvam AI**: voice RSVPs in Hinglish and regional languages (Saaras), structured extraction (Sarvam LLM), spoken confirmations (Bulbul).
- **Flagsmith**: per-segment +1 rules, RSVP prompt A/B variant, catering lock kill switch.
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
