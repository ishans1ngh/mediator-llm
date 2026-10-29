import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Load the CSV results
csv_path = Path("results/mri_segmentation_results.csv")
df = pd.read_csv(csv_path)

# Extract data
case_ids = df['case_id'].tolist()
iou_scores = df['iou'].tolist()

# Calculate statistics from the actual data
mean_iou = np.mean(iou_scores)
min_iou = np.min(iou_scores)
max_iou = np.max(iou_scores)
std_iou = np.std(iou_scores)
num_cases = len(case_ids)

print(f"Number of cases: {num_cases}")
print(f"Mean IoU: {mean_iou:.4f}")
print(f"Std Dev IoU: {std_iou:.4f}")
print(f"Min IoU: {min_iou:.4f}")
print(f"Max IoU: {max_iou:.4f}")

# Create figure with appropriate size for readability
fig_width = max(14, num_cases * 0.45)
fig_height = 6

fig, ax = plt.subplots(figsize=(fig_width, fig_height))

# Create bar chart with color coding based on performance
colors = []
for score in iou_scores:
    if score >= 0.8:
        colors.append('#2E86AB')  # Excellent - blue
    elif score >= 0.6:
        colors.append('#56C596')  # Good - green
    elif score >= 0.4:
        colors.append('#F18F01')  # Fair - orange
    else:
        colors.append('#C73E1D')  # Poor - red

bars = ax.bar(case_ids, iou_scores, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)

# Add horizontal reference line for mean IoU
ax.axhline(y=mean_iou, color='black', linestyle='--', linewidth=2, alpha=0.7, label=f'Mean IoU: {mean_iou:.4f}')

# Customize the plot
ax.set_xlabel('MRI Case', fontsize=12, fontweight='bold')
ax.set_ylabel('IoU Score', fontsize=12, fontweight='bold')
ax.set_title('Intersection over Union (IoU) Across MRI Cases', fontsize=14, fontweight='bold')
ax.set_ylim([0, 1.05])
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Rotate x-axis labels for readability
ax.set_xticks(range(len(case_ids)))
ax.set_xticklabels(case_ids, rotation=45, ha='right', fontsize=9)

# Add legend
ax.legend(fontsize=10, loc='upper right')

# Add performance threshold lines
ax.axhline(y=0.8, color='green', linestyle=':', alpha=0.4, linewidth=1)
ax.axhline(y=0.6, color='orange', linestyle=':', alpha=0.4, linewidth=1)
ax.axhline(y=0.4, color='red', linestyle=':', alpha=0.4, linewidth=1)

plt.tight_layout()

# Save the figure
output_path = Path("results/figure_3_iou_scores.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"\nGraph saved to: {output_path}")
print(f"Cases plotted: {num_cases}")
print(f"Mean IoU (from CSV): {mean_iou:.4f}")
print(f"Standard deviation: {std_iou:.4f}")
print(f"Minimum IoU: {min_iou:.4f}")
print(f"Maximum IoU: {max_iou:.4f}")
