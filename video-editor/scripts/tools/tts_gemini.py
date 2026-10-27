# Optional voiceover: Gemini TTS over the Interactions REST API. Usage: tts_gemini.py lines.json outdir [voice] [model] [--retake l05,l07]
# lines.json: [{"id": "l01", "text": "..."}]. Writes all.wav (whole script, one call: free tier is 10/day); --retake adds <id>.wav per named line.
# Key: GEMINI_API_KEY, else the .env file named by ENV_FILE. Style: TTS_STYLE overrides the default narrator note.
import json, sys, os, time, base64, urllib.request, urllib.error
KEY = os.environ.get("GEMINI_API_KEY") or next(l.split("=", 1)[1].strip().strip("\"'") for l in open(os.environ["ENV_FILE"], encoding="utf-8") if l.startswith("GEMINI_API_KEY="))
STYLE = os.environ.get("TTS_STYLE") or ("Warm, natural narrator. Unhurried, measured pace with small pauses; "
                                        "clear diction; sincere, never salesy or over-excited.")
def tts(text, voice="Charon", model="gemini-3.8-flash-tts", style=STYLE, tries=5):
    body = {"model": model, "response_format": {"type": "audio"},
            "input": [{"type": "text", "text": text, "annotations": [{"type": "speech_metadata", "style": style}]}],
            "generation_config": {"speech_config": [{"voice": voice}]}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/interactions", json.dumps(body).encode(),
                                 {"x-goog-api-key": KEY, "Content-Type": "application/json"})
    for n in range(tries):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=180))
            return next(base64.b64decode(c["data"]) for s in d["steps"] for c in s.get("content", []) if c.get("type") == "audio")
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 503) or n == tries - 1: raise RuntimeError(f"TTS HTTP {e.code}: {e.read().decode()[:300]}")
            time.sleep(15 * (n + 1))
if __name__ == "__main__":
    retake = sys.argv[sys.argv.index("--retake") + 1].split(",") if "--retake" in sys.argv else []
    if retake: del sys.argv[sys.argv.index("--retake"):sys.argv.index("--retake") + 2]
    lines, out = json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else "Charon"; model = sys.argv[4] if len(sys.argv) > 4 else "gemini-3.8-flash-tts"
    os.makedirs(out, exist_ok=True)
    whole = " <long pause> ".join(l["text"] for l in lines)  # one take: consistent prosody across lines
    if not retake:
        audio = tts(whole, voice, model)  # written only after it succeeds, so a 429 leaves no empty file
        open(os.path.join(out, "all.wav"), "wb").write(audio); print("all.wav")
    for l in (l for l in lines if l["id"] in retake):
        audio = tts(l["text"], voice, model)
        open(os.path.join(out, f"{l['id']}.wav"), "wb").write(audio); print(l["id"])
