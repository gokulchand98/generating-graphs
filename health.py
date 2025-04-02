import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
import os
import numpy as np
from datetime import datetime

# Load data from CSV file
df = pd.read_csv('IHME_HEALTH_SPENDING_1995_2021.CSV')

# Filter data for the last two decades (2003-2021)
df = df[df['year'].between(2003, 2021)]


# Function to generate HTML with custom dashboard
def generate_dashboard(selected_location):
    # Filter data for the selected location
    df_location = df[df['location_name'] == selected_location]

    if df_location.empty:
        print(f"No data found for '{selected_location}'. Please check the spelling or choose another location.")
        return None

    # Calculate some statistics for the dashboard cards
    latest_year = df_location['year'].max()
    earliest_year = df_location['year'].min()

    latest_the = df_location[df_location['year'] == latest_year]['the_total_mean'].values[0]
    earliest_the = df_location[df_location['year'] == earliest_year]['the_total_mean'].values[0]

    percent_change = ((latest_the - earliest_the) / earliest_the) * 100

    # Calculate average annual growth
    years_span = latest_year - earliest_year
    avg_annual_growth = (((latest_the / earliest_the) ** (1 / years_span)) - 1) * 100

    # Convert values to millions for display
    latest_the_millions = latest_the / 1000000
    earliest_the_millions = earliest_the / 1000000

    # Get the funding source composition for the latest year
    funding_columns = ['ghes_total_mean', 'ppp_total_mean', 'oop_total_mean', 'dah_total_mean']
    latest_data = df_location[df_location['year'] == latest_year]

    funding_composition = {}
    for col in funding_columns:
        if col in latest_data.columns:
            value = latest_data[col].values[0]
            if not np.isnan(value):
                funding_composition[col] = value

    # Calculate percentages
    total_specified = sum(funding_composition.values())
    funding_percentages = {k: (v / latest_the) * 100 for k, v in funding_composition.items()}

    # Define funding sources with their labels and columns
    funding_sources = [
        ('Total Health Expenditure', 'the_total_mean', '#3B82F6'),  # Modern blue
        ('Government Health Expenditure', 'ghes_total_mean', '#EF4444'),  # Modern red
        ('Prepaid Private Plans', 'ppp_total_mean', '#10B981'),  # Modern green
        ('Out-of-Pocket Spending', 'oop_total_mean', '#F59E0B'),  # Modern amber
        ('Development Assistance for Health', 'dah_total_mean', '#8B5CF6')  # Modern purple
    ]

    # Create a figure with subplots
    fig = make_subplots(rows=1, cols=1)

    # Add traces for each funding source
    for source_name, column, color in funding_sources:
        # Check if the column exists
        if column not in df_location.columns:
            continue

        # Get corresponding lower and upper bound columns
        lower_col = column.replace('_mean', '_lower')
        upper_col = column.replace('_mean', '_upper')

        # Create customdata for hover information
        years = df_location['year'].values

        # Convert the main values to millions for display
        y_values_millions = df_location[column].values / 1000000

        if lower_col in df_location.columns and upper_col in df_location.columns:
            # Add customdata for hover information
            customdata = np.column_stack((
                df_location[lower_col].values / 1000000,  # Lower bound in millions
                df_location[upper_col].values / 1000000,  # Upper bound in millions
                years  # Year
            ))

            # Simple hover template with white text - FIXED TOOLTIP VALUES
            hovertemplate = (
                    '<span style="color: white; font-weight: bold; font-family: Inter, sans-serif;">' +
                    'Year: %{customdata[2]}<br>' +
                    f'{source_name}<br>' +
                    'Value: $%{customdata[0]:.1f}M - $%{customdata[1]:.1f}M<br>' +
                    'Mean: $%{y:.1f}M<br>' +
                    '</span>' +
                    '<extra></extra>'
            )
        else:
            customdata = np.column_stack((years,))

            hovertemplate = (
                    '<span style="color: white; font-weight: bold; font-family: Inter, sans-serif;">' +
                    'Year: %{customdata[0]}<br>' +
                    f'{source_name}<br>' +
                    'Value: $%{y:.1f}M<br>' +
                    '</span>' +
                    '<extra></extra>'
            )

        # Add boxplot trace with enhanced styling for better box visibility
        fig.add_trace(
            go.Box(
                y=y_values_millions,  # Use values in millions
                x=df_location['year'],
                name=source_name,
                marker=dict(
                    color=color,
                    size=10,  # Increased marker size
                    line=dict(
                        width=2,
                        color='rgba(255, 255, 255, 0.8)'
                    ),
                    opacity=0.8  # Slightly reduce opacity of points to make boxes more visible
                ),
                line=dict(
                    color=color,
                    width=4  # Significantly increased line width for better visibility
                ),
                fillcolor=color.replace('rgb', 'rgba').replace(')', ', 0.2)'),  # Increased fill opacity
                hovertemplate=hovertemplate,
                customdata=customdata,
                boxpoints='all',  # Show all points
                jitter=0.2,  # Reduced jitter to keep points closer to the box
                pointpos=0,  # Position of points relative to box
                boxmean=True,  # Show the mean
                whiskerwidth=1.0,  # Maximum valid whisker width (must be between 0 and 1)
                notched=True,  # Add notches to boxplot
                notchwidth=0.5,
                quartilemethod="linear"  # Ensure consistent quartile calculation
            )
        )

    # Update layout with enhanced styling for better box visibility
    fig.update_layout(
        template='plotly_white',
        height=550,
        width=None,  # Set width to None to make it fully responsive
        margin=dict(t=20, b=130, l=80, r=40),  # Increased bottom margin for legend
        plot_bgcolor='rgba(249, 250, 251, 0.5)',  # Lighter background to make boxes stand out more
        paper_bgcolor='rgba(0,0,0,0)',
        boxmode='group',  # Group boxes of the same x value
        boxgap=0.3,  # Increased gap between boxes for better separation
        boxgroupgap=0.4,  # Increased gap between box groups
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.25,  # Moved legend further down
            xanchor="center",
            x=0.5,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(229, 231, 235, 0.7)',
            borderwidth=1,
            font=dict(
                family="Inter, sans-serif",
                size=12,
                color='#1F2937'
            )
        ),
        font=dict(
            family="Inter, sans-serif",
            color='#1F2937'
        ),
        autosize=True  # Enable autosize for responsiveness
    )

    # Update axes with modern styling
    fig.update_xaxes(
        tickangle=45,
        tickmode='array',
        tickvals=sorted(df_location['year'].unique()),
        title=dict(
            text='Year',
            font=dict(
                family="Inter, sans-serif",
                size=14,
                color='#111827'
            )
        ),
        tickfont=dict(
            family="Inter, sans-serif",
            size=12,
            color='#374151'
        ),
        showgrid=True,
        gridcolor='rgba(229, 231, 235, 0.5)',
        showline=True,
        linewidth=1,
        linecolor='rgba(209, 213, 219, 0.8)',
        zeroline=False
    )

    # Format y-axis for currency with modern styling
    fig.update_yaxes(
        tickprefix='$',
        ticksuffix='M',  # Add 'M' suffix to indicate millions
        title=dict(
            text='Spending (Millions USD)',  # Updated label to clarify millions
            font=dict(
                family="Inter, sans-serif",
                size=14,
                color='#111827'
            ),
            standoff=15
        ),
        tickfont=dict(
            family="Inter, sans-serif",
            size=12,
            color='#374151'
        ),
        showgrid=True,
        gridcolor='rgba(229, 231, 235, 0.5)',
        showline=True,
        linewidth=1,
        linecolor='rgba(209, 213, 219, 0.8)',
        zeroline=False
    )

    # Convert the plot to JSON for embedding
    plot_json = fig.to_json()

    # Generate HTML with custom dashboard
    html_content = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Health Financing Dashboard - {selected_location}</title>

        <!-- Google Fonts -->
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Merriweather:wght@300;400;700;900&display=swap" rel="stylesheet">

        <!-- Modern UI Libraries -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

        <!-- Plotly.js -->
        <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>

        <!-- GSAP for animations -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.11.4/gsap.min.js"></script>

        <!-- Custom Styling -->
        <style>
            :root {{
                --primary-color: #3B82F6;
                --secondary-color: #EF4444;
                --tertiary-color: #10B981;
                --quaternary-color: #F59E0B;
                --accent-color: #8B5CF6;
                --light-bg: #F9FAFB;
                --dark-bg: #111827;
                --text-color: #1F2937;
                --light-text: #6B7280;
                --header-font: 'Merriweather', serif;
                --body-font: 'Inter', sans-serif;
                --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
                --shadow-md: 0 4px 6px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.1);
                --shadow-lg: 0 10px 15px rgba(0,0,0,0.05), 0 4px 6px rgba(0,0,0,0.05);
                --rounded-sm: 0.25rem;
                --rounded-md: 0.375rem;
                --rounded-lg: 0.5rem;
                --transition-normal: all 0.3s ease;
            }}

            body {{
                font-family: var(--body-font);
                color: var(--text-color);
                background: linear-gradient(135deg, var(--light-bg) 0%, #eef2f7 100%);
                margin: 0;
                padding: 0;
                min-height: 100vh;
                line-height: 1.6;
            }}

            h1, h2, h3, h4, h5, h6 {{
                font-family: var(--header-font);
                font-weight: 700;
                color: var(--dark-bg);
                line-height: 1.3;
            }}

            .dashboard-container {{
                max-width: 1280px;
                margin: 0 auto;
                padding: 2rem;
            }}

            .dashboard-header {{
                padding: 1.5rem 0;
                margin-bottom: 2rem;
                border-bottom: 1px solid rgba(0,0,0,0.05);
            }}

            .dashboard-title {{
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
                color: var(--dark-bg);
                letter-spacing: -0.025em;
            }}

            .dashboard-subtitle {{
                font-size: 1.2rem;
                color: var(--light-text);
                font-weight: 400;
            }}

            /* Enhanced location display */
            .dashboard-headline {{
                position: relative;
            }}

            .dashboard-location-badge {{
                display: inline-block;
                font-size: 1.1rem;
                font-weight: 600;
                color: var(--primary-color);
                background-color: rgba(59, 130, 246, 0.1);
                padding: 0.35rem 0.75rem;
                border-radius: var(--rounded-md);
                margin-bottom: 0.5rem;
                border-left: 4px solid var(--primary-color);
            }}

            .dashboard-logo {{
                margin-bottom: 1.5rem;
            }}

            .time-period {{
                font-size: 0.9rem;
                color: var(--light-text);
                background: rgba(0,0,0,0.05);
                padding: 0.25rem 0.5rem;
                border-radius: var(--rounded-sm);
                margin-left: 0.5rem;
            }}

            .stat-card {{
                background: white;
                border-radius: var(--rounded-md);
                box-shadow: var(--shadow-md);
                padding: 1.5rem;
                height: 100%;
                transition: var(--transition-normal);
                display: flex;
                flex-direction: column;
                position: relative;
                overflow: hidden;
                border: 1px solid rgba(229, 231, 235, 0.5);
            }}

            .stat-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background-color: var(--primary-color);
                opacity: 0;
                transition: var(--transition-normal);
            }}

            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: var(--shadow-lg);
            }}

            .stat-card:hover::before {{
                opacity: 1;
            }}

            .stat-card-title {{
                font-size: 0.9rem;
                font-weight: 600;
                color: var(--light-text);
                margin-bottom: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}

            .stat-card-value {{
                font-size: 2rem;
                font-weight: 700;
                margin-bottom: 0.25rem;
                letter-spacing: -0.025em;
            }}

            .stat-card-subtitle {{
                font-size: 0.9rem;
                color: var(--light-text);
                margin-top: auto;
            }}

            .trend-positive {{
                color: var(--tertiary-color);
            }}

            .trend-negative {{
                color: var(--secondary-color);
            }}

            .chart-container {{
                background: white;
                border-radius: var(--rounded-md);
                box-shadow: var(--shadow-md);
                padding: 1.75rem;
                margin-top: 2rem;
                border: 1px solid rgba(229, 231, 235, 0.5);
                transition: var(--transition-normal);
            }}

            .chart-container:hover {{
                box-shadow: var(--shadow-lg);
            }}

            .chart-title {{
                font-size: 1.5rem;
                margin-bottom: 1rem;
                color: var(--dark-bg);
                letter-spacing: -0.025em;
            }}

            .source-tag {{
                display: inline-block;
                padding: 0.35rem 0.75rem;
                border-radius: var(--rounded-sm);
                margin-right: 0.5rem;
                margin-bottom: 0.5rem;
                font-size: 0.85rem;
                font-weight: 600;
                transition: var(--transition-normal);
            }}

            .source-tag:hover {{
                transform: translateY(-2px);
            }}

            .source-the {{
                background: rgba(59, 130, 246, 0.1);
                color: #3B82F6;
            }}

            .source-ghes {{
                background: rgba(239, 68, 68, 0.1);
                color: #EF4444;
            }}

            .source-ppp {{
                background: rgba(16, 185, 129, 0.1);
                color: #10B981;
            }}

            .source-oop {{
                background: rgba(245, 158, 11, 0.1);
                color: #F59E0B;
            }}

            .source-dah {{
                background: rgba(139, 92, 246, 0.1);
                color: #8B5CF6;
            }}

            .footer {{
                margin-top: 3rem;
                padding: 1.5rem 0;
                border-top: 1px solid rgba(229, 231, 235, 0.5);
                text-align: center;
                font-size: 0.9rem;
                color: var(--light-text);
            }}

            /* Responsive adjustments */
            @media (max-width: 992px) {{
                .dashboard-container {{
                    padding: 1.25rem;
                }}

                .dashboard-title {{
                    font-size: 2rem;
                }}

                .stat-card {{
                    margin-bottom: 1rem;
                }}
            }}

            @media (max-width: 768px) {{
                .dashboard-container {{
                    padding: 1rem;
                }}

                .dashboard-title {{
                    font-size: 1.75rem;
                }}

                .chart-title {{
                    font-size: 1.25rem;
                }}

                .stat-card-value {{
                    font-size: 1.5rem;
                }}
            }}

            /* Custom styling for tooltip */
            .plotly-tooltip {{
                font-family: var(--body-font) !important;
                border-radius: var(--rounded-md) !important;
                box-shadow: var(--shadow-md) !important;
            }}

            /* Progress bar styling for funding composition */
            .funding-bar {{
                height: 28px;
                border-radius: var(--rounded-sm);
                margin-bottom: 0.75rem;
                overflow: hidden;
                background-color: #F3F4F6;
                box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
            }}

            .funding-bar-item {{
                height: 100%;
                float: left;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 0.75rem;
                font-weight: 600;
                transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
                position: relative;
            }}

            .funding-bar-ghes {{
                background-color: #EF4444;
            }}

            .funding-bar-ppp {{
                background-color: #10B981;
            }}

            .funding-bar-oop {{
                background-color: #F59E0B;
            }}

            .funding-bar-dah {{
                background-color: #8B5CF6;
            }}

            .funding-legend {{
                display: flex;
                flex-wrap: wrap;
                margin-top: 1rem;
                font-size: 0.875rem;
            }}

            .funding-legend-item {{
                display: flex;
                align-items: center;
                margin-right: 1.25rem;
                margin-bottom: 0.75rem;
                transition: var(--transition-normal);
            }}

            .funding-legend-item:hover {{
                transform: translateY(-2px);
            }}

            .funding-legend-color {{
                width: 14px;
                height: 14px;
                border-radius: 4px;
                margin-right: 6px;
                box-shadow: var(--shadow-sm);
            }}

            /* Sticky header with location name for better visibility */
            .sticky-location {{
                position: sticky;
                top: 0;
                z-index: 100;
                background: linear-gradient(135deg, rgba(249, 250, 251, 0.95) 0%, rgba(238, 242, 247, 0.95) 100%);
                padding: 1rem;
                border-bottom: 3px solid var(--primary-color);
                display: none;  /* Initially hidden, will show on scroll */
                align-items: center;
                justify-content: space-between;
                backdrop-filter: blur(8px);
                -webkit-backdrop-filter: blur(8px);
                box-shadow: var(--shadow-md);
            }}

            .sticky-location-name {{
                font-family: var(--header-font);
                font-weight: 700;
                color: var(--primary-color);
                font-size: 1.25rem;
                margin: 0;
                display: flex;
                align-items: center;
            }}

            .sticky-location-btn {{
                background-color: var(--primary-color);
                color: white;
                border: none;
                border-radius: var(--rounded-sm);
                padding: 0.4rem 0.75rem;
                font-size: 0.85rem;
                font-weight: 500;
                cursor: pointer;
                transition: var(--transition-normal);
                display: flex;
                align-items: center;
                gap: 0.25rem;
            }}

            .sticky-location-btn:hover {{
                background-color: #2563EB;
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
            }}

            /* Animation classes */
            .fade-in {{
                animation: fadeIn 0.5s ease-in-out forwards;
            }}

            .slide-up {{
                animation: slideUp 0.5s ease-in-out forwards;
            }}

            @keyframes fadeIn {{
                from {{ opacity: 0; }}
                to {{ opacity: 1; }}
            }}

            @keyframes slideUp {{
                from {{ transform: translateY(20px); opacity: 0; }}
                to {{ transform: translateY(0); opacity: 1; }}
            }}

            /* Icons styling */
            .icon-circle {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 28px;
                height: 28px;
                background-color: rgba(59, 130, 246, 0.1);
                border-radius: 50%;
                margin-right: 0.5rem;
            }}

            /* Modern card hover effects */
            .card-hover-effect {{
                transition: var(--transition-normal);
            }}

            .card-hover-effect:hover {{
                transform: translateY(-5px);
                box-shadow: var(--shadow-lg);
            }}
        </style>
    </head>
    <body>
        <!-- Sticky header with location name -->
        <div class="sticky-location" id="stickyLocation">
            <div class="sticky-location-name">
                <i class="fas fa-map-marker-alt me-2"></i>{selected_location} Health Financing
            </div>
            <button class="sticky-location-btn" onclick="scrollToTop()">
                <i class="fas fa-arrow-up"></i><span>Top</span>
            </button>
        </div>

        <div class="dashboard-container">
            <!-- Dashboard Header -->
            <div class="dashboard-header" id="dashboardTop">
                <div class="dashboard-logo fade-in">
                    <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="40" cy="40" r="40" fill="#3B82F6" opacity="0.1"/>
                        <path d="M56 24C56 25.6569 54.6569 27 53 27C51.3431 27 50 25.6569 50 24C50 22.3431 51.3431 21 53 21C54.6569 21 56 22.3431 56 24Z" fill="#3B82F6"/>
                        <path d="M18 56C18 57.6569 16.6569 59 15 59C13.3431 59 12 57.6569 12 56C12 54.3431 13.3431 53 15 53C16.6569 53 18 54.3431 18 56Z" fill="#EF4444"/>
                        <path d="M32 34C32 35.6569 30.6569 37 29 37C27.3431 37 26 35.6569 26 34C26 32.3431 27.3431 31 29 31C30.6569 31 32 32.3431 32 34Z" fill="#10B981"/>
                        <path d="M46 46C46 47.6569 44.6569 49 43 49C41.3431 49 40 47.6569 40 46C40 44.3431 41.3431 43 43 43C44.6569 43 46 44.3431 46 46Z" fill="#8B5CF6"/>
                        <path d="M53 27L43 43" stroke="#3B82F6" stroke-width="3" stroke-linecap="round"/>
                        <path d="M43 43L29 34" stroke="#3B82F6" stroke-width="3" stroke-linecap="round"/>
                        <path d="M29 34L15 56" stroke="#3B82F6" stroke-width="3" stroke-linecap="round"/>
                        <path d="M15 18L15 62" stroke="#3B82F6" stroke-width="3" stroke-linecap="round"/>
                        <path d="M10 56L62 56" stroke="#3B82F6" stroke-width="3" stroke-linecap="round"/>
                    </svg>
                </div>
                <div class="dashboard-headline slide-up">
                    <h1 class="dashboard-title">Health Financing Dashboard</h1>
                    <div class="dashboard-location-badge">
                        <i class="fas fa-map-marker-alt me-2"></i>{selected_location}
                    </div>
                    <p class="dashboard-subtitle">Financial Health Expenditure Analysis <span class="time-period">2003-2021</span></p>
                </div>
            </div>

            <!-- Key Statistics -->
            <div class="row">
                <div class="col-md-3 mb-4">
                    <div class="stat-card card-hover-effect">
                        <div class="stat-card-title">
                            <div class="icon-circle">
                                <i class="fas fa-chart-line"></i>
                            </div>
                            Total Health Expenditure
                        </div>
                        <div class="stat-card-value">${latest_the_millions:,.1f}M</div>
                        <div class="stat-card-subtitle">Recorded in {latest_year}</div>
                    </div>
                </div>

                <div class="col-md-3 mb-4">
                    <div class="stat-card card-hover-effect">
                        <div class="stat-card-title">
                            <div class="icon-circle">
                                <i class="fas fa-percentage"></i>
                            </div>
                            Overall Growth
                        </div>
                        <div class="stat-card-value {'trend-positive' if percent_change >= 0 else 'trend-negative'}">
                            {'+' if percent_change >= 0 else ''}{percent_change:.1f}%
                        </div>
                        <div class="stat-card-subtitle">Since {earliest_year}</div>
                    </div>
                </div>

                <div class="col-md-3 mb-4">
                    <div class="stat-card card-hover-effect">
                        <div class="stat-card-title">
                            <div class="icon-circle">
                                <i class="fas fa-calendar-day"></i>
                            </div>
                            Annual Growth Rate
                        </div>
                        <div class="stat-card-value {'trend-positive' if avg_annual_growth >= 0 else 'trend-negative'}">
                            {'+' if avg_annual_growth >= 0 else ''}{avg_annual_growth:.1f}%
                        </div>
                        <div class="stat-card-subtitle">Average per year</div>
                    </div>
                </div>

                <div class="col-md-3 mb-4">
                    <div class="stat-card card-hover-effect">
                        <div class="stat-card-title">
                            <div class="icon-circle">
                                <i class="fas fa-clock"></i>
                            </div>
                            Study Period
                        </div>
                        <div class="stat-card-value">{years_span} years</div>
                        <div class="stat-card-subtitle">{earliest_year} to {latest_year}</div>
                    </div>
                </div>
            </div>

            <!-- Funding Composition Section -->
            <div class="row">
                <div class="col-12 mb-4">
                    <div class="stat-card card-hover-effect">
                        <div class="stat-card-title mb-3">
                            <div class="icon-circle">
                                <i class="fas fa-pie-chart"></i>
                            </div>
                            Funding Composition ({latest_year})
                        </div>

                        <!-- Progress bar for funding composition -->
                        <div class="funding-bar">
                            {''.join([
        f'<div class="funding-bar-item funding-bar-{k.split("_")[0]}" style="width: {v}%"></div>'
        for k, v in funding_percentages.items()
    ])}
                        </div>

                        <!-- Legend -->
                        <div class="funding-legend">
                            {''.join([
        f"""
                                <div class="funding-legend-item">
                                    <div class="funding-legend-color" style="background-color: {'#EF4444' if 'ghes' in k else '#10B981' if 'ppp' in k else '#F59E0B' if 'oop' in k else '#8B5CF6'}"></div>
                                    <span>{'Government' if 'ghes' in k else 'Private Plans' if 'ppp' in k else 'Out-of-Pocket' if 'oop' in k else 'Development Aid'}: {v:.1f}%</span>
                                </div>
                                """
        for k, v in funding_percentages.items()
    ])}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main Chart -->
            <div class="chart-container card-hover-effect">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h2 class="chart-title m-0">Health Financing Trends Over Time</h2>
                    <div>
                        <span class="source-tag source-the">THE</span>
                        <span class="source-tag source-ghes">GHES</span>
                        <span class="source-tag source-ppp">PPP</span>
                        <span class="source-tag source-oop">OOP</span>
                        <span class="source-tag source-dah">DAH</span>
                    </div>
                </div>
                <div id="boxplot-chart" style="width:100%; height:550px;"></div>
                <div class="text-center mt-3">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        Hover over data points for detailed information. Each box represents the distribution of values for that year.
                    </small>
                </div>
            </div>

            <!-- Data Sources & Methodology -->
            <div class="row mt-4">
                <div class="col-md-6 mb-4">
                    <div class="stat-card card-hover-effect">
                        <div class="stat-card-title">
                            <div class="icon-circle">
                                <i class="fas fa-database"></i>
                            </div>
                            Data Sources
                        </div>
                        <p>This dashboard is based on the IHME Health Spending dataset (1995-2021), which provides comprehensive data on health financing across different countries and regions.</p>
                        <p class="small text-muted mb-0">Source: Institute for Health Metrics and Evaluation (IHME)</p>
                    </div>
                </div>

                <div class="col-md-6 mb-4">
                    <div class="stat-card card-hover-effect">
                        <div class="stat-card-title">
                            <div class="icon-circle">
                                <i class="fas fa-book"></i>
                            </div>
                            Abbreviations
                        </div>
                        <div>
                            <span><strong>THE</strong>: Total Health Expenditure</span><br>
                            <span><strong>GHES</strong>: Government Health Expenditure</span><br>
                            <span><strong>PPP</strong>: Prepaid Private Plans</span><br>
                            <span><strong>OOP</strong>: Out-of-Pocket Spending</span><br>
                            <span><strong>DAH</strong>: Development Assistance for Health</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <div class="footer">
                <p>Created with Plotly and Python | Data Source: IHME Health Spending Dataset (1995-2021)</p>
                <p class="mb-0">Generated on {datetime.now().strftime('%Y-%m-%d')}</p>
            </div>
        </div>

        <!-- JavaScript libraries -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

        <!-- Initialize the chart -->
        <script>
            // Parse the JSON data for the plot
            const plotData = {plot_json};

            // Render the plot
            Plotly.newPlot('boxplot-chart', plotData.data, plotData.layout, {{
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['select2d', 'lasso2d', 'resetScale2d', 'toggleHover'],
                displaylogo: false,
                toImageButtonOptions: {{
                    format: 'png',
                    filename: 'health_financing_{selected_location}',
                    height: 550,
                    width: 1100,
                    scale: 2
                }}
            }});

            // Add scroll animations
            document.addEventListener('DOMContentLoaded', function() {{
                // Animate elements when they come into view
                const observer = new IntersectionObserver((entries) => {{
                    entries.forEach(entry => {{
                        if (entry.isIntersecting) {{
                            entry.target.classList.add('fade-in');
                            observer.unobserve(entry.target);
                        }}
                    }});
                }}, {{ threshold: 0.1 }});

                // Observe all stat cards
                document.querySelectorAll('.stat-card').forEach(card => {{
                    observer.observe(card);
                }});

                // Observe chart container
                observer.observe(document.querySelector('.chart-container'));
            }});

            // Show/hide sticky header with location name
            window.addEventListener('scroll', function() {{
                const header = document.getElementById('stickyLocation');
                if (window.scrollY > 200) {{
                    header.style.display = 'flex';
                }} else {{
                    header.style.display = 'none';
                }}
            }});

            // Function to scroll back to top
            function scrollToTop() {{
                window.scrollTo({{
                    top: 0,
                    behavior: 'smooth'
                }});
            }}

            // Animate funding bar on load
            document.addEventListener('DOMContentLoaded', function() {{
                setTimeout(() => {{
                    const fundingBarItems = document.querySelectorAll('.funding-bar-item');
                    fundingBarItems.forEach(item => {{
                        const width = item.style.width;
                        item.style.width = '0%';

                        setTimeout(() => {{
                            item.style.width = width;
                        }}, 300);
                    }});
                }}, 500);

                // Apply custom styling to tooltips when they appear
                const observer = new MutationObserver((mutations) => {{
                    for (const mutation of mutations) {{
                        if (mutation.addedNodes.length) {{
                            const tooltips = document.querySelectorAll('.js-plotly-plot .plotly');
                            tooltips.forEach(tooltip => {{
                                const tooltipEl = tooltip.querySelector('.hovertext');
                                if (tooltipEl) {{
                                    tooltipEl.classList.add('plotly-tooltip');
                                }}
                            }});
                        }}
                    }}
                }});

                observer.observe(document.body, {{ childList: true, subtree: true }});
            }});
        </script>
    </body>
    </html>
    '''

    return html_content


# Get unique locations
locations = sorted(df['location_name'].unique())
print("Available locations:")
for i, loc in enumerate(locations):
    print(f"  {i + 1}. {loc}")

# Get user input for location
selected_location = input("\nPlease select a location from the list above: ")
# Handle both direct name input and numeric selection
if selected_location.isdigit() and 1 <= int(selected_location) <= len(locations):
    selected_location = locations[int(selected_location) - 1]

# Generate the dashboard
html_content = generate_dashboard(selected_location)

if html_content:
    # Save to HTML file
    output_filename = f"health_financing_dashboard_{selected_location.lower().replace(' ', '_')}.html"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"\nDashboard saved as '{output_filename}'")
    print(f"Open this file in your web browser to view the interactive dashboard for {selected_location}.")
