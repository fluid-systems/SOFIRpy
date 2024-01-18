"""This module provides a easy function for plotting the simulation results."""

from __future__ import annotations

from pathlib import Path

import matplotlib.axes
import matplotlib.figure
import matplotlib.pyplot as plt
import pandas as pd


def plot_results(
    results: pd.DataFrame,
    x_name: str,
    y_name: str | list[str],
    x_label: str | None = None,
    y_label: str | None = None,
    title: str | None = None,
    legend: str | list[str] | None = None,
    style_sheet_path: str | Path | None = None,
) -> tuple[matplotlib.axes.Axes, matplotlib.figure.Figure]:
    """Plot the simulation results.

    Args:
        results (pd.DataFrame): Simulation results.
        x_name (str): Name of data that should be on the x-axis.
        y_name (str | list[str]): Name of data that should be on the
            y-axis. For multiple plots, give a list with names as the argument.
        x_label (str, optional): X-label for the plot. Defaults to None.
        y_label (str, optional): Y-label for the plot. Defaults to None.
        title (str, optional): Title for the plot. Defaults to None.
        legend (str | list[str] | None, optional): Legend for the plot. For multiple
            plots give a list of strings as the argument. Defaults to None.
        style_sheet_path (str | Path | None, optional): Path to a matplotlib
            style sheet. Defaults to None.

    Returns:
        tuple[Axes, Figure]: Matplotlib Axes and figure object.
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
