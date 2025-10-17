# Bitaxe Hashrate Benchmark

**A fork for the NerdQAxe++ from the excellent work here [mrv777/Bitaxe-Hashrate-Benchmark](https://github.com/mrv777/Bitaxe-Hashrate-Benchmark)**

A Python-based benchmarking tool for optimizing NerdQAxe++ mining performance by testing different voltage and frequency combinations while monitoring hashrate, temperature, and power efficiency.

## TL;DR - Quick Start

**What it does:** Automatically tests different voltage/frequency combinations to find the optimal settings for your NerdQAxe++ miner.

**Quick start:**
```bash
python3 nerdqaxeplusplus_hashrate_benchmark.py -i <MINER_IP>
```

**Time required:** 1.5-4 hours for typical scan (depends on thermal limits)

**Safety:** Multi-layer protection prevents unsafe settings. Monitors temperature (68°C chip / 85°C VR), power (100W), and voltage (11.6-12.4V). Auto-stops on any limit.

**Output:** JSON file with all results, ranked by hashrate and efficiency. Best settings automatically applied at end.

---

## Features

- Automated benchmarking of different voltage/frequency combinations
- Intelligent adaptive testing algorithm (increases frequency when stable, increases voltage when unstable)
- Dual temperature monitoring (chip and voltage regulator) with safety cutoffs
- Input voltage monitoring with safety thresholds
- Power consumption monitoring with safety limits
- Power efficiency calculations (J/TH)
- Automatic saving of benchmark results with timestamped filenames
- Top 5 highest hashrate and most efficient configurations
- Graceful shutdown with best settings retention
- Comprehensive error handling and retry logic
- Expected hashrate validation based on ASIC configuration
- Outlier removal for accurate measurements
- Docker support for easy deployment

## Prerequisites

- Python 3.11 or higher
- Access to a Bitaxe miner on your network
- Docker (optional, for containerized deployment)
- Git (optional, for cloning the repository)

## Installation

### Standard Installation

1. Clone the repository:
```bash
git clone https://github.com/RussellTaylor83/NerdQAxePlusPlus-Hashrate-Benchmark.git
cd NerdQAxePlusPlus-Hashrate-Benchmark
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Docker Installation

1. Build the Docker image:
```bash
docker build -t bitaxe-benchmark .
```

## Usage

### Standard Usage

Run the benchmark tool by providing your Bitaxe's IP address:

```bash
python bitaxe_hashrate_benchmark.py <bitaxe_ip>
```

Optional parameters:
- `-v, --voltage`: Initial voltage in mV (default: 1150)
- `-f, --frequency`: Initial frequency in MHz (default: 600)

Example:
```bash
python bitaxe_hashrate_benchmark.py 192.168.2.26 -v 1150 -f 600
```

**Note:** If no arguments are provided, the script will display help information and exit.

### Docker Usage (Optional)

Run the container with your Bitaxe's IP address:

```bash
docker run --rm bitaxe-benchmark <bitaxe_ip> [options]
```

Example:
```bash
docker run --rm bitaxe-benchmark 192.168.2.26 -v 1150 -f 600
```

## Configuration

The script includes several configurable parameters (defined in the script):

- **Benchmark duration:** 300 seconds (5 minutes)
- **Sample interval:** 15 seconds
- **Stabilization:** Smart stabilization with temperature monitoring (30-180 seconds)
- **Maximum chip temperature:** 68°C
- **Maximum VR temperature:** 85°C
- **Maximum allowed voltage:** 1250mV
- **Minimum allowed voltage:** 1120mV
- **Maximum allowed frequency:** 800MHz
- **Minimum allowed frequency:** 600MHz
- **Maximum power consumption:** 100W
- **Minimum input voltage:** 11600mV (11.6V)
- **Maximum input voltage:** 12400mV (12.4V)
- **Voltage increment:** 10mV
- **Frequency increment:** 20MHz
- **Default safe voltage:** 1150mV
- **Default safe frequency:** 600MHz
- **Minimum required samples:** 7 (for valid data processing)

These values can be modified directly in the script if needed for your specific hardware configuration.

## Output

The benchmark results are saved to `nerdqaxeplusplus_benchmark_results_<ip_address>_<timestamp>.json`, containing:

### File Structure:
- **all_results:** Complete test results for all combinations tested
- **top_performers:** Top 5 configurations ranked by highest hashrate
- **most_efficient:** Top 5 configurations ranked by best efficiency (J/TH)

### Each Configuration Includes:
- Core voltage (mV)
- Frequency (MHz)
- Average hashrate (GH/s) with outlier removal
- Average temperature (°C) excluding warmup period
- Average VR temperature (°C) when available
- Efficiency (J/TH)
- Rank position

## Safety Features

- **Automatic temperature monitoring:**
  - Chip temperature cutoff at 68°C
  - Voltage regulator (VR) temperature cutoff at 85°C
  - Temperature validation (must be above 5°C to detect sensor issues)
- **Input voltage monitoring:**
  - Minimum threshold: 11.6V
  - Maximum threshold: 12.4V
- **Power consumption monitoring:** Safety cutoff at 100W
- **Voltage and frequency validation:**
  - Enforces minimum and maximum safe ranges
  - Validates user inputs before starting
- **Graceful shutdown:** Ctrl+C handling with automatic reset to best settings
- **Automatic reset:** Applies best performing settings after benchmarking
- **Hashrate validation:** Ensures stability within 10% of expected performance
- **System restart after each test:** Ensures stable baseline for each configuration
- **Protection against invalid data:** Comprehensive error handling and retry logic
- **Outlier removal:** Removes extreme values for accurate measurements

## Benchmarking Process

The tool follows this intelligent adaptive process:

1. **Initialization:**
   - Fetches current system settings and ASIC configuration
   - Displays disclaimer and safety information
   - Validates user-provided voltage and frequency parameters

2. **Testing Loop:**
   - Applies voltage/frequency settings and restarts system
   - Waits 300 seconds for system stabilization
   - Collects samples every 15 seconds during 5-minute benchmark period
   - Monitors temperature, power, voltage, and hashrate in real-time

3. **Adaptive Algorithm:**
   - Calculates expected hashrate based on ASIC configuration
   - If hashrate is within 10% of expected (stable):
     - Increases frequency by 20MHz and retests
     - When max frequency is reached, increases voltage and resets frequency to explore higher voltage ranges
   - If hashrate is below 90% of expected (unstable):
     - Increases voltage by 10mV and retests same frequency
     - If max voltage is reached, moves to next frequency
   - Continues until both maximum voltage and maximum frequency are tested
   - Stops when reaching thermal limits, power limits, or both maximums are explored

4. **Data Collection:**
   - Records all successful test results
   - Saves results after each iteration
   - Continues until limits are reached

5. **Completion:**
   - Ranks all configurations by hashrate and efficiency
   - Automatically applies the best performing settings
   - Saves comprehensive results with top performers highlighted
   - Restarts system with optimal configuration

## Data Processing

The tool implements several data processing techniques to ensure accurate results:

- **Hashrate outlier removal:** Removes 3 highest and 3 lowest readings
- **Temperature warmup exclusion:** Excludes first 6 temperature readings
- **VR temperature processing:** Excludes first 6 readings when available
- **Expected hashrate calculation:** Based on frequency × (small_core_count × asic_count) / 1000
- **Hashrate validation:** Ensures performance is within 10% of theoretical maximum
- **Power averaging:** Calculates average across entire test period
- **Efficiency calculation:** Joules per Terahash (J/TH) = Power (W) / (Hashrate (GH/s) / 1000)
- **Zero hashrate protection:** Skips efficiency calculation if hashrate is zero

## Error Handling

The script includes comprehensive error handling for various failure scenarios:

- System info fetch failures with retry logic (3 attempts)
- Temperature data unavailability
- Hashrate/power data unavailability
- Thermal limit exceeded (chip or VR)
- Input voltage out of range
- Power consumption exceeded
- Zero hashrate detection
- Connection errors and timeouts
- Graceful interrupt handling (Ctrl+C)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Disclaimer

**USE AT YOUR OWN RISK**

This tool will stress test your NerdQAxe++ by running it at various voltages and frequencies. While safeguards are in place, running hardware outside of standard parameters carries inherent risks. The author(s) are not responsible for any damage to your hardware.

**Important Note:** Ambient temperature significantly affects these results. The optimal settings found may not work well if room temperature changes substantially. Re-run the benchmark if environmental conditions change.

Always ensure proper cooling and monitor your device during benchmarking.
## Benchmarking Process

The tool follows this intelligent adaptive process:

1. **Initialization:**
   - Fetches current system settings and ASIC configuration
   - Displays disclaimer and safety information
   - Validates user-provided voltage and frequency parameters

2. **Testing Loop:**
   - Applies voltage/frequency settings and restarts system
   - **Smart Stabilization (30-180 seconds):**
     - Waits 30 seconds for initial restart
     - Monitors temperature every 15 seconds
     - Requires 3 consecutive stable readings (within 2°C)
     - Verifies system is actively hashing
     - Maximum wait: 180 seconds
   - **Benchmark Period (300 seconds):**
     - Collects samples every 15 seconds (20 total samples)
     - Monitors temperature, power, voltage, and hashrate in real-time
     - **Early Failure Detection:**
       - After 75 seconds (5 samples), checks if hashrate < 50% of expected
       - Monitors for rapid temperature rise (>10°C/min)
       - Terminates early if configuration is clearly failing

3. **Adaptive Algorithm:**
   - Calculates expected hashrate based on ASIC configuration
   - Tracks tested combinations to prevent duplicates
   - **If hashrate is within 10% of expected (stable):**
     - Increases frequency by 20MHz and retests
     - When max frequency is reached, increases voltage and resets frequency to explore higher voltage ranges
   - **If hashrate is below 90% of expected (unstable):**
     - Increases voltage by 10mV and retests same frequency
     - If max voltage is reached, moves to next frequency
   - Continues until both maximum voltage and maximum frequency are tested
   - Stops when reaching thermal limits, power limits, or both maximums are explored

4. **Data Collection:**
   - Records all successful test results
   - Saves results after each iteration (incremental saves)
   - Continues until limits are reached

5. **Completion:**
   - Ranks all configurations by hashrate and efficiency
   - Automatically applies the best performing settings
   - Saves comprehensive results with top performers highlighted
   - Restarts system with optimal configuration

## Data Processing

The tool implements several data processing techniques to ensure accurate results:

- **Hashrate outlier removal:** Removes 3 highest and 3 lowest readings
- **Temperature warmup exclusion:** Excludes first 6 temperature readings
- **VR temperature processing:** Excludes first 6 readings when available
- **Expected hashrate calculation:** Based on frequency × (small_core_count × asic_count) / 1000
- **Hashrate validation:** Ensures performance is within 10% of theoretical maximum
- **Power averaging:** Calculates average across entire test period
- **Efficiency calculation:** Joules per Terahash (J/TH) = Power (W) / (Hashrate (GH/s) / 1000)
- **Zero hashrate protection:** Skips efficiency calculation if hashrate is zero
- **Early failure detection:** Identifies failing configurations within 75 seconds

## Error Handling

The script includes comprehensive error handling for various failure scenarios:

- System info fetch failures with retry logic (3 attempts)
- Temperature data unavailability
- Hashrate/power data unavailability
- Thermal limit exceeded (chip or VR)
- Input voltage out of range
- Power consumption exceeded
- Zero hashrate detection
- Early failure detection (low hashrate or rapid temp rise)
- Connection errors and timeouts
- Graceful interrupt handling (Ctrl+C)
- Duplicate test prevention
- Multi-layer safety validation failures
- Input voltage out of range
- Power consumption exceeded
- Zero hashrate detection
- Connection errors and timeouts
- Graceful interrupt handling (Ctrl+C)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Disclaimer

**USE AT YOUR OWN RISK**

This tool will stress test your Bitaxe by running it at various voltages and frequencies. While safeguards are in place, running hardware outside of standard parameters carries inherent risks. The author(s) are not responsible for any damage to your hardware.

**Important Note:** Ambient temperature significantly affects these results. The optimal settings found may not work well if room temperature changes substantially. Re-run the benchmark if environmental conditions change.

Always ensure proper cooling and monitor your device during benchmarking.
