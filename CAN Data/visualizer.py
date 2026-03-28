import re
import sys
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

BITRATE = 1000000
WINDOW = 0.1

line_re = re.compile(r"^\s*([\d.]+)\s+\d+\s+([0-9A-Fa-f]+)\s+\w+\s+d\s+(\d+)")

filename = sys.argv[1]

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

if not times:
    print("no can frames found")
    raise SystemExit

duration = max(times) - min(times)
total_messages = len(ids)
id_counts = Counter(ids)

max_bits_per_window = BITRATE * WINDOW
x = []
y = []

for bucket in sorted(bits_per_window):
    t0 = bucket * WINDOW
    load = 100 * bits_per_window[bucket] / max_bits_per_window
    x.append(t0)
    y.append(load)

avg_load = sum(y) / len(y)
max_load = max(y)

print("file:", filename)
print("total messages:", total_messages)
print("avg messages/sec:", round(total_messages / duration, 2))
print("avg bus load:", round(avg_load, 2), "%")
print("max bus load:", round(max_load, 2), "%")
print()

print("top 5 can ids")
for can_id, count in id_counts.most_common(5):
    print(f"{can_id}: {count / duration:.2f} msg/s")

plt.plot(x, y)
plt.axhline(40, linestyle="--", label="40% target")
plt.xlabel("Time (s)")
plt.ylabel("Bus load (%)")
plt.title("CAN bus load over time")
plt.legend()
plt.show()

labels = [can_id for can_id, count in id_counts.most_common()]
rates = [count / duration for can_id, count in id_counts.most_common()]

plt.figure(figsize=(12, 6))
plt.bar(labels, rates)
plt.xlabel("CAN ID")
plt.ylabel("Messages per second")
plt.title("Message rate by CAN ID")
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()
