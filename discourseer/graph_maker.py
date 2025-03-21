import matplotlib.pyplot as plt
import numpy as np
from io import StringIO
import pandas as pd

# Usage example:
# data = StringIO("""basic experiment	0.3780	0.724
# different_prompt_schema_gpt_3.5/default	0.3598	0.702
# different_prompt_schema_gpt_3.5/extensive	0.3760	0.724
# different_codebooks_gpt_3.5/gaza_v0_kveten	0.3600	0.724
# different_codebooks_gpt_3.5/gaza_v0_kveten_eng	0.3878	0.722
# different_codebooks_gpt_3.5/gaza_v1_červen	0.3538	0.729""")
# plot_kripp_alpha_and_majority_agreement(data, to_file='kripp_alpha_and_majority_agreement.png', title='Different\ experiments')

# sources:
# - two_scales for ax.plot: [matplotlib.org/.../two_scales.html](https://matplotlib.org/stable/gallery/subplots_axes_and_figures/two_scales.html)
# - twinx for ax.bar: [stackoverflow.com/.../bar-plot-with-two-bars-and-two-y-axis](https://stackoverflow.com/questions/24183101/bar-plot-with-two-bars-and-two-y-axis)

def plot_kripp_alpha_and_majority_agreement(
    data: str | StringIO | pd.DataFrame, to_file: str = None, title: str = None) -> plt.Figure:
    if isinstance(data, str):
        df = pd.read_csv(data)
    elif isinstance(data, StringIO):
        df = pd.read_csv(data, delimiter='\t', skipinitialspace=True, header=None)
        df = df.rename(columns={0: 'experiment_name', 1: 'kripp_alpha', 2: 'majority_agreement'})        
    elif isinstance(data, pd.DataFrame):
        df = data
    else:
        raise ValueError(f'data must be either a string or a pandas DataFrame, you provided a {type(data)}\n{data}')

    assert 'experiment_name' in df.columns, f'data must have a column named "experiment_name", but it has {df.columns}'
    assert 'kripp_alpha' in df.columns, f'data must have a column named "kripp_alpha", but it has {df.columns}'
    assert 'majority_agreement' in df.columns, f'data must have a column named "majority_agreement", but it has {df.columns}'
    assert len(df) > 0, f'data must have at least one row, but it has {len(df)}'

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax2 = ax.twinx() # Create another axes that shares the same x-axis as ax.

    col_1, col_2 = 'tab:green', 'tab:blue'
    width = 0.4

    df.kripp_alpha.plot(kind='bar', color=col_1, ax=ax, width=width, position=1)
    df.majority_agreement.plot(kind='bar', color=col_2, ax=ax2, width=width, position=0)

    # add all names to title like "0: orig, 1: new, 2: new2"
    title = r'$\bf{' + title + '}$:\n' if title else ''
    title += '\n'.join([f'{i}: {name}' for i, name in enumerate(df.experiment_name)])
    ax.set_title(title, loc='left', fontsize='small')

    ax.set_xlim(-.5, len(df.index)-.5)
    ax.set_xlabel('Experiment')

    ax.set_ylabel('Kripp Alpha <-1,1>', color=col_1)
    ax.yaxis.label.set_color(col_1)
    ax.tick_params(axis='y', colors=col_1)
    ax2.set_ylabel('Majority Agreement <0,1>', color=col_2)
    ax2.tick_params(axis='y', labelcolor=col_2)
    ax2.yaxis.label.set_color(col_2)

    plt.tight_layout()
    if to_file:
        plt.savefig(to_file)

    return fig
