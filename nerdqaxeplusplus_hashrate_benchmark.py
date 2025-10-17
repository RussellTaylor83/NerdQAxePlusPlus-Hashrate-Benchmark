import requests
import time
import json
import signal
import sys
import argparse
from datetime import datetime
START_TIME = datetime.now().strftime("%Y-%m-%d_%H")


if 'START_TIME' not in globals():
    START_TIME = datetime.now().strftime("%Y-%m-%d_%H")

# ANSI Color Codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Configuration
voltage_increment = 10
frequency_increment = 20
benchmark_time = 300            # 5 minutes benchmark time
sample_interval = 15            # 15 seconds sample interval
max_temp = 68                   # Will stop if temperature reaches or exceeds this value
max_allowed_voltage = 1250      # Maximum allowed core voltage
max_allowed_frequency = 800     # Maximum allowed core frequency
max_vr_temp = 85                # Maximum allowed voltage regulator temperature
min_input_voltage = 11600       # Minimum allowed input voltage
max_input_voltage = 12400       # Maximum allowed input voltage
max_power = 100                 # Max of 100W based on 120w PSU and on DC plug
default_safe_voltage = 1150     # Predefined safe default voltage
default_safe_frequency = 600    # Predefined safe default frequency

# Run time arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='NerdQAxe++ Hashrate Benchmark Tool')
    parser.add_argument('nerdqaxeplusplus_ip', nargs='?', help='IP address of the NerdQAxe++ (e.g., 192.168.2.26)')
    parser.add_argument('-v', '--voltage', type=int, default=default_safe_voltage,
                       help='Initial voltage in mV (default: {default_safe_voltage})')
    parser.add_argument('-f', '--frequency', type=int, default=default_safe_frequency,
                       help='Initial frequency in MHz (default: {default_safe_frequency})')

    # If no arguments are provided, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()

# Replace the configuration section
args = parse_arguments()
nerdqaxeplusplus_ip = f"http://{args.nerdqaxeplusplus_ip}"
initial_voltage = args.voltage
initial_frequency = args.frequency

# Add these variables to the global configuration section
small_core_count = None
asic_count = None

# Add these constants to the configuration section
min_allowed_voltage = 1120  # Minimum allowed core voltage
min_allowed_frequency = 600  # Minimum allowed frequency

# Validate core voltages
if initial_voltage > max_allowed_voltage:
    raise ValueError(RED + f"Error: Initial voltage exceeds the maximum allowed value of {max_allowed_voltage}mV. Please check the input and try again." + RESET)

# Validate frequency
if initial_frequency > max_allowed_frequency:
    raise ValueError(RED + f"Error: Initial frequency exceeds the maximum allowed value of {max_allowed_frequency}Mhz. Please check the input and try again." + RESET)

# Add these validation checks after the existing ones
if initial_voltage < min_allowed_voltage:
    raise ValueError(RED + f"Error: Initial voltage is below the minimum allowed value of {min_allowed_voltage}mV." + RESET)

if initial_frequency < min_allowed_frequency:
    raise ValueError(RED + f"Error: Initial frequency is below the minimum allowed value of {min_allowed_frequency}MHz." + RESET)

if benchmark_time / sample_interval < 7:
    raise ValueError(RED + f"Error: Benchmark time is too short. Please increase the benchmark time or decrease the sample interval. At least 7 samples are required." + RESET)

# Results storage
results = []

# Dynamically determined default settings
default_voltage = None
default_frequency = None

# Check if we're handling an interrupt (Ctrl+C)
handling_interrupt = False
def fetch_default_settings():
    global default_voltage, default_frequency, small_core_count, asic_count
    try:
        response = requests.get(f"{nerdqaxeplusplus_ip}/api/system/info", timeout=10)
        response.raise_for_status()
        system_info = response.json()
        default_voltage = system_info.get("coreVoltage", default_safe_voltage)  # Fallback to safe value if not found
        default_frequency = system_info.get("frequency", default_safe_frequency)  # Fallback to safe value if not found
        small_core_count = system_info.get("smallCoreCount", 0)
        asic_count = system_info.get("asicCount", 0)
        print(GREEN + f"Current settings determined:\n"
                      f"  Core Voltage: {default_voltage}mV\n"
                      f"  Frequency: {default_frequency}MHz\n"
                      f"  ASIC Configuration: {small_core_count * asic_count} total cores" + RESET)
    except requests.exceptions.RequestException as e:
        print(RED + f"Error fetching default system settings: {e}. Using fallback defaults." + RESET)
        default_voltage = default_safe_voltage
        default_frequency = default_safe_frequency
        small_core_count = 0
        asic_count = 0

