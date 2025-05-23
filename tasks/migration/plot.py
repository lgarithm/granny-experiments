from glob import glob
from invoke import task
from matplotlib.pyplot import hlines, subplots
import matplotlib.pyplot as plt
from numpy import arange
from os.path import join
from pandas import read_csv
from tasks.util.env import PROJ_ROOT
from tasks.util.migration import MIGRATION_PLOTS_DIR
from tasks.util.plot import UBENCH_PLOT_COLORS, save_plot


ALL_WORKLOADS = [
    "all-to-all",
    "compute",
    "network",
    "og-network",
    "very-network",
]

FONT_SIZE = 14
LABEL_SIZE = 12
LINE_WIDTH = 2

plt.rcParams.update(
    {
        "text.usetex": True,  # Use LaTeX for all text
        "font.family": "serif",  # Use serif fonts (like LaTeX default)
        "font.serif": [
            "Times"
        ],  # Use Times font (matches ACM's acmart class default)
        "axes.labelsize": 12,  # Font size for axes labels
        "font.size": 12,  # General font size
        "legend.fontsize": 12,  # Font size for legend
        "xtick.labelsize": 10,  # Font size for x tick labels
        "ytick.labelsize": 10,  # Font size for y tick labels
    }
)


def _read_results():
    results_dir = join(PROJ_ROOT, "results", "migration")
    result_dict = {}

    for csv in glob(join(results_dir, "migration_*.csv")):
        workload = csv.split("_")[-1].split(".")[0]
        if workload not in ALL_WORKLOADS:
            continue

        results = read_csv(csv)
        groupped_results = results.groupby("Check", as_index=False)

        if workload not in result_dict:
            result_dict[workload] = {}

        result_dict[workload] = {
            "checks": groupped_results.mean()["Check"].to_list(),
            "mean": groupped_results.mean()["Time"].to_list(),
            "sem": groupped_results.sem()["Time"].to_list(),
        }

    return result_dict


@task(default=True)
def plot(ctx):
    """
    Plot migration figure
    """
    migration_results = _read_results()

    do_plot("all-to-all", migration_results)
    # do_plot("compute", migration_results)
    # do_plot("network", migration_results)
    do_plot("very-network", migration_results)
    # do_plot("og-network", migration_results)


def do_plot(workload, migration_results):
    fig, ax = subplots(figsize=(3, 2))
    xs = [0, 2, 4, 6, 8]
    xticks = arange(1, 6)
    width = 0.5
    idx_ref = migration_results[workload]["checks"].index(10)
    ys = []
    for x in xs:
        idx_granny = migration_results[workload]["checks"].index(x)
        ys.append(
            float(
                migration_results[workload]["mean"][idx_ref]
                / migration_results[workload]["mean"][idx_granny]
            )
        )

    color_idx = list(migration_results.keys()).index(workload)

    ax.bar(
        xticks,
        ys,
        width,
        label=workload,
        color=UBENCH_PLOT_COLORS[color_idx],
        edgecolor="black",
        zorder=3,
    )

    # Aesthetics
    ax.set_ylabel("Speed-up \n [No mig. / mig.]", fontsize=FONT_SIZE)
    ax.set_xlabel(r"\% of execution when to migrate", fontsize=FONT_SIZE)
    ax.set_xticks(xticks)
    ax.set_xticklabels(["1 VM", "20", "40", "60", "80"])
    ax.tick_params(axis="both", labelsize=LABEL_SIZE)
    ax.xaxis.set_label_coords(0.35, -0.25)
    xlim_left = 0.5
    xlim_right = 5.5
    ax.set_xlim(left=xlim_left, right=xlim_right)

    if workload == "all-to-all":
        ax.text(
            xticks[0] - 0.1,
            1.5,
            "{:.1f}".format(ys[0]),
            rotation="vertical",
            fontsize=10,
            bbox={
                "boxstyle": "Square, pad=0.2",
                "edgecolor": "black",
                "facecolor": "white",
            },
        )
        ax.set_ylim(bottom=0, top=6)
    else:
        ax.set_ylim(bottom=0)
    ax.grid(zorder=0)
    hlines(
        1,
        xlim_left,
        xlim_right,
        linestyle="dashed",
        colors="red",
        zorder=4,
        linewidth=LINE_WIDTH,
    )

    save_plot(
        fig, MIGRATION_PLOTS_DIR, "migration_speedup_{}".format(workload)
    )
