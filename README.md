# NerdQAxe++ Hashrate Benchmark

**A fork for the NerdQAxe++ from the excellent work by [mrv777/Bitaxe-Hashrate-Benchmark](https://github.com/mrv777/Bitaxe-Hashrate-Benchmark)**

Automatically tests different voltage and frequency combinations to find optimal settings for your NerdQAxe++ miner.

---

## ⚠️ DISCLAIMER

**USE AT YOUR OWN RISK.** This tool stress tests your hardware by running it at various voltages and frequencies. While safety protections are implemented, overclocking carries inherent risks including hardware damage, reduced lifespan, and voided warranties. The author(s) are NOT liable for any damage. Ensure adequate cooling and monitor your device during testing.

---

## Quick Start

```bash
python3 nerdqaxeplusplus_hashrate_benchmark.py <MINER_IP>
```

**Time required:** 1.5-4 hours depending on thermal limits

**What you get:** JSON file with all results ranked by hashrate and efficiency. Best settings automatically applied.

---

## How It Works

The tool tests voltage/frequency combinations using an adaptive algorithm:

1. **Starts at your specified voltage and frequency** (defaults: 1150mV, 600MHz)
2. **Tests each configuration** for 5 minutes while monitoring temperature, power, and hashrate
3. **Adapts based on results:**
   - If hashrate is stable (within 10% of expected): increases frequency
   - If hashrate is unstable: increases voltage
4. **Stops when limits are reached:** thermal limits (68°C chip / 85°C VR), power limit (100W), or maximum values
5. **Applies best settings** and saves comprehensive results

**Safety features:** 4-layer validation, smart stabilization, early failure detection, real-time monitoring, PSU warnings, and graceful Ctrl+C handling.

---

## Installation

```bash
git clone https://github.com/RussellTaylor83/NerdQAxePlusPlus-Hashrate-Benchmark.git
cd NerdQAxePlusPlus-Hashrate-Benchmark
pip install -r requirements.txt
```

---

## Usage

**Basic:**
```bash
python3 nerdqaxeplusplus_hashrate_benchmark.py 192.168.1.100
```

**With custom starting values:**
```bash
python3 nerdqaxeplusplus_hashrate_benchmark.py 192.168.1.100 -v 1150 -f 600
```

**Parameters:**
- `MINER_IP` - IP address of your NerdQAxe++ (required)
- `-v, --voltage` - Starting voltage in mV (default: 1150, range: 1120-1250)
- `-f, --frequency` - Starting frequency in MHz (default: 600, range: 600-800)

---

## Each Test Undergoes

1. **System Restart:** ~5-10 seconds
2. **Smart Stabilization:** 30-180 seconds (adaptive)
   - Waits for 3 consecutive stable temperature readings (within 2°C)
   - Verifies system is hashing
3. **Benchmark Period:** 300 seconds (5 minutes)
   - Collects 20 samples at 15-second intervals
   - Continuous safety monitoring
4. **Early Termination:** May stop after 75 seconds if clearly failing

**Total per test:** ~5.5-8 minutes

---

## Configuration Limits

These safety limits are hardcoded in the script:

- **Voltage:** 1120-1250mV (increments of 10mV)
- **Frequency:** 600-800MHz (increments of 20MHz)
- **Chip temperature:** 68°C maximum
- **VR temperature:** 85°C maximum
- **Power consumption:** 100W maximum (warning at 90W)
- **Input voltage:** 11.6-12.4V

---

## Output

Results saved to: `nerdqaxeplusplus_benchmark_results_<ip>_<timestamp>.json`

**File contains:**
- All test results
- Top 5 configurations by hashrate
- Top 5 configurations by efficiency (J/TH)

**Real-time display:** After each test, see current best hashrate and efficiency.

---

## Docker (Optional)

```bash
docker build -t nerdqaxeplusplus-benchmark .
docker run --rm nerdqaxeplusplus-benchmark 192.168.1.100 -v 1150 -f 600
```

---

## License

GNU General Public License v3.0 - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Forked from [mrv777/Bitaxe-Hashrate-Benchmark](https://github.com/mrv777/Bitaxe-Hashrate-Benchmark) and adapted for NerdQAxe++ with enhanced safety features and optimizations.
