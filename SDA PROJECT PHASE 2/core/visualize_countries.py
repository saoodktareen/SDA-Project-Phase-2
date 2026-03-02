import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from functools import reduce
from itertools import cycle
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

# Set professional theme globally
sns.set_palette(PROFESSIONAL_PALETTE)

def configure_plot_style():
    """Configure professional matplotlib styling with proper centering."""
    plt.style.use("dark_background")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 12,
        "axes.titlesize": 18,
        "axes.titleweight": "bold",
        "axes.labelsize": 13,
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
        "figure.autolayout": True,
    })

# ==================== UTILITY FUNCTIONS ====================

def prepare_country_data(df, countries, operation):
    """Prepare aggregated data for each country using functional approach."""
    aggregate_func = "sum" if operation == "sum" else "mean"
    
    return dict(
        map(
            lambda country: (
                country,
                df[df["Country Name"] == country]
                .groupby("Year")["GDP"]
                .agg(aggregate_func)
                .reset_index()
            ),
            countries
        )
    )

def print_summary_stats(country_data, operation):
    """Print country statistics using functional style."""
    print("\n" + "="*60)
    print("📊 COUNTRY GDP ANALYSIS SUMMARY".center(60))
    print("="*60)
    
    list(
        map(
            lambda item: print(
                f"\n{item[0]:>20} → {'Total GDP: $' + f'{item[1]['GDP'].sum():,.2f}' + 'T' if operation == 'sum' else 'Avg GDP: $' + f'{item[1]['GDP'].mean():,.2f}' + 'T'}"
            ),
            country_data.items()
        )
    )
    print("\n" + "="*60 + "\n")

def maximize_window():
    """Maximize the plot window if possible."""
    try:
        manager = plt.get_current_fig_manager()
        manager.window.state('zoomed')
    except:
        pass

# ==================== VISUALIZATION FUNCTIONS ====================

def create_line_chart(country_data):
    """Create professional line chart with proper styling."""
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Plot lines using functional style with enumeration for colors
    list(
        map(
            lambda idx_item: ax.plot(
                idx_item[1][1]["Year"],
                idx_item[1][1]["GDP"],
                marker="o",
                linewidth=2.5,
                markersize=6,
                color=PROFESSIONAL_PALETTE[idx_item[0] % len(PROFESSIONAL_PALETTE)],
                label=idx_item[1][0],
                alpha=0.9
            ),
            enumerate(country_data.items())
        )
    )
    
    # Professional styling
    ax.set_title("GDP Trends Over Time", fontsize=22, fontweight="bold", pad=20, color="#FFFFFF")
    ax.set_xlabel("Year", fontsize=14, fontweight="bold", labelpad=10)
    ax.set_ylabel("GDP (Trillions USD)", fontsize=14, fontweight="bold", labelpad=10)
    
    # Centered legend with professional styling
    ax.legend(
        loc="upper left",
        frameon=True,
        fancybox=True,
        shadow=True,
        ncol=2 if len(country_data) > 4 else 1,
        fontsize=11
    )
    
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.8)
    plt.tight_layout()
    
    # Add Next button
    ax_button = plt.axes([0.02, 0.02, 0.1, 0.05])
    btn = Button(ax_button, 'Next →', color='white', hovercolor='#E5E7EB')
    btn.label.set_color('black')
    btn.label.set_fontweight('bold')
    btn.on_clicked(lambda event: plt.close())
    
    maximize_window()
    plt.show()

def create_bar_comparison(country_data, operation):
    """Create centered bar chart comparing countries."""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Calculate aggregate values
    countries = list(country_data.keys())
    values = list(
        map(
            lambda item: item[1]["GDP"].sum() if operation == "sum" else item[1]["GDP"].mean(),
            country_data.items()
        )
    )
    
    # Create centered bar chart
    bars = ax.bar(
        countries,
        values,
        color=PROFESSIONAL_PALETTE[:len(countries)],
        edgecolor="white",
        linewidth=1.5,
        alpha=0.85,
        width=0.6
    )
    
    # Add value labels on top of bars
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
    
    title_text = "Total GDP Comparison" if operation == "sum" else "Average GDP Comparison"
    ax.set_title(title_text, fontsize=22, fontweight="bold", pad=20, color="#FFFFFF")
    ax.set_ylabel("GDP (Trillions USD)", fontsize=14, fontweight="bold", labelpad=10)
    ax.set_xlabel("Country", fontsize=14, fontweight="bold", labelpad=10)
    
    # Rotate x-labels for better readability
    plt.xticks(rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle="--", linewidth=0.8)
    
    plt.tight_layout()
    
    # Add Next button
    ax_button = plt.axes([0.02, 0.02, 0.1, 0.05])
    btn = Button(ax_button, 'Next →', color='white', hovercolor='#E5E7EB')
    btn.label.set_color('black')
    btn.label.set_fontweight('bold')
    btn.on_clicked(lambda event: plt.close())
    
    maximize_window()
    plt.show()

