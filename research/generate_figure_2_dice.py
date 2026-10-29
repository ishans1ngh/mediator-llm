import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Load the CSV results
csv_path = Path("results/mri_segmentation_results.csv")
df = pd.read_csv(csv_path)

# Extract data
case_ids = df['case_id'].tolist()
dice_scores = df['dice_score'].tolist()

# Calculate statistics from the actual data
mean_dice = np.mean(dice_scores)
min_dice = np.min(dice_scores)
max_dice = np.max(dice_scores)
num_cases = len(case_ids)

print(f"Number of cases: {num_cases}")
print(f"Mean Dice: {mean_dice:.4f}")
print(f"Min Dice: {min_dice:.4f}")
print(f"Max Dice: {max_dice:.4f}")

# Create figure with appropriate size for readability
fig_width = max(14, num_cases * 0.45)
fig_height = 6

fig, ax = plt.subplots(figsize=(fig_width, fig_height))

# Create bar chart with color coding based on performance
colors = []
for score in dice_scores:
    if score >= 0.9:
        colors.append('#2E86AB')  # Excellent - blue
    elif score >= 0.8:
        colors.append('#56C596')  # Good - green
    elif score >= 0.7:
        colors.append('#F18F01')  # Fair - orange
    else:
        colors.append('#C73E1D')  # Poor - red

bars = ax.bar(case_ids, dice_scores, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)

# Add horizontal reference line for mean Dice
ax.axhline(y=mean_dice, color='black', linestyle='--', linewidth=2, alpha=0.7, label=f'Mean Dice: {mean_dice:.4f}')

# Customize the plot
ax.set_xlabel('MRI Case', fontsize=12, fontweight='bold')
ax.set_ylabel('Dice Score', fontsize=12, fontweight='bold')
ax.set_title('Dice Score Across MRI Cases', fontsize=14, fontweight='bold')
ax.set_ylim([0, 1.05])
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Rotate x-axis labels for readability
ax.set_xticks(range(len(case_ids)))
ax.set_xticklabels(case_ids, rotation=45, ha='right', fontsize=9)

# Add legend
ax.legend(fontsize=10, loc='upper right')

# Add performance threshold lines
ax.axhline(y=0.9, color='green', linestyle=':', alpha=0.4, linewidth=1)
ax.axhline(y=0.8, color='orange', linestyle=':', alpha=0.4, linewidth=1)
ax.axhline(y=0.7, color='red', linestyle=':', alpha=0.4, linewidth=1)

plt.tight_layout()

# Save the figure
output_path = Path("results/figure_2_dice_scores.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"\nGraph saved to: {output_path}")
print(f"Cases plotted: {num_cases}")
print(f"Mean Dice (from CSV): {mean_dice:.4f}")
print(f"Minimum Dice: {min_dice:.4f}")
print(f"Maximum Dice: {max_dice:.4f}")
