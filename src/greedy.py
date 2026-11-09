import matplotlib.pyplot as plt

COST_GAS = 60
PENALTY_CURTAIL = 20
PENALTY_BLACKOUT = 1000

BATTERY_MAX_STORAGE = 8000
BATTERY_MAX_POWER = 2000
TRANSMISSION_LIMIT = 10000

def simple_greedy_solver(hours, solar_data, demand_data):
    current_battery_level = 0
    total_cost = 0

    saved_solar_used = []
    saved_battery_used = []
    saved_gas_used = []
    saved_curtailed = []
    
    for i in range(len(hours)):
        solar = solar_data[i]
        demand = demand_data[i]
        
        gas_used = 0
        curtailed = 0
        battery_discharged = 0
        blackout = 0
        
        if solar >= demand:
            extra_solar = solar - demand
            
            if solar > TRANSMISSION_LIMIT:
                trapped_solar = solar - TRANSMISSION_LIMIT
                extra_solar -= trapped_solar
                curtailed += trapped_solar
            
            room_in_battery = BATTERY_MAX_STORAGE - current_battery_level
            charge_amount = min(extra_solar, BATTERY_MAX_POWER, room_in_battery)
            current_battery_level += charge_amount
            
            leftover_solar = extra_solar - charge_amount
            curtailed += leftover_solar
            
            saved_solar_used.append(demand)

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
                
        hour_cost = (gas_used * COST_GAS) + (curtailed * PENALTY_CURTAIL) + (blackout * PENALTY_BLACKOUT)
        total_cost += hour_cost
        
        saved_battery_used.append(battery_discharged)
        saved_gas_used.append(gas_used)
        saved_curtailed.append(curtailed)

    return total_cost, saved_solar_used, saved_battery_used, saved_gas_used, saved_curtailed


if __name__ == "__main__":
    hours = list(range(1, 25))

    demand = [4000, 3800, 3500, 3500, 4000, 5000, 6000, 7000, 7500, 7000, 6500, 6000, 
              6000, 6500, 7000, 8000, 9000, 10000, 9500, 8500, 7500, 6000, 5000, 4500]

    solar = [0, 0, 0, 0, 0, 1000, 3000, 6000, 9000, 11000, 12000, 12500, 
             12500, 12000, 10000, 7000, 4000, 1000, 0, 0, 0, 0, 0, 0]

    total_cost, solar_used, battery_used, gas_used, curtailed = simple_greedy_solver(hours, solar, demand)

    print(f"Total System Cost for 24 hours: ${total_cost:,.2f}")
    
    plt.figure(figsize=(12, 6))
    plt.plot(hours, demand, label='Urban Demand', color='black', linewidth=2, linestyle='--')
    
    plt.fill_between(hours, 0, solar_used, label='Solar Dispatch', color='gold', alpha=0.5)
    
    battery_bottom = solar_used
    battery_top = [s + b for s, b in zip(solar_used, battery_used)]
    plt.fill_between(hours, battery_bottom, battery_top, label='Battery Discharge', color='purple', alpha=0.6)
    
    gas_top = [t + g for t, g in zip(battery_top, gas_used)]
    plt.fill_between(hours, battery_top, gas_top, label='Gas Peaker', color='brown', alpha=0.7)
    
    plt.bar(hours, curtailed, label='Curtailed Solar', color='red', alpha=0.8, width=0.4)
    
    plt.title("Greedy Heuristic Dispatch (Simple 24-Hour Test)", fontsize=14, fontweight='bold')
    plt.xlabel("Hour of Day")
    plt.ylabel("Megawatts (MW)")
    plt.legend(loc='upper right')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()