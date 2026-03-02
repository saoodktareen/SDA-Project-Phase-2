import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from .process import process
from functools import reduce
from matplotlib.widgets import Button

# ==================== PROFESSIONAL COLOR SCHEME ====================
PROFESSIONAL_PALETTE = [
    "#3B82F6",  # Professional Blue
    "#10B981",  # Success Green
    "#F59E0B",  # Warm Amber
    "#8B5CF6",  # Royal Purple
    "#EF4444",  # Confident Red
    "#06B6D4",  # Modern Cyan
    "#EC4899",  # Vibrant Pink
    "#14B8A6",  # Teal
]

HIGHLIGHT_COLOR = "#F59E0B"  # Amber for focus regions

def configure_plot_style():
    """Configure professional matplotlib styling."""
    plt.style.use("dark_background")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 12,
        "axes.titlesize": 20,
        "axes.titleweight": "bold",
        "axes.labelsize": 14,
        "axes.labelweight": "bold",
        "axes.edgecolor": "#555555",
        "axes.linewidth": 1.5,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "grid.color": "#555555",
        "figure.facecolor": "#1a1a1a",
        "axes.facecolor": "#262626",
        "legend.fontsize": 11,
        "legend.framealpha": 0.9,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "figure.autolayout": False,
    })

def maximize_window():
    """Maximize the plot window if possible."""
    try:
        manager = plt.get_current_fig_manager()
        manager.window.state('zoomed')
    except:
        try:
            manager.window.showMaximized()
        except:
            pass

def create_bar_chart(region_gdp, focus_regions, year, operation):
    """Create professional bar chart for regions."""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Assign colors using functional style
    colors = list(
        map(
            lambda item: HIGHLIGHT_COLOR if item[1] in focus_regions 
            else PROFESSIONAL_PALETTE[item[0] % len(PROFESSIONAL_PALETTE)],
            enumerate(region_gdp["Continent"])
        )
    )
    
    # Create bars
    bars = ax.bar(
        region_gdp["Continent"],
        region_gdp["GDP"],
        color=colors,
        edgecolor="white",
        linewidth=1.5,
        alpha=0.85,
        width=0.65
    )
    
    # Add value labels on top of bars using map
    list(
        map(
            lambda bar: ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f'${bar.get_height():.2f}T',
                ha='center',
                va='bottom',
                fontsize=11,
                fontweight='bold',
                color='white'
            ),
            bars
        )
    )
    
    # Styling
    ax.set_title(
        f"{operation.capitalize()} GDP by Region ({year})",
        fontsize=22,
        fontweight="bold",
        pad=20,
        color="#FFFFFF"
    )
    ax.set_xlabel("Region", fontsize=14, fontweight="bold", labelpad=10)
    ax.set_ylabel(f"{operation.capitalize()} GDP (Trillions USD)", fontsize=14, fontweight="bold", labelpad=10)
    
    # Highlight focus region labels using map
    list(
        map(
            lambda label: (
                label.set_color(HIGHLIGHT_COLOR),
                label.set_fontweight("bold"),
                label.set_fontsize(13)
            ) if label.get_text() in focus_regions else (
                label.set_color("white"),
            ),
            ax.get_xticklabels()
        )
    )
    
    plt.xticks(rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle="--", linewidth=0.8)
    
    # Extra space at bottom and proper layout
    plt.subplots_adjust(left=0.1, right=0.95, top=0.92, bottom=0.18)
    
    # Add Next button
    ax_button = plt.axes([0.02, 0.02, 0.1, 0.05])
    btn = Button(ax_button, 'Next →', color='white', hovercolor='#E5E7EB')
    btn.label.set_color('black')
    btn.label.set_fontweight('bold')
    btn.on_clicked(lambda event: plt.close())
    
    maximize_window()
    plt.show()

