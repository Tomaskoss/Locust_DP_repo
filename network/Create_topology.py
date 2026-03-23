#!/usr/bin/env python3
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import os


def _format_source_ip(source_ip):
    """
    Skráti dlhé IPv6 range pre zobrazenie v diagrame.
    fd00::10 - fd00::40  →  fd00::10
                             - fd00::40
    192.168.10.10-40     →  192.168.10.10-40  (nezmenené)
    """
   
    if " - " in source_ip:
        parts = source_ip.split(" - ", 1)
        return parts[0] + "\n- " + parts[1]
   
    if ":" in source_ip and "/" in source_ip:
        return source_ip

    return source_ip


def _is_ipv6_source(source_ip):
    return ":" in source_ip


def create_topology_diagram(
    target_ip   = "142.251.36.110",
    source_ip   = "192.168.10.10-40",
    interface   = "ens33",
    output_file = "topology_diagram.png",
    reach_src_ip= None
):
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # ── Cloud (target) ────────────────────────────────────────────
    cloud_x, cloud_y = 5, 8

    cloud_circles = [
        Circle((cloud_x - 0.4, cloud_y),        0.35, color='lightblue', ec='black', linewidth=2, zorder=3),
        Circle((cloud_x,       cloud_y + 0.2),  0.40, color='lightblue', ec='black', linewidth=2, zorder=3),
        Circle((cloud_x + 0.4, cloud_y),        0.35, color='lightblue', ec='black', linewidth=2, zorder=3),
        Circle((cloud_x,       cloud_y - 0.15), 0.30, color='lightblue', ec='black', linewidth=2, zorder=3),
    ]
    for circle in cloud_circles:
        ax.add_patch(circle)

    globe = Circle((cloud_x, cloud_y), 0.25, color='white', ec='black', linewidth=1.5, zorder=4)
    ax.add_patch(globe)
    ax.plot([cloud_x, cloud_x], [cloud_y - 0.25, cloud_y + 0.25], 'k-', linewidth=1, zorder=5)
    ax.plot([cloud_x - 0.25, cloud_x + 0.25], [cloud_y, cloud_y],  'k-', linewidth=1, zorder=5)

    ellipse1 = mpatches.Ellipse((cloud_x, cloud_y), 0.5, 0.25, fill=False,
                                edgecolor='black', linewidth=1,   zorder=5)
    ellipse2 = mpatches.Ellipse((cloud_x, cloud_y), 0.5, 0.15, fill=False,
                                edgecolor='black', linewidth=0.8, zorder=5)
    ax.add_patch(ellipse1)
    ax.add_patch(ellipse2)

    # Target IP — pri IPv6 adrese menší font
    target_fontsize = 11 if ":" in target_ip else 16
    ax.text(cloud_x, cloud_y - 0.7, target_ip,
            ha='center', va='top',
            fontsize=target_fontsize, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black'))

    # ── Boxy dole ─────────────────────────────────────────────────
    box_y      = 2
    box_width  = 2.5
    box_height = 0.8

    # Attack
    attack_x   = 2
    ax.add_patch(FancyBboxPatch(
        (attack_x - box_width/2, box_y - box_height/2),
        box_width, box_height, boxstyle="round,pad=0.1",
        edgecolor='black', facecolor='#ffcccc', linewidth=2))
    ax.text(attack_x, box_y, 'Attack',
            ha='center', va='center', fontsize=16, fontweight='bold')

    # Tester
    tester_x = 5
    ax.add_patch(FancyBboxPatch(
        (tester_x - box_width/2, box_y - box_height/2),
        box_width, box_height, boxstyle="round,pad=0.1",
        edgecolor='black', facecolor='#ffffcc', linewidth=2))
    ax.text(tester_x, box_y, 'Tester',
            ha='center', va='center', fontsize=16, fontweight='bold')

    # Reachability
    reach_x = 8
    ax.add_patch(FancyBboxPatch(
        (reach_x - box_width/2, box_y - box_height/2),
        box_width, box_height, boxstyle="round,pad=0.1",
        edgecolor='black', facecolor='#ccffcc', linewidth=2))
    ax.text(reach_x, box_y, 'Reachability',
            ha='center', va='center', fontsize=16, fontweight='bold')

    # ── Info pod boxmi ────────────────────────────────────────────
    info_y = box_y - 1

    # IPv6 badge — oranžový štítok ak je IPv6
    if _is_ipv6_source(source_ip):
        for bx in (attack_x, reach_x):
            ax.add_patch(FancyBboxPatch(
                (bx - 0.55, info_y + 0.55), 1.1, 0.32,
                boxstyle="round,pad=0.05",
                edgecolor='#cc7700', facecolor='#fff0cc', linewidth=1.5, zorder=6))
            ax.text(bx, info_y + 0.71, 'IPv6',
                    ha='center', va='center',
                    fontsize=10, fontweight='bold', color='#cc7700', zorder=7)

    # Attack side info

    src_label = _format_source_ip(source_ip)
    base_font = 10 if _is_ipv6_source(source_ip) else 13

    ax.text(attack_x, info_y,        f'Interface: {interface}',
            ha='center', va='top', fontsize=base_font, fontstyle='italic')
    ax.text(attack_x, info_y - 0.30, 'IP source:',
            ha='center', va='top', fontsize=base_font, fontstyle='italic')
    ax.text(attack_x, info_y - 0.60, src_label,
            ha='center', va='top', fontsize=base_font, fontweight='bold')

    # Reachability side info
    ax.text(reach_x, info_y, f'Interface: {interface}',
            ha='center', va='top', fontsize=base_font, fontstyle='italic')
    
    if reach_src_ip:
        ax.text(reach_x, info_y - 0.30, 'IP source:',
                ha='center', va='top', fontsize=base_font, fontstyle='italic')
        ax.text(reach_x, info_y - 0.60, reach_src_ip,
                ha='center', va='top', fontsize=base_font, fontweight='bold')

    # ── Šípky k cloudu ────────────────────────────────────────────
    arrow_props = dict(arrowstyle='->', lw=3, color='black',
                       connectionstyle="arc3,rad=0", mutation_scale=30)

    ax.add_patch(FancyArrowPatch(
        (attack_x, box_y + box_height/2 + 0.1),
        (cloud_x - 0.8, cloud_y - 0.6), **arrow_props))

    ax.add_patch(FancyArrowPatch(
        (reach_x, box_y + box_height/2 + 0.1),
        (cloud_x + 0.8, cloud_y - 0.6), **arrow_props))

    # ── Spodná linka ──────────────────────────────────────────────
    line_y = box_y - box_height/2 - 0.3
    ax.plot([attack_x,              tester_x - box_width/2], [line_y, line_y], 'k-', linewidth=2)
    ax.plot([tester_x + box_width/2, reach_x],               [line_y, line_y], 'k-', linewidth=2)
    ax.plot([attack_x, attack_x], [box_y - box_height/2, line_y], 'k-', linewidth=2)
    ax.plot([reach_x,  reach_x],  [box_y - box_height/2, line_y], 'k-', linewidth=2)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"Topology diagram saved to: {output_file}")
    return output_file


