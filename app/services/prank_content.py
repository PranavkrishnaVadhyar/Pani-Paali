"""
Generates the per-call content for each prank type:

- meme_soundboard: picks a random-order playlist of local audio files.
  This one does NOT go through Vapi/an LLM at all -- it's just Twilio
  playing pre-recorded clips back-to-back, since there's no conversation
  to have. See app/services/twiml_service.py.

- hiring_manager: builds a system prompt + first message for a fake,
  comedic screening interview using a randomly picked funny Malayalam-
  film-flavored role + interviewer name.

- movie_spoiler: uses OpenAI to write a paraphrased "disguised" retelling
  of a movie's plot that avoids obviously naming the film, characters, or
  franchise while talking, and only reveals "by the way, that was a
  spoiler for <Movie>" at the very end. This is generated up front and
  passed to the Vapi assistant as its script/system prompt, since we want
  the story to actually stay on-track rather than have the LLM impro
  itself into revealing the movie mid-call.
"""

import os
import random
from dataclasses import dataclass

from openai import OpenAI

from app.config import get_settings

settings = get_settings()

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg"}


@dataclass
class CallScript:
    system_prompt: str
    first_message: str


# ---------------------------------------------------------------------------
# 1) Meme soundboard
# ---------------------------------------------------------------------------

def get_random_meme_playlist(limit: int | None = None) -> list[str]:
    """Returns filenames (not full paths) from MEME_SOUND_DIR in random order."""
    folder = settings.MEME_SOUND_DIR
    if not os.path.isdir(folder):
        return []
    files = [
        f for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS
    ]
    random.shuffle(files)
    if limit:
        files = files[:limit]
    return files


# ---------------------------------------------------------------------------
# 2) Fake hiring manager - funny Malayalam-film-flavored roles
# ---------------------------------------------------------------------------

# Comedic, clearly fictional roles/company names inspired by the general
# vibe of Malayalam comedy films. Names are original/generic, not lifted
# verbatim from any specific copyrighted character.
FUNNY_ROLES = [
    "Chief Undercover Uncle Spotter",
    "Senior Bus Conductor Whistle Consultant",
    "Head of Tharavadu Property Disputes",
    "Onasadya Banana Leaf Folding Specialist",
    "Autorickshaw Meter Philosophy Officer",
    "Toddy Shop Ambience Manager",
    "Wedding Video Slow-Motion Director",
    "Chief Fish Curry Tasting Officer",
    "Local Committee Election Strategist",
    "Umbrella Repair & Monsoon Readiness Lead",
]

FUNNY_INTERVIEWER_NAMES = [
    "Pankajakshan Pillai",
    "Bhaskara Menon",
    "Ouseppachan Varkey",
    "Kuttyachan Thomas",
    "Vilasini Amma",
    "Sudhakaran Nair",
    "Kochouseph Chazhikadan",
    "Ammini Teacher",
]

FUNNY_COMPANIES = [
    "Malabar Marvel Enterprises Pvt Ltd",
    "Onam Vibes Consultancy",
    "Global Nadan Solutions",
    "Kerala Blasters of Bureaucracy Inc.",
]


