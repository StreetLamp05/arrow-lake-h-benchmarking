"""Generate the PIE -> PMCSched -> HARP timeline for §2 of the paper.

Shows that all three reviewed papers were evaluated on at most 2 core types,
and that Arrow Lake-H (with 3 tiers) postdates only HARP — leaving the binary
assumption untested on the new hardware.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(11, 5.0))
ax.set_xlim(2010.5, 2026.5)
ax.set_ylim(-2.4, 4.0)
ax.axis('off')

c_pie = '#3498DB'
c_pmc = '#27AE60'
c_harp = '#9B59B6'
c_hw = '#E67E22'
c_alh = '#C0392B'

# Main timeline axis
ax.annotate('', xy=(2026.3, 0), xytext=(2011, 0),
            arrowprops=dict(arrowstyle='->', color='#34495E', lw=2.0))
for year in (2012, 2014, 2016, 2018, 2020, 2022, 2024, 2026):
    ax.plot([year, year], [-0.12, 0.12], color='#34495E', lw=1.0)
    ax.text(year, -0.45, str(year), fontsize=9, ha='center', color='#34495E')

# ------- Hardware milestones (below the line) -------
def hw_milestone(year, label, sublabel, ypos=-1.5, color='#7F8C8D', fontsize=8.5):
    ax.plot([year, year], [-0.25, ypos + 0.3], color=color, lw=1.0, linestyle=':')
    ax.text(year, ypos, label, fontsize=fontsize, ha='center',
            color=color, fontweight='bold')
    ax.text(year, ypos - 0.35, sublabel, fontsize=7.5, ha='center',
            color=color, style='italic')

hw_milestone(2011, 'ARM big.LITTLE', '2 core types', ypos=-1.3)
hw_milestone(2021.7, 'Alder Lake', '2 core types (P+E)', ypos=-1.3)
hw_milestone(2023.4, 'Meteor Lake', '3 tiers (P+E+LP E)', ypos=-1.85)
ax.plot([2024.6, 2024.6], [-0.25, -1.45], color=c_alh, lw=1.5)
ax.text(2024.6, -1.6, 'Arrow Lake-H', fontsize=10, ha='center',
        color=c_alh, fontweight='bold')
ax.text(2024.6, -1.95, '3 tiers — this paper', fontsize=8.5, ha='center',
        color=c_alh, style='italic')

# ------- Reviewed-paper milestones (above the line) -------
def paper_box(year, ypos, title, subtitle, eval_text, color, dx=0):
    # Vertical connector
    ax.plot([year, year], [0.18, ypos - 0.4], color=color, lw=1.5)
    # Box
    width = 2.4
    height = 1.2
    box = mpatches.FancyBboxPatch((year - width/2 + dx, ypos - 0.4), width, height,
                                    boxstyle="round,pad=0.04,rounding_size=0.08",
                                    linewidth=1.4, edgecolor=color,
                                    facecolor='white', zorder=3)
    ax.add_patch(box)
    ax.text(year + dx, ypos + 0.55, title, fontsize=10, fontweight='bold',
            color=color, ha='center', zorder=4)
    ax.text(year + dx, ypos + 0.20, subtitle, fontsize=8.5, color='#34495E',
            ha='center', style='italic', zorder=4)
    ax.text(year + dx, ypos - 0.20, eval_text, fontsize=8, color='#34495E',
            ha='center', zorder=4)

paper_box(2012, 1.3, 'PIE [1]',
          'Van Craeynest et al., ISCA',
          'Evaluated: simulated big/little\n(2 core types, no real silicon)',
          c_pie)

paper_box(2023, 1.3, 'PMCSched [2]',
          'Bilbao, Saez, Prieto-Matías, CCPE',
          'Evaluated: Alder Lake P+E\n(2 core types, single die)',
          c_pmc, dx=-0.3)

paper_box(2025.5, 1.3, 'HARP [3]',
          'Smejkal et al., Middleware',
          'Evaluated: Raptor Lake P+E,\nOdroid big.LITTLE (2 types each)',
          c_harp, dx=-0.05)

# Top banner
ax.text(2018.5, 3.4,
        'All three reviewed papers evaluated on ≤ 2 CPU core types',
        fontsize=12, fontweight='bold', color='#34495E', ha='center')
ax.text(2018.5, 3.0,
        '— and none on a CPU with a physically separated 3rd tile —',
        fontsize=10, style='italic', color='#34495E', ha='center')

# Annotation arrow from HARP forward to Arrow Lake-H question
ax.annotate('Does the binary model still hold\non 3-tier Arrow Lake-H?',
            xy=(2024.6, -0.05), xytext=(2025.5, 2.3),
            fontsize=9, color=c_alh, fontweight='bold', ha='center',
            arrowprops=dict(arrowstyle='->', color=c_alh, lw=1.2,
                            connectionstyle='arc3,rad=0.25'))

fig.suptitle('Hybrid-CPU scheduling research and Intel hybrid hardware: a 13-year window',
             fontsize=12, fontweight='bold', y=0.98)
fig.text(0.5, 0.015,
         'PIE [1], PMCSched [2], HARP [3] — none evaluated on a CPU with three core tiers',
         ha='center', fontsize=8.5, style='italic', color='#555')

plt.tight_layout(rect=[0, 0.02, 1, 0.96])

out_pdf = '/home/davidkan/Projects/ArrowLakeHBenchmarking/presentation/fig_paper_timeline.pdf'
out_png = '/home/davidkan/Projects/ArrowLakeHBenchmarking/presentation/fig_paper_timeline.png'
plt.savefig(out_pdf, format='pdf', bbox_inches='tight')
plt.savefig(out_png, format='png', dpi=160, bbox_inches='tight')
print(f'Saved: {out_pdf}\n       {out_png}')
