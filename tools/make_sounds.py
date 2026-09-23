r"""Regenerate the synthesised chimes in assets/sounds (ping.wav, beep-modern.wav).

    .venv\Scripts\python.exe tools\make_sounds.py
"""
import array
import math
import wave
from pathlib import Path

RATE = 48000
OUT = Path(__file__).resolve().parent.parent / "assets" / "sounds"


def save(name, samples):
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(samples.tobytes())
    print("wrote", name, "%.1fs" % (len(samples) / RATE))


def bell(name, partials, dur, amp=0.55):
    """Additive bell. partials: (frequency Hz, level, decay seconds)."""
    n = int(dur * RATE)
    a = array.array("h", bytes(2 * n))
    for i in range(n):
        t = i / RATE
        v = sum(l * math.sin(2 * math.pi * f * t) * math.exp(-t / d) for f, l, d in partials)
        env = min(t / 0.004, 1.0) * min((dur - t) / 0.05, 1.0)
        a[i] = int(max(-1.0, min(1.0, v * amp * env)) * 32767)
    save(name, a)


def beep(name, notes, gap=0.06):
    """Electronic beep: notes are (frequency Hz, seconds), played in sequence; 0 Hz is a rest."""
    seg = []
    for f, d in notes:
        n = int(d * RATE)
        for i in range(n):
            if f == 0:
                seg.append(0)
                continue
            tone = 0.7 * math.sin(2 * math.pi * f * i / RATE) + 0.3 * math.sin(2 * math.pi * 2 * f * i / RATE)
            env = min(i / (0.003 * RATE), 1) * min((n - i) / (0.02 * RATE), 1)
            seg.append(int(0.4 * 32767 * tone * env))
        seg += [0] * int(gap * RATE)
    save(name, array.array("h", seg))


if __name__ == "__main__":
    f0 = 1760.0   # a clean glass-like ping: fundamental plus inharmonic bell partials
    bell("ping.wav", [(f0, 1.0, 0.9), (f0 * 2.76, 0.35, 0.45), (f0 * 5.4, 0.15, 0.25), (f0 * 0.5, 0.25, 1.2)], 2.6)
    beep("beep-modern.wav", [(880, 0.11), (1174.7, 0.11), (1568, 0.22)])   # a rising three-note beep
    # Digital alarm clock: two bursts of four short high beeps.
    burst = [(2093, 0.07), (0, 0.05)] * 4 + [(0, 0.28)]
    beep("alarm-beep.wav", burst * 2, gap=0.0)
