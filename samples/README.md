# Sample voice notes

Real recordings, so the demo works without a microphone.

| File | Language | What it says | Household | Expected result |
| --- | --- | --- | --- | --- |
| `sample_tamil.ogg` | Tamil | Our family is 7 people in all, everyone is vegetarian | 2, Iyer Family | 7 guests, veg |
| `sample_hinglish.ogg` | Hinglish | From the Sharma family, me and Sharma uncle, 3 people in total, all pure vegetarian | 1, Sharma Parivar | 3 guests, veg |
| `intro_video.mp4` | | Intro video, shown on the demo stage | | |

Run one:

```bash
curl -X POST "localhost:8000/api/rsvp/voice/sample/sample_tamil?household_id=2"
```

To add another, drop in any ogg, m4a, mp3, wav or webm file under 30 seconds. Its name becomes
the sample's name. Only add recordings whose speaker agreed to it: this repository is public.
