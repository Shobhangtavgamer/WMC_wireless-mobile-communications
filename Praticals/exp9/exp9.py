import os
import csv
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# Constants and Sample Data
# ---------------------------------------------------------
WAVELENGTH_M = 0.125  # 12.5 cm at 2.4 GHz

# Sample data matching Section 5 (Step 4) and Section 8
SAMPLE_SCAN_CSV = """Position_cm,RSSI_Indoor_dBm,RSSI_Outdoor_dBm
0,-50,-57
10,-56,-58
20,-47,-58
30,-60,-59
40,-51,-59
50,-58,-60
"""

SAMPLE_STATIONARY_CSV = """Time_s,RSSI_dBm
0,-51
5,-52
10,-50
15,-54
20,-52
25,-53
30,-51
35,-55
40,-52
45,-54
50,-53
55,-52
"""


# ---------------------------------------------------------
# Step 1: Data Input Functions
# ---------------------------------------------------------
def load_scan(fname="scan.csv"):
    if not os.path.exists(fname):
        open(fname, "w").write(SAMPLE_SCAN_CSV)
    pos, indoor, outdoor = [], [], []
    for r in csv.reader(open(fname)):
        if not r or r[0].startswith("Position"):
            continue
        pos.append(float(r[0]))
        indoor.append(float(r[1]))
        outdoor.append(float(r[2]) if len(r) > 2 and r[2].strip() else np.nan)
    return np.array(pos), np.array(indoor), np.array(outdoor)


def load_stationary(fname="stationary.csv"):
    if not os.path.exists(fname):
        open(fname, "w").write(SAMPLE_STATIONARY_CSV)
    time_s, rssi = [], []
    for r in csv.reader(open(fname)):
        if not r or r[0].startswith("Time"):
            continue
        time_s.append(float(r[0]))
        rssi.append(float(r[1]))
    return np.array(time_s), np.array(rssi)


# ---------------------------------------------------------
# Step 2: Metrics Quantifying Multipath
# ---------------------------------------------------------
def roughness(r):
    # Mean absolute step-to-step change: smooth traces -> small, multipath traces -> large
    valid = r[~np.isnan(r)]
    return float(np.mean(np.abs(np.diff(valid))))


def fade_depth(r):
    # Peak-to-null swing, dB
    valid = r[~np.isnan(r)]
    return float(valid.max() - valid.min())


def reversals(r):
    # % of steps where RSSI got STRONGER while moving further away
    valid = r[~np.isnan(r)]
    d = np.diff(valid)
    return 100.0 * float(np.sum(d > 0)) / d.size


# ---------------------------------------------------------
# Step 3: Two-Ray Theoretical Pattern
# ---------------------------------------------------------
def two_ray_pattern(pos_cm, start_extra_cm=0.0):
    lam_cm = WAVELENGTH_M * 100.0  # 12.5 cm at 2.4 GHz
    extra = start_extra_cm + 2.0 * pos_cm  # extra path grows as you move
    phase = 2 * np.pi * extra / lam_cm  # phase difference
    amp = np.abs(1.0 + np.exp(1j * phase))  # 0 (null) .. 2 (peak)
    return 20.0 * np.log10(np.clip(amp / 2.0, 1e-3, 1.0))  # dB relative to the peak


# ---------------------------------------------------------
# Step 4: Text Report
# ---------------------------------------------------------
def print_report(pos, indoor, outdoor, time_s, stat_rssi):
    r_ind = roughness(indoor)
    r_out = roughness(outdoor)
    f_ind = fade_depth(indoor)
    f_out = fade_depth(outdoor)
    rev_ind = reversals(indoor)
    rev_out = reversals(outdoor)

    print("=== Multipath fading survey ===")
    print("Wavelength at 2.4 GHz = 12.5 cm -> peaks/nulls repeat about every 6.2cm\n")
    print(
        f"{'Trace':<10} | {'Mean (dBm)':<11} | {'Spread(dB)':<11} | {'Roughness (dB)':<15} | {'FadeDepth(dB)':<14} | {'Reversals'}")
    print("-" * 75)
    print(
        f"{'Indoor':<10} | {np.mean(indoor):<11.1f} | {np.std(indoor):<11.1f} | {r_ind:<15.1f} | {f_ind:<14.1f} | {rev_ind:.0f}%")
    print(
        f"{'Outdoor':<10} | {np.nanmean(outdoor):<11.1f} | {np.nanstd(outdoor):<11.1f} | {r_out:<15.1f} | {f_out:<14.1f} | {rev_out:.0f}%")

    stat_mean = np.mean(stat_rssi)
    stat_spread = stat_rssi.max() - stat_rssi.min()
    print(f"\nStanding still: mean {stat_mean:.1f} dBm, but the reading still varied by {stat_spread:.0f} dB")
    print("without moving at all (people/doors changing the reflections).\n")

    ratio = r_ind / r_out if r_out > 0 else 0
    print("HEADLINE: the indoor trace is {:.1f}x rougher than outdoors ({:.1f} vs {:.1f} dB per step),".format(ratio,
                                                                                                               r_ind,
                                                                                                               r_out))
    print(f"with a {f_ind:.0f} dB peak-to-null swing over just {int(pos[-1] - pos[0])} cm, and RSSI got STRONGER on")
    print(f"{rev_ind:.0f}% of steps taken AWAY from the transmitter -- impossible under distance")
    print("loss alone. That is multipath fading.\n")


