import re
import sys
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

BITRATE = 1000000
WINDOW = 0.1

line_re = re.compile(r"^\s*([\d.]+)\s+\d+\s+([0-9A-Fa-f]+)\s+\w+\s+d\s+(\d+)")

BUS_COLORS = ["tab:blue", "tab:orange"]


def parse_file(filename):
    times = []
    ids = []
    bits_per_window = defaultdict(int)

    with open(filename, "r", errors="ignore") as f:
        for line in f:
            m = line_re.match(line.strip())
            if not m:
                continue

            t, can_id, dlc = m.groups()
            t = float(t)
            can_id = can_id.upper()
            dlc = int(dlc)

            times.append(t)
            ids.append(can_id)

            bits = 47 + 8 * dlc
            bucket = int(t / WINDOW)
            bits_per_window[bucket] += bits

    return times, ids, bits_per_window


filenames = sys.argv[1:]
if not filenames:
    print("usage: visualizer.py <bus1.asc> [bus2.asc ...]")
    raise SystemExit

max_bits_per_window = BITRATE * WINDOW

fig_load, ax_load = plt.subplots()
ax_load.axhline(40, linestyle="--", color="gray", label="40% target")

for filename, color in zip(filenames, BUS_COLORS):
    times, ids, bits_per_window = parse_file(filename)

    if not times:
        print(f"no CAN frames found in {filename}")
        continue

    duration = max(times) - min(times)
    total_messages = len(ids)
    id_counts = Counter(ids)

    x = []
    y = []
    for bucket in sorted(bits_per_window):
        t0 = bucket * WINDOW
        load = 100 * bits_per_window[bucket] / max_bits_per_window
        x.append(t0)
        y.append(load)

    avg_load = sum(y) / len(y)
    max_load = max(y)

    label = filename.split("/")[-1]
    ax_load.plot(x, y, color=color, label=label)

    print(f"file: {filename}")
    print(f"  total messages: {total_messages}")
    print(f"  avg messages/sec: {round(total_messages / duration, 2)}")
    print(f"  avg bus load: {round(avg_load, 2)} %")
    print(f"  max bus load: {round(max_load, 2)} %")
    print()
    print(f"  top 5 CAN IDs:")
    for can_id, count in id_counts.most_common(5):
        print(f"    {can_id}: {count / duration:.2f} msg/s")
    print()

    # Per-file message rate bar chart
    bar_labels = [can_id for can_id, count in id_counts.most_common()]
    rates = [count / duration for can_id, count in id_counts.most_common()]

    fig_bar, ax_bar = plt.subplots(figsize=(12, 6))
    ax_bar.bar(bar_labels, rates, color=color)
    ax_bar.set_xlabel("CAN ID")
    ax_bar.set_ylabel("Messages per second")
    ax_bar.set_title(f"Message rate by CAN ID — {label}")
    plt.xticks(rotation=90)
    plt.tight_layout()

ax_load.set_xlabel("Time (s)")
ax_load.set_ylabel("Bus load (%)")
ax_load.set_title("CAN bus load over time")
ax_load.legend()
plt.show()