def create_area_chart(country_data):
    """Create stacked area chart for GDP trends."""
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Get all years (assuming all countries have same years)
    first_country_data = next(iter(country_data.values()))
    years = first_country_data["Year"].values
    
    # Stack data for area plot
    gdp_values = np.column_stack([
        country_data[country]["GDP"].values
        for country in country_data.keys()
    ])
    
    ax.stackplot(
        years,
        gdp_values.T,
        labels=list(country_data.keys()),
        colors=PROFESSIONAL_PALETTE[:len(country_data)],
        alpha=0.7,
        edgecolor='white',
        linewidth=0.5
    )
    
    ax.set_title("Cumulative GDP Contribution Over Time", fontsize=22, fontweight="bold", pad=20, color="#FFFFFF")
    ax.set_xlabel("Year", fontsize=14, fontweight="bold", labelpad=10)
    ax.set_ylabel("Cumulative GDP (Trillions USD)", fontsize=14, fontweight="bold", labelpad=10)
    
    ax.legend(
        loc="upper left",
        frameon=True,
        fancybox=True,
        shadow=True,
        ncol=2 if len(country_data) > 4 else 1
    )
    
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.8)
    plt.tight_layout()
    
    # Add Next button
    ax_button = plt.axes([0.02, 0.02, 0.1, 0.05])
    btn = Button(ax_button, 'Next →', color='white', hovercolor='#E5E7EB')
    btn.label.set_color('black')
    btn.label.set_fontweight('bold')
    btn.on_clicked(lambda event: plt.close())
    
    maximize_window()
    plt.show()

def create_scatter_with_trend(country_data):
    """Create scatter plot with trend lines."""
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Plot scatter and trend lines
    list(
        map(
            lambda idx_item: (
                ax.scatter(
                    idx_item[1][1]["Year"],
                    idx_item[1][1]["GDP"],
                    s=80,
                    color=PROFESSIONAL_PALETTE[idx_item[0] % len(PROFESSIONAL_PALETTE)],
                    label=idx_item[1][0],
                    alpha=0.7,
                    edgecolors='white',
                    linewidth=0.5
                ),
                # Add trend line
                ax.plot(
                    idx_item[1][1]["Year"],
                    np.poly1d(np.polyfit(idx_item[1][1]["Year"], idx_item[1][1]["GDP"], 2))(idx_item[1][1]["Year"]),
                    color=PROFESSIONAL_PALETTE[idx_item[0] % len(PROFESSIONAL_PALETTE)],
                    linestyle='--',
                    linewidth=2,
                    alpha=0.5
                )
            ),
            enumerate(country_data.items())
        )
    )
    
    ax.set_title("GDP Scatter Analysis with Trend Lines", fontsize=22, fontweight="bold", pad=20, color="#FFFFFF")
    ax.set_xlabel("Year", fontsize=14, fontweight="bold", labelpad=10)
    ax.set_ylabel("GDP (Trillions USD)", fontsize=14, fontweight="bold", labelpad=10)
    
    ax.legend(
        loc="upper left",
        frameon=True,
        fancybox=True,
        shadow=True,
        ncol=2 if len(country_data) > 4 else 1
    )
    
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.8)
    plt.tight_layout()
    
    # Add Next button
    ax_button = plt.axes([0.02, 0.02, 0.1, 0.05])
    btn = Button(ax_button, 'Next →', color='white', hovercolor='#E5E7EB')
    btn.label.set_color('black')
    btn.label.set_fontweight('bold')
    btn.on_clicked(lambda event: plt.close())
    
    maximize_window()
    plt.show()

# ==================== MAIN VISUALIZATION FUNCTION ====================

# ==================== COLORS ====================
COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#06B6D4", "#EC4899", "#14B8A6"]

# ==================== SETUP ====================
def setup_style():
    """Setup plot style - dark background"""
    plt.style.use("dark_background")
    plt.rcParams["font.size"] = 10
    plt.rcParams["figure.facecolor"] = "#1a1a1a"
    plt.rcParams["axes.facecolor"] = "#262626"

# ==================== HELPER FUNCTIONS ====================
def get_country_data(df, country, operation):
    """Get GDP data for one country"""
    country_df = df[df["Country Name"] == country]
    
    if operation == "sum":
        result = country_df.groupby("Year")["GDP"].sum().reset_index()
    else:
        result = country_df.groupby("Year")["GDP"].mean().reset_index()
    
    return result

