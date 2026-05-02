"""Generate the HARP-per-platform results bar chart for slide 11."""
import matplotlib.pyplot as plt
import numpy as np

platforms = ['Intel Raptor Lake i9-13900K\n(vs CFS)', 'Odroid XU3-E\n(vs EAS)']
time_reduction = [12, 12]
energy_reduction = [30, 25]

x = np.arange(len(platforms))
width = 0.35

fig, ax = plt.subplots(figsize=(7.5, 4.5))

c_time = '#2E86C1'
c_energy = '#27AE60'

bars1 = ax.bar(x - width/2, time_reduction, width, label='Execution-time reduction', color=c_time, edgecolor='white')
bars2 = ax.bar(x + width/2, energy_reduction, width, label='Energy reduction', color=c_energy, edgecolor='white')

ax.set_ylabel('Reduction vs baseline (%)   — higher is better', fontsize=11)
ax.set_title("HARP improvements, two hybrid platforms", fontsize=13, pad=12)
ax.set_xticks(x)
ax.set_xticklabels(platforms, fontsize=10.5)
ax.legend(loc='upper right', fontsize=10, frameon=False)
ax.set_ylim(0, 38)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

for bars in (bars1, bars2):
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f'{h}%',
                    xy=(bar.get_x() + bar.get_width()/2, h),
                    xytext=(0, 3),
                    textcoords='offset points',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')

fig.text(0.5, 0.02,
         'Source: HARP (Smejkal et al., Middleware \'25) §6.6, p.281',
         ha='center', fontsize=8.5, style='italic', color='#555')

plt.tight_layout(rect=[0, 0.04, 1, 1])

out_pdf = '/home/davidkan/Projects/ArrowLakeHBenchmarking/presentation/fig_harp_results.pdf'
out_png = '/home/davidkan/Projects/ArrowLakeHBenchmarking/presentation/fig_harp_results.png'
plt.savefig(out_pdf, format='pdf', bbox_inches='tight')
plt.savefig(out_png, format='png', dpi=160, bbox_inches='tight')
print(f'Saved: {out_pdf}\n       {out_png}')
