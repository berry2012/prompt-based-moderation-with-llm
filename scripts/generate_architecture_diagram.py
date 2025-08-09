#!/usr/bin/env python3
"""
Generate System Architecture Diagram
Creates a visual representation of the Real-Time Moderation System architecture
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_architecture_diagram():
    """Create the main architecture diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Define colors
    colors = {
        'input': '#E3F2FD',      # Light Blue
        'processing': '#F3E5F5',  # Light Purple
        'llm': '#E8F5E8',        # Light Green
        'decision': '#FFF3E0',    # Light Orange
        'storage': '#FFEBEE',     # Light Red
        'monitoring': '#F1F8E9'   # Light Lime
    }
    
    # Title
    ax.text(8, 11.5, 'Real-Time Moderation System Architecture', 
            fontsize=20, fontweight='bold', ha='center')
    
    # Input Layer
    chat_sim = FancyBboxPatch((0.5, 9), 3, 1.5, 
                              boxstyle="round,pad=0.1", 
                              facecolor=colors['input'], 
                              edgecolor='black', linewidth=1.5)
    ax.add_patch(chat_sim)
    ax.text(2, 9.75, 'Chat Simulator\n• WebSocket\n• Message Gen\n• Whisper STT', 
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Processing Layer
    filter_box = FancyBboxPatch((5, 9), 3, 1.5, 
                                boxstyle="round,pad=0.1", 
                                facecolor=colors['processing'], 
                                edgecolor='black', linewidth=1.5)
    ax.add_patch(filter_box)
    ax.text(6.5, 9.75, 'Lightweight Filter\n• Keyword Filter\n• Rate Limiting\n• PII Detection', 
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    mcp_box = FancyBboxPatch((10, 9), 3, 1.5, 
                             boxstyle="round,pad=0.1", 
                             facecolor=colors['processing'], 
                             edgecolor='black', linewidth=1.5)
    ax.add_patch(mcp_box)
    ax.text(11.5, 9.75, 'MCP Server\n• Prompt Management\n• LLM Interface\n• Validation', 
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Template System
    template_box = FancyBboxPatch((10, 6.5), 3, 1.5, 
                                  boxstyle="round,pad=0.1", 
                                  facecolor=colors['processing'], 
                                  edgecolor='black', linewidth=1.5)
    ax.add_patch(template_box)
    ax.text(11.5, 7.25, 'Prompt Templates\n• 7 Templates\n• Versioning\n• YAML Config', 
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    # LLM Layer
    llm_box = FancyBboxPatch((5, 6.5), 3, 1.5, 
                             boxstyle="round,pad=0.1", 
                             facecolor=colors['llm'], 
                             edgecolor='black', linewidth=1.5)
    ax.add_patch(llm_box)
    ax.text(6.5, 7.25, 'DeepSeek LLM\n• Chat API\n• JSON Response\n• Error Handling', 
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Decision Layer
    decision_box = FancyBboxPatch((5, 4), 3, 1.5, 
                                  boxstyle="round,pad=0.1", 
                                  facecolor=colors['decision'], 
                                  edgecolor='black', linewidth=1.5)
    ax.add_patch(decision_box)
    ax.text(6.5, 4.75, 'Decision Handler\n• Policy Engine\n• Action Execution\n• User History', 
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Storage Layer
    db_box = FancyBboxPatch((0.5, 4), 3, 1.5, 
                            boxstyle="round,pad=0.1", 
                            facecolor=colors['storage'], 
                            edgecolor='black', linewidth=1.5)
    ax.add_patch(db_box)
    ax.text(2, 4.75, 'Database Storage\n• PostgreSQL\n• User History\n• Decisions', 
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    redis_box = FancyBboxPatch((10, 4), 3, 1.5, 
                               boxstyle="round,pad=0.1", 
                               facecolor=colors['storage'], 
                               edgecolor='black', linewidth=1.5)
    ax.add_patch(redis_box)
    ax.text(11.5, 4.75, 'Redis Cache\n• Rate Limiting\n• Session Data\n• Temp Storage', 
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Monitoring Layer
    metrics_box = FancyBboxPatch((2.5, 1.5), 4, 1.5, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor=colors['monitoring'], 
                                 edgecolor='black', linewidth=1.5)
    ax.add_patch(metrics_box)
    ax.text(4.5, 2.25, 'Metrics & Monitoring\n• Prometheus • Grafana\n• Jaeger Tracing • Structured Logs', 
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    notification_box = FancyBboxPatch((9.5, 1.5), 4, 1.5, 
                                      boxstyle="round,pad=0.1", 
                                      facecolor=colors['monitoring'], 
                                      edgecolor='black', linewidth=1.5)
    ax.add_patch(notification_box)
    ax.text(11.5, 2.25, 'Notifications\n• Slack/Teams Webhooks\n• Alert Manager\n• Email Alerts', 
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Add arrows for data flow
    arrows = [
        # Main flow
        ((3.5, 9.75), (5, 9.75)),      # Chat Sim -> Filter
        ((8, 9.75), (10, 9.75)),       # Filter -> MCP
        ((11.5, 9), (11.5, 8)),        # MCP -> Templates
        ((10, 7.25), (8, 7.25)),       # Templates -> LLM
        ((6.5, 6.5), (6.5, 5.5)),      # LLM -> Decision
        ((5, 4.75), (3.5, 4.75)),      # Decision -> DB
        ((8, 4.75), (10, 4.75)),       # Decision -> Redis
        
        # Monitoring connections
        ((2, 5.5), (3, 3)),            # DB -> Metrics
        ((6.5, 4), (4.5, 3)),          # Decision -> Metrics
        ((8.5, 4.75), (10, 3)),        # Decision -> Notifications
    ]
    
    for start, end in arrows:
        arrow = ConnectionPatch(start, end, "data", "data",
                               arrowstyle="->", shrinkA=5, shrinkB=5,
                               mutation_scale=20, fc="black", lw=2)
        ax.add_patch(arrow)
    
    # Add legend
    legend_elements = [
        patches.Patch(color=colors['input'], label='Input Layer'),
        patches.Patch(color=colors['processing'], label='Processing Layer'),
        patches.Patch(color=colors['llm'], label='LLM Layer'),
        patches.Patch(color=colors['decision'], label='Decision Layer'),
        patches.Patch(color=colors['storage'], label='Storage Layer'),
        patches.Patch(color=colors['monitoring'], label='Monitoring Layer')
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
    
    # Add performance metrics
    ax.text(0.5, 0.5, 'Performance Targets:\n• Filter: <10ms\n• MCP: <200ms\n• Decision: <50ms\n• End-to-end: <500ms', 
            fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray'))
    
    plt.tight_layout()
    return fig

def create_deployment_diagram():
    """Create Kubernetes deployment diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(7, 9.5, 'EKS Cluster Deployment Architecture', 
            fontsize=18, fontweight='bold', ha='center')
    
    # Custom Nodepool
    custom_nodepool = FancyBboxPatch((1, 6), 12, 2.5, 
                                     boxstyle="round,pad=0.1", 
                                     facecolor='#E3F2FD', 
                                     edgecolor='blue', linewidth=2)
    ax.add_patch(custom_nodepool)
    ax.text(7, 8.2, 'Custom Nodepool (role=custom-workload)', 
            fontsize=14, fontweight='bold', ha='center')
    
    # Services in custom nodepool
    services = [
        ('MCP Server\n3 replicas\nHPA', 2, 7),
        ('Chat Simulator\n1 replica\nLoadBalancer', 5, 7),
        ('Lightweight Filter\n2 replicas\nClusterIP', 8, 7),
        ('Decision Handler\n2 replicas\nClusterIP', 11, 7)
    ]
    
    for service, x, y in services:
        service_box = FancyBboxPatch((x-0.8, y-0.4), 1.6, 0.8, 
                                     boxstyle="round,pad=0.05", 
                                     facecolor='white', 
                                     edgecolor='blue', linewidth=1)
        ax.add_patch(service_box)
        ax.text(x, y, service, ha='center', va='center', fontsize=8)
    
    # Default Nodepool
    default_nodepool = FancyBboxPatch((1, 3), 12, 2.5, 
                                      boxstyle="round,pad=0.1", 
                                      facecolor='#F3E5F5', 
                                      edgecolor='purple', linewidth=2)
    ax.add_patch(default_nodepool)
    ax.text(7, 5.2, 'Default Nodepool', 
            fontsize=14, fontweight='bold', ha='center')
    
    # Infrastructure services
    infra_services = [
        ('PostgreSQL\nStatefulSet', 2, 4),
        ('Redis\nDeployment', 4.5, 4),
        ('Prometheus\nDeployment', 7, 4),
        ('Grafana\nDeployment', 9.5, 4),
        ('DeepSeek LLM\nExisting', 12, 4)
    ]
    
    for service, x, y in infra_services:
        service_box = FancyBboxPatch((x-0.7, y-0.4), 1.4, 0.8, 
                                     boxstyle="round,pad=0.05", 
                                     facecolor='white', 
                                     edgecolor='purple', linewidth=1)
        ax.add_patch(service_box)
        ax.text(x, y, service, ha='center', va='center', fontsize=8)
    
    # Storage layer
    storage_box = FancyBboxPatch((1, 0.5), 12, 1.5, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor='#FFEBEE', 
                                 edgecolor='red', linewidth=2)
    ax.add_patch(storage_box)
    ax.text(7, 1.7, 'Persistent Storage', 
            fontsize=14, fontweight='bold', ha='center')
    
    storage_items = [
        ('PostgreSQL PVC\n10Gi', 3, 1.2),
        ('Prometheus PVC\n20Gi', 7, 1.2),
        ('Grafana PVC\n5Gi', 11, 1.2)
    ]
    
    for item, x, y in storage_items:
        item_box = FancyBboxPatch((x-0.8, y-0.3), 1.6, 0.6, 
                                  boxstyle="round,pad=0.05", 
                                  facecolor='white', 
                                  edgecolor='red', linewidth=1)
        ax.add_patch(item_box)
        ax.text(x, y, item, ha='center', va='center', fontsize=8)
    
    plt.tight_layout()
    return fig

def main():
    """Generate and save architecture diagrams"""
    import os
    
    # Create output directory
    output_dir = "../docs/images"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate main architecture diagram
    print("Generating main architecture diagram...")
    fig1 = create_architecture_diagram()
    fig1.savefig(f"{output_dir}/system_architecture.png", dpi=300, bbox_inches='tight')
    fig1.savefig(f"{output_dir}/system_architecture.pdf", bbox_inches='tight')
    
    # Generate deployment diagram
    print("Generating deployment diagram...")
    fig2 = create_deployment_diagram()
    fig2.savefig(f"{output_dir}/deployment_architecture.png", dpi=300, bbox_inches='tight')
    fig2.savefig(f"{output_dir}/deployment_architecture.pdf", bbox_inches='tight')
    
    print(f"Diagrams saved to {output_dir}/")
    print("Files generated:")
    print("- system_architecture.png")
    print("- system_architecture.pdf")
    print("- deployment_architecture.png")
    print("- deployment_architecture.pdf")
    
    # Show diagrams
    plt.show()

if __name__ == "__main__":
    main()
