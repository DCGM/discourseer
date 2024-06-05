import os
import numpy as np
from matplotlib import pyplot as plt
import csv

# # Load the results from the file
# DIR='../results/testing_voxel_click_mini'
# RESULT_FILE = os.path.join(DIR, 'result_summary.txt')
# print(f'Loading results from {RESULT_FILE}')
#
# # read RESULT_FILE as csv and print. ignore headers!!
# with open(RESULT_FILE, 'r') as f:
#     reader = csv.reader(f, delimiter=',', skipinitialspace=True)
#     rows = [row for row in reader if row[2] != 'None']
#     if rows[0][0] == 'voxel_size':
#         rows = rows[1:]
#
#     rows = [[float(val) for val in row] for row in rows]
#     rows = [[voxel_size, click_area, round(IOU, 2)] for voxel_size, click_area, IOU in rows if IOU != 0]
#
# for row in rows:
#     print(row)
#
# data_orig = rows
#
# def get_click_voxel_ratio(click_area, voxel_size):
#     return round(click_area / voxel_size, 1)
#
# # data with voxel_click ratio:
# data = [(get_click_voxel_ratio(click_area, voxel_size), voxel_size, IOU) for voxel_size, click_area, IOU in data_orig]
#
# # Arrange data by voxel_click_ratio and voxel_size
# data_dict = {}
# for voxel_click_ratio, voxel_size, IOU in data:
#     if voxel_click_ratio not in [1, 1.5, 2]:
#         continue
#     if voxel_click_ratio not in data_dict:
#         data_dict[voxel_click_ratio] = {}
#     data_dict[voxel_click_ratio][voxel_size] = IOU
#
# # Sort the data by voxel_size
# data_dict_sorted = {}
# for voxel_click_ratio, results in data_dict.items():
#     # results = sorted(results, key=lambda x: x[0])
#     results = [results[voxel_size] for voxel_size in sorted(results.keys())]
#     # results = [round(IOU, 2) for voxel_size, IOU in results]
#     data_dict_sorted[f'{voxel_click_ratio}*voxel_size'] = results
#
# print('data dict sorted:')
# for k, v in data_dict_sorted.items():
#     print(k, v)
#
# x_labels = list(map(str, np.unique([voxel_size for voxel_size, _, _ in data_orig])))
# ratio_restults = data_dict_sorted


# Data should look something like this:
x_labels = ("Overall", "mean_through_topics", "misto", "rozsah")
values_by_color_label = {
    'best_case': (0.91, 0.78, 0.97, 1.0),
    'with_model': (0.85, 0.59, 0.94, 0.51),
    'worst_case': (0.73, 0.34, 0.86, 0.33),
    # 'worst_case': (0.73, 0.34, 0.86, -0.53),
    'without_model': (0.89, 0.70, 0.96, 1.0),
}

# Prepare plot
x = np.arange(len(x_labels))  # the label locations
width = 1 / (len(values_by_color_label) + 1)  # the width of the bars

fig, ax = plt.subplots(layout='constrained')

multiplier = 0
for attribute, measurement in values_by_color_label.items():
    offset = width * multiplier
    rects = ax.bar(x + offset, measurement, width, label=attribute)
    ax.bar_label(rects, padding=3)
    multiplier += 1

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Topic')
ax.set_title('Effect of voxel size and click area on mean IOU in S3DIS dataset.')
ax.set_xticks(x + width, x_labels)
ax.set_xlabel('Voxel size')
ax.legend(loc='upper left', ncols=1)
max_value = max([max(measurement) for measurement in values_by_color_label.values()])
min_value = min([min(measurement) for measurement in values_by_color_label.values()])
ax.set_ylim(min_value * 1.2 if min_value <= 0 else 0, max_value * 1.2)
plt.tight_layout()

plt.show()
# Save the plot
# out_file_png = os.path.join(DIR, 'voxel_click_IOU.png')
# out_file_svg = os.path.join(DIR, 'voxel_click_IOU.svg')
# plt.savefig(out_file_png)
# plt.savefig(out_file_svg)
# plt.clf()
# print(f'Groupbar chart saved to {out_file_png} and {out_file_svg}')
