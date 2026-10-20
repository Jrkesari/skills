# Records a page with CDP screencast (JPEG frames + timestamps) and encodes a constant-fps mp4.
import base64, json, os, subprocess, time
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
FF = os.path.join(ROOT, r"bin\ffmpeg.exe")
HIDE = "nextjs-portal{display:none!important}"

class Recorder:
    def __init__(self, page, out_dir, quality=92, max_side=None):
        self.page, self.out, self.q = page, out_dir, quality
        os.makedirs(out_dir, exist_ok=True)
        self.cdp = page.context.new_cdp_session(page)
        self.frames = []
        self.cdp.on("Page.screencastFrame", self._on)
        self.max_side = max_side
    def _on(self, ev):
        n = len(self.frames)
        path = os.path.join(self.out, f"f{n:06d}.jpg")
        with open(path, "wb") as f:
            f.write(base64.b64decode(ev["data"]))
        self.frames.append((ev["metadata"]["timestamp"], path))
        try:
            self.cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        except Exception:
            pass
    def start(self):
        args = {"format": "jpeg", "quality": self.q, "everyNthFrame": 1}
        if self.max_side:
            args.update(maxWidth=self.max_side, maxHeight=self.max_side)
        self.cdp.send("Page.startScreencast", args)
    def stop(self, mp4, fps=30):
        self.cdp.send("Page.stopScreencast")
        time.sleep(0.3)
        lst = os.path.join(self.out, "list.txt")
        with open(lst, "w") as f:
            for i, (t, p) in enumerate(self.frames):
                d = (self.frames[i + 1][0] - t) if i + 1 < len(self.frames) else 1 / fps
                f.write(f"file '{p}'\nduration {max(d, 0.001):.4f}\n")
            f.write(f"file '{self.frames[-1][1]}'\n")
        subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                        "-vf", f"fps={fps},format=yuv420p", "-c:v", "libx264", "-crf", "12", "-preset", "medium", mp4], check=True)
        span = self.frames[-1][0] - self.frames[0][0]
        return {"frames": len(self.frames), "seconds": round(span, 2), "fps": round(len(self.frames) / max(span, 1e-3), 1)}
