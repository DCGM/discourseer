from typing import List, Dict

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle

from discourseer.inter_rater_reliability import IRRResult, IRRResults, IRRVariants


def make_error_boxes(ax, xdata, ydata, xerror, yerror, without_model_error, x_ticks: List[str]):
    # Loop over data points; create box from errors at each point
    errorboxes = [Rectangle((x - xe[0], y - ye[0]), xe.sum(), ye.sum())
                  for x, y, xe, ye in zip(xdata, ydata, xerror.T, yerror.T)]

    # Create patch collection with specified colour/alpha
    ax.add_collection(PatchCollection(errorboxes, facecolor='gray', alpha=0.5, edgecolor='none'))

    ax.errorbar(xdata, ydata + yerror[1], xerr=xerror, fmt='none', label='best case', ecolor='g')
    ax.errorbar(xdata, ydata - yerror[0], xerr=xerror, fmt='none', label='worst case', ecolor='r')
    ax.errorbar(xdata, ydata + without_model_error, xerr=xerror, fmt='none', label='without model', ecolor='b')
    ax.errorbar(xdata, ydata, xerr=xerror, fmt='none', label='with model', ecolor='k')

    max_y = max(ydata + yerror[1])
    min_y = min(ydata - yerror[0])
    ax.set_ylim(min_y * 1.2 if min_y <= 0 else 0, max_y * 1.2)

    ax.set_ylabel('Inter-rater reliability')
    ax.set_title('Inter-rater reliability for different questions.')

    ax.legend(bbox_to_anchor=(1.2, 1.0))
    ax.set_xticks(xdata)
    ax.set_xticklabels(x_ticks)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()


def irr_variants_to_data(irr_results: Dict[str, IRRVariants]):
    n = len(irr_results)
    x = np.arange(0, n, 1)
    xerr = np.ones((2, n)) * 0.45

    y = np.zeros(n)
    yerr = np.zeros((2, n))
    without_model_error = np.zeros(n)
    labels = []

    for i, (question, irr_variants) in enumerate(irr_results.items()):
        y[i] = irr_variants.with_model
        yerr[0, i] = irr_variants.with_model - irr_variants.worst_case
        yerr[1, i] = irr_variants.best_case - irr_variants.with_model
        without_model_error[i] = abs(irr_variants.without_model - irr_variants.with_model)
        labels.append(question)

    return x, y, xerr, yerr, without_model_error, labels


def visualize_results(results: IRRResults, location: str = None):
    results = results.to_dict_of_results()
    results = {k: v.gwet_ac1 for k, v in results.items()}  # visualize only gwet_ac1
    # results = {k: v.krippendorff_alpha for k, v in results.items()}

    x, y, xerr, yerr, without_model_error, labels = irr_variants_to_data(results)

    fig, ax = plt.subplots(1)
    make_error_boxes(ax, x, y, xerr, yerr, without_model_error, labels)

    if location:
        plt.savefig(location)
    else:
        plt.show()


def test_dummy():
    x, y, xerr, yerr, without_model_error, labels = prepare_dummy_data()
    fig, ax = plt.subplots(1)
    make_error_boxes(ax, x, y, xerr, yerr, without_model_error, labels)
    plt.show()


def prepare_dummy_data():
    """Show what shapes are expected for the data."""
    # Number of data points
    n = 5

    # Dummy data
    np.random.seed(19680801)
    x = np.arange(0, n, 1)
    y = np.array([3.1, 4.3, 2.2, 5.2, 1.1])

    xerr = np.ones((2, n)) * 0.45
    yerr = np.array([[0.3, 0.1, 0.4, 0.2, 0.5],
                     [0.1, 0.4, 0.5, 0.2, 0.3]]) * 2

    without_model_error = np.array([0.1, 0.2, 0.3, 0.5, 0.5])
    labels = ['A', 'B', 'C', 'D', 'E']

    return x, y, xerr, yerr, without_model_error, labels


if __name__ == '__main__':
    test_dummy()
