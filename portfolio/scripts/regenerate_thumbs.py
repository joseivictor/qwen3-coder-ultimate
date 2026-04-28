import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "videos.json"


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def duration_seconds(video):
    try:
        out = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video),
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return max(1.0, float(out))
    except Exception:
        return 8.0


def target_size(category):
    if category == "youtube":
        return 1280, 720
    return 1080, 1920


def make_thumb(video, thumb, category):
    duration = duration_seconds(video)
    # Frame after intro, but not too late for very short reels.
    at = min(max(duration * 0.28, 1.2), max(duration - 0.5, 1.0))
    width, height = target_size(category)
    thumb.parent.mkdir(parents=True, exist_ok=True)
    tmp = thumb.with_suffix(".tmp.jpg")
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        "eq=contrast=1.04:saturation=1.06:brightness=0.01"
    )
    run([
        "ffmpeg",
        "-y",
        "-ss",
        f"{at:.2f}",
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-vf",
        vf,
        "-q:v",
        "3",
        str(tmp),
    ])
    tmp.replace(thumb)


def main():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    videos = payload.get("videos", [])
    made = 0
    skipped = 0
    for item in videos:
        src = item.get("src")
        thumb = item.get("thumb")
        if not src or not thumb:
            skipped += 1
            continue
        video = ROOT / src
        out = ROOT / thumb
        if not video.exists():
            skipped += 1
            continue
        make_thumb(video, out, item.get("category"))
        made += 1
    print(f"generated={made} skipped={skipped}")


if __name__ == "__main__":
    main()
