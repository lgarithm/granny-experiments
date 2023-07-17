from glob import glob
from invoke import task
from numpy import arange
from os import makedirs
from os.path import join
from pandas import read_csv
from tasks.util.env import PLOTS_ROOT, PROJ_ROOT
from tasks.util.plot import PLOT_COLORS, PLOT_PATTERNS

import matplotlib.pyplot as plt

RESULTS_DIR = join(PROJ_ROOT, "results", "mpi")
PLOTS_DIR = join(PLOTS_ROOT, "mpi")


def _read_kernels_results():
    result_dict = {}
    results_dir = join(PROJ_ROOT, "results", "mpi")

    kernels_to_plot = ["reduce", "p2p", "nstream", "stencil"]

    for csv in glob(join(results_dir, "kernels_*.csv")):
        results = read_csv(csv)

        baseline = csv.split("_")[1]
        kernel = csv.split("_")[-1].split(".")[0]

        if kernel not in kernels_to_plot:
            continue

        # First filter only the timing stats, and then group by kernel
        # results = results.loc[results["StatName"] == "Avg time (s)"]

        groupped_results = results.groupby("WorldSize", as_index=False)
        if baseline not in result_dict:
            result_dict[baseline] = {}
        if kernel not in result_dict[baseline]:
            result_dict[baseline][kernel] = {}

        result_dict[baseline][kernel] = {
            "num-procs": groupped_results.mean()["WorldSize"].to_list(),
            "mean": groupped_results.mean()["ActualTime"].to_list(),
            "sem": groupped_results.sem()["ActualTime"].to_list(),
        }

    return result_dict


@task
def kernels(ctx):
    """
    Plot the slowdown of MPI's ParRes kernels
    """
    out_file_name = "mpi_kernels_slowdown.pdf"
    result_dict = _read_kernels_results()
    makedirs(PLOTS_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 2))
    xs = arange(1, 9)
    width = 0.15
    for ind, kernel in enumerate(result_dict["granny"]):
        ys = []
        for x in 2 * xs:
            try:
                idx_wasm = result_dict["granny"][kernel]["num-procs"].index(x)
                idx_native = result_dict["native"][kernel]["num-procs"].index(
                    x
                )
                ys.append(
                    float(
                        result_dict["native"][kernel]["mean"][idx_native]
                        / result_dict["granny"][kernel]["mean"][idx_wasm]
                    )
                )
            except ValueError:
                ys.append(0)
        ax.bar(
            xs - width * 2 + width * ind,
            ys,
            width,
            label=kernel,
            color=list(PLOT_COLORS.values())[ind],
            hatch=PLOT_PATTERNS[ind],
            edgecolor="black",
        )
    xlabels = 2 * xs
    ax.set_xticks(xs)
    ax.set_xticklabels(xlabels)
    xlim_left = 0.5
    xlim_right = 8.5
    plt.hlines(1, xlim_left, xlim_right, linestyle="dashed", colors="red")
    ax.set_xlim(left=xlim_left, right=xlim_right)
    ax.set_xlabel("Number of MPI processes")
    ax.set_ylim(bottom=0, top=2.5)
    ax.set_ylabel("Speed-up \n [OpenMPI / Granny]")
    ax.legend(loc="upper right", ncol=4)

    fig.tight_layout()
    plt.savefig(
        join(PLOTS_DIR, out_file_name), format="pdf", bbox_inches="tight"
    )

    print("Plot saved to: {}".format(join(PLOTS_DIR, out_file_name)))
