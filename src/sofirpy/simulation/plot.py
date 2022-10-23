"""This module provides a easy function for plotting the simulation results."""

from pathlib import Path
from typing import Optional, Union

import matplotlib.pyplot as plt
import pandas as pd


def plot_results(
    results: pd.DataFrame,
    x_name: str,
    y_name: Union[str, list[str]],
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    title: Optional[str] = None,
    legend: Optional[Union[str, list[str]]] = None,
    style_sheet_path: Optional[Union[str, Path]] = None,
) -> tuple[plt.Axes, plt.Figure]:
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
        tuple[plt.Axes, plt.Figure]: Matplotlib Axes and figure object.
    """
    if style_sheet_path:
        plt.style.use(style_sheet_path)

    figure = plt.figure()
    axes = plt.gca()

    if title:
        axes.set_title(title)
    if x_label:
        axes.set_xlabel(x_label)
    if y_label:
        axes.set_ylabel(y_label)
    if isinstance(y_name, list):
        for name in y_name:
            axes.plot(results[x_name], results[name])
    else:
        axes.plot(results[x_name], results[y_name])
    if legend:
        axes.legend(legend)

    return axes, figure
