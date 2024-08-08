from typing import List, Dict
import logging

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle

from discourseer.inter_rater_reliability import IRRResult, IRRResults, IRRVariants

logger = logging.getLogger()


def make_error_boxes(xdata, ydata, xerror, yerror, without_model_results, majority_agreements, x_ticks: List[str], metric: str):
    # fig, (ax2, ax) = plt.subplots(figsize=(12, 8), nrows=2, sharex=True)
    fig = plt.figure(figsize=(12, 8))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1, 2])

    ax2 = plt.subplot(gs[0])
    ax = plt.subplot(gs[1], sharex=ax2)

    # Loop over data points; create box from errors at each point
    errorboxes = [Rectangle((x - xe[0], y - ye[0]), xe.sum(), ye.sum())
                  for x, y, xe, ye in zip(xdata, ydata, xerror.T, yerror.T)]

    # Create patch collection with specified colour/alpha
    ax.add_collection(PatchCollection(errorboxes, facecolor='gray', alpha=0.5, edgecolor='none'))

    ax.errorbar(xdata, ydata + yerror[1], xerr=xerror, fmt='none', label='best case', ecolor='g')
    ax.errorbar(xdata, ydata - yerror[0], xerr=xerror, fmt='none', label='worst case', ecolor='r')
    ax.errorbar(xdata, without_model_results, xerr=xerror, fmt='none', label='without model', ecolor='darkorange')
    ax.errorbar(xdata, ydata, xerr=xerror, fmt='none', label='with model', ecolor='k')
    # ax.errorbar(xdata, majority_agreements, xerr=xerror, fmt='none', label='majority agreement', ecolor='b')

    max_y = max(ydata + yerror[1])
    min_y = min(ydata - yerror[0])
    ax.set_ylim(min_y * 1.2 if min_y <= 0 else 0, max_y * 1.2)

    ax.set_title(f'Inter-rater reliability: {metric}.')
    ax.set_ylabel(metric)

    ax.legend(bbox_to_anchor=(1.2, 1.0))
    # ax.set_xticks(xdata)
    # ax.set_xticklabels(x_ticks)

    plt.setp(ax2.get_xticklabels(), visible=False)

    # print(f'xerr: {xerr}')
    # print(f'majority_agreements: {majority_agreements}')
    bar_x = np.arange(len(majority_agreements))
    ax2.bar(bar_x, majority_agreements, label='majority agreement')
    ax2.set_ylim(0, 1)
    ax2.set_ylabel('Majority agreement')
    ax2.set_title('Majority agreement')
    ax2.legend(bbox_to_anchor=(1.2, 1.0))
    ax2.set_xticks(xdata)
    ax2.set_xticklabels(x_ticks, rotation=45, ha='right')

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

    # fig, (ax1, ax2) = plt.subplots(1, figsize=(12, 4), nrows=2, sharex=True)
    # # fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True)
    # make_error_boxes(ax1, ax2, x, y, xerr, yerr, without_model_results, majority_agreements, labels)
    # make_error_boxes(ax1, ax2, x, y, xerr, yerr, without_model_error, majority_agreements, labels)

    # fig, (ax1, ax2) = plt.subplots(figsize=(12, 8), nrows=2, sharex=True)
    make_error_boxes(x, y, xerr, yerr, without_model_results, majority_agreements, labels, metric)

    # fig.suptitle('Results for different questions.')
    # plt.tight_layout()

    if location:
        plt.savefig(location)
    else:
        plt.show()

def visualize_irr_results_only_with_model(results: IRRResults, location: str = None, metric: str = 'krippendorff_alpha'):
    visualize_irr_results_only_something(results, location, metric, 'with_model')


def visualize_irr_results_only_human_raters(results: IRRResults, location: str = None, metric: str = 'krippendorff_alpha'):
    visualize_irr_results_only_something(results, location, metric, 'without_model')


def visualize_irr_results_only_something(results: IRRResults, location: str = None, metric: str = 'krippendorff_alpha', something: str = 'without_model'):
    if results.is_empty():
        logger.info('No results to visualize, see \{output_folder\}/irr_results.json.')
        return
    results = results.to_dict_of_results()
    results = {k: getattr(v, metric)    for k, v in results.items()}  # visualize only given metric
    results = {k: getattr(v, something) for k, v in results.items()}  # visualize only something from given metric

    bar_plot(list(results.keys()), list(results.values()), f'Inter-rater reliability {metric} for different questions.', location)


def bar_plot(names: List[str], values: List[float], title: str, location: str = None, x_label: str = 'Questions', y_label: str = 'Inter-rater reliability'):
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(names, values)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
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
