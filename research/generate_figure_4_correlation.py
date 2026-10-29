import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy import stats

# Load the CSV results
csv_path = Path("results/mri_segmentation_results.csv")
df = pd.read_csv(csv_path)

# Extract data
gt_voxels = df['ground_truth_tumor_voxels'].tolist()
pred_voxels = df['predicted_tumor_voxels'].tolist()
case_ids = df['case_id'].tolist()

# Calculate statistics
num_cases = len(gt_voxels)
mean_gt = np.mean(gt_voxels)
mean_pred = np.mean(pred_voxels)

# Calculate Pearson correlation coefficient and R²
pearson_r, p_value = stats.pearsonr(gt_voxels, pred_voxels)
r_squared = pearson_r ** 2

# Linear regression
slope, intercept, r_value, p_value_reg, std_err = stats.linregress(gt_voxels, pred_voxels)
regression_line = slope * np.array(gt_voxels) + intercept

print(f"Number of cases: {num_cases}")
print(f"Pearson r: {pearson_r:.4f}")
print(f"R²: {r_squared:.4f}")
print(f"Mean ground-truth tumor voxels: {mean_gt:.2f}")
print(f"Mean predicted tumor voxels: {mean_pred:.2f}")
print(f"Regression slope: {slope:.4f}")
print(f"Regression intercept: {intercept:.4f}")

# Create figure
fig, ax = plt.subplots(figsize=(10, 8))

# Create scatter plot
scatter = ax.scatter(gt_voxels, pred_voxels, alpha=0.7, color='#2E86AB', edgecolors='black', linewidth=0.5, s=80)

# Add y=x reference line (perfect agreement)
max_val = max(max(gt_voxels), max(pred_voxels))
ax.plot([0, max_val], [0, max_val], 'r--', linewidth=2, alpha=0.7, label='Perfect Agreement (y=x)')

# Add linear regression line
ax.plot(gt_voxels, regression_line, 'g-', linewidth=2, alpha=0.7, label=f'Linear Regression (y={slope:.2f}x+{intercept:.0f})')

# Customize the plot
ax.set_xlabel('Ground Truth Tumor Voxels', fontsize=12, fontweight='bold')
ax.set_ylabel('Predicted Tumor Voxels', fontsize=12, fontweight='bold')
ax.set_title('Ground-Truth vs Predicted Tumor Volume', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, linestyle='--')

# Set equal aspect ratio for better comparison
ax.set_aspect('equal', adjustable='box')

# Add statistics text box
stats_text = f'r = {pearson_r:.4f}\nR² = {r_squared:.4f}\nN = {num_cases}'
ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=11,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Add legend
ax.legend(fontsize=10, loc='lower right')

plt.tight_layout()

# Save the figure
output_path = Path("results/figure_4_tumor_volume_correlation.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"\nGraph saved to: {output_path}")
print(f"Cases plotted: {num_cases}")
print(f"Pearson r: {pearson_r:.4f}")
print(f"R²: {r_squared:.4f}")
print(f"Mean ground-truth tumor voxels: {mean_gt:.2f}")
print(f"Mean predicted tumor voxels: {mean_pred:.2f}")