# Add a global flag to track whether the system has already been reset
system_reset_done = False

def handle_sigint(signum, frame):
    global system_reset_done, handling_interrupt
    
    # If we're already handling an interrupt or have completed reset, ignore this signal
    if handling_interrupt or system_reset_done:
        return
        
    handling_interrupt = True
    print(RED + "Benchmarking interrupted by user." + RESET)
    
    try:
        if results:
            reset_to_best_setting()
            save_results()
            print(GREEN + "Bitaxe reset to best or default settings and results saved." + RESET)
        else:
            print(YELLOW + "No valid benchmarking results found. Applying predefined default settings." + RESET)
            set_system_settings(default_voltage, default_frequency)
    finally:
        system_reset_done = True
        handling_interrupt = False
        sys.exit(0)

# Register the signal handler
signal.signal(signal.SIGINT, handle_sigint)

def get_system_info():
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(f"{nerdqaxeplusplus_ip}/api/system/info", timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.Timeout:
            print(YELLOW + f"Timeout while fetching system info. Attempt {attempt + 1} of {retries}." + RESET)
        except requests.exceptions.ConnectionError:
            print(RED + f"Connection error while fetching system info. Attempt {attempt + 1} of {retries}." + RESET)
        except requests.exceptions.RequestException as e:
            print(RED + f"Error fetching system info: {e}" + RESET)
            break
        time.sleep(5)  # Wait before retrying
    return None

def set_system_settings(core_voltage, frequency):
    # Safety validation before applying settings
    if core_voltage < min_allowed_voltage:
        print(RED + f"SAFETY ERROR: Attempted to set voltage {core_voltage}mV below minimum {min_allowed_voltage}mV. Aborting." + RESET)
        raise ValueError(f"Voltage {core_voltage}mV is below minimum allowed {min_allowed_voltage}mV")

    if core_voltage > max_allowed_voltage:
        print(RED + f"SAFETY ERROR: Attempted to set voltage {core_voltage}mV above maximum {max_allowed_voltage}mV. Aborting." + RESET)
        raise ValueError(f"Voltage {core_voltage}mV exceeds maximum allowed {max_allowed_voltage}mV")

    if frequency < min_allowed_frequency:
        print(RED + f"SAFETY ERROR: Attempted to set frequency {frequency}MHz below minimum {min_allowed_frequency}MHz. Aborting." + RESET)
        raise ValueError(f"Frequency {frequency}MHz is below minimum allowed {min_allowed_frequency}MHz")

    if frequency > max_allowed_frequency:
        print(RED + f"SAFETY ERROR: Attempted to set frequency {frequency}MHz above maximum {max_allowed_frequency}MHz. Aborting." + RESET)
        raise ValueError(f"Frequency {frequency}MHz exceeds maximum allowed {max_allowed_frequency}MHz")

    settings = {
        "coreVoltage": core_voltage,
        "frequency": frequency
    }
    try:
        response = requests.patch(f"{nerdqaxeplusplus_ip}/api/system", json=settings, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print(YELLOW + f"Applying settings: Voltage = {core_voltage}mV, Frequency = {frequency}MHz" + RESET)
        time.sleep(2)
        restart_system()
    except requests.exceptions.RequestException as e:
        print(RED + f"Error setting system settings: {e}" + RESET)

def restart_system():
    try:
        # Check if we're being called from handle_sigint
        is_interrupt = handling_interrupt

        # Restart here as some nerdqaxeplusplus devices get unstable with bad settings
        # If not an interrupt, wait for system stabilization as some nerdqaxeplusplus devices are slow to ramp up
        if not is_interrupt:
            print(YELLOW + "Applying new settings and restarting system..." + RESET)
            response = requests.post(f"{nerdqaxeplusplus_ip}/api/system/restart", timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Smart stabilization: wait for system to come online and stabilize
            print(YELLOW + "Waiting for system to restart and stabilize..." + RESET)
            time.sleep(30)  # Initial wait for restart

            # Monitor temperature stability
            stable_readings = 0
            required_stable_readings = 3
            previous_temp = None
            max_stabilization_time = 180  # Maximum 3 minutes
            start_time = time.time()

            while stable_readings < required_stable_readings:
                if time.time() - start_time > max_stabilization_time:
                    print(YELLOW + f"Stabilization timeout reached ({max_stabilization_time}s). Proceeding with benchmark." + RESET)
                    break

                info = get_system_info()
                if info is not None:
                    current_temp = info.get("temp")
                    hash_rate = info.get("hashRate")

                    if current_temp is not None and hash_rate is not None and hash_rate > 0:
                        if previous_temp is not None:
                            temp_change = abs(current_temp - previous_temp)
                            if temp_change <= 2:  # Temperature stable within 2°C
                                stable_readings += 1
                                print(YELLOW + f"Stabilization check {stable_readings}/{required_stable_readings}: Temp={current_temp}°C, HashRate={hash_rate:.1f} GH/s" + RESET)
                            else:
                                stable_readings = 0  # Reset if temperature fluctuates
                        previous_temp = current_temp

                time.sleep(15)  # Check every 15 seconds

            print(GREEN + "System stabilized and ready for benchmarking." + RESET)
        else:
            print(YELLOW + "Applying final settings..." + RESET)
            response = requests.post(f"{nerdqaxeplusplus_ip}/api/system/restart", timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print(RED + f"Error restarting the system: {e}" + RESET)

def benchmark_iteration(core_voltage, frequency):
    current_time = time.strftime("%H:%M:%S")
    print(GREEN + f"[{current_time}] Starting benchmark for Core Voltage: {core_voltage}mV, Frequency: {frequency}MHz" + RESET)
    hash_rates = []
    temperatures = []
    power_consumptions = []
    vr_temps = []
    total_samples = benchmark_time // sample_interval
    expected_hashrate = frequency * ((small_core_count * asic_count) / 1000)  # Calculate expected hashrate based on frequency
    
    for sample in range(total_samples):
        info = get_system_info()
        if info is None:
            print(YELLOW + "Skipping this iteration due to failure in fetching system info." + RESET)
            return None, None, None, False, None, "SYSTEM_INFO_FAILURE"
        
        temp = info.get("temp")
        vr_temp = info.get("vrTemp")  # Get VR temperature if available
        voltage = info.get("voltage")
        if temp is None:
            print(YELLOW + "Temperature data not available." + RESET)
            return None, None, None, False, None, "TEMPERATURE_DATA_FAILURE"
        
        if temp < 5:
            print(YELLOW + "Temperature is below 5°C. This is unexpected. Please check the system." + RESET)
            return None, None, None, False, None, "TEMPERATURE_BELOW_5"
        
        # Check both chip and VR temperatures
        if temp >= max_temp:
            print(RED + f"Chip temperature of {temp}°C exceeded {max_temp}°C! Stopping current benchmark." + RESET)
            return None, None, None, False, None, "CHIP_TEMP_EXCEEDED"
            
        if vr_temp is not None and vr_temp >= max_vr_temp:
            print(RED + f"Voltage regulator temperature of {vr_temp}°C exceeded {max_vr_temp}°C! Stopping current benchmark." + RESET)
            return None, None, None, False, None, "VR_TEMP_EXCEEDED"

        if voltage < min_input_voltage:
            print(RED + f"Input voltage of {voltage}mV is below the minimum allowed value of {min_input_voltage}mV! Stopping current benchmark." + RESET)
            return None, None, None, False, None, "INPUT_VOLTAGE_BELOW_MIN"
        
        if voltage > max_input_voltage:
            print(RED + f"Input voltage of {voltage}mV is above the maximum allowed value of {max_input_voltage}mV! Stopping current benchmark." + RESET)
            return None, None, None, False, None, "INPUT_VOLTAGE_ABOVE_MAX"
        
        hash_rate = info.get("hashRate")
        power_consumption = info.get("power")
        
        if hash_rate is None or power_consumption is None:
            print(YELLOW + "Hashrate or Watts data not available." + RESET)
            return None, None, None, False, None, "HASHRATE_POWER_DATA_FAILURE"
        
        if power_consumption > max_power:
            print(RED + f"Power consumption exceeded {max_power}W! Stopping current benchmark." + RESET)
            return None, None, None, False, None, "POWER_CONSUMPTION_EXCEEDED"

        hash_rates.append(hash_rate)
        temperatures.append(temp)
        power_consumptions.append(power_consumption)
        if vr_temp is not None and vr_temp > 0:
            vr_temps.append(vr_temp)

        # Early failure detection after collecting enough samples
        if sample >= 4:  # After 5 samples (75 seconds)
            recent_hashrates = hash_rates[-5:]  # Last 5 samples
            avg_recent_hashrate = sum(recent_hashrates) / len(recent_hashrates)

            # If hashrate is consistently very low (< 50% of expected), fail early
            if avg_recent_hashrate < expected_hashrate * 0.5:
                print(RED + f"Early failure detected: Hashrate {avg_recent_hashrate:.1f} GH/s is less than 50% of expected {expected_hashrate:.1f} GH/s" + RESET)
                return None, None, None, False, None, "EARLY_FAILURE_LOW_HASHRATE"

            # If temperature is rising too quickly, fail early
            if len(temperatures) >= 5:
                temp_trend = temperatures[-1] - temperatures[-5]
                if temp_trend > 10:  # Temperature rose more than 10°C in last minute
                    print(RED + f"Early failure detected: Temperature rising too quickly ({temp_trend}°C in 60s)" + RESET)
                    return None, None, None, False, None, "EARLY_FAILURE_TEMP_RISING"

        # Calculate percentage progress
        percentage_progress = ((sample + 1) / total_samples) * 100
        status_line = (
            f"[{sample + 1:2d}/{total_samples:2d}] "
            f"{percentage_progress:5.1f}% | "
            f"CV: {core_voltage:4d}mV | "
            f"F: {frequency:4d}MHz | "
            f"H: {int(hash_rate):4d} GH/s | "
            f"IV: {int(voltage):4d}mV | "
            f"T: {int(temp):2d}°C"
        )
        if vr_temp is not None and vr_temp > 0:
            status_line += f" | VR: {int(vr_temp):2d}°C"
        print(status_line + RESET)

        # Only sleep if it's not the last iteration
        if sample < total_samples - 1:
            time.sleep(sample_interval)
    
    if hash_rates and temperatures and power_consumptions:
        # Remove 3 highest and 3 lowest hashrates in case of outliers
        sorted_hashrates = sorted(hash_rates)
        trimmed_hashrates = sorted_hashrates[3:-3]  # Remove first 3 and last 3 elements
        average_hashrate = sum(trimmed_hashrates) / len(trimmed_hashrates)
        
        # Sort and trim temperatures (remove lowest 6 readings during warmup)
        sorted_temps = sorted(temperatures)
        trimmed_temps = sorted_temps[6:]  # Remove first 6 elements only
        average_temperature = sum(trimmed_temps) / len(trimmed_temps)
        
        # Only process VR temps if we have valid readings
        average_vr_temp = None
        if vr_temps:
            sorted_vr_temps = sorted(vr_temps)
            trimmed_vr_temps = sorted_vr_temps[6:]  # Remove first 6 elements only
            average_vr_temp = sum(trimmed_vr_temps) / len(trimmed_vr_temps)
        
        average_power = sum(power_consumptions) / len(power_consumptions)
        
        # Add protection against zero hashrate
        if average_hashrate > 0:
            efficiency_jth = average_power / (average_hashrate / 1_000)
        else:
            print(RED + "Warning: Zero hashrate detected, skipping efficiency calculation" + RESET)
            return None, None, None, False, None, "ZERO_HASHRATE"
        
        # Calculate if hashrate is within 10% of expected
        hashrate_within_tolerance = (average_hashrate >= expected_hashrate * 0.90)
        
        print(GREEN + f"Average Hashrate: {average_hashrate:.2f} GH/s (Expected: {expected_hashrate:.2f} GH/s)" + RESET)
        print(GREEN + f"Average Temperature: {average_temperature:.2f}°C" + RESET)
        if average_vr_temp is not None:
            print(GREEN + f"Average VR Temperature: {average_vr_temp:.2f}°C" + RESET)
        print(GREEN + f"Efficiency: {efficiency_jth:.2f} J/TH" + RESET)
        
        return average_hashrate, average_temperature, efficiency_jth, hashrate_within_tolerance, average_vr_temp, None
    else:
        print(YELLOW + "No Hashrate or Temperature or Watts data collected." + RESET)
        return None, None, None, False, None, "NO_DATA_COLLECTED"

def save_results():
    try:
        # Extract IP from nerdqaxeplusplus_ip global variable and remove 'http://'
        ip_address = nerdqaxeplusplus_ip.replace('http://', '')
        filename = f"nerdqaxeplusplus_benchmark_results_{ip_address}_{START_TIME}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=4)
        print(GREEN + f"Results saved to {filename}" + RESET)
        print()  # Add empty line

    except IOError as e:
        print(RED + f"Error saving results to file: {e}" + RESET)

def reset_to_best_setting():
    if not results:
        print(YELLOW + "No valid benchmarking results found. Applying predefined default settings." + RESET)
        set_system_settings(default_voltage, default_frequency)
    else:
        best_result = sorted(results, key=lambda x: x["averageHashRate"], reverse=True)[0]
        best_voltage = best_result["coreVoltage"]
        best_frequency = best_result["frequency"]

        print(GREEN + f"Applying the best settings from benchmarking:\n"
                      f"  Core Voltage: {best_voltage}mV\n"
                      f"  Frequency: {best_frequency}MHz" + RESET)
        set_system_settings(best_voltage, best_frequency)
    
    restart_system()

# Main benchmarking process
try:
    fetch_default_settings()
    
    # Add disclaimer
    # Add disclaimer
    print(RED + "\nDISCLAIMER:" + RESET)
    print("This tool will stress test your NerdQAxe++ by running it at various voltages and frequencies.")
    print("While safeguards are in place, running hardware outside of standard parameters carries inherent risks.")
    print("Use this tool at your own risk. The author(s) are not responsible for any damage to your hardware.")
    print("\nNOTE: Ambient temperature significantly affects these results. The optimal settings found may not")
    print("work well if room temperature changes substantially. Re-run the benchmark if conditions change.\n")
    
    current_voltage = initial_voltage
    current_frequency = initial_frequency

    # Track if we've reached maximums
    max_voltage_reached = False
    max_frequency_reached = False

    # Track tested combinations to avoid duplicates
    tested_combinations = set()

    while not (max_voltage_reached and max_frequency_reached):
        # Create a unique key for this combination
        combination_key = (current_voltage, current_frequency)

        # Skip if we've already tested this combination
        if combination_key in tested_combinations:
            print(YELLOW + f"Skipping already tested combination: Voltage={current_voltage}mV, Frequency={current_frequency}MHz" + RESET)
            # Move to next combination
            if current_frequency + frequency_increment <= max_allowed_frequency:
                current_frequency += frequency_increment
            elif current_voltage + voltage_increment <= max_allowed_voltage:
                current_voltage += voltage_increment
                current_frequency = initial_frequency
            else:
                # Both at max, we're done
                max_voltage_reached = True
                max_frequency_reached = True
                break
            continue

        # Mark this combination as tested
        tested_combinations.add(combination_key)

        # Validate values before applying (belt and suspenders approach)
        if current_voltage > max_allowed_voltage or current_frequency > max_allowed_frequency:
            print(RED + f"SAFETY CHECK: Attempted to test unsafe values (V={current_voltage}mV, F={current_frequency}MHz). Stopping." + RESET)
            break

        if current_voltage < min_allowed_voltage or current_frequency < min_allowed_frequency:
            print(RED + f"SAFETY CHECK: Values below minimum (V={current_voltage}mV, F={current_frequency}MHz). Stopping." + RESET)
            break

        set_system_settings(current_voltage, current_frequency)
        avg_hashrate, avg_temp, efficiency_jth, hashrate_ok, avg_vr_temp, error_reason = benchmark_iteration(current_voltage, current_frequency)

        if avg_hashrate is not None and avg_temp is not None and efficiency_jth is not None:
            result = {
                "coreVoltage": current_voltage,
                "frequency": current_frequency,
                "averageHashRate": avg_hashrate,
                "averageTemperature": avg_temp,
                "efficiencyJTH": efficiency_jth
            }

            # Only add VR temp if it exists
            if avg_vr_temp is not None:
                result["averageVRTemp"] = avg_vr_temp

            results.append(result)

            # Display current best results after each test (incremental results display)
            print(CYAN + "\n" + "="*70 + RESET)
            print(CYAN + "CURRENT BEST RESULTS:" + RESET)

            # Find current best hashrate
            best_hashrate_result = max(results, key=lambda x: x["averageHashRate"])
            print(GREEN + f"  Best Hashrate: {best_hashrate_result['averageHashRate']:.2f} GH/s" + RESET)
            print(f"    └─ Voltage: {best_hashrate_result['coreVoltage']}mV, Frequency: {best_hashrate_result['frequency']}MHz")
            print(f"    └─ Temp: {best_hashrate_result['averageTemperature']:.1f}°C, Efficiency: {best_hashrate_result['efficiencyJTH']:.2f} J/TH")

            # Find current best efficiency
            best_efficiency_result = min(results, key=lambda x: x["efficiencyJTH"])
            print(GREEN + f"  Best Efficiency: {best_efficiency_result['efficiencyJTH']:.2f} J/TH" + RESET)
            print(f"    └─ Voltage: {best_efficiency_result['coreVoltage']}mV, Frequency: {best_efficiency_result['frequency']}MHz")
            print(f"    └─ Hashrate: {best_efficiency_result['averageHashRate']:.2f} GH/s, Temp: {best_efficiency_result['averageTemperature']:.1f}°C")

            print(CYAN + f"  Total configurations tested: {len(results)}" + RESET)
            print(CYAN + "="*70 + "\n" + RESET)

            if hashrate_ok:
                # If hashrate is good, try increasing frequency
                if current_frequency + frequency_increment <= max_allowed_frequency:
                    current_frequency += frequency_increment
                else:
                    max_frequency_reached = True
                    # If we've reached max frequency, try increasing voltage if not at max
                    if current_voltage + voltage_increment <= max_allowed_voltage:
                        current_voltage += voltage_increment
                        # Reset frequency to initial to explore higher voltage with all frequencies
                        current_frequency = initial_frequency
                        max_frequency_reached = False  # Reset since we're exploring new voltage
                        print(YELLOW + f"Max frequency reached. Increasing voltage to {current_voltage}mV and resetting frequency to {current_frequency}MHz" + RESET)
                    else:
                        max_voltage_reached = True
                        print(GREEN + f"Reached maximum voltage ({max_allowed_voltage}mV) and frequency ({max_allowed_frequency}MHz) with good results." + RESET)
            else:
                # If hashrate is not good, increase voltage and retry same frequency
                if current_voltage + voltage_increment <= max_allowed_voltage:
                    current_voltage += voltage_increment
                    print(YELLOW + f"Hashrate too low compared to expected. Increasing voltage to {current_voltage}mV and retrying frequency {current_frequency}MHz" + RESET)
                else:
                    max_voltage_reached = True
                    # If we can't increase voltage, try next frequency if available
                    if current_frequency + frequency_increment <= max_allowed_frequency:
                        current_frequency += frequency_increment
                        print(YELLOW + f"Max voltage reached. Moving to next frequency: {current_frequency}MHz" + RESET)
                    else:
                        max_frequency_reached = True
                        print(YELLOW + f"Reached maximum voltage ({max_allowed_voltage}mV) and frequency ({max_allowed_frequency}MHz) but hashrate is below expected." + RESET)
        else:
            # If we hit thermal limits or other issues, we've found the highest safe settings
            print(GREEN + f"Reached thermal or stability limits at V={current_voltage}mV, F={current_frequency}MHz. Stopping further testing." + RESET)
            break  # Stop testing higher values

        save_results()

except Exception as e:
    print(RED + f"An unexpected error occurred: {e}" + RESET)
    if results:
        reset_to_best_setting()
        save_results()
    else:
        print(YELLOW + "No valid benchmarking results found. Applying predefined default settings." + RESET)
        set_system_settings(default_voltage, default_frequency)
        restart_system()
finally:
    if not system_reset_done:
        if results:
            reset_to_best_setting()
            save_results()
            print(GREEN + "Bitaxe reset to best or default settings and results saved." + RESET)
        else:
            print(YELLOW + "No valid benchmarking results found. Applying predefined default settings." + RESET)
            set_system_settings(default_voltage, default_frequency)
            restart_system()
        system_reset_done = True

    # Print results summary only if we have results
    if results:
        # Sort results by averageHashRate in descending order and get the top 5
        top_5_results = sorted(results, key=lambda x: x["averageHashRate"], reverse=True)[:5]
        top_5_efficient_results = sorted(results, key=lambda x: x["efficiencyJTH"], reverse=False)[:5]
        
        # Create a dictionary containing all results and top performers
        final_data = {
            "all_results": results,
            "top_performers": [
                {
                    "rank": i,
                    "coreVoltage": result["coreVoltage"],
                    "frequency": result["frequency"],
                    "averageHashRate": result["averageHashRate"],
                    "averageTemperature": result["averageTemperature"],
                    "efficiencyJTH": result["efficiencyJTH"],
                    **({"averageVRTemp": result["averageVRTemp"]} if "averageVRTemp" in result else {})
                }
                for i, result in enumerate(top_5_results, 1)
            ],
            "most_efficient": [
                {
                    "rank": i,
                    "coreVoltage": result["coreVoltage"],
                    "frequency": result["frequency"],
                    "averageHashRate": result["averageHashRate"],
                    "averageTemperature": result["averageTemperature"],
                    "efficiencyJTH": result["efficiencyJTH"],
                    **({"averageVRTemp": result["averageVRTemp"]} if "averageVRTemp" in result else {})
                }
                for i, result in enumerate(top_5_efficient_results, 1)
            ]
        }
        
        # Save the final data to JSON
        ip_address = nerdqaxeplusplus_ip.replace('http://', '')
        filename = f"nerdqaxeplusplus_benchmark_results_{ip_address}_{START_TIME}.json"
        with open(filename, "w") as f:
            json.dump(final_data, f, indent=4)
        
        print(GREEN + "Benchmarking completed." + RESET)
        if top_5_results:
            print(GREEN + "\nTop 5 Highest Hashrate Settings:" + RESET)
            for i, result in enumerate(top_5_results, 1):
                print(GREEN + f"\nRank {i}:" + RESET)
                print(GREEN + f"  Core Voltage: {result['coreVoltage']}mV" + RESET)
                print(GREEN + f"  Frequency: {result['frequency']}MHz" + RESET)
                print(GREEN + f"  Average Hashrate: {result['averageHashRate']:.2f} GH/s" + RESET)
                print(GREEN + f"  Average Temperature: {result['averageTemperature']:.2f}°C" + RESET)
                print(GREEN + f"  Efficiency: {result['efficiencyJTH']:.2f} J/TH" + RESET)
                if "averageVRTemp" in result:
                    print(GREEN + f"  Average VR Temperature: {result['averageVRTemp']:.2f}°C" + RESET)
            
            print(GREEN + "\nTop 5 Most Efficient Settings:" + RESET)
            for i, result in enumerate(top_5_efficient_results, 1):
                print(GREEN + f"\nRank {i}:" + RESET)
                print(GREEN + f"  Core Voltage: {result['coreVoltage']}mV" + RESET)
                print(GREEN + f"  Frequency: {result['frequency']}MHz" + RESET)
                print(GREEN + f"  Average Hashrate: {result['averageHashRate']:.2f} GH/s" + RESET)
                print(GREEN + f"  Average Temperature: {result['averageTemperature']:.2f}°C" + RESET)
                print(GREEN + f"  Efficiency: {result['efficiencyJTH']:.2f} J/TH" + RESET)
                if "averageVRTemp" in result:
                    print(GREEN + f"  Average VR Temperature: {result['averageVRTemp']:.2f}°C" + RESET)
        else:
            print(RED + "No valid results were found during benchmarking." + RESET)

# Add this new function to handle cleanup
def cleanup_and_exit(reason=None):
    global system_reset_done
    if system_reset_done:
        return
        
    try:
        if results:
            reset_to_best_setting()
            save_results()
            print(GREEN + "Bitaxe reset to best settings and results saved." + RESET)
        else:
            print(YELLOW + "No valid benchmarking results found. Applying predefined default settings." + RESET)
            set_system_settings(default_voltage, default_frequency)
    finally:
        system_reset_done = True
        if reason:
            print(RED + f"Benchmarking stopped: {reason}" + RESET)
        print(GREEN + "Benchmarking completed." + RESET)
        sys.exit(0)
