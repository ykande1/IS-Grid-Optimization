import pandas as pd
import matplotlib.pyplot as plt

# --- 1. OBJECTIVE FUNCTION PENALTIES ($/MWh) ---
COST_GAS = 50              
PENALTY_CURTAIL = 100       
PENALTY_BLACKOUT = 1000    

# --- 2. PHYSICAL GRID CONSTRAINTS (MW / MWh) ---
BATTERY_MAX_STORAGE = 8000 
BATTERY_MAX_POWER = 2000   
TRANSMISSION_LIMIT = 10000 

def simple_greedy_solver(time_series_data):
    current_battery_level = 0
    total_cost = 0

    saved_solar_used = []
    saved_battery_used = []
    saved_gas_used = []
    saved_curtailed = []
    
    # --- 3. LOOP THROUGH EACH HOUR IN THE DATASET ---
    for index, row in time_series_data.iterrows():
        # Scale the CAISO demand data to the SP15 region (45%)
        demand = row['Total_Demand_MW'] * 0.45 
        raw_solar = row['Solar_Generation_MW']
        
        gas_used = 0
        curtailed = 0
        battery_discharged = 0
        blackout = 0
        
        # Calculate what can reach the city
        deliverable_solar = min(raw_solar, TRANSMISSION_LIMIT)
        trapped_solar = raw_solar - deliverable_solar
        curtailed += trapped_solar 
        
        # SCENARIO A: SURPLUS SOLAR
        if deliverable_solar >= demand:
            extra_solar = deliverable_solar - demand
            
            room_in_battery = BATTERY_MAX_STORAGE - current_battery_level
            charge_amount = min(extra_solar, BATTERY_MAX_POWER, room_in_battery)
            current_battery_level += charge_amount
            
            leftover_solar = extra_solar - charge_amount
            curtailed += leftover_solar
            
            saved_solar_used.append(demand)

        # SCENARIO B: SOLAR DEFICIT 
        else:
            power_needed = demand - deliverable_solar
            saved_solar_used.append(deliverable_solar)
            
            discharge_amount = min(power_needed, BATTERY_MAX_POWER, current_battery_level)
            current_battery_level -= discharge_amount
            battery_discharged = discharge_amount
            power_needed -= discharge_amount
            
            if power_needed > 0:
                gas_used = min(power_needed, 5000)
                power_needed -= gas_used
                
            if power_needed > 0:
                blackout = power_needed
                
        # --- 4. CALCULATE HOUR COST & SAVE DATA ---
        hour_cost = (gas_used * COST_GAS) + (curtailed * PENALTY_CURTAIL) + (blackout * PENALTY_BLACKOUT)
        total_cost += hour_cost
        
        saved_battery_used.append(battery_discharged)
        saved_gas_used.append(gas_used)
        saved_curtailed.append(curtailed)

    return total_cost, saved_solar_used, saved_battery_used, saved_gas_used, saved_curtailed


if __name__ == "__main__":
    print("Loading data from CAISO...")
    try:
        # Load the processed data from data_prep.py
        caiso_data = pd.read_csv('../data/processed/pypsa_1week_input.csv')
        
        # Extract hours and apply the SP15 scale factor for the visualization
        hours = list(range(len(caiso_data)))
        demand_raw = caiso_data['Total_Demand_MW'].tolist()
        demand = [d * 0.45 for d in demand_raw]
        
    except FileNotFoundError:
        print("Error: Could not find '../data/processed/pypsa_1week_input.csv'. Make sure data_prep.py was run first.")
        exit()

    # Run solver
    total_cost, solar_used, battery_used, gas_used, curtailed = simple_greedy_solver(caiso_data)

    print(f"Total System Cost for 168 hours: ${total_cost:,.2f}")
    
    # --- 6. PLOT THE VISUALIZATION ---
    blackouts = [max(0, d - (s + b + g)) for d, s, b, g in zip(demand, solar_used, battery_used, gas_used)]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    # TOP PANEL: GENERATION VS. DEMAND
    ax1.plot(hours, demand, label='Urban Demand (SP15 Scaled)', color='black', linewidth=1, linestyle='--')
    
    ax1.fill_between(hours, 0, solar_used, label='Solar Dispatch', color='gold', alpha=0.5)
    
    battery_bottom = solar_used
    battery_top = [s + b for s, b in zip(solar_used, battery_used)]
    ax1.fill_between(hours, battery_bottom, battery_top, label='Battery Discharge', color='purple', alpha=0.6)
    
    gas_top = [t + g for t, g in zip(battery_top, gas_used)]
    ax1.fill_between(hours, battery_top, gas_top, label='Gas Plant', color='brown', alpha=0.7)
    
    ax1.set_title("Greedy Heuristic Dispatch (168-Hour CAISO Data)", fontsize=14, fontweight='bold')
    ax1.set_ylabel("Megawatts (MW)")
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax1.grid(alpha=0.3)

    # BOTTOM PANEL: SYSTEM INEFFICIENCIES
    ax2.bar(hours, curtailed, label='Curtailed Solar', color='red', alpha=0.8, width=1.0)
    ax2.bar(hours, blackouts, label='Unmet Demand', color='black', alpha=0.8, width=1.0)
    
    ax2.set_title("System Inefficiencies (Penalties)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Hour of Simulation (0 to 168)")
    ax2.set_ylabel("Megawatts (MW)")
    ax2.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()