# ---------------------------------------------------------
# Step 5: Plotting Functions
# ---------------------------------------------------------
def plot_scan(pos, indoor, outdoor):
    plt.figure(figsize=(8, 4.5))
    plt.plot(pos, indoor, 'o-', color='#3b3b3b', label='Indoor (many reflectors)')
    plt.plot(pos, outdoor, 's--', color='#7a7a7a', label='Outdoor (few reflectors)')
    plt.title('Multipath fading: RSSI vs position, indoor vs outdoor')
    plt.xlabel('Position along the scan (cm)')
    plt.ylabel('RSSI (dBm)')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()


def plot_stationary(time_s, rssi):
    plt.figure(figsize=(8, 4.5))
    plt.plot(time_s, rssi, 'o-', color='#5c5c5c')
    mean_val = np.mean(rssi)
    plt.axhline(mean_val, color='gray', linestyle=':', alpha=0.7)
    spread = rssi.max() - rssi.min()
    plt.title(f'Standing perfectly still: RSSI still varies by {spread:.0f} dB')
    plt.text(time_s[-1], rssi.max(), f'mean: {mean_val:.1f} dBm', ha='right', va='top')
    plt.xlabel('Time (s)')
    plt.ylabel('RSSI (dBm)')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()


def plot_roughness(indoor, outdoor):
    labels = ['Indoor', 'Outdoor']
    rough = [roughness(indoor), roughness(outdoor)]
    fade = [fade_depth(indoor), fade_depth(outdoor)]

    x = np.arange(len(labels))
    width = 0.35

    plt.figure(figsize=(7, 4.5))
    plt.bar(x - width / 2, rough, width, label='Roughness (mean |step|, dB)', color='#5a5a5a')
    plt.bar(x + width / 2, fade, width, label='Fade depth (peak to null, dB)', color='#c7b299')

    for i in range(len(labels)):
        plt.text(x[i] - width / 2, rough[i] + 0.2, f'{rough[i]:.1f}', ha='center')
        plt.text(x[i] + width / 2, fade[i] + 0.2, f'{fade[i]:.1f}', ha='center')

    plt.title('Indoor vs outdoor: how jagged is the signal?')
    plt.ylabel('dB')
    plt.xticks(x, labels)
    plt.legend()
    plt.grid(axis='y', linestyle=':', alpha=0.6)
    plt.tight_layout()


def plot_two_ray():
    pos = np.linspace(0, 50, 500)
    sig_db = two_ray_pattern(pos)

    plt.figure(figsize=(8, 4))
    plt.plot(pos, sig_db, color='#5c5c5c')
    plt.title('Two-ray theory: peaks and nulls repeat every ~6.2 cm (half a wavelength)')
    plt.xlabel('Receiver position (cm)')
    plt.ylabel('Combined signal (dB relative to peak)')
    plt.ylim(-30, 2)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()


def show_figures():
    plt.show()


# ---------------------------------------------------------
# Main Execution
# ---------------------------------------------------------
if __name__ == "__main__":
    # Load or generate sample CSVs
    pos, indoor, outdoor = load_scan()
    time_s, stat_rssi = load_stationary()

    # Print comparison report
    print_report(pos, indoor, outdoor, time_s, stat_rssi)

    # Render expected figures
    plot_scan(pos, indoor, outdoor)
    plot_stationary(time_s, stat_rssi)
    plot_roughness(indoor, outdoor)

    plot_two_ray()

    show_figures()