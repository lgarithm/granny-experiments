from glob import glob
from invoke import task
from matplotlib.pyplot import subplots
import matplotlib.pyplot as plt
from os import makedirs
from os.path import join
from pandas import read_csv
from tasks.util.env import SYSTEM_NAME
from tasks.util.lammps import (
    LAMMPS_PLOTS_DIR,
    LAMMPS_RESULTS_DIR,
    LAMMPS_SIM_WORKLOAD_CONFIGS,
)
from tasks.util.plot import UBENCH_PLOT_COLORS, SINGLE_COL_FIGSIZE, save_plot

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
    glob_str = "lammps_*.csv"
    result_dict = {}

    for csv in glob(join(LAMMPS_RESULTS_DIR, glob_str)):
        baseline = csv.split("_")[1]
        workload = csv.split("_")[-1][0:-4]

        if workload not in LAMMPS_SIM_WORKLOAD_CONFIGS:
            continue

        if baseline not in result_dict:
            result_dict[baseline] = {}

        results = read_csv(csv)
        grouped = results.groupby("WorldSize", as_index=False)

        result_dict[baseline][workload] = {
            "world-size": grouped.mean()["WorldSize"].to_list(),
            "exec-time-mean": grouped.mean()["Time"].to_list(),
            "exec-time-sem": grouped.sem()["Time"].to_list(),
        }

    return result_dict


@task(default=True)
def plot(ctx, plot_elapsed_times=True):
    """
    Plot the LAMMPS results
    """
    makedirs(LAMMPS_PLOTS_DIR, exist_ok=True)
    result_dict = _read_results()

    workloads = result_dict["granny"]
    num_workloads = len(workloads)
    num_procs = result_dict["granny"]["network"]["world-size"]

    fig, ax = subplots(figsize=SINGLE_COL_FIGSIZE)
    width = 0.3
    for workload_ind, workload in enumerate(workloads):
        x_wload_offset = (
            -int(num_workloads) / 2 * width
            + width * workload_ind
            + width * 0.5 * (num_workloads % 2 == 0)
        )
        slowdown = [
            float(granny_time / native_time)
            for (native_time, granny_time) in zip(
                result_dict["native"][workload]["exec-time-mean"],
                result_dict["granny"][workload]["exec-time-mean"],
            )
        ]

        x = [np - x_wload_offset for np in num_procs]
        ax.bar(
            x,
            slowdown,
            width=width,
            label=workload,
            color=UBENCH_PLOT_COLORS[workload_ind],
            edgecolor="black",
            zorder=3,
        )

    xmin = 0
    ymin = 0
    ymax = 1.5
    xmax = max(num_procs) + 1
    ax.hlines(
        y=1,
        color="red",
        xmin=xmin,
        xmax=xmax,
        zorder=4,
        linestyle="dashed",
        linewidth=LINE_WIDTH,
    )
    ax.set_xlim(left=xmin)
    ax.set_xticks(list(range(17)))
    ax.set_ylim(bottom=ymin, top=ymax)
    ax.legend(ncols=2, loc="upper center")
    ax.set_xlabel(r"\# MPI Processes", fontsize=FONT_SIZE)
    ax.set_ylabel(
        "Slowdown\n[{} / OpenMPI]".format(SYSTEM_NAME), fontsize=FONT_SIZE
    )
    ax.tick_params(axis="both", labelsize=LABEL_SIZE)
    ax.grid(zorder=0)

    save_plot(fig, LAMMPS_PLOTS_DIR, "lammps_slowdown")
