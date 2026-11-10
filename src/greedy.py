import matplotlib.pyplot as plt

# 1.OBJECTIVE FUNCTION PENALTIES
COST_GAS = 60              
PENALTY_CURTAIL = 20       
PENALTY_BLACKOUT = 1000  

# 2.PHYSICAL GRID CONSTRAINTS
BATTERY_MAX_STORAGE = 8000
BATTERY_MAX_POWER = 2000   
TRANSMISSION_LIMIT = 10000 

def simple_greedy_solver(hours, solar_data, demand_data):
    
    current_battery_level = 0
    total_cost = 0

    # Lists to store the hourly decisions so we can graph them later
    saved_solar_used = []
    saved_battery_used = []
    saved_gas_used = []
    saved_curtailed = []
    
    # 3.OBJECTIVE FUNCTION PENALTIES
    for i in range(len(hours)):
        solar = solar_data[i]
        demand = demand_data[i]
        
        # Reset hourly actions to zero
        gas_used = 0
        curtailed = 0
        battery_discharged = 0
        blackout = 0
        
        # SCENARIO A: SOLAR SURPLUS 
        if solar >= demand:
            extra_solar = solar - demand
            
            # If generated more than the lines can carry, curtail the excess solar
            if solar > TRANSMISSION_LIMIT:
                trapped_solar = solar - TRANSMISSION_LIMIT
                extra_solar -= trapped_solar
                curtailed += trapped_solar 
            
            # Store the remaining extra solar in the battery
            room_in_battery = BATTERY_MAX_STORAGE - current_battery_level
            charge_amount = min(extra_solar, BATTERY_MAX_POWER, room_in_battery)
            current_battery_level += charge_amount
            
            # Any solar left over that couldn't fit in the battery is curtailed
            leftover_solar = extra_solar - charge_amount
            curtailed += leftover_solar
            
            # Record that solar covered 100% of the city demand this hour
            saved_solar_used.append(demand)

        # SCENARIO B: SOLAR DEFICIT 
        # Solar alone cannot meet the city demand.
        else:
            
            power_needed = demand - solar
            saved_solar_used.append(solar)
            
            
            discharge_amount = min(power_needed, BATTERY_MAX_POWER, current_battery_level)
            current_battery_level -= discharge_amount
            battery_discharged = discharge_amount
            power_needed -= discharge_amount
            
            
            if power_needed > 0:
                gas_used = min(power_needed, 5000)
                power_needed -= gas_used
                
            
            if power_needed > 0:
                blackout = power_needed
                
        # --- 4. CALCULATE HOUR COST AND SAVE THE DATA
        # Calculate the objective function value for this specific hour
        hour_cost = (gas_used * COST_GAS) + (curtailed * PENALTY_CURTAIL) + (blackout * PENALTY_BLACKOUT)
        total_cost += hour_cost
        
        # Save our decisions for the graph
        saved_battery_used.append(battery_discharged)
        saved_gas_used.append(gas_used)
        saved_curtailed.append(curtailed)

    return total_cost, saved_solar_used, saved_battery_used, saved_gas_used, saved_curtailed


if __name__ == "__main__":
    #INPUT VALIDATION DATA
    hours = list(range(1, 25))

    # Synthetic duck curve demand
    demand = [4000, 3800, 3500, 3500, 4000, 5000, 6000, 7000, 7500, 7000, 6500, 6000, 
              6000, 6500, 7000, 8000, 9000, 10000, 9500, 8500, 7500, 6000, 5000, 4500]

    # Synthetic solar generation 
    solar = [0, 0, 0, 0, 0, 1000, 3000, 6000, 9000, 11000, 12000, 12500, 
             12500, 12000, 10000, 7000, 4000, 1000, 0, 0, 0, 0, 0, 0]

    # Run the heuristic solver
    total_cost, solar_used, battery_used, gas_used, curtailed = simple_greedy_solver(hours, solar, demand)

    # Print the final Objective Function (Z) result
    print(f"Total System Cost for 24 hours: ${total_cost:,.2f}")
    
    # 6. PLOT THE TWO-PANEL VISUALIZATION
    # Calculate blackouts (Unmet Demand) for the bottom graph
    blackouts = [max(0, d - (s + b + g)) for d, s, b, g in zip(demand, solar_used, battery_used, gas_used)]

    # Create a figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    # TOP PANEL: GENERATION VS. DEMAND
    # Plot the target demand line
    ax1.plot(hours, demand, label='Urban Demand', color='black', linewidth=2, linestyle='--')
    
    # Stack the energy sources up to the demand line
    ax1.fill_between(hours, 0, solar_used, label='Solar Dispatch', color='gold', alpha=0.5)
    
    battery_bottom = solar_used
    battery_top = [s + b for s, b in zip(solar_used, battery_used)]
    ax1.fill_between(hours, battery_bottom, battery_top, label='Battery Discharge', color='purple', alpha=0.6)
    
    gas_top = [t + g for t, g in zip(battery_top, gas_used)]
    ax1.fill_between(hours, battery_top, gas_top, label='Gas Plant', color='brown', alpha=0.7)
    
    ax1.set_title("Greedy Heuristic Dispatch (Generation vs. Urban Demand)", fontsize=14, fontweight='bold')
    ax1.set_ylabel("Megawatts (MW)")
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax1.grid(alpha=0.3)

    # BOTTOM PANEL: SYSTEM INEFFICIENCIES
    # Show where the heuristic failed (wasted energy or power outages)
    ax2.bar(hours, curtailed, label='Curtailed Solar', color='red', alpha=0.8, width=0.5)
    ax2.bar(hours, blackouts, label='Unmet Demand', color='black', alpha=0.8, width=0.5)
    
    ax2.set_title("System Inefficiencies", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Hour of Day")
    ax2.set_ylabel("Megawatts (MW)")
    ax2.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()