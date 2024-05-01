from invoke import task
from matplotlib.pyplot import subplots
from os import makedirs
from os.path import join
from tasks.util.env import PLOTS_ROOT
from tasks.util.makespan import do_makespan_plot, read_makespan_results
from tasks.util.plot import save_plot
from tasks.util.spot import plot_spot_results, read_spot_results

MOTIVATION_PLOTS_DIR = join(PLOTS_ROOT, "motivation")


@task(default=True)
def plot(ctx):
    """
    Plot the motivation figure illustrating the trade-off between locality and
    utilisation
    """
    # num_vms = [16, 24, 32, 48, 64]
    # num_tasks = [50, 75, 100, 150, 200]
    num_vms = 16
    num_tasks = 100
    num_cpus_per_vm = 8

    results = {}
    results[num_vms] = read_makespan_results(num_vms, num_tasks, num_cpus_per_vm)
    makedirs(MOTIVATION_PLOTS_DIR, exist_ok=True)

    # ----------
    # Plot 1: timeseries of the percentage of idle vCPUs
    # ----------

    fig, ax1 = subplots(figsize=(6, 2))
    do_makespan_plot("ts_vcpus", results, ax1, num_vms, num_tasks)
    ax1.legend()
    save_plot(fig, MOTIVATION_PLOTS_DIR, "motivation_vcpus")

    # ----------
    # Plot 2: timeseries of the number of cross-VM links
    # ----------

    fig, ax2 = subplots(figsize=(6, 2))
    do_makespan_plot("ts_xvm_links", results, ax2, num_vms, num_tasks)
    save_plot(fig, MOTIVATION_PLOTS_DIR, "motivation_xvm_links")


@task
def spot(ctx):
    """
    Subset of the makespan.spot plot to include in the motivation section
    """
    num_vms = [4]
    num_tasks = [10]
    num_cpus_per_vm = 8

    results = {}
    for (n_vms, n_tasks) in zip(num_vms, num_tasks):
        results[n_vms] = read_spot_results(n_vms, n_tasks, num_cpus_per_vm)

    # ----------
    # Plot 1: makespan slowdown (spot / no spot)
    # ----------

    fig, ax1 = subplots(figsize=(2, 2))
    plot_spot_results(
        "makespan",
        results,
        ax1,
        num_vms=num_vms,
        num_tasks=num_tasks,
        tight=True,
    )

    save_plot(fig, MOTIVATION_PLOTS_DIR, "motivation_spot_makespan")

    # ----------
    # Plot 2: stacked cost bar plot (spot) + real cost (no spot)
    # ----------

    fig, ax2 = subplots(figsize=(2, 2))
    plot_spot_results(
        "cost",
        results,
        ax2,
        num_vms=num_vms,
        num_tasks=num_tasks,
        tight=True,
    )

    save_plot(fig, MOTIVATION_PLOTS_DIR, "motivation_spot_cost")
