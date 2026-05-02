"""Generate a schematic block diagram of the Core Ultra 9 285H die for §1 of the paper.

Compute tile (left): 6 P-cores + 8 E-cores in 2 clusters of 4, shared 24 MB L3.
SoC tile (right): 2 LP E-cores with their own L2, no L3 connection.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(10, 5.5))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8.5)
ax.set_aspect('equal')
ax.axis('off')

c_p = '#3498DB'
c_e = '#27AE60'
c_lpe = '#E67E22'
c_l3 = '#95A5A6'
c_l2 = '#BDC3C7'
c_tile = '#ECF0F1'

# ---------- Compute tile (left, big) ----------
compute_tile = mpatches.FancyBboxPatch(
    (0.3, 0.5), 9.2, 7.5,
    boxstyle="round,pad=0.05,rounding_size=0.15",
    linewidth=2, edgecolor='#34495E', facecolor=c_tile, zorder=1)
ax.add_patch(compute_tile)
ax.text(0.5, 8.15, 'Compute tile', fontsize=11, fontweight='bold', color='#34495E')

# 6 P-cores along the top
for i in range(6):
    x = 0.7 + i * 1.4
    box = mpatches.FancyBboxPatch((x, 6.5), 1.2, 1.2,
                                    boxstyle="round,pad=0.02,rounding_size=0.06",
                                    linewidth=1.2, edgecolor='#1F618D',
                                    facecolor=c_p, zorder=3)
    ax.add_patch(box)
    ax.text(x + 0.6, 7.35, f'P{i}', fontsize=10, fontweight='bold', color='white', ha='center')
    ax.text(x + 0.6, 6.95, 'Lion', fontsize=7.5, color='white', ha='center')
    ax.text(x + 0.6, 6.65, 'Cove', fontsize=7.5, color='white', ha='center')

# Label P tier
ax.text(0.5, 7.75, '6 P-cores @ 2.9 GHz (no-turbo)', fontsize=9.5,
        color='#1F618D', fontweight='bold')

# E-cluster 0 (CPUs 6-9)
e_cluster_0 = mpatches.FancyBboxPatch((0.6, 3.3), 4.1, 2.4,
                                        boxstyle="round,pad=0.04,rounding_size=0.08",
                                        linewidth=1.4, edgecolor='#196F3D',
                                        facecolor='#D5F5E3', zorder=2)
ax.add_patch(e_cluster_0)
for i in range(4):
    x = 0.85 + i * 0.95
    box = mpatches.FancyBboxPatch((x, 4.6), 0.85, 0.95,
                                    boxstyle="round,pad=0.02,rounding_size=0.04",
                                    linewidth=1, edgecolor='#196F3D',
                                    facecolor=c_e, zorder=3)
    ax.add_patch(box)
    ax.text(x + 0.43, 5.05, f'E{6+i}', fontsize=9, fontweight='bold', color='white', ha='center')
ax.text(2.65, 3.55, 'L2 4 MB shared', fontsize=8.5, color='#196F3D', ha='center', style='italic')

# E-cluster 1 (CPUs 10-13)
e_cluster_1 = mpatches.FancyBboxPatch((4.95, 3.3), 4.1, 2.4,
                                        boxstyle="round,pad=0.04,rounding_size=0.08",
                                        linewidth=1.4, edgecolor='#196F3D',
                                        facecolor='#D5F5E3', zorder=2)
ax.add_patch(e_cluster_1)
for i in range(4):
    x = 5.2 + i * 0.95
    box = mpatches.FancyBboxPatch((x, 4.6), 0.85, 0.95,
                                    boxstyle="round,pad=0.02,rounding_size=0.04",
                                    linewidth=1, edgecolor='#196F3D',
                                    facecolor=c_e, zorder=3)
    ax.add_patch(box)
    ax.text(x + 0.43, 5.05, f'E{10+i}', fontsize=9, fontweight='bold', color='white', ha='center')
ax.text(7.0, 3.55, 'L2 4 MB shared', fontsize=8.5, color='#196F3D', ha='center', style='italic')

ax.text(0.5, 5.85, '8 E-cores @ 2.7 GHz (Skymont, 2 clusters of 4)',
        fontsize=9.5, color='#196F3D', fontweight='bold')

# Shared 24 MB L3
l3 = mpatches.FancyBboxPatch((0.6, 1.4), 8.4, 1.5,
                              boxstyle="round,pad=0.04,rounding_size=0.08",
                              linewidth=1.4, edgecolor='#566573',
                              facecolor=c_l3, zorder=2)
ax.add_patch(l3)
ax.text(4.8, 2.15, '24 MB L3 (shared by CPUs 0–13)',
        fontsize=11, fontweight='bold', color='white', ha='center')
ax.text(4.8, 1.7, 'last-level cache, compute tile only',
        fontsize=8.5, color='white', ha='center', style='italic')

# DRAM controller stub
ax.text(4.8, 0.95, 'DRAM controller', fontsize=8.5, color='#7F8C8D', ha='center', style='italic')

# ---------- SoC tile (right, smaller) ----------
soc_tile = mpatches.FancyBboxPatch(
    (10.0, 0.5), 3.6, 7.5,
    boxstyle="round,pad=0.05,rounding_size=0.15",
    linewidth=2, edgecolor='#A04000', facecolor='#FCF3CF', zorder=1)
ax.add_patch(soc_tile)
ax.text(10.2, 8.15, 'SoC tile', fontsize=11, fontweight='bold', color='#A04000')

# 2 LP E-cores
for i in range(2):
    x = 10.4 + i * 1.55
    box = mpatches.FancyBboxPatch((x, 5.5), 1.4, 1.5,
                                    boxstyle="round,pad=0.02,rounding_size=0.06",
                                    linewidth=1.2, edgecolor='#A04000',
                                    facecolor=c_lpe, zorder=3)
    ax.add_patch(box)
    ax.text(x + 0.7, 6.55, f'LP E{14+i}', fontsize=10, fontweight='bold', color='white', ha='center')
    ax.text(x + 0.7, 6.15, 'Skymont', fontsize=7.5, color='white', ha='center')
    ax.text(x + 0.7, 5.75, '@ 1 GHz', fontsize=7.5, color='white', ha='center')

ax.text(10.2, 7.30, '2 LP E-cores (same Skymont µarch as E)',
        fontsize=9.0, color='#A04000', fontweight='bold')

# LP E shared L2
lpe_l2 = mpatches.FancyBboxPatch((10.4, 3.6), 2.95, 1.4,
                                  boxstyle="round,pad=0.04,rounding_size=0.08",
                                  linewidth=1.2, edgecolor='#7F8C8D',
                                  facecolor=c_l2, zorder=2)
ax.add_patch(lpe_l2)
ax.text(11.875, 4.55, '2 MB L2', fontsize=11, fontweight='bold', color='#34495E', ha='center')
ax.text(11.875, 4.15, 'shared by LP E pair', fontsize=8.5, color='#34495E', ha='center', style='italic')

# "No L3" callout box where L3 would be
no_l3 = mpatches.FancyBboxPatch((10.4, 1.4), 2.95, 1.5,
                                 boxstyle="round,pad=0.04,rounding_size=0.08",
                                 linewidth=1.4, edgecolor='#C0392B',
                                 facecolor='#FADBD8', zorder=2,
                                 linestyle='--')
ax.add_patch(no_l3)
ax.text(11.875, 2.15, 'NO L3', fontsize=12, fontweight='bold',
        color='#C0392B', ha='center')
ax.text(11.875, 1.7, '(LP E off-tile)', fontsize=8.5,
        color='#C0392B', ha='center', style='italic')

# ---------- Tile-boundary arrow ----------
ax.annotate('', xy=(10.0, 4.25), xytext=(9.5, 4.25),
            arrowprops=dict(arrowstyle='<->', color='#C0392B', lw=2))
ax.text(9.75, 4.65, 'tile\nboundary', fontsize=8, color='#C0392B',
        ha='center', fontweight='bold')

# Title
fig.suptitle('Intel Core Ultra 9 285H — three core tiers across two physical tiles',
             fontsize=12.5, fontweight='bold', y=0.98)

fig.text(0.5, 0.02,
         'Tile assignment from /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_max_freq and lstopo',
         ha='center', fontsize=8.5, style='italic', color='#555')

plt.tight_layout(rect=[0, 0.03, 1, 0.96])

out_pdf = '/home/davidkan/Projects/ArrowLakeHBenchmarking/presentation/fig_chip_schematic.pdf'
out_png = '/home/davidkan/Projects/ArrowLakeHBenchmarking/presentation/fig_chip_schematic.png'
plt.savefig(out_pdf, format='pdf', bbox_inches='tight')
plt.savefig(out_png, format='png', dpi=160, bbox_inches='tight')
print(f'Saved: {out_pdf}\n       {out_png}')
