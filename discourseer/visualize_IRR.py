from typing import List, Dict
import logging

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle

from discourseer.inter_rater_reliability import IRRResults, IRRVariants

logger = logging.getLogger()


def make_error_boxes(xdata, ydata, xerror, yerror, without_model_results, majority_agreements, x_ticks: List[str], metric: str,
                     thresholds_maj: List[float] = None, thresholds_irr: List[float] = None):
    fig = plt.figure(figsize=(12, 8))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1, 2])

    ax_maj = plt.subplot(gs[0])
    ax_irr = plt.subplot(gs[1], sharex=ax_maj)

    # Loop over data points; create box from errors at each point
    errorboxes = [Rectangle((x - xe[0], y - ye[0]), xe.sum(), ye.sum())
                  for x, y, xe, ye in zip(xdata, ydata, xerror.T, yerror.T)]

    # Create patch collection with specified colour/alpha
    ax_irr.add_collection(PatchCollection(errorboxes, facecolor='gray', alpha=0.5, edgecolor='none'))

    ax_irr.errorbar(xdata, ydata + yerror[1], xerr=xerror, fmt='none', label='best case', ecolor='g')
    ax_irr.errorbar(xdata, ydata - yerror[0], xerr=xerror, fmt='none', label='worst case', ecolor='r')
    ax_irr.errorbar(xdata, without_model_results, xerr=xerror, fmt='none', label='without model', ecolor='darkorange')
    ax_irr.errorbar(xdata, ydata, xerr=xerror, fmt='none', label='with model', ecolor='k')

    min_y = min(ydata - yerror[0])
    ax_irr.set_ylim(min_y * 1.2 if min_y <= 0 else 0, 1.05)

    for threshold in thresholds_irr:
        ax_irr.axhline(y=threshold, color='g', linestyle='--', label='threshold ' + str(threshold), linewidth=1, alpha=0.5)

    ax_irr.set_title(f'Inter-rater reliability: {metric}.')
    ax_irr.set_ylabel(metric)
    ax_irr.legend(bbox_to_anchor=(1.2, 1.0))

    # Hide x-ticks on the upper subplot since they are shared with ax2
    plt.setp(ax_maj.get_xticklabels(), visible=False)

    bar_x = np.arange(len(majority_agreements))
    ax_maj.bar(bar_x, majority_agreements, label='majority agreement')
    for threshold in thresholds_maj:
        ax_maj.axhline(y=threshold, color='g', linestyle='--', label='threshold ' + str(threshold), linewidth=1, alpha=0.5)

    ax_maj.set_ylim(0, 1)
    ax_maj.set_ylabel('Majority agreement')
    ax_maj.set_title('Majority agreement')
    ax_maj.legend(bbox_to_anchor=(1.2, 1.0))

    # Set x-ticks and labels on the lower subplot
    ax_maj.set_xticks(xdata)
    ax_maj.set_xticklabels(x_ticks, rotation=45, ha='right')

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()


def irr_variants_to_data(irr_results: Dict[str, IRRVariants]):
    n = len(irr_results)
    x = np.arange(0, n, 1)
    xerr = np.ones((2, n)) * 0.45

    y = np.zeros(n)
    yerr = np.zeros((2, n))
    without_model_results = np.zeros(n)
    labels = []

    for i, (question, irr_variants) in enumerate(irr_results.items()):
        y[i] = irr_variants.with_model
        yerr[0, i] = irr_variants.with_model - irr_variants.worst_case
        yerr[1, i] = irr_variants.best_case - irr_variants.with_model
        without_model_results[i] = irr_variants.without_model
        labels.append(question)

    return x, y, xerr, yerr, without_model_results, labels


def visualize_results(results: IRRResults, location: str = None, metric: str = 'krippendorff_alpha'):
    if results.is_empty():
        logger.info('No results to visualize, see \{output_folder\}/irr_results.json.')
        return
    results = results.to_dict_of_results()
    majority_agreements = [k.majority_agreement for k in results.values()]
    results = {k: getattr(v, metric) for k, v in results.items()}  # visualize only given metric

    x, y, xerr, yerr, without_model_results, labels = irr_variants_to_data(results)

    make_error_boxes(x, y, xerr, yerr, without_model_results, majority_agreements, labels, metric, thresholds_maj=[0.6], thresholds_irr=[0.8, 0.6])

    if location:
        plt.savefig(location)
    else:
        plt.show()

def visualize_irr_results_only_with_model(results: IRRResults, location: str = None, metric: str = 'krippendorff_alpha', thresholds: List[float] = None):
    visualize_irr_results_only_something(results, location, metric, 'with_model', thresholds)


def visualize_irr_results_only_human_raters(results: IRRResults, location: str = None, metric: str = 'krippendorff_alpha', thresholds: List[float] = None):
    visualize_irr_results_only_something(results, location, metric, 'without_model', thresholds)


def visualize_irr_results_only_something(results: IRRResults, location: str = None, metric: str = 'krippendorff_alpha',
                                         something: str = 'without_model', thresholds: List[float] = None):
    if results.is_empty():
        logger.info('No results to visualize, see \{output_folder\}/irr_results.json.')
        return
    results = results.to_dict_of_results()
    results = {k: getattr(v, metric)    for k, v in results.items()}  # visualize only given metric
    results = {k: getattr(v, something) for k, v in results.items()}  # visualize only something from given metric

    bar_plot(list(results.keys()), list(results.values()), thresholds, f'Inter-rater reliability {metric} for different questions.', location, y_label=metric)


def bar_plot(names: List[str], values: List[float], thresholds: List[float] = None, title: str = '', location: str = None, x_label: str = '', y_label: str = '') -> None:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(names, values)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

    min_value = min(values)
    ax.set_ylim(min_value * 1.2 if min_value <= 0 else 0, 1)

    for threshold in thresholds:
        ax.axhline(y=threshold, color='g', linestyle='--', label='threshold ' + str(threshold))
    ax.legend(bbox_to_anchor=(1.2, 1.0))

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    if location:
        plt.savefig(location)
    else:
        plt.show()
    
    plt.close()


#------------ Test the visualize_results function --------------

def test_dummy():
    x, y, xerr, yerr, without_model_error, labels = prepare_dummy_data()
    majority_agreements = [0.5, 0.6, 0.7, 0.8, 0.9]

    make_error_boxes(x, y, xerr, yerr, without_model_error, majority_agreements, labels, "test_metric")
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
    labels = ['Aaaaaaaaa_aaaaaaaa', 'Bbbbbebebebe_beb_bebeb', 'Casdfasdf_asdfas', 'DDDDddd_dd', 'Ee']

    return x, y, xerr, yerr, without_model_error, labels


if __name__ == '__main__':
    test_dummy()
