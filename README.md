# Prank Call Service

FastAPI + Vapi + Deepgram + OpenAI + Twilio outbound prank-call app.

## ⚠️ Before you point this at real people

- **Recording consent**: this records calls. Many places (several US
  states, many countries) require *all* parties to consent to a call
  being recorded. Don't ship this without a real consent flow (e.g. only
  ever call numbers that opted in, and/or play a recording disclosure).
- **Robocall / auto-dial rules**: automated/AI-voice calls to phones can
  trigger TCPA-style regulations even outside marketing contexts. Check
  the rules for your jurisdiction and your recipients'.
- **DNC list is enforced**, but it's opt-out, not opt-in — consider
  flipping to an opt-in contact list before using this beyond you and
  consenting friends.

## Prank types

| `prank_type` | What it does |
|---|---|
| `meme_soundboard` | Plays local audio clips (from `app/data/meme_sounds/`) back-to-back in random order. Placed directly via Twilio (no Vapi/LLM involved — there's no conversation to have). |
| `hiring_manager` | Vapi/GPT-4o-mini assistant runs a deadpan fake screening interview for a randomly-picked absurd Malayalam-comedy-flavored role/company/interviewer name. |
| `movie_spoiler` | OpenAI pre-writes a paraphrased, de-identified retelling of a movie's plot (incl. ending); the Vapi assistant tells it as "something that happened to a friend," then reveals at the end which movie it spoiled. Requires `context` = movie title. |

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in .env with your real keys

# terminal 1
uvicorn app.main:app --reload --port 8000

# terminal 2
cloudflared tunnel --url http://localhost:8000
# copy the https://xxxx.trycloudflare.com URL into .env as
# VAPI_WEBHOOK_URL=.../webhooks/vapi and PUBLIC_BASE_URL=... (no path)
# then restart uvicorn so it picks up the new .env values
```

No database to provision — call state and the DNC list live in memory
(`app/store.py`) for the lifetime of the process. See the storage note
below.

Add a few short `.mp3`/`.wav` files to `app/data/meme_sounds/` if you want
to test `meme_soundboard`.

## Storage: none, on purpose

There's no database. `app/store.py` keeps calls and the DNC suppression
list in a plain in-memory dict, guarded by a lock. That means:

- **Nothing survives a restart.** Call history, transcripts, DNC entries —
  gone the moment the process stops.
- **Only safe with a single process.** Run `uvicorn` with one worker
  (the default). If you ever deploy with `--workers N > 1`, multiple
  replicas, or behind a load balancer with more than one backend
  instance, each process gets its own memory — a call created on one
  instance won't be visible to `GET /api/calls/{id}` if that request
  lands on a different instance, and the same goes for webhooks needing
  to look a call up by `vapi_call_id`.

If you outgrow either of those constraints later, only `app/store.py`
needs to change (e.g. to Redis or Postgres) — routers and services just
call its functions and don't know how it's implemented.

## API

- `POST /api/calls/preview` — generates the AI script (system prompt + opening
  line) for `hiring_manager` or `movie_spoiler` **without placing a call or
  storing anything**. Use this to show the user what the AI came up with
  before they commit to dialing.
  ```json
  // request
  {
    "contact_name": "Anjali",
    "prank_type": "movie_spoiler",
    "context": "Drishyam"
  }
  ```
  ```json
  // response
  {
    "prank_type": "movie_spoiler",
    "system_prompt": "You are Anjali's friend, calling to tell them ...",
    "first_message": "Hey Anjali, oh my god, you will not believe what just happened, do you have a sec?"
  }
  ```
  Let the user edit `system_prompt`/`first_message` in the UI if they want,
  then send those exact strings back in the next call.

- `POST /api/calls` — trigger a call. Pass the (optionally edited)
  `system_prompt` + `first_message` from `/preview` to skip regeneration
  and use exactly what was reviewed:
  ```json
  {
    "contact_name": "Anjali",
    "contact_phone": "+91XXXXXXXXXX",
    "prank_type": "movie_spoiler",
    "context": "Drishyam",
    "system_prompt": "...(from preview, possibly edited)...",
    "first_message": "...(from preview, possibly edited)..."
  }
  ```
  If `system_prompt`/`first_message` are omitted, the endpoint generates
  them on the fly exactly as before (useful if you skip the preview step,
  or for `meme_soundboard`, which has no script at all).

  Both `hiring_manager` and `movie_spoiler` accept an optional nested object
  letting the caller override any/all of what the AI would otherwise pick.
  Anything left out (or the whole object omitted) falls back to the AI
  default from before.

  `hiring_manager` — override role/interviewer/company, or add extra
  direction for the AI to follow:
  ```json
  {
    "contact_name": "Anjali",
    "contact_phone": "+91XXXXXXXXXX",
    "prank_type": "hiring_manager",
    "hiring_manager_input": {
      "role": "Chief Biriyani Quality Officer",
      "interviewer_name": "Sunny Kutty",
      "company_name": "Spice Route Global",
      "extra_instructions": "Ask her about her 5-year plan for sambar consistency."
    }
  }
  ```

  `movie_spoiler` — either steer the AI's retelling with `custom_notes`, or
  skip AI generation entirely and supply your own disguised story via
  `user_written_story` (still gets the automatic reveal line added at the end):
  ```json
  {
    "contact_name": "Anjali",
    "contact_phone": "+91XXXXXXXXXX",
    "prank_type": "movie_spoiler",
    "context": "Drishyam",
    "movie_spoiler_input": {
      "custom_notes": "Tell it like something that happened to a neighbor, keep it short."
    }
  }
  ```
  or
  ```json
  {
    "contact_name": "Anjali",
    "contact_phone": "+91XXXXXXXXXX",
    "prank_type": "movie_spoiler",
    "context": "Drishyam",
    "movie_spoiler_input": {
      "user_written_story": "So okay, this family covers up an accident by burying..."
    }
  }
  ```
- `GET /api/calls/{id}` — status, transcript, summary, analysis
- `POST /api/contacts/opt-out` — add a phone number to the in-memory DNC list
  ```json
  { "phone": "+91XXXXXXXXXX", "reason": "asked to stop" }
  ```
- `POST /webhooks/vapi` — Vapi server events (status-update, end-of-call-report, hang)
- `GET /health`

## Testing

```bash
python test_call.py
```

Edit `TEST_PHONE_NUMBER` in `test_call.py` first — only use a number you
own or have explicit consent to call.

## Known gotchas already handled here

- Vapi assistant config omits `firstMessageMode`.
- `DEEPGRAM_VOICE` is a bare name (`asteria`), not `aura-asteria-en`.
- `X-Vapi-Secret` header is verified before any webhook payload is
  processed.
- DNC check runs before every call is placed.
- Webhooks return `200` immediately and do real work in
  `BackgroundTasks`.
- `end-of-call-report` falls back to polling `GET /call/{id}` after a
  5s delay if `structuredData` wasn't present yet.
- In-memory store is thread-lock-protected but single-process only (see
  "Storage: none, on purpose" above).