def print_stats(country, data, operation):
    """Print stats for one country"""
    if operation == "sum":
        total = data["GDP"].sum()
        print(f"{country:>20} → Total GDP: ${total:,.2f}T")
    else:
        avg = data["GDP"].mean()
        print(f"{country:>20} → Avg GDP: ${avg:,.2f}T")

# ==================== CHART DRAWING FUNCTIONS ====================
def draw_line_chart(ax, country_data_list, countries):
    """Draw line chart"""
    ax.clear()
    
    for i, (country, data) in enumerate(zip(countries, country_data_list)):
        color = COLORS[i % len(COLORS)]
        ax.plot(data["Year"], data["GDP"], marker="o", linewidth=2,
               markersize=5, color=color, label=country, alpha=0.9)
    
    ax.set_title("GDP Trends Over Time", fontsize=16, fontweight="bold", pad=10)
    ax.set_xlabel("Year", fontsize=11, fontweight="bold")
    ax.set_ylabel("GDP (Trillions USD)", fontsize=11, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle="--")

def draw_bar_chart(ax, country_data_list, countries, operation):
    """Draw bar chart"""
    ax.clear()
    
    if operation == "sum":
        values = list(map(lambda data: data["GDP"].sum(), country_data_list))
        title = "Total GDP Comparison"
    else:
        values = list(map(lambda data: data["GDP"].mean(), country_data_list))
        title = "Average GDP Comparison"
    
    colors_list = [COLORS[i % len(COLORS)] for i in range(len(countries))]
    bars = ax.bar(countries, values, color=colors_list, edgecolor="white",
                 linewidth=1.2, alpha=0.85, width=0.6)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height, f'${height:.2f}T',
               ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax.set_title(title, fontsize=16, fontweight="bold", pad=10)
    ax.set_ylabel("GDP (Trillions USD)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Country", fontsize=11, fontweight="bold")
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle="--")

def draw_area_chart(ax, country_data_list, countries):
    """Draw area chart"""
    ax.clear()
    
    years = country_data_list[0]["Year"].values
    gdp_matrix = np.column_stack([data["GDP"].values for data in country_data_list])
    
    colors_list = [COLORS[i % len(COLORS)] for i in range(len(countries))]
    ax.stackplot(years, gdp_matrix.T, labels=countries, colors=colors_list,
                alpha=0.7, edgecolor='white', linewidth=0.5)
    
    ax.set_title("Cumulative GDP Over Time", fontsize=16, fontweight="bold", pad=10)
    ax.set_xlabel("Year", fontsize=11, fontweight="bold")
    ax.set_ylabel("Cumulative GDP (Trillions USD)", fontsize=11, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle="--")

def draw_scatter_chart(ax, country_data_list, countries):
    """Draw scatter plot"""
    ax.clear()
    
    for i, (country, data) in enumerate(zip(countries, country_data_list)):
        color = COLORS[i % len(COLORS)]
        years = data["Year"].values
        gdp = data["GDP"].values
        
        ax.scatter(years, gdp, s=80, color=color, label=country,
                  alpha=0.7, edgecolors='white', linewidth=1)
        
        trend = np.poly1d(np.polyfit(years, gdp, 2))
        ax.plot(years, trend(years), color=color, linestyle='--',
               linewidth=2, alpha=0.5)
    
    ax.set_title("GDP Scatter with Trend Lines", fontsize=16, fontweight="bold", pad=10)
    ax.set_xlabel("Year", fontsize=11, fontweight="bold")
    ax.set_ylabel("GDP (Trillions USD)", fontsize=11, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle="--")

# ==================== MAIN VISUALIZATION ====================
def visualize_countries(df, config):
    """
    Main visualization function using functional programming style.
    Creates multiple professional, centered visualizations.
    """
    # Configure styling
    configure_plot_style()
    
    # Extract configuration
    countries = config["country"]
    operation = config["operation"]
    
    # Prepare data
    country_data = prepare_country_data(df, countries, operation)
    
    # Print summary
    print_summary_stats(country_data, operation)
    
    # Create all visualizations using functional composition
    visualizations = [
        create_line_chart,
        create_bar_comparison,
        create_area_chart,
        create_scatter_with_trend
    ]
    
    # Execute visualizations
    list(
        map(
            lambda viz_func: (
                viz_func(country_data, operation) 
                if viz_func == create_bar_comparison 
                else viz_func(country_data)
            ),
            visualizations
        )
    )
