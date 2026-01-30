"""
Azerbaijan Electricity Production Analysis - Chart Generation Script
Generates business-focused visualizations for executive decision-making
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set professional styling
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Create charts directory
Path('charts').mkdir(exist_ok=True)

# Load cleaned data
data = pd.read_csv('data/cleaned_energy_data.csv')

print("Generating business intelligence charts...")
print("=" * 60)

# Chart 1: Historical Production Growth (1913-2024)
print("\n1. Creating Historical Growth Trend chart...")
plt.figure(figsize=(14, 7))
plt.plot(data['Year'], data['Total_Production'], linewidth=2.5, color='#2E86AB', marker='o', markersize=4)
plt.fill_between(data['Year'], data['Total_Production'], alpha=0.3, color='#2E86AB')
plt.title('Electricity Production Growth: 111-Year Journey (1913-2024)', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Year', fontsize=13)
plt.ylabel('Production (Million kWh)', fontsize=13)
plt.grid(True, alpha=0.3)

# Add annotations for key milestones
milestones = [
    (1913, data[data['Year']==1913]['Total_Production'].values[0], 'Inception\n111 kWh'),
    (1990, data[data['Year']==1990]['Total_Production'].values[0], 'Peak Soviet Era\n23,153 kWh'),
    (2024, data[data['Year']==2024]['Total_Production'].values[0], 'Current\n28,413 kWh')
]
for year, value, label in milestones:
    plt.annotate(label, xy=(year, value), xytext=(10, 20), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

plt.tight_layout()
plt.savefig('charts/01_historical_growth.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Saved: charts/01_historical_growth.png")

# Chart 2: Energy Mix Evolution (Stacked Area Chart)
print("\n2. Creating Energy Mix Evolution chart...")
recent_data = data[data['Year'] >= 2000].copy()
fig, ax = plt.subplots(figsize=(14, 8))

# Calculate renewables
recent_data['Renewables'] = recent_data['Wind'] + recent_data['Solar'] + recent_data['Waste']

# Create stacked area chart
ax.fill_between(recent_data['Year'], 0, recent_data['Fuel_Powered'],
                label='Fuel-Powered', alpha=0.8, color='#A23B72')
ax.fill_between(recent_data['Year'], recent_data['Fuel_Powered'],
                recent_data['Fuel_Powered'] + recent_data['Hydroelectric'],
                label='Hydroelectric', alpha=0.8, color='#2E86AB')
ax.fill_between(recent_data['Year'],
                recent_data['Fuel_Powered'] + recent_data['Hydroelectric'],
                recent_data['Total_Production'],
                label='Renewables (Wind/Solar/Waste)', alpha=0.8, color='#18A558')

ax.set_title('Energy Mix Evolution: Strategic Shift Toward Sustainability (2000-2024)',
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('Year', fontsize=13)
ax.set_ylabel('Production (Million kWh)', fontsize=13)
ax.legend(loc='upper left', fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('charts/02_energy_mix_evolution.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Saved: charts/02_energy_mix_evolution.png")

# Chart 3: Renewable Energy Growth Trajectory
print("\n3. Creating Renewable Energy Growth chart...")
renewables_data = data[data['Year'] >= 2009].copy()
renewables_data['Total_Renewables'] = renewables_data['Wind'] + renewables_data['Solar'] + renewables_data['Waste']

fig, ax = plt.subplots(figsize=(14, 7))
ax.plot(renewables_data['Year'], renewables_data['Wind'], marker='o', linewidth=2.5,
        label='Wind Energy', color='#6C9BD1')
ax.plot(renewables_data['Year'], renewables_data['Solar'], marker='s', linewidth=2.5,
        label='Solar Energy', color='#F4A259')
ax.plot(renewables_data['Year'], renewables_data['Waste'], marker='^', linewidth=2.5,
        label='Waste-to-Energy', color='#BC4B51')
ax.plot(renewables_data['Year'], renewables_data['Total_Renewables'], marker='D', linewidth=3,
        label='Total Renewables', color='#18A558', linestyle='--')

ax.set_title('Renewable Energy Portfolio Growth (2009-2024)', fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('Year', fontsize=13)
ax.set_ylabel('Production (Million kWh)', fontsize=13)
ax.legend(loc='upper left', fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('charts/03_renewables_growth.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Saved: charts/03_renewables_growth.png")

# Chart 4: Solar Energy Acceleration (Recent 5 Years)
print("\n4. Creating Solar Energy Acceleration chart...")
solar_recent = data[data['Year'] >= 2020][['Year', 'Solar']].copy()
fig, ax = plt.subplots(figsize=(12, 7))

bars = ax.bar(solar_recent['Year'], solar_recent['Solar'], color=['#F4A259', '#F4A259', '#F4A259', '#F4A259', '#E63946'],
              edgecolor='black', linewidth=1.5, width=0.6)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=12, fontweight='bold')

ax.set_title('Solar Energy Breakthrough: 10x Growth in 4 Years (2020-2024)',
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('Year', fontsize=13)
ax.set_ylabel('Solar Production (Million kWh)', fontsize=13)
ax.set_xticks(solar_recent['Year'])
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('charts/04_solar_acceleration.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Saved: charts/04_solar_acceleration.png")

# Chart 5: Year-over-Year Growth Rates
print("\n5. Creating Year-over-Year Growth Analysis chart...")
growth_data = data[data['Year'] >= 2000].copy()
growth_data['YoY_Growth'] = growth_data['Total_Production'].pct_change() * 100

fig, ax = plt.subplots(figsize=(14, 7))
colors = ['#18A558' if x >= 0 else '#E63946' for x in growth_data['YoY_Growth'].fillna(0)]
bars = ax.bar(growth_data['Year'], growth_data['YoY_Growth'].fillna(0), color=colors,
              edgecolor='black', linewidth=1, width=0.7)

ax.axhline(y=0, color='black', linewidth=1.5)
ax.set_title('Annual Growth Rate: Performance Volatility Analysis (2000-2024)',
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('Year', fontsize=13)
ax.set_ylabel('Year-over-Year Growth (%)', fontsize=13)
ax.grid(True, alpha=0.3, axis='y')

# Highlight 2024 decline
ax.annotate('2024 Decline\n-3.0%', xy=(2024, growth_data[growth_data['Year']==2024]['YoY_Growth'].values[0]),
            xytext=(-40, -40), textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc='#E63946', alpha=0.7, edgecolor='black'),
            arrowprops=dict(arrowstyle='->', color='black', lw=2),
            fontsize=11, fontweight='bold', color='white')

plt.tight_layout()
plt.savefig('charts/05_yoy_growth_rates.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Saved: charts/05_yoy_growth_rates.png")

# Chart 6: Hydroelectric Volatility Risk
print("\n6. Creating Hydroelectric Volatility chart...")
hydro_data = data[data['Year'] >= 2000][['Year', 'Hydroelectric']].copy()

fig, ax = plt.subplots(figsize=(14, 7))
ax.plot(hydro_data['Year'], hydro_data['Hydroelectric'], linewidth=2.5,
        color='#2E86AB', marker='o', markersize=6)

# Add average line
avg_hydro = hydro_data['Hydroelectric'].mean()
ax.axhline(y=avg_hydro, color='#F77F00', linestyle='--', linewidth=2,
           label=f'Average: {avg_hydro:.0f} kWh')

# Shade volatility bands
std_hydro = hydro_data['Hydroelectric'].std()
ax.fill_between(hydro_data['Year'], avg_hydro - std_hydro, avg_hydro + std_hydro,
                alpha=0.2, color='#F77F00', label='±1 Std Dev')

ax.set_title('Hydroelectric Production Volatility: Dependency Risk (2000-2024)',
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('Year', fontsize=13)
ax.set_ylabel('Hydroelectric Production (Million kWh)', fontsize=13)
ax.legend(loc='upper right', fontsize=11)
ax.grid(True, alpha=0.3)

# Highlight 2024 spike
ax.annotate('2024 Spike\n+71% YoY',
            xy=(2024, hydro_data[hydro_data['Year']==2024]['Hydroelectric'].values[0]),
            xytext=(-60, -40), textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.8, edgecolor='black'),
            arrowprops=dict(arrowstyle='->', color='black', lw=2),
            fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('charts/06_hydroelectric_volatility.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Saved: charts/06_hydroelectric_volatility.png")

# Chart 7: 2024 Energy Mix Breakdown (Horizontal Bar)
print("\n7. Creating 2024 Energy Mix Breakdown chart...")
latest = data[data['Year']==2024].iloc[0]
mix_2024 = {
    'Fuel-Powered': latest['Fuel_Powered'],
    'Hydroelectric': latest['Hydroelectric'],
    'Solar': latest['Solar'],
    'Waste-to-Energy': latest['Waste'],
    'Wind': latest['Wind']
}

fig, ax = plt.subplots(figsize=(12, 8))
sources = list(mix_2024.keys())
values = list(mix_2024.values())
percentages = [(v/latest['Total_Production'])*100 for v in values]

# Sort by value
sorted_indices = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
sources = [sources[i] for i in sorted_indices]
values = [values[i] for i in sorted_indices]
percentages = [percentages[i] for i in sorted_indices]

colors_map = ['#A23B72', '#2E86AB', '#F4A259', '#BC4B51', '#6C9BD1']
bars = ax.barh(sources, values, color=colors_map, edgecolor='black', linewidth=1.5)

# Add value and percentage labels
for i, (bar, val, pct) in enumerate(zip(bars, values, percentages)):
    ax.text(val + 200, bar.get_y() + bar.get_height()/2,
            f'{val:.0f} kWh ({pct:.1f}%)',
            ha='left', va='center', fontsize=12, fontweight='bold')

ax.set_title('2024 Energy Mix: Current Production Portfolio', fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('Production (Million kWh)', fontsize=13)
ax.grid(True, alpha=0.3, axis='x')
ax.set_xlim(0, max(values) * 1.15)

plt.tight_layout()
plt.savefig('charts/07_2024_energy_mix.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Saved: charts/07_2024_energy_mix.png")

# Chart 8: Fuel Dependency Trend
print("\n8. Creating Fuel Dependency Trend chart...")
dependency_data = data[data['Year'] >= 2000].copy()
dependency_data['Fuel_Percentage'] = (dependency_data['Fuel_Powered'] / dependency_data['Total_Production']) * 100
dependency_data['Non_Fuel_Percentage'] = 100 - dependency_data['Fuel_Percentage']

fig, ax = plt.subplots(figsize=(14, 7))
ax.plot(dependency_data['Year'], dependency_data['Fuel_Percentage'],
        linewidth=3, color='#A23B72', marker='o', markersize=6, label='Fuel Dependency')
ax.plot(dependency_data['Year'], dependency_data['Non_Fuel_Percentage'],
        linewidth=3, color='#18A558', marker='s', markersize=6, label='Non-Fuel Sources')

ax.fill_between(dependency_data['Year'], dependency_data['Fuel_Percentage'],
                100, alpha=0.3, color='#18A558')
ax.fill_between(dependency_data['Year'], 0, dependency_data['Fuel_Percentage'],
                alpha=0.3, color='#A23B72')

ax.set_title('Energy Independence Progress: Reducing Fuel Dependency (2000-2024)',
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('Year', fontsize=13)
ax.set_ylabel('Percentage of Total Production (%)', fontsize=13)
ax.legend(loc='center right', fontsize=12)
ax.grid(True, alpha=0.3)
ax.set_ylim(0, 100)

# Add current value annotation
current_fuel_pct = dependency_data[dependency_data['Year']==2024]['Fuel_Percentage'].values[0]
ax.annotate(f'2024: {current_fuel_pct:.0f}% Fuel\n{100-current_fuel_pct:.0f}% Alternative',
            xy=(2024, current_fuel_pct),
            xytext=(-120, 30), textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.7', fc='white', alpha=0.9, edgecolor='black', linewidth=2),
            arrowprops=dict(arrowstyle='->', color='black', lw=2),
            fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('charts/08_fuel_dependency_trend.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Saved: charts/08_fuel_dependency_trend.png")

# Chart 9: Production Peaks and Troughs Analysis
print("\n9. Creating Production Performance Milestones chart...")
milestones_data = data[data['Year'].isin([1913, 1990, 2009, 2022, 2023, 2024])].copy()

fig, ax = plt.subplots(figsize=(12, 8))
colors_timeline = ['#6C9BD1', '#18A558', '#E63946', '#18A558', '#18A558', '#E63946']
bars = ax.bar(milestones_data['Year'].astype(str), milestones_data['Total_Production'],
              color=colors_timeline, edgecolor='black', linewidth=2, width=0.6)

# Add value labels
for bar, year_val in zip(bars, milestones_data['Year']):
    height = bar.get_height()
    row = milestones_data[milestones_data['Year']==year_val].iloc[0]

    if year_val == 2024:
        change = ((row['Total_Production'] / data[data['Year']==2023]['Total_Production'].values[0]) - 1) * 100
        label = f"{height:.0f}\n({change:+.1f}%)"
    else:
        label = f"{height:.0f}"

    ax.text(bar.get_x() + bar.get_width()/2., height,
            label, ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_title('Production Milestones: Key Performance Inflection Points',
             fontsize=16, fontweight='bold', pad=20)
ax.set_ylabel('Production (Million kWh)', fontsize=13)
ax.grid(True, alpha=0.3, axis='y')

# Add milestone descriptions
descriptions = ['Inception', 'Soviet Peak', 'Crisis Low', 'Record High', 'Peak', '2024']
for i, (bar, desc) in enumerate(zip(bars, descriptions)):
    ax.text(bar.get_x() + bar.get_width()/2., -1500, desc,
            ha='center', va='top', fontsize=10, style='italic')

plt.tight_layout()
plt.savefig('charts/09_performance_milestones.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Saved: charts/09_performance_milestones.png")

print("\n" + "=" * 60)
print("✓ Chart generation complete!")
print(f"✓ All 9 charts saved to: charts/")
print("=" * 60)