def generate_hiring_prank_script(
    contact_name: str,
    role: str | None = None,
    interviewer_name: str | None = None,
    company_name: str | None = None,
    extra_instructions: str | None = None,
) -> CallScript:
    """Any of role/interviewer_name/company_name left as None falls back to
    a random AI-picked value. `extra_instructions` (e.g. specific questions
    to ask, a tone to use) is appended to the system prompt verbatim when
    given."""
    role = role or random.choice(FUNNY_ROLES)
    interviewer = interviewer_name or random.choice(FUNNY_INTERVIEWER_NAMES)
    company = company_name or random.choice(FUNNY_COMPANIES)

    system_prompt = f"""You are {interviewer}, a painfully serious and deadpan HR manager at
{company}, conducting a phone screening interview for the role of "{role}".
You genuinely believe this is a completely normal, real job.

Ground rules:
- Stay 100% in character. Never say you are an AI or that this is a prank,
  no matter what the candidate says, unless they explicitly ask "is this a
  prank?" or "who set this up?" more than once -- only then you may gently
  break character and reveal it was a prank call.
- Ask absurd, over-the-top interview questions related to the fake role
  as if they are completely standard (e.g. for "{role}", ask about
  relevant but ridiculous scenarios).
- React to answers with exaggerated bureaucratic seriousness -- "noted",
  "I will have to escalate that to the committee", etc.
- Keep your own turns short (2-4 sentences) so the candidate, {contact_name},
  has room to talk and react.
- Never use slurs, insults, or anything genuinely mean -- the humor should
  come from absurdity, not from mocking the person.
- After roughly 4-6 exchanges, or if they seem confused/uncomfortable,
  wrap up warmly, reveal it was a prank call set up by their friend, and
  wish them a good day.
"""

    if extra_instructions:
        system_prompt += f"\nAdditional direction from the person who set up this prank:\n{extra_instructions}\n"

    first_message = (
        f"Hello, is this {contact_name}? This is {interviewer} calling from "
        f"{company} regarding your application for the {role} position. "
        f"Do you have a few minutes for a quick screening interview?"
    )

    return CallScript(system_prompt=system_prompt, first_message=first_message)


# ---------------------------------------------------------------------------
# 3) Movie spoiler, disguised as an "original" story until the reveal
# ---------------------------------------------------------------------------

def generate_spoiler_script(
    movie_title: str,
    contact_name: str,
    custom_notes: str | None = None,
    user_written_story: str | None = None,
) -> CallScript:
    """
    Produces the disguised spoiler narrative for `movie_title` one of two ways:

    - If `user_written_story` is given, it's used exactly as written --
      no AI call is made for the story itself.
    - Otherwise, calls OpenAI once, ahead of the call, to draft a paraphrased
      spoiler narrative. `custom_notes` (e.g. "focus on the twist ending",
      "tell it like gossip about a wedding") is folded into the generation
      prompt to steer style/focus.

    Either way, the model is instructed to:
      - retell the plot (including the ending) using generic character
        descriptions instead of real names, and without naming the film,
        actors, or franchise
      - sound like a friend telling a story that "happened to someone I know"
      - only reveal the real movie title at the very end
    We generate the story text up front so it's returned as part of the
    assistant's script, and give the live call assistant a system prompt
    that tells it to deliver this specific story and improvise natural
    listener back-and-forth around it.
    """
    if user_written_story:
        disguised_story = user_written_story.strip()
    else:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        gen_prompt = f"""Write a spoken-style retelling (250-400 words) of the full plot,
including the ending, of the movie "{movie_title}".

Rules:
- Do NOT mention the movie's title, any actor names, character names as
  written in the film, or the franchise/studio.
- Replace character names with generic descriptions (e.g. "this guy",
  "the older brother", "her best friend") and invent simple placeholder
  names if needed.
- Tell it like a personal anecdote or gossip ("So okay, this is wild, let
  me tell you what happened...") rather than a plot summary.
- Cover the major twists and the ending clearly, since the whole point is
  that it's a spoiler.
- End the retelling naturally (don't announce "the end").
Return ONLY the story text, nothing else.
"""
        if custom_notes:
            gen_prompt += f"\nAdditional style/focus guidance: {custom_notes}\n"

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": gen_prompt}],
            temperature=0.9,
        )
        disguised_story = resp.choices[0].message.content.strip()

    system_prompt = f"""You are {contact_name}'s friend, calling to tell them "something wild
that happened." You have a specific story to tell them, given below. Deliver
it conversationally, pausing for their reactions, and adapt naturally to
whatever they say (confusion, questions, "wait what", etc.) without
changing the actual plot events.

STORY TO TELL (do not deviate from these plot points, but you may
paraphrase the wording live and react in character):
---
{disguised_story}
---

After you finish telling the story and the listener has reacted at least
once, say something like: "Okay, I have to come clean -- that was actually
the plot of the movie '{movie_title}'. Sorry, that was a spoiler! Enjoy
watching it though." Then wrap up the call warmly.

Never reveal the movie title before that final reveal line.
"""

    first_message = (
        f"Hey {contact_name}, oh my god, you will not believe what just happened, "
        f"do you have a sec?"
    )

    return CallScript(system_prompt=system_prompt, first_message=first_message)