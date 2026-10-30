import pypsa
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# 1. Skeleton Matrix for the SP15 Grid

# NODES
sp15_buses = {
    # Demand Centers (city)
    "Los_Angeles": {"x": -118.2437, "y": 34.0522, "type": "Load"}, #Longitude is X, Latitude is Y
    "San_Diego": {"x": -117.1611, "y": 32.7157, "type": "Load"},
    "Anaheim": {"x": -117.9143, "y": 33.8366, "type": "Load"},
    
    # Solar Plants (desert)
    "Imperial_Valley": {"x": -115.4243, "y": 32.8481, "type": "Solar"},
    "Riverside_East": {"x": -114.9733, "y": 33.7222, "type": "Solar"},
    "Mojave": {"x": -118.1751, "y": 35.0526, "type": "Solar"},  
    
    # Gas Plants
    "Inland_Empire_Gas": {"x": -117.2898, "y": 34.1083, "type": "Gas"},

    # Battery Storage
    "LA_Basin_Battery": {"x": -118.0, "y": 33.9, "type": "Storage"}
}

# 2. EDGES (Transmission Lines)
sp15_lines = [
    # Desert to City lines (This is where curtailment is physically forced)
    {"name": "Imperial_to_SD", "bus0": "Imperial_Valley", "bus1": "San_Diego", "capacity_mw": 2500},
    {"name": "Riverside_to_Anaheim", "bus0": "Riverside_East", "bus1": "Anaheim", "capacity_mw": 3500},
    {"name": "Mojave_to_LA", "bus0": "Mojave", "bus1": "Los_Angeles", "capacity_mw": 4000},
    
    # Inter-City connectivity
    {"name": "LA_to_Anaheim", "bus0": "Los_Angeles", "bus1": "Anaheim", "capacity_mw": 2000},
    {"name": "Anaheim_to_SD", "bus0": "Anaheim", "bus1": "San_Diego", "capacity_mw": 1500},
    
    # Gas Connectivity
    {"name": "Gas_to_LA", "bus0": "Inland_Empire_Gas", "bus1": "Los_Angeles", "capacity_mw": 5000},

    # Battery Storage Connectivity
    {"name": "Battery_to_LA", "bus0": "LA_Basin_Battery", "bus1": "Los_Angeles", "capacity_mw": 2000}
]

def create_sp15_network():
    # Initialize the empty mathematical network
    network = pypsa.Network()
    
    # Build the Buses with Geographic Coordinates
    for bus_name, specs in sp15_buses.items():
        network.add("Bus", 
                    name=bus_name, 
                    v_nom=500, # 500kV High Voltage lines
                    x=specs["x"], 
                    y=specs["y"])
        
    # Connect the Buses with Transmission Lines
    for line in sp15_lines:
        network.add("Line", 
                    name=line["name"], 
                    bus0=line["bus0"], 
                    bus1=line["bus1"], 
                    s_nom=line["capacity_mw"], # The thermal limit
                    x=0.001) # Standardized line reactance
                    
    print(f"SP15 Grid successfully initialized with {len(network.buses)} buses and {len(network.lines)} transmission lines.")
    return network

if __name__ == "__main__":
    net = create_sp15_network()
    
    # Set up map projection
    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={'projection': ccrs.PlateCarree()})
    
    # Add map features
    ax.add_feature(cfeature.OCEAN, facecolor='aliceblue')
    ax.add_feature(cfeature.LAND, facecolor='floralwhite')
    ax.add_feature(cfeature.STATES, edgecolor='gray', linewidth=0.5)
    ax.coastlines(resolution='50m', linewidth=1)
    
    # --- COLOR CODING LOGIC ---
    color_mapping = {"Solar": "gold", "Gas": "brown", "Storage": "purple", "Load": "gray"}
    node_colors = pd.Series({bus: color_mapping[specs["type"]] for bus, specs in sp15_buses.items()})
    line_capacities = net.lines.s_nom
    
    # Plot the network
    net.plot(
        ax=ax, 
        margin=0.2, 
        bus_sizes=0.003,
        bus_colors=node_colors,             
        line_colors=line_capacities,        
        line_cmap=plt.cm.winter             
    )
    
    # --- LEGEND AND COLORBAR ---
    # 1. Build the Node Legend
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Solar (Renewable)', markerfacecolor='gold', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Gas Peaker', markerfacecolor='brown', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Battery Storage', markerfacecolor='purple', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Urban Demand', markerfacecolor='gray', markersize=10)
    ]
    ax.legend(handles=legend_elements, loc='upper right', title="Facility Types", framealpha=0.9, edgecolor='gray')
    
    # 2. Build the Transmission Line Colorbar
    sm = plt.cm.ScalarMappable(cmap=plt.cm.winter, norm=plt.Normalize(vmin=line_capacities.min(), vmax=line_capacities.max()))
    sm._A = [] # Empty array required for matplotlib workaround
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.03, aspect=20)
    cbar.set_label("Transmission Line Capacity (MW)", fontweight='bold')
    
    # Loop through the nodes and label them on the map
    for bus in net.buses.index:
        x_shift = 0.08
        alignment = 'left'
        
        if bus == "LA_Basin_Battery":
            x_shift = -0.08
            alignment = 'right'
            
        ax.text(net.buses.loc[bus, 'x'] + x_shift, 
                net.buses.loc[bus, 'y'], 
                bus.replace('_', ' '),           
                transform=ccrs.PlateCarree(),
                fontsize=9, 
                fontweight='bold',
                ha=alignment,                       
                va='center',                     
                bbox=dict(facecolor='white', edgecolor='lightgray', boxstyle='round,pad=0.3', alpha=0.9))
        
    plt.title("Southern California (SP15) Grid Topology", fontsize=14, fontweight='bold', pad=15)
    plt.show()