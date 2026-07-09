import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

import scienceplots
plt.style.use('science')


HUMAN_AGREEMENT = {'krippendorff': {'zpravodajske_hodnoty-negativita': {'mean': 0.3293,
                                                      'ci_low': 0.179,
                                                      'ci_high': 0.482},
                  'zpravodajske_hodnoty-blizkost': {'mean': 0.8287,
                                                    'ci_low': 0.6965,
                                                    'ci_high': 0.9369},
                  'zpravodajske_hodnoty-eliti_osoby': {'mean': 0.5696,
                                                       'ci_low': 0.4462,
                                                       'ci_high': 0.6917},
                  'zpravodajske_hodnoty-personalizace': {'mean': 0.5129,
                                                         'ci_low': 0.3172,
                                                         'ci_high': 0.6854},
                  'zpravodajske_hodnoty-dopad': {'mean': 0.0061,
                                                 'ci_low': -0.0999,
                                                 'ci_high': 0.1165},
                  'temata_clanku-vnitrni_politicke_deni': {'mean': 0.5389,
                                                           'ci_low': 0.3989,
                                                           'ci_high': 0.668},
                  'temata_clanku-mezinarodni_politicke_reakce': {'mean': 0.5846,
                                                                 'ci_low': 0.4598,
                                                                 'ci_high': 0.7012},
                  'temata_clanku-vojenske_operace_izraele': {'mean': 0.317,
                                                             'ci_low': 0.1892,
                                                             'ci_high': 0.4453},
                  'temata_clanku-teroristicke_operace': {'mean': 0.3027,
                                                         'ci_low': 0.1712,
                                                         'ci_high': 0.4376},
                  'temata_clanku-dopad_na_izraelske_civilisty': {'mean': 0.4598,
                                                                 'ci_low': 0.3288,
                                                                 'ci_high': 0.5859},
                  'temata_clanku-dopad_na_palestinske_civilisty': {'mean': 0.4777,
                                                                   'ci_low': 0.3472,
                                                                   'ci_high': 0.6093},
                  'temata_clanku-humanitarni_pomoc': {'mean': 0.3915,
                                                      'ci_low': 0.2346,
                                                      'ci_high': 0.5584},
                  'temata_clanku-globalni_reakce_verejnosti': {'mean': 0.8113,
                                                               'ci_low': 0.6936,
                                                               'ci_high': 0.9125},
                  'temata_clanku-ekonomicke_dusledky': {'mean': 0.396,
                                                        'ci_low': 0.1299,
                                                        'ci_high': 0.6389},
                  'temata_clanku-historie': {'mean': 0.2743,
                                             'ci_low': 0.0222,
                                             'ci_high': 0.5132},
                  'hlavni_tema_clanku': {'mean': 0.6821,
                                         'ci_low': 0.598,
                                         'ci_high': 0.7663},
                  'medialni_ramce-ramec_konfliktu': {'mean': 0.1618,
                                                     'ci_low': 0.0066,
                                                     'ci_high': 0.3308},
                  'medialni_ramce-ramec_budovani_miru': {'mean': 0.3809,
                                                         'ci_low': 0.1753,
                                                         'ci_high': 0.5723},
                  'medialni_ramce-humanitarni_ramec': {'mean': 0.3494,
                                                       'ci_low': 0.2138,
                                                       'ci_high': 0.4815},
                  'medialni_ramce-historicko_kulturni_ramec': {'mean': 0.3976,
                                                               'ci_low': 0.1481,
                                                               'ci_high': 0.6245},
                  'medialni_ramce-geopoliticky_ramec': {'mean': 0.6309,
                                                        'ci_low': 0.5061,
                                                        'ci_high': 0.747},
                  'medialni_ramce-lokalni_ramec': {'mean': 0.3914,
                                                   'ci_low': 0.2627,
                                                   'ci_high': 0.5211},
                  'mluvci-politicti_predstavitele_izraele': {'mean': 0.7766,
                                                             'ci_low': 0.6595,
                                                             'ci_high': 0.8792},
                  'mluvci-politicti_predstavitele_palestiny': {'mean': 0.4958,
                                                               'ci_low': 0.2865,
                                                               'ci_high': 0.6938},
                  'mluvci-politici_z_blizkovychodnich_zemi': {'mean': 0.6614,
                                                              'ci_low': 0.4026,
                                                              'ci_high': 0.8646},
                  'mluvci-politici_ze_ostatnich_svetovych_zemi': {'mean': 0.8076,
                                                                  'ci_low': 0.7104,
                                                                  'ci_high': 0.8936},
                  'mluvci-predstavitele_mezinarodnich_a_neziskovych_organizaci': {'mean': 0.4653,
                                                                                  'ci_low': 0.2757,
                                                                                  'ci_high': 0.6412},
                  'mluvci-vojensti_predstavitele_izraele': {'mean': 0.8585,
                                                            'ci_low': 0.7294,
                                                            'ci_high': 0.9579},
                  'mluvci-clenove_teroristickych_skupin': {'mean': 0.6469,
                                                           'ci_low': 0.4321,
                                                           'ci_high': 0.832},
                  'mluvci-nezavisli_experti_a_analytici': {'mean': 0.7498,
                                                           'ci_low': 0.5595,
                                                           'ci_high': 0.9033},
                  'mluvci-media_a_novinari': {'mean': 0.3319,
                                              'ci_low': 0.1722,
                                              'ci_high': 0.4882},
                  'mluvci-ociti_svedci_a_civiliste_z_izraele': {'mean': 0.7969,
                                                                'ci_low': 0.5917,
                                                                'ci_high': 0.9466},
                  'mluvci-ociti_svedci_a_civiliste_z_palestiny': {'mean': 0.6951,
                                                                  'ci_low': 0.322,
                                                                  'ci_high': 0.9379},
                  'zpravodajske_hodnoty': {'mean': 0.4489,
                                           'ci_low': 0.384,
                                           'ci_high': 0.5115},
                  'temata_clanku': {'mean': 0.4559,
                                    'ci_low': 0.4023,
                                    'ci_high': 0.5093},
                  'medialni_ramce': {'mean': 0.3847,
                                     'ci_low': 0.3094,
                                     'ci_high': 0.454},
                  'mluvci': {'mean': 0.6636,
                             'ci_low': 0.6082,
                             'ci_high': 0.7162},
                  'overall': {'mean': 0.5176,
                              'ci_low': 0.4822,
                              'ci_high': 0.5518}}}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results",
        type=Path,
        required=True,
        help="Path to the CSV file containing the results.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory where to save the resulting plots.",
    )
    return parser.parse_args()


SUFFIX = "_krippendorff_mean"


def get_major_categories(df: pd.DataFrame) -> list[str]:
    categories = []
    for col in df.columns:
        if col.endswith(SUFFIX) and "-" not in col:
            cat = col[: -len(SUFFIX)]
            if cat != "overall" and cat not in categories:
                categories.append(cat)
    return categories


def get_minor_categories(df: pd.DataFrame, major: str) -> list[str]:
    minors = []
    prefix = f"{major}-"
    for col in df.columns:
        if col.startswith(prefix) and col.endswith(SUFFIX):
            minor = col[len(prefix) : -len(SUFFIX)]
            if minor not in minors:
                minors.append(minor)
    return minors


def plot_errorbar(
    x_labels,
    means,
    ci_low,
    ci_high,
    title: str,
    ylabel: str,
    output_path: Path,
    sort_desc: bool = True,
    human_ref: dict = None,
):
    data = list(zip(x_labels, means, ci_low, ci_high))
    if sort_desc:
        data.sort(key=lambda row: row[1], reverse=True)

    x_labels, means, ci_low, ci_high = zip(*data)
    yerr_low = [max(m - lo, 0) for m, lo in zip(means, ci_low)]
    yerr_high = [max(hi - m, 0) for m, hi in zip(means, ci_high)]

    fig, ax = plt.subplots(figsize=(min(max(4, len(x_labels) * 0.7), 12), 5))
    x_pos = range(len(x_labels))

    # Lists to dynamically determine global min/max bounds for this specific plot
    all_lows = list(ci_low)
    all_highs = list(ci_high)

    # Plot Model Data
    ax.errorbar(
        x_pos,
        means,
        yerr=[yerr_low, yerr_high],
        fmt="o",
        capsize=5,
        markersize=7,
        linestyle="none",
        color="tab:blue",
        ecolor="tab:blue",
        elinewidth=1.5,
        label="Model",
    )

    # Plot Human Baseline if available
    if human_ref is not None:
        if "mean" in human_ref:
            h_mean = human_ref["mean"]
            h_low = human_ref["ci_low"]
            h_high = human_ref["ci_high"]
            
            all_lows.append(h_low)
            all_highs.append(h_high)

            ax.axhline(h_mean, color="darkorange", linestyle="--", linewidth=1.5, label="Human Baseline")
            ax.axhspan(h_low, h_high, color="darkorange", alpha=0.12, label="Human 95% CI")
        else:
            h_means, h_lows, h_highs, h_x = [], [], [], []
            for idx, label in enumerate(x_labels):
                if label in human_ref:
                    ref = human_ref[label]
                    h_means.append(ref["mean"])
                    h_lows.append(max(ref["mean"] - ref["ci_low"], 0))
                    h_highs.append(max(ref["ci_high"] - ref["mean"], 0))
                    h_x.append(idx)
                    
                    all_lows.append(ref["ci_low"])
                    all_highs.append(ref["ci_high"])

            if h_means:
                ax.errorbar(
                    h_x,
                    h_means,
                    yerr=[h_lows, h_highs],
                    fmt="d",
                    capsize=4,
                    markersize=6,
                    linestyle="none",
                    color="darkorange",
                    ecolor="darkorange",
                    elinewidth=1.2,
                    alpha=0.85,
                    label="Human Baseline",
                )

        ax.legend(loc="best", frameon=True)

    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(x_labels, rotation=90, ha="center")
    ax.set_xlim(-0.5, len(x_labels) - 0.5)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    
    # Calculate fully decoupled custom Y bounds with a 0.05 padding margin
    ymin = min(all_lows) - 0.05
    ymax = max(all_highs) + 0.05
    ax.set_ylim(ymin, ymax)
    
    # Maintain strict 0.1 minor grid lines aligned cleanly across dynamic ranges
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.grid(True, axis="y", alpha=0.3)
    
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_models_per_combo(df: pd.DataFrame, output_dir: Path):
    """1. Models against each other with overall alpha, 1 plot per codebook x individual_questions combo."""
    for codebook in sorted(df["codebook"].unique()):
        for iq in sorted(df["individual_questions"].unique()):
            subset = df[(df["codebook"] == codebook) & (df["individual_questions"] == iq)]
            if subset.empty:
                continue

            plot_errorbar(
                x_labels=subset["rater"].tolist(),
                means=subset["overall_krippendorff_mean"].tolist(),
                ci_low=subset["overall_krippendorff_ci_low"].tolist(),
                ci_high=subset["overall_krippendorff_ci_high"].tolist(),
                title=f"Overall Krippendorff's alpha by model\ncodebook={codebook}, individual_questions={iq}",
                ylabel="Krippendorff's alpha",
                output_path=output_dir / f"1_models_overall_{codebook}_iq_{iq}.png",
                human_ref=HUMAN_AGREEMENT["krippendorff"]["overall"],
            )


def plot_best_model_across_combos(df: pd.DataFrame, best_row: pd.Series, output_dir: Path):
    """2. For the best model, errorbar with 4 columns (one per codebook-questions combo)."""
    best_model = best_row["rater"]
    subset = df[df["rater"] == best_model].copy()
    subset["combo"] = subset["codebook"].astype(str) + " / iq=" + subset["individual_questions"].astype(str)

    plot_errorbar(
        x_labels=subset["combo"].tolist(),
        means=subset["overall_krippendorff_mean"].tolist(),
        ci_low=subset["overall_krippendorff_ci_low"].tolist(),
        ci_high=subset["overall_krippendorff_ci_high"].tolist(),
        title=f"Overall Krippendorff's alpha across codebook/question settings\nmodel={best_model}",
        ylabel="Krippendorff's alpha",
        output_path=output_dir / "2_best_model_across_combos.png",
        sort_desc=False,
        human_ref=HUMAN_AGREEMENT["krippendorff"]["overall"],
    )


def plot_best_model_categories(df: pd.DataFrame, best_row: pd.Series, output_dir: Path):
    """3. For the best model (best row), plot as many columns as there are major categories."""
    categories = get_major_categories(df)

    means, ci_low, ci_high, labels = [], [], [], []
    human_ref_subset = {}

    for cat in categories:
        mean_col = f"{cat}_krippendorff_mean"
        low_col = f"{cat}_krippendorff_ci_low"
        high_col = f"{cat}_krippendorff_ci_high"
        if mean_col in df.columns:
            means.append(best_row[mean_col])
            ci_low.append(best_row[low_col])
            ci_high.append(best_row[high_col])
            labels.append(cat)
            
            if cat in HUMAN_AGREEMENT["krippendorff"]:
                human_ref_subset[cat] = HUMAN_AGREEMENT["krippendorff"][cat]

    plot_errorbar(
        x_labels=labels,
        means=means,
        ci_low=ci_low,
        ci_high=ci_high,
        title=(
            f"Krippendorff's alpha by major category\n"
            f"model={best_row['rater']}, codebook={best_row['codebook']}, "
            f"individual_questions={best_row['individual_questions']}"
        ),
        ylabel="Krippendorff's alpha",
        output_path=output_dir / "3_best_model_categories.png",
        sort_desc=False,
        human_ref=human_ref_subset,
    )


def plot_best_model_minor_categories(df: pd.DataFrame, best_row: pd.Series, output_dir: Path):
    """4. For the best model, one errorbar plot per major category showing its minor categories."""
    categories = get_major_categories(df)

    for cat in categories:
        minors = get_minor_categories(df, cat)
        if not minors:
            continue

        means, ci_low, ci_high, labels = [], [], [], []
        human_ref_subset = {}

        for minor in minors:
            mean_col = f"{cat}-{minor}_krippendorff_mean"
            low_col = f"{cat}-{minor}_krippendorff_ci_low"
            high_col = f"{cat}-{minor}_krippendorff_ci_high"
            means.append(best_row[mean_col])
            ci_low.append(best_row[low_col])
            ci_high.append(best_row[high_col])
            labels.append(minor)
            
            full_key = f"{cat}-{minor}"
            if full_key in HUMAN_AGREEMENT["krippendorff"]:
                human_ref_subset[minor] = HUMAN_AGREEMENT["krippendorff"][full_key]

        plot_errorbar(
            x_labels=labels,
            means=means,
            ci_low=ci_low,
            ci_high=ci_high,
            title=(
                f"Krippendorff's alpha by minor category ({cat})\n"
                f"model={best_row['rater']}, codebook={best_row['codebook']}, "
                f"individual_questions={best_row['individual_questions']}"
            ),
            ylabel="Krippendorff's alpha",
            output_path=output_dir / f"4_best_model_{cat}_minors.png",
            sort_desc=False,
            human_ref=human_ref_subset,
        )


def main():
    args = parse_args()
    df = pd.read_csv(args.results)
    args.output.mkdir(parents=True, exist_ok=True)

    best_row = df.loc[df["overall_krippendorff_mean"].idxmax()]

    plot_models_per_combo(df, args.output)
    plot_best_model_across_combos(df, best_row, args.output)
    plot_best_model_categories(df, best_row, args.output)
    plot_best_model_minor_categories(df, best_row, args.output)

    print(f"Best model: {best_row['rater']} (codebook={best_row['codebook']}, "
          f"individual_questions={best_row['individual_questions']}, "
          f"overall alpha={best_row['overall_krippendorff_mean']:.3f})")
    print(f"Plots saved to: {args.output}")


if __name__ == "__main__":
    main()