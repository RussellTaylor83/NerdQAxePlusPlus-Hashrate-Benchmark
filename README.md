# NerdQAxe++ Hashrate Benchmark

**A fork for the NerdQAxe++ from the excellent work here [mrv777/Bitaxe-Hashrate-Benchmark](https://github.com/mrv777/Bitaxe-Hashrate-Benchmark)**

A Python-based benchmarking tool for optimizing NerdQAxe++ mining performance by testing different voltage and frequency combinations while monitoring hashrate, temperature, and power efficiency.

---

## ⚠️ DISCLAIMER - READ BEFORE USE

**USE AT YOUR OWN RISK**

This tool will stress test your NerdQAxe++ hardware by running it at various voltages and frequencies to find optimal performance settings. While multiple layers of safety protections are implemented, **overclocking and stress testing hardware carries inherent risks** including but not limited to:

- Hardware damage or failure
- Reduced hardware lifespan
- Voided warranties
- Fire hazard if cooling is inadequate
- Data loss or system instability

**By using this software, you acknowledge and accept that:**
- You are solely responsible for any damage to your hardware
- The author(s) and contributors are NOT liable for any hardware damage, data loss, or other issues
- You understand the risks of overclocking and stress testing
- You will ensure adequate cooling and monitoring during testing
- You will not hold the author(s) responsible for any consequences

**Important Environmental Note:** Ambient temperature significantly affects benchmark results. Optimal settings found at one temperature may be unstable at different temperatures. Re-run the benchmark if environmental conditions change substantially.

**Always ensure proper cooling and actively monitor your device during benchmarking.**

---

## TL;DR - Quick Start

**What it does:** Automatically tests different voltage/frequency combinations to find the optimal settings for your NerdQAxe++ miner.

**Quick start:**
```bash
python3 nerdqaxeplusplus_hashrate_benchmark.py -i <MINER_IP> -sv 1150 -sf 600 -mv 1250 -mf 800
```

**Time required:** 1.5-4 hours for typical scan (depends on thermal limits)

**Safety:** Multi-layer protection prevents unsafe settings. Monitors temperature (68°C chip / 85°C VR), power (100W), and voltage (11.6-12.4V). Auto-stops on any limit.

**Output:** JSON file with all results, ranked by hashrate and efficiency. Best settings automatically applied at end.

**Key features:**
- ✅ Smart stabilization (30-180s adaptive wait)
- ✅ Early failure detection (stops bad configs in 75s)
- ✅ Real-time progress display with current best results
- ✅ PSU capacity warnings at 90% threshold
- ✅ 4-layer safety validation
- ✅ Graceful Ctrl+C handling

---

## Features

- Automated benchmarking of different voltage/frequency combinations
- Intelligent adaptive testing algorithm (increases frequency when stable, increases voltage when unstable)
- Smart stabilization with temperature monitoring (30-180 seconds adaptive)
- Early failure detection (terminates bad configurations in 75 seconds)
- Real-time progress display showing current best results after each test
- Dual temperature monitoring (chip and voltage regulator) with safety cutoffs
- Input voltage monitoring with safety thresholds (11.6-12.4V)
- Power consumption monitoring with safety limits and PSU capacity warnings
- Power efficiency calculations (J/TH)
- Automatic saving of benchmark results with timestamped filenames
- Top 5 highest hashrate and most efficient configurations
- Graceful shutdown with best settings retention
- Comprehensive error handling and retry logic
- Expected hashrate validation based on ASIC configuration
- Outlier removal for accurate measurements
- Duplicate test prevention
- Multi-layer safety validation (4 layers of protection)
- Docker support for easy deployment

## Prerequisites

- Python 3.11 or higher
- Access to a NerdQAxe++ miner on your network
- Docker (optional, for containerized deployment)
- Git (optional, for cloning the repository)

## Installation

### Standard Installation

1. Clone the repository:
```bash
git clone https://github.com/RussellTaylor83/NerdQAxePlusPlus-Hashrate-Benchmark.git
cd NerdQAxePlusPlus-Hashrate-Benchmark
```

2. Create and activate a virtual environment (recommended):
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
docker build -t nerdqaxeplusplus-benchmark .
```

## Usage

### Standard Usage

Run the benchmark tool by providing your NerdQAxe++'s IP address and voltage/frequency parameters:

```bash
python3 nerdqaxeplusplus_hashrate_benchmark.py -i <MINER_IP> -sv <START_VOLTAGE> -sf <START_FREQUENCY> -mv <MAX_VOLTAGE> -mf <MAX_FREQUENCY>
```

**Required parameters:**
- `-i, --ip`: IP address of your NerdQAxe++ miner

**Optional parameters:**
- `-sv, --start-voltage`: Starting voltage in mV (default: 1150, min: 1120, max: 1250)
- `-sf, --start-frequency`: Starting frequency in MHz (default: 600, min: 600, max: 800)
- `-mv, --max-voltage`: Maximum voltage in mV (default: 1250, min: 1120, max: 1250)
- `-mf, --max-frequency`: Maximum frequency in MHz (default: 800, min: 600, max: 800)

**Examples:**

Basic usage with defaults:
```bash
python3 nerdqaxeplusplus_hashrate_benchmark.py -i 192.168.1.100
```

Custom voltage and frequency range:
```bash
python3 nerdqaxeplusplus_hashrate_benchmark.py -i 192.168.1.100 -sv 1150 -sf 600 -mv 1250 -mf 800
```

Conservative testing (lower max values):
```bash
python3 nerdqaxeplusplus_hashrate_benchmark.py -i 192.168.1.100 -sv 1150 -sf 600 -mv 1200 -mf 750
```

**Note:** If no arguments are provided, the script will display help information and exit.

### Docker Usage (Optional)

Run the container with your NerdQAxe++'s IP address:

```bash
docker run --rm nerdqaxeplusplus-benchmark -i <MINER_IP> [options]
```

Example:
```bash
docker run --rm nerdqaxeplusplus-benchmark -i 192.168.1.100 -sv 1150 -sf 600 -mv 1250 -mf 800
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
- **PSU capacity warning threshold:** 90W (90% of max)
- **Minimum input voltage:** 11600mV (11.6V)
- **Maximum input voltage:** 12400mV (12.4V)
- **Voltage increment:** 10mV
- **Frequency increment:** 20MHz
- **Default safe voltage:** 1150mV
- **Default safe frequency:** 600MHz
- **Minimum required samples:** 7 (for valid data processing)

These values can be modified directly in the script if needed for your specific hardware configuration.

## Testing Duration Per Configuration

Each configuration undergoes:

1. **System Restart:** ~5-10 seconds
2. **Smart Stabilization:** 30-180 seconds (adaptive based on temperature stability)
   - Waits for 3 consecutive stable temperature readings (within 2°C)
   - Maximum wait time: 180 seconds
   - Monitors hashrate to ensure system is hashing
3. **Benchmark Period:** 300 seconds (5 minutes)
   - Collects 20 samples at 15-second intervals
   - Continuous monitoring of temperature, power, and hashrate
4. **Early Failure Detection:** May terminate early if:
   - Hashrate is < 50% of expected after 75 seconds
   - Temperature rising > 10°C per minute

**Total time per configuration:** Approximately 5.5-8 minutes (depending on stabilization)

**Estimated total benchmark time:** Varies based on how many configurations are tested before hitting limits. With default settings (1150mV-1250mV voltage range, 600-800MHz frequency range), expect 1.5-4 hours for a complete benchmark.

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

### Real-Time Progress Display

After each successful test, the script displays:
- Current best hashrate with configuration details
- Current best efficiency with configuration details
- Total configurations tested so far

This allows you to monitor progress and decide whether to continue or stop early (Ctrl+C) if satisfied with results.

## Safety Features

The script implements multiple layers of protection:

- **Multi-layer safety validation:**
  - Initial user input validation
  - Loop logic prevents exceeding limits
  - Pre-application safety checks
  - Function-level validation before API calls
- **Automatic temperature monitoring:**
  - Chip temperature cutoff at 68°C
  - Voltage regulator (VR) temperature cutoff at 85°C
  - Temperature validation (must be above 5°C to detect sensor issues)
  - Early detection of rapid temperature rise (>10°C/min)
- **Input voltage monitoring:**
  - Minimum threshold: 11.6V
  - Maximum threshold: 12.4V
- **Power consumption monitoring:**
  - Safety cutoff at 100W
  - Warning at 90W (90% of maximum)
- **Voltage and frequency validation:**
  - Enforces minimum and maximum safe ranges at 4 different points
  - Validates user inputs before starting
  - Prevents duplicate testing of same combinations
- **Early failure detection:**
  - Stops testing if hashrate < 50% of expected
  - Detects rapid temperature increases
  - Saves time and reduces hardware stress
- **Smart stabilization:**
  - Monitors temperature stability before benchmarking
  - Ensures system is hashing before starting test
  - Adaptive wait time based on actual stability
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
   - Displays current best results after each test
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

This project is a fork of the excellent work by [mrv777/Bitaxe-Hashrate-Benchmark](https://github.com/mrv777/Bitaxe-Hashrate-Benchmark), adapted specifically for the NerdQAxe++ hardware with enhanced safety features and optimizations.
