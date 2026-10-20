# Record a structured cue from Lyria RealTime by steering it on a timeline. Usage: lyria_rt_cue.py out.wav cue.json
# cue.json: {"bpm": 100, "seconds": 56, "steps": [{"t": 0, "prompts": [["warm analog pads", 1.0]], "density": 0.2, "brightness": 0.4}, ...]}
import asyncio, json, os, sys, wave
from google import genai
from google.genai import types
KEY = os.environ.get("GEMINI_API_KEY") or next(l.split("=", 1)[1].strip().strip("\"'") for l in open(os.environ["ENV_FILE"], encoding="utf-8") if l.startswith("GEMINI_API_KEY="))  # env var, else the netigen-draft .env named by ENV_FILE
SR, BPS = 48000, 48000 * 2 * 2  # 48 kHz stereo 16-bit
async def main(out, cue):
    client = genai.Client(api_key=KEY, http_options={"api_version": "v1beta"})
    buf, steps = bytearray(), sorted(cue["steps"], key=lambda s: s["t"])
    async def apply(s, st):
        await s.set_weighted_prompts(prompts=[types.WeightedPrompt(text=t, weight=w) for t, w in st["prompts"]])
        await s.set_music_generation_config(config=types.LiveMusicGenerationConfig(
            bpm=cue["bpm"], scale=getattr(types.Scale, cue.get("scale", "D_MAJOR_B_MINOR")), guidance=st.get("guidance", 4.0),
            density=st.get("density", 0.4), brightness=st.get("brightness", 0.5), mute_drums=st.get("mute_drums", False)))
    async with client.aio.live.music.connect(model="models/lyria-realtime-exp") as s:
        await apply(s, steps.pop(0)); await s.play()
        async for m in s.receive():  # steps fire on received audio time, so the cue lines up with the file
            for c in (m.server_content.audio_chunks if m.server_content and m.server_content.audio_chunks else []): buf.extend(c.data)
            while steps and len(buf) / BPS >= steps[0]["t"]: await apply(s, steps.pop(0))
            if len(buf) >= cue["seconds"] * BPS: break
        await s.stop()
    with wave.open(out, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(bytes(buf[:int(cue["seconds"] * BPS)]))
    print(out, len(buf) / BPS, "s")
asyncio.run(main(sys.argv[1], json.load(open(sys.argv[2], encoding="utf-8"))))
