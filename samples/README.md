# Sample voice notes

Two short recordings so the demo works without a microphone.
Any common audio format works (m4a, mp3, wav, ogg, webm). Keep each under 30 seconds.

| File name | Language | What to say | Household |
| --- | --- | --- | --- |
| `hinglish` | Hinglish | "Haan beta, main aur Sharma uncle ke teen log aa rahe hain, pure veg" | 1, Sharma Parivar (invited 6) |
| `tamil` or `kannada` | Tamil or Kannada | Your own line: you are coming, how many people, veg or non-veg | 2, Iyer Family (Tamil, invited 8) or 3, Gowda Kutumba (Kannada, invited 10) |

Only the name before the dot matters, so `hinglish.m4a` and `hinglish.mp3` both work.
Keep one file per name.

Run one:

```bash
curl -X POST "localhost:8000/api/rsvp/voice/sample/hinglish?household_id=1"
```

Expected for `hinglish`: attending, headcount 4, plus_ones 0, diet veg.

Use your own voice, or a recording whose speaker agreed to it being public: this repository is public.
