#!/usr/bin/env python
import argparse
import csv
import os


DEFAULT_MODES = ["odom", "odom_imu", "odom_imu_gps"]
METRICS = [
    ("samples", "samples"),
    ("rmse_position_m", "rmse_pos_m"),
    ("final_position_error_m", "final_pos_m"),
    ("rmse_yaw_rad", "rmse_yaw_rad"),
    ("final_yaw_error_rad", "final_yaw_rad"),
]


def read_summary(path):
    data = {}
    with open(path) as summary:
        for line in summary:
            if ":" not in line:
                continue
            key, value = line.strip().split(":", 1)
            data[key.strip()] = value.strip()
    return data


def read_metrics(path):
    rows = []
    with open(path) as metrics_file:
        reader = csv.DictReader(metrics_file)
        for row in reader:
            try:
                rows.append({
                    "time": float(row["time"]),
                    "filtered_x": float(row["filtered_x"]),
                    "filtered_y": float(row["filtered_y"]),
                    "gt_x": float(row["gt_x"]),
                    "gt_y": float(row["gt_y"]),
                    "position_error": float(row["position_error"]),
                    "yaw_error_rad": float(row["yaw_error_rad"]),
                })
            except (KeyError, TypeError, ValueError):
                continue
    return rows


def fmt(value):
    try:
        return "%.6f" % float(value)
    except (TypeError, ValueError):
        return value or "-"


def print_table(rows):
    headers = ["mode"] + [label for _, label in METRICS]
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row)]

    def print_row(values):
        print("  ".join(value.ljust(width) for value, width in zip(values, widths)))

    print_row(headers)
    print_row(["-" * width for width in widths])
    for row in rows:
        print_row(row)


def plot_results(results_dir, metrics_by_mode):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available; skipping comparison plots")
        return []

    if not metrics_by_mode:
        return []

    paths = []

    fig, ax = plt.subplots(figsize=(9, 5))
    for mode, rows in metrics_by_mode.items():
        if not rows:
            continue
        t0 = rows[0]["time"]
        times = [row["time"] - t0 for row in rows]
        errors = [row["position_error"] for row in rows]
        ax.plot(times, errors, label=mode)
    ax.set_title("Erro de posicao por metodo")
    ax.set_xlabel("tempo [s]")
    ax.set_ylabel("erro [m]")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path = os.path.join(results_dir, "comparison_position_error.png")
    fig.savefig(path, dpi=140)
    plt.close(fig)
    paths.append(path)

    fig, ax = plt.subplots(figsize=(9, 5))
    for mode, rows in metrics_by_mode.items():
        if not rows:
            continue
        t0 = rows[0]["time"]
        times = [row["time"] - t0 for row in rows]
        yaw_errors = [row["yaw_error_rad"] for row in rows]
        ax.plot(times, yaw_errors, label=mode)
    ax.set_title("Erro de yaw por metodo")
    ax.set_xlabel("tempo [s]")
    ax.set_ylabel("erro [rad]")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path = os.path.join(results_dir, "comparison_yaw_error.png")
    fig.savefig(path, dpi=140)
    plt.close(fig)
    paths.append(path)

    fig, ax = plt.subplots(figsize=(7, 7))
    first_mode = next(iter(metrics_by_mode))
    gt_rows = metrics_by_mode[first_mode]
    if gt_rows:
        ax.plot([row["gt_x"] for row in gt_rows],
                [row["gt_y"] for row in gt_rows],
                color="black", linewidth=2.0, label="gt")
    for mode, rows in metrics_by_mode.items():
        if not rows:
            continue
        ax.plot([row["filtered_x"] for row in rows],
                [row["filtered_y"] for row in rows],
                label=mode)
    ax.set_title("Trajetorias estimadas vs ground truth")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path = os.path.join(results_dir, "comparison_trajectories.png")
    fig.savefig(path, dpi=140)
    plt.close(fig)
    paths.append(path)

    return paths


def main():
    parser = argparse.ArgumentParser(description="Compare localization summary and metrics files.")
    parser.add_argument("--results-dir", default=os.path.expanduser("~/catkin_ws/src/Localiza-o-Robotica/results"))
    parser.add_argument("--modes", nargs="+", default=DEFAULT_MODES)
    parser.add_argument("--no-plots", action="store_true", help="Only print the summary table.")
    args = parser.parse_args()

    rows = []
    metrics_by_mode = {}
    missing = []
    for mode in args.modes:
        summary_path = os.path.join(args.results_dir, "%s_summary.txt" % mode)
        metrics_path = os.path.join(args.results_dir, "%s_metrics.csv" % mode)
        if not os.path.exists(summary_path):
            missing.append(summary_path)
            continue
        data = read_summary(summary_path)
        rows.append([mode] + [fmt(data.get(key)) for key, _ in METRICS])

        if os.path.exists(metrics_path):
            metrics = read_metrics(metrics_path)
            if metrics:
                metrics_by_mode[mode] = metrics
        else:
            missing.append(metrics_path)

    if missing:
        print("Missing files:")
        for path in missing:
            print("  %s" % path)

    if not rows:
        return 1

    print_table(rows)

    if not args.no_plots:
        plot_paths = plot_results(args.results_dir, metrics_by_mode)
        if plot_paths:
            print("\nComparison plots:")
            for path in plot_paths:
                print("  %s" % path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
