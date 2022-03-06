from matplotlib import style
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
from typing import Union, Optional
from pathlib import Path
import pandas as pd

def plot_results(
    results: pd.DataFrame,
    x_name: str,
    y_name: Union[str, list[str]],
    x_label: Optional[str] =None,
    y_label: Optional[str] =None,
    title: Optional[str] =None,
    legend: Optional[Union[str, list]] =None,
    style_sheet_path: Optional[Union[str, Path]] = None
) -> Axes:
    """Plot the simulation results.

    Args:
        results (pd.DataFrame): Simulation results.
        x_name (str): Name of data that should be on the x-axis.
        y_name (Union[str, list[str]]): Name of data that should be on the
            y-axis. For multiple plots, give a list with names as the argument.
        x_label (str, optional): X-label for the plot. Defaults to None.
        y_label (str, optional): Y-label for the plot. Defaults to None.
        title (str, optional): Title for the plot. Defaults to None.
        legend (Union[str, list], optional): Legend for the plot. For multiple
            plots give a list of strings as the argument. Defaults to None.
        style_sheet_path (Union[str, Path], optional): Path to a matplotlib
            style sheet. Defaults to None.

    Returns:
        Axes: Matplotlib Axes object.
    """
    if style_sheet_path:
        plt.style.use(style_sheet_path)

    plt.figure()
    ax = plt.gca()

    if title:
        ax.set_title(title)
    if x_label:
        ax.set_xlabel(x_label)
    if y_label:
        ax.set_ylabel(y_label)
    if isinstance(y_name, list):
        for y in y_name:
            ax.plot(results[x_name], results[y])
    else:
        ax.plot(results[x_name], results[y_name])
    if legend:
        ax.legend(legend)

    return ax