# ============================================================
#  INTEGRATION — PDF report
# ============================================================

def add_topology_to_report(story, styles, target_ip, source_ip, interface="ens33", reach_src_ip=None):
    from reportlab.platypus import Image, Paragraph, Spacer

    topology_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "topology_diagram.png")
    create_topology_diagram(target_ip, source_ip, interface, topology_file, reach_src_ip)

    story.append(Paragraph("<b>Network Topology</b>", styles["Heading1"]))
    story.append(Spacer(1, 12))

    if os.path.exists(topology_file):
        story.append(Image(topology_file, width=450, height=360))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "Network topology showing the test configuration with attack, "
            "monitoring (tester), and reachability testing components.",
            styles["Normal"]
        ))
        story.append(Spacer(1, 12))

    return topology_file


# ============================================================
#  STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    # IPv4 test
    create_topology_diagram(
        target_ip   = "142.251.36.110",
        source_ip   = "192.168.10.10-40",
        interface   = "ens33",
        output_file = "topology_diagram_v4.png"
    )
    # IPv6 test
    create_topology_diagram(
        target_ip   = "2a00:1450:4001:82b::2003",
        source_ip   = "fd00::10 - fd00::40",
        interface   = "ens33",
        output_file = "topology_diagram_v6.png"
    )
    print("Both topology diagrams created successfully!")

