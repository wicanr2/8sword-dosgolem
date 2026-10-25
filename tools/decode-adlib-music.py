"""AdLib MUS/SND source decoder for spec 008 research and local HD arrangements.
No runtime integration or game-state edits.

Format facts: AdPlug mus.h/mus.cpp at commit in adplug-source.json.
Independent strict byte parser; no AdPlug implementation is incorporated.
"""
import collections
import hashlib
import json
from pathlib import Path
import struct
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def decode(path):
    raw = path.read_bytes()
    h = struct.unpack("<BBI30sBBIII8sBBH8s", raw[:70])
    major, minor, ident, title, tpb, meter, total, size, commands, pad, mode, bend, bpm, tail = h
    assert (major, minor, ident) == (1, 0, 0)
    assert size + 70 == len(raw) and tpb and bpm
    bank_path = path.with_name("S" + path.name[1:])
    bank = bank_path.read_bytes()
    vm, vn, count, offset = struct.unpack("<BBHH", bank[:6])
    assert (vm, vn, offset, len(bank)) == (1, 0, 6 + count * 9, 6 + count * 65)
    names = [bank[6 + i * 9:15 + i * 9].split(b"\0")[0].decode("ascii") for i in range(count)]
    events = []
    p, ticks, status = 70, 0, None
    # Every event is preceded by a delay. F8 contributes 240 ticks.
    while p < len(raw):
        delay = 0
        while raw[p] == 0xF8:
            delay += 240
            p += 1
        assert raw[p] < 0xF0
        ticks += delay + raw[p]
        p += 1
        start = p
        code = raw[p]
        if code >= 0x80:
            p += 1
        else:
            assert status is not None
            code = status
        if code == 0xFC:
            events.append(dict(offset=start, tick=ticks, status=code, data=[]))
            assert p == len(raw)
            break
        if code == 0xF0:
            end = raw.index(0xF7, p)
            data = list(raw[p:end + 1])
            assert len(data) == 5 and data[:2] == [0x7F, 0]
            assert data[2] or data[3]
            p = end + 1
        else:
            status = code
            kind = code & 0xF0
            assert kind in (0x80, 0x90, 0xA0, 0xB0, 0xC0, 0xD0, 0xE0)
            n = 1 if kind in (0xA0, 0xC0, 0xD0) else 2
            data = list(raw[p:p + n])
            assert len(data) == n and all(d < 128 for d in data)
            p += n
            if kind == 0xC0:
                assert data[0] < count
        events.append(dict(offset=start, tick=ticks, status=code, data=data))
    assert events[-1]["status"] == 0xFC
    result = dict(source=path.name, sha256=sha(raw), bank=bank_path.name,
                  bank_sha256=sha(bank), header=dict(ticks_per_beat=tpb, meter=meter,
                  total_ticks=total, data_bytes=size, command_count=commands,
                  rhythm_mode=mode, bend_semitones=bend, basic_bpm=bpm),
                  instruments=names, decoded_commands=len(events),
                  decoded_ticks=ticks, events=events)
    assert ticks == total, (path.name, ticks, total)
    return result


def main():
    source, out = map(Path, sys.argv[1:])
    assert out.stat().st_uid == 1000
    results = []
    for path in sorted(source.glob("M*.AY")):
        if path.read_bytes()[:36] != b"\x01" + bytes(35):
            continue
        r = decode(path)
        (out / (path.stem.lower() + "-events.json")).write_text(json.dumps(r, indent=2) + "\n")
        counts = collections.Counter(hex(e["status"] & 0xF0) for e in r["events"])
        summary = {k: v for k, v in r.items() if k != "events"}
        summary["event_kinds"] = dict(counts)
        summary["tempo_messages"] = [e for e in r["events"] if e["status"] == 0xF0]
        results.append(summary)
        print(path.name, r["decoded_commands"], r["decoded_ticks"], dict(counts), summary["tempo_messages"])
    (out / "source-catalog.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