def create_pie_chart(region_gdp, focus_regions, year, operation):
    """Create professional pie chart for regions."""
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Assign colors using functional style with stateful closure
    def create_color_mapper():
        state = {"color_index": 0}
        
        def get_color(region):
            if region in focus_regions:
                return HIGHLIGHT_COLOR
            else:
                color = PROFESSIONAL_PALETTE[state["color_index"] % len(PROFESSIONAL_PALETTE)]
                state["color_index"] += 1
                return color
        
        return get_color
    
    pie_colors = list(map(create_color_mapper(), region_gdp["Continent"]))
    
    # Create pie chart WITHOUT explode (no protrusion)
    wedges, texts, autotexts = ax.pie(
        region_gdp["GDP"],
        labels=region_gdp["Continent"],
        autopct='%1.1f%%',
        colors=pie_colors,
        startangle=140,
        shadow=True,
        textprops={'fontsize': 12, 'fontweight': 'bold'}
    )
    
    # Highlight focus labels using map
    list(
        map(
            lambda text: (
                text.set_color(HIGHLIGHT_COLOR),
                text.set_fontweight("bold"),
                text.set_fontsize(14)
            ) if text.get_text() in focus_regions else (
                text.set_color("white"),
                text.set_fontsize(12)
            ),
            texts
        )
    )
    
    # Style percentage text using map
    list(
        map(
            lambda autotext: (
                autotext.set_color('white'),
                autotext.set_fontweight('bold'),
                autotext.set_fontsize(11)
            ),
            autotexts
        )
    )
    
    ax.set_title(
        f"{operation.capitalize()} GDP Share by Region ({year})",
        fontsize=22,
        fontweight="bold",
        pad=15,
        color="#FFFFFF",
        y=0.98
    )
    
    # Proper spacing for pie chart with more top margin
    plt.subplots_adjust(left=0.05, right=0.95, top=0.88, bottom=0.05)
    
    # Add Next button
    ax_button = plt.axes([0.02, 0.02, 0.1, 0.05])
    btn = Button(ax_button, 'Next →', color='white', hovercolor='#E5E7EB')
    btn.label.set_color('black')
    btn.label.set_fontweight('bold')
    btn.on_clicked(lambda event: plt.close())
    
    maximize_window()
    plt.show()

def create_heatmap(region_gdp, focus_regions, year, operation):
    """Create professional heatmap for regions."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create heatmap
    sns.heatmap(
        region_gdp.set_index("Continent"),
        annot=True,
        fmt=".2f",
        cmap="rocket_r",
        cbar_kws={'label': 'GDP (Trillions USD)'},
        linewidths=2,
        linecolor='#1a1a1a',
        ax=ax,
        annot_kws={'fontsize': 12, 'fontweight': 'bold'}
    )
    
    # Highlight focus region labels using map
    list(
        map(
            lambda label: (
                label.set_color(HIGHLIGHT_COLOR),
                label.set_fontweight("bold"),
                label.set_fontsize(14)
            ) if label.get_text() in focus_regions else (
                label.set_color("white"),
                label.set_fontsize(12)
            ),
            ax.get_yticklabels()
        )
    )
    
    ax.set_title(
        f"{operation.capitalize()} GDP Heatmap ({year})",
        fontsize=22,
        fontweight="bold",
        pad=20,
        color="#FFFFFF"
    )
    ax.set_xlabel("GDP Value", fontsize=14, fontweight="bold", labelpad=10)
    ax.set_ylabel("Region", fontsize=14, fontweight="bold", labelpad=10)
    
    # Style colorbar
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=11, colors='white')
    cbar.set_label('GDP (Trillions USD)', fontsize=12, fontweight='bold', color='white')
    
    plt.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.1)
    
    # Add Next button
    ax_button = plt.axes([0.02, 0.02, 0.1, 0.05])
    btn = Button(ax_button, 'Next →', color='white', hovercolor='#E5E7EB')
    btn.label.set_color('black')
    btn.label.set_fontweight('bold')
    btn.on_clicked(lambda event: plt.close())
    
    maximize_window()
    plt.show()

def visualize_regions(df, config):
    """
    Main visualization function for regions with professional styling.
    Uses pure functional programming style.
    """
    # Configure styling
    configure_plot_style()
    
    years = config["year"]
    focus_regions = config["region"]
    operation = config["operation"]

    print("\n" + "="*60)
    print("📊 REGION GDP ANALYSIS".center(60))
    print("="*60)

    # Process each year using map (functional style)
    def process_year(year):
        year_df = df[df["Year"] == year]
        region_gdp = process(year_df, config, "Continent").sort_values("GDP", ascending=False)
        
        # Terminal output
        print(f"\n{'Year: ' + str(year):^60}")
        print("-" * 60)
        
        # Conditional output based on operation (functional style)
        if operation == "sum":
            list(
                map(
                    lambda row: print(f"  {row[1]['Continent']:>20} → Total GDP: ${row[1]['GDP']:.2f}T"),
                    filter(
                        lambda row: row[1]["Continent"] in focus_regions,
                        region_gdp.iterrows()
                    )
                )
            )
        elif operation == "average":
            print(f"  {'Average GDP across all regions:':<40} ${region_gdp['GDP'].mean():.2f}T")
        
        print("-" * 60)
        
        # Create visualizations
        create_bar_chart(region_gdp, focus_regions, year, operation)
        create_pie_chart(region_gdp, focus_regions, year, operation)
        create_heatmap(region_gdp, focus_regions, year, operation)
    
    list(map(process_year, years))

    print("\n" + "="*60 + "\n")