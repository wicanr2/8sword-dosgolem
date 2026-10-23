#!/usr/bin/env python3
"""Compare a parsed source score with a normal dosgolem OPL capture.

First-pass onsets only. Timing follows spec 008's hardware-spec approximation.
Run inside the pinned music Docker image; no original data is modified.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(args):
    source = json.loads(args.events.read_text())
    receipt = json.loads(args.receipt.read_text())
    assert receipt["normal_input_replay"] and not receipt["snapshot_loaded"]
    assert receipt["cycles_per_ms"] == 3000 and not receipt["unimplemented"]
    assert not receipt["text"]["Errors"] and receipt["text"]["MissingGlyphs"] == 0
    header = source["header"]
    assert header["rhythm_mode"] in (0, 1)
    melodic_count = 6 if header["rhythm_mode"] else 9
    registers = [0] * 256
    actual = {c: [] for c in range(11)}
    with args.opl.open() as stream:
        for line in stream:
            write = json.loads(line)
            assert write["Bank"] == 0
            reg, value = write["Reg"], write["Val"]
            previous, registers[reg] = registers[reg], value
            if write["Cycles"] < receipt["start_cycles"]:
                continue
            if 0xB0 <= reg < 0xB0 + melodic_count and value & 32 and not previous & 32:
                c = reg - 0xB0
                frequency = registers[0xA0+c] | ((value & 3) << 8)
                hz = 49716 * frequency * 2 ** (((value >> 2) & 7) - 20)
                actual[c].append((write["Cycles"], 69 + 12 * math.log2(hz/440)))
            if header["rhythm_mode"] and reg == 0xBD and value & 32:
                for c, bit in {6: 16, 7: 8, 8: 4, 9: 2, 10: 1}.items():
                    if value & bit and not previous & bit:
                        actual[c].append((write["Cycles"], None))
    expected = {c: [] for c in range(11)}
    bends = [0] * 11
    tempo, last, seconds = header["basic_bpm"], 0, Fraction(0)
    for event in source["events"]:
        seconds += Fraction((event["tick"]-last)*60, header["ticks_per_beat"]*tempo)
        last = event["tick"]
        status, data = event["status"], event["data"]
        c, kind = status & 15, status & 0xF0
        if status == 0xF0:
            tempo = header["basic_bpm"]*data[2] + ((header["basic_bpm"]*data[3]) >> 7)
        elif kind == 0xE0:
            bends[c] = (data[0] + data[1]*128 - 8192)/8192 * header["bend_semitones"]
        elif kind == 0x90 and data[1]:
            expected[c].append((float(seconds), data[0] + bends[c]))
    assert last == header["total_ticks"]
    # Existing capture contract selects an idle music-appreciation entry.
    # Choose a voice with an onset at tick zero to avoid offsetting its delay.
    anchors = [c for c, notes in expected.items() if notes and notes[0][0] == 0]
    assert anchors, "需要起始 tick 有音符的原曲"
    anchor = min(anchors)
    first = actual[anchor][0][0]
    rows = []
    for c, notes in expected.items():
        if not notes:
            continue
        observed = actual[c]
        assert len(observed) >= len(notes), (c, len(observed), len(notes))
        timing = [(a[0]-first)/3000000-e[0] for a, e in zip(observed, notes)]
        assert max(map(abs, timing)) < 0.05, (c, min(timing), max(timing))
        row = dict(voice=c, onsets=len(notes), timing_min_seconds=min(timing),
                   timing_max_seconds=max(timing))
        if c < melodic_count:
            pitch = [a[1]-e[1] for a, e in zip(observed, notes)]
            assert max(map(abs, pitch)) < 0.1, (c, min(pitch), max(pitch))
            row["pitch_max_abs_semitones"] = max(map(abs, pitch))
        rows.append(row)
    assert len(actual[anchor]) > len(expected[anchor]), "擷取未涵蓋完整首輪及循環"
    loop = (actual[anchor][len(expected[anchor])][0]-first)/3000000
    return dict(status="passed", source=source["source"], source_sha256=source["sha256"],
                bank_sha256=source["bank_sha256"], normal_cold_input=True,
                snapshot_loaded=False, source_duration_seconds=float(seconds),
                first_note_cycles=first, observed_loop_seconds=loop, voices=rows,
                melodic_onsets=sum(len(expected[c]) for c in range(melodic_count)),
                rhythm_onsets=sum(len(expected[c]) for c in range(melodic_count, 11)),
                inputs={str(p): digest(p) for p in (args.events, args.receipt, args.opl)},
                tool_sha256=digest(Path(__file__)),
                source_pitch_contract="49716*fnum*2**(block-20); source pitch-bend range",
                percussion_contract="YM3812 BD bits: voices 6..10 = 16,8,4,2,1",
                claim="First-pass onsets, melodic pitches and rhythm triggers within fixed bounds; hardware-spec approximation, not cycle-exact parity")


def main():
    parser = argparse.ArgumentParser()
    for name in ("events", "receipt", "opl", "out"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists(), "拒絕覆寫既有核對收據"
    report = audit(args)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
