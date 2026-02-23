#!/usr/bin/env python3
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import os

def create_topology_diagram(target_ip="142.251.36.110", source_ip="192.168.10.10-40", 
                           interface="ens33", output_file="topology_diagram.png"):
    """
    Creates a network topology diagram showing Attack -> Target <- Tester configuration.
    
    Args:
        target_ip: IP address of the target cloud server
        source_ip: IP address of the source machine
        interface: Network interface name
        output_file: Path to save the diagram
    """
    
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Cloud (target) at top
    cloud_x, cloud_y = 5, 8
    
    # Draw cloud shape
    cloud_circles = [
        Circle((cloud_x - 0.4, cloud_y), 0.35, color='lightblue', ec='black', linewidth=2, zorder=3),
        Circle((cloud_x, cloud_y + 0.2), 0.4, color='lightblue', ec='black', linewidth=2, zorder=3),
        Circle((cloud_x + 0.4, cloud_y), 0.35, color='lightblue', ec='black', linewidth=2, zorder=3),
        Circle((cloud_x, cloud_y - 0.15), 0.3, color='lightblue', ec='black', linewidth=2, zorder=3),
    ]
    
    for circle in cloud_circles:
        ax.add_patch(circle)
    
    # Globe icon inside cloud (simplified)
    globe = Circle((cloud_x, cloud_y), 0.25, color='white', ec='black', linewidth=1.5, zorder=4)
    ax.add_patch(globe)
    
    # Globe lines (latitude/longitude)
    ax.plot([cloud_x, cloud_x], [cloud_y - 0.25, cloud_y + 0.25], 'k-', linewidth=1, zorder=5)
    ax.plot([cloud_x - 0.25, cloud_x + 0.25], [cloud_y, cloud_y], 'k-', linewidth=1, zorder=5)
    
    # Ellipses for globe
    ellipse1 = mpatches.Ellipse((cloud_x, cloud_y), 0.5, 0.25, fill=False, 
                                edgecolor='black', linewidth=1, zorder=5)
    ellipse2 = mpatches.Ellipse((cloud_x, cloud_y), 0.5, 0.15, fill=False, 
                                edgecolor='black', linewidth=0.8, zorder=5)
    ax.add_patch(ellipse1)
    ax.add_patch(ellipse2)
    
    # Target IP below cloud
    ax.text(cloud_x, cloud_y - 0.7, target_ip, ha='center', va='top', 
            fontsize=16, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', 
            facecolor='white', edgecolor='black'))
    
    # Bottom boxes
    box_y = 2
    box_width = 2.5
    box_height = 0.8
    
    # Attack box (left)
    attack_x = 2
    attack_box = FancyBboxPatch((attack_x - box_width/2, box_y - box_height/2), 
                               box_width, box_height, boxstyle="round,pad=0.1",
                               edgecolor='black', facecolor='#ffcccc', linewidth=2)
    ax.add_patch(attack_box)
    ax.text(attack_x, box_y, 'Attack', ha='center', va='center', 
            fontsize=16, fontweight='bold')
    
    # Tester box (middle)
    tester_x = 5
    tester_box = FancyBboxPatch((tester_x - box_width/2, box_y - box_height/2), 
                               box_width, box_height, boxstyle="round,pad=0.1",
                               edgecolor='black', facecolor='#ffffcc', linewidth=2)
    ax.add_patch(tester_box)
    ax.text(tester_x, box_y, 'Tester', ha='center', va='center', 
            fontsize=16, fontweight='bold')
    
    # Reachability box (right)
    reach_x = 8
    reach_box = FancyBboxPatch((reach_x - box_width/2, box_y - box_height/2), 
                              box_width, box_height, boxstyle="round,pad=0.1",
                              edgecolor='black', facecolor='#ccffcc', linewidth=2)
    ax.add_patch(reach_box)
    ax.text(reach_x, box_y, 'Reachability', ha='center', va='center', 
            fontsize=16, fontweight='bold')
    
    # Interface and IP info below boxes
    info_y = box_y - 1
    
    # Left info (Attack side)
    ax.text(attack_x, info_y, f'Interface: {interface}', ha='center', va='top', 
            fontsize=16, fontstyle='italic')
    ax.text(attack_x, info_y - 0.25, f'IP source:', ha='center', va='top', 
            fontsize=16, fontstyle='italic')
    ax.text(attack_x, info_y - 0.5, source_ip, ha='center', va='top', 
            fontsize=16, fontweight='bold')
    
    # Right info (Reachability side)
    ax.text(reach_x, info_y, f'Interface: {interface}', ha='center', va='top', 
            fontsize=16, fontstyle='italic')
    
    # Arrows from boxes to cloud
    arrow_props = dict(arrowstyle='->', lw=3, color='black', 
                      connectionstyle="arc3,rad=0", mutation_scale=30)
    
    # Left arrow (Attack -> Cloud)
    left_arrow = FancyArrowPatch((attack_x, box_y + box_height/2 + 0.1), 
                                (cloud_x - 0.8, cloud_y - 0.6),
                                **arrow_props)
    ax.add_patch(left_arrow)
    
    # Right arrow (Reachability -> Cloud)
    right_arrow = FancyArrowPatch((reach_x, box_y + box_height/2 + 0.1), 
                                 (cloud_x + 0.8, cloud_y - 0.6),
                                 **arrow_props)
    ax.add_patch(right_arrow)
    
    # Connecting line at bottom (between Attack and Reachability through Tester)
    line_y = box_y - box_height/2 - 0.3
    ax.plot([attack_x, tester_x - box_width/2], [line_y, line_y], 
            'k-', linewidth=2)
    ax.plot([tester_x + box_width/2, reach_x], [line_y, line_y], 
            'k-', linewidth=2)
    
    # Vertical lines connecting boxes to horizontal line
    ax.plot([attack_x, attack_x], [box_y - box_height/2, line_y], 
            'k-', linewidth=2)
    ax.plot([reach_x, reach_x], [box_y - box_height/2, line_y], 
            'k-', linewidth=2)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Topology diagram saved to: {output_file}")
    return output_file


# Integration function for locust_report.py
def add_topology_to_report(story, styles, target_ip, source_ip, interface="ens33"):
    """
    Adds the topology diagram to the PDF report story.
    
    Args:
        story: ReportLab story list
        styles: ReportLab styles
        target_ip: Target IP address
        source_ip: Source IP address  
        interface: Network interface name
    """
    from reportlab.platypus import Image, Paragraph, Spacer
    
    topology_file = "topology_diagram.png"
    create_topology_diagram(target_ip, source_ip, interface, topology_file)
    
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


# Standalone test
if __name__ == "__main__":
    create_topology_diagram(
        target_ip="142.251.36.110",
        source_ip="192.168.10.10-40",
        interface="ens33",
        output_file="topology_diagram.png"
    )
    print("Topology diagram created successfully!")
