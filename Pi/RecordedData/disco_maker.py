#!/usr/bin/env python3
"""
generate_telemetry.py  — FRACTIONAL HOURS EDITION

Create timestamp-angle telemetry text files to drive ISS Mimic motors.
The first column is *fractional hours* (e.g., 1 second ≈ 0.000278 hr),
the second column is the motor angle in degrees.

Examples:
  # 24 minutes of a 90/180 step pattern, 1 Hz (1 s) cadence:
  python generate_telemetry.py --pattern stepseq --seq 90 180 --duration 1440 --dt 1 -o S_step.txt

  # 10 minutes of repeating 0,45,90,135 at 1 Hz:
  python generate_telemetry.py --pattern stepseq --seq 0 45 90 135 --duration 600 --dt 1 -o S_quads.txt

  # 5 minutes of a sine wave, 30 s period, ±90°, quantized to nearest 5° at 2 Hz:
  python generate_telemetry.py --pattern sine --amp 90 --period 30 --duration 300 --dt 0.5 --quant 5 -o S_sine.txt

  # Multi-segment "choreography" from a JSON program:
  python generate_telemetry.py --program program.json --dt 1 -o choreo.txt

program.json schema (list of segments in order):
[
  {"type": "hold",    "angle": 0,               "duration": 60},
  {"type": "stepseq", "seq": [90,180],          "duration": 600},
  {"type": "stepseq", "seq": [0,45,90,135],     "duration": 300},
  {"type": "sine",    "amp": 90, "offset": 0, "period": 120, "duration": 600, "quant": 5},
  {"type": "ramp",    "start": -180, "stop": 180, "duration": 120},
  {"type": "triangle","low": -120, "high": 120, "period": 60, "duration": 180},
  {"type": "saw",     "low": -180, "high": 180, "period": 45, "duration": 180},
  {"type": "random",  "low": -235, "high": 235, "duration": 120, "seed": 42}
]

Notes:
- Time units:
  * --dt is in seconds and becomes fractional HOURS in the output.
  * --duration in single-pattern mode is in seconds.
  * For --program, each segment's "duration" is in seconds.
- Angles default to integers. Use --angle-decimals to keep fractional degrees.
- Quantization (--quant N) snaps the angle to the nearest N degrees.
- Clamp with --min-angle/--max-angle, or wrap with --wrap (-180..180 or 0..360).
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

SECONDS_PER_HOUR = 3600.0

def sec_to_hour_fraction(t_s: float) -> float:
    return t_s / SECONDS_PER_HOUR

def quantize(val: float, q: Optional[float]) -> float:
    if q and q > 0:
        return round(val / q) * q
    return val

def clamp(val: float, lo: Optional[float], hi: Optional[float]) -> float:
    if lo is not None and val < lo:
        return lo
    if hi is not None and val > hi:
        return hi
    return val

def wrap_angle(val: float, mode: Optional[str]) -> float:
    if not mode:
        return val
    if mode == "-180..180":
        # Wrap to (-180, 180]
        v = (val + 180.0) % 360.0 - 180.0
        if v == -180.0:
            v = 180.0
        return v
    if mode == "0..360":
        return val % 360.0
    raise ValueError(f"Unknown wrap mode: {mode}")

def format_angle(val: float, decimals: int) -> str:
    return f"{val:.{decimals}f}" if decimals > 0 else f"{int(round(val))}"

def iter_times(duration_s: float, dt_s: float, t0_s: float = 0.0, include_zero: bool = False) -> Iterable[float]:
    """Yield sample times [s] from t0 upward at steps of dt.
       By default the first sample is at t0+dt (matching many logs).
       Use include_zero=True to include a t==t0 line first."""
    if dt_s <= 0:
        raise ValueError("--dt must be > 0")
    n = max(1, int(round(duration_s / dt_s)))
    if include_zero:
        yield t0_s
    start = 0 if include_zero else 1
    for i in range(start, n + 1):
        yield t0_s + i * dt_s

# ---------------------- Pattern Generators ----------------------

def gen_hold(angle: float, duration_s: float, dt_s: float, t0_s: float, include_zero=False) -> List[Tuple[float,float]]:
    return [(t, angle) for t in iter_times(duration_s, dt_s, t0_s, include_zero)]

def gen_stepseq(seq: Sequence[float], duration_s: float, dt_s: float, t0_s: float, include_zero=False) -> List[Tuple[float,float]]:
    out = []
    if not seq:
        return out
    for idx, t in enumerate(iter_times(duration_s, dt_s, t0_s, include_zero)):
        out.append((t, seq[idx % len(seq)]))
    return out

def gen_sine(amp: float, offset: float, period_s: float, duration_s: float, dt_s: float, t0_s: float, include_zero=False) -> List[Tuple[float,float]]:
    out = []
    if period_s <= 0:
        raise ValueError("sine period must be > 0")
    for t in iter_times(duration_s, dt_s, t0_s, include_zero):
        theta = 2.0 * math.pi * ((t - t0_s) / period_s)
        out.append((t, offset + amp * math.sin(theta)))
    return out

def gen_ramp(start: float, stop: float, duration_s: float, dt_s: float, t0_s: float, bounce: bool=False, include_zero=False) -> List[Tuple[float,float]]:
    out = []
    if duration_s <= 0:
        return out
    if bounce:
        half = duration_s / 2.0
        out += gen_ramp(start, stop, half, dt_s, t0_s, bounce=False, include_zero=include_zero)
        last_t = out[-1][0] if out else t0_s
        out += gen_ramp(stop, start, half, dt_s, last_t, bounce=False, include_zero=False)
        return out
    for t in iter_times(duration_s, dt_s, t0_s, include_zero):
        u = (t - t0_s) / duration_s if duration_s != 0 else 0.0
        out.append((t, start + (stop - start) * u))
    return out

def gen_triangle(low: float, high: float, period_s: float, duration_s: float, dt_s: float, t0_s: float, include_zero=False) -> List[Tuple[float,float]]:
    if period_s <= 0:
        raise ValueError("triangle period must be > 0")
    mid = (low + high) / 2.0
    amp = (high - low) / 2.0
    def tri(u):
        return (2.0 / math.pi) * math.asin(math.sin(2.0 * math.pi * u))
    out = []
    for t in iter_times(duration_s, dt_s, t0_s, include_zero):
        u = (t - t0_s) / period_s
        out.append((t, mid + amp * tri(u)))
    return out

def gen_saw(low: float, high: float, period_s: float, duration_s: float, dt_s: float, t0_s: float, include_zero=False) -> List[Tuple[float,float]]:
    if period_s <= 0:
        raise ValueError("saw period must be > 0")
    span = high - low
    out = []
    for t in iter_times(duration_s, dt_s, t0_s, include_zero):
        u = ((t - t0_s) / period_s) % 1.0
        out.append((t, low + span * u))
    return out

def gen_random(low: float, high: float, duration_s: float, dt_s: float, t0_s: float, seed: Optional[int]=None, include_zero=False) -> List[Tuple[float,float]]:
    rng = random.Random(seed)
    out = []
    for t in iter_times(duration_s, dt_s, t0_s, include_zero):
        out.append((t, rng.uniform(low, high)))
    return out

# ---------------------- Composition ----------------------

@dataclass
class PostProcess:
    quant: Optional[float]
    clamp_lo: Optional[float]
    clamp_hi: Optional[float]
    wrap: Optional[str]
    angle_decimals: int

    def apply(self, angle: float) -> float:
        angle = quantize(angle, self.quant)
        angle = clamp(angle, self.clamp_lo, self.clamp_hi)
        angle = wrap_angle(angle, self.wrap)
        if self.angle_decimals == 0:
            angle = round(angle)
        else:
            angle = round(angle, self.angle_decimals)
        return angle

def write_pairs(pairs: List[Tuple[float,float]], out_path: str, angle_decimals: int):
    with open(out_path, "w", encoding="utf-8") as f:
        for t_s, ang in pairs:
            hour_frac = sec_to_hour_fraction(t_s)
            f.write(f"{hour_frac:.6f} {format_angle(ang, angle_decimals)}\n")

def build_from_program(program: List[dict], dt_s: float, post: PostProcess, include_zero: bool=False) -> List[Tuple[float,float]]:
    t0 = 0.0
    all_pairs: List[Tuple[float,float]] = []
    for seg in program:
        typ = seg.get("type")
        duration = float(seg["duration"])
        if typ == "hold":
            angle = float(seg["angle"])
            pairs = gen_hold(angle, duration, dt_s, t0, include_zero=include_zero and not all_pairs)
        elif typ == "stepseq":
            seq = list(map(float, seg["seq"]))
            pairs = gen_stepseq(seq, duration, dt_s, t0, include_zero=include_zero and not all_pairs)
        elif typ == "sine":
            amp = float(seg["amp"]); offset = float(seg.get("offset", 0.0)); period = float(seg["period"])
            pairs = gen_sine(amp, offset, period, duration, dt_s, t0, include_zero=include_zero and not all_pairs)
        elif typ == "ramp":
            start = float(seg["start"]); stop = float(seg["stop"]); bounce = bool(seg.get("bounce", False))
            pairs = gen_ramp(start, stop, duration, dt_s, t0, bounce=bounce, include_zero=include_zero and not all_pairs)
        elif typ == "triangle":
            low = float(seg["low"]); high = float(seg["high"]); period = float(seg["period"])
            pairs = gen_triangle(low, high, period, duration, dt_s, t0, include_zero=include_zero and not all_pairs)
        elif typ == "saw":
            low = float(seg["low"]); high = float(seg["high"]); period = float(seg["period"])
            pairs = gen_saw(low, high, period, duration, dt_s, t0, include_zero=include_zero and not all_pairs)
        elif typ == "random":
            low = float(seg["low"]); high = float(seg["high"]); seed = seg.get("seed")
            pairs = gen_random(low, high, duration, dt_s, t0, seed=seed, include_zero=include_zero and not all_pairs)
        else:
            raise ValueError(f"Unknown segment type: {typ}")
        pairs = [(t, post.apply(a)) for t, a in pairs]
        all_pairs.extend(pairs)
        t0 = all_pairs[-1][0] if all_pairs else t0
    return all_pairs

def main():
    p = argparse.ArgumentParser(description="Generate ISS Mimic telemetry (fractional-hour timestamp, angle).")
    # Top-level
    p.add_argument("-o", "--out", required=True, help="Output .txt path")
    p.add_argument("--dt", type=float, default=1.0, help="Sample period, seconds (default: 1)")
    p.add_argument("--angle-decimals", type=int, default=0, help="Angle decimals (default: 0 = integers)")
    p.add_argument("--quant", type=float, default=None, help="Quantize angle to nearest N degrees")
    p.add_argument("--min-angle", type=float, default=None, help="Clamp: minimum angle")
    p.add_argument("--max-angle", type=float, default=None, help="Clamp: maximum angle")
    p.add_argument("--wrap", choices=["-180..180", "0..360"], default=None, help="Wrap angle range (applied after clamp/quant)")
    p.add_argument("--include-zero", action="store_true", help="Include a 0.000000 timestamp as the first line")

    # Single-pattern mode
    sp = p.add_argument_group("single-pattern mode")
    sp.add_argument("--pattern", choices=["hold","stepseq","sine","ramp","triangle","saw","random"], help="Pattern to generate")
    sp.add_argument("--duration", type=float, help="Pattern duration, seconds")
    sp.add_argument("--angle", type=float, help="For hold: angle")
    sp.add_argument("--seq", nargs="+", type=float, help="For stepseq: list of angles, e.g. --seq 0 45 90 135")
    sp.add_argument("--amp", type=float, help="For sine: amplitude")
    sp.add_argument("--offset", type=float, default=0.0, help="For sine: offset (center)")
    sp.add_argument("--period", type=float, help="For sine/triangle/saw: period in seconds")
    sp.add_argument("--start", type=float, help="For ramp: start angle")
    sp.add_argument("--stop", type=float, help="For ramp: stop angle")
    sp.add_argument("--bounce", action="store_true", help="For ramp: go up then back down")
    sp.add_argument("--low", type=float, help="For triangle/saw/random: low angle")
    sp.add_argument("--high", type=float, help="For triangle/saw/random: high angle")
    sp.add_argument("--seed", type=int, help="For random: RNG seed")

    # Program mode
    p.add_argument("--program", type=str, help="Path to JSON program (list of segments)")

    args = p.parse_args()

    post = PostProcess(
        quant=args.quant,
        clamp_lo=args.min_angle,
        clamp_hi=args.max_angle,
        wrap=args.wrap,
        angle_decimals=args.angle_decimals,
    )

    if args.program:
        import json
        with open(args.program, "r", encoding="utf-8") as f:
            program = json.load(f)
        pairs = build_from_program(program, args.dt, post, include_zero=args.include_zero)

    else:
        if not args.pattern or args.duration is None:
            p.error("Either --program or ( --pattern and --duration ) is required.")
        typ = args.pattern
        dur = args.duration
        inc0 = args.include_zero
        if typ == "hold":
            if args.angle is None:
                p.error("--angle is required for hold")
            pairs = gen_hold(args.angle, dur, args.dt, 0.0, include_zero=inc0)
        elif typ == "stepseq":
            if not args.seq:
                p.error("--seq is required for stepseq")
            pairs = gen_stepseq(args.seq, dur, args.dt, 0.0, include_zero=inc0)
        elif typ == "sine":
            if args.amp is None or args.period is None:
                p.error("--amp and --period are required for sine")
            pairs = gen_sine(args.amp, args.offset, args.period, dur, args.dt, 0.0, include_zero=inc0)
        elif typ == "ramp":
            if args.start is None or args.stop is None:
                p.error("--start and --stop are required for ramp")
            pairs = gen_ramp(args.start, args.stop, dur, args.dt, 0.0, bounce=args.bounce, include_zero=inc0)
        elif typ == "triangle":
            if args.low is None or args.high is None or args.period is None:
                p.error("--low --high --period are required for triangle")
            pairs = gen_triangle(args.low, args.high, args.period, dur, args.dt, 0.0, include_zero=inc0)
        elif typ == "saw":
            if args.low is None or args.high is None or args.period is None:
                p.error("--low --high --period are required for saw")
            pairs = gen_saw(args.low, args.high, args.period, dur, args.dt, 0.0, include_zero=inc0)
        elif typ == "random":
            if args.low is None or args.high is None:
                p.error("--low and --high are required for random")
            pairs = gen_random(args.low, args.high, dur, args.dt, 0.0, seed=args.seed, include_zero=inc0)
        else:
            p.error(f"Unknown pattern {typ}")

        pairs = [(t, post.apply(a)) for t, a in pairs]

    write_pairs(pairs, args.out, post.angle_decimals)

if __name__ == "__main__":
    main()
