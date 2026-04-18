# Testing Instructions (Phase 3, 4 & 5)

This file contains the step-by-step commands you need to run to verify that the controller and the topology are working as expected and to capture the evidence required for Phase 5.

### Terminal 1: Start the Controller
Start the Ryu controller and log its output to both the terminal and a file for later analysis.

```bash
cd ~/Projects/sdn-traffic-monitor
ryu-manager controller/traffic_monitor.py 2>&1 | tee logs/controller.log
```

*Note: Leave this terminal running. You should see it periodically outputting stats once switches connect.*

### Terminal 2: Start the Mininet Topology
With the controller running, open a second terminal to start your custom Mininet topology.

```bash
cd ~/Projects/sdn-traffic-monitor
sudo python3 topology/topo.py
```

*Wait for Mininet to start up and drop you into the `mininet>` prompt.*

---

## Phase 5: Testing Scenarios & Evidence Capture

You must capture specific logs and outputs to the `screenshots/` directory as proof of functional correctness.

### Scenario 1: Normal Traffic (Allowed Flow)
**Purpose:** Demonstrate learning-switch forwarding and statistic generation.

1. **Ping All Hosts:**
   Inside the Mininet CLI:
   ```bash
   mininet> pingall
   ```
   *Expected: All succeed except h2 -> h3.*

2. **Generate Throughput (h1 to h3):**
   In Mininet CLI:
   ```bash
   mininet> h1 iperf3 -s &
   mininet> h3 iperf3 -c 10.0.0.1 -t 15 > iperf_temp.txt
   ```

3. **Capture Evidence (Terminal 3):**
   Open a third terminal and run:
   ```bash
   ./tests/test_scenario_1.sh
   ```
   *Expected: Flow tables and iperf results (if saved to iperf_temp.txt) are moved to screenshots/ folder.*

### Scenario 2: Blocked Traffic (Firewall Rule)
**Purpose:** Demonstrate that the h2 -> h3 drop rule is active and specifically targeting that pair.

1. **Allowed Ping (h1 -> h3):**
   ```bash
   mininet> h1 ping -c 4 h3
   ```
   *Expected: 0% packet loss.*

2. **Blocked Ping (h2 -> h3):**
   ```bash
   mininet> h2 ping -c 4 h3
   ```
   *Expected: 100% packet loss.*

3. **Capture Evidence (Terminal 3):**
   ```bash
   ./tests/test_scenario_2.sh
   ```
   *Expected: The DROP rule (priority 10) is extracted from s1 and saved.*

---

### Automated Test Scripts
The scripts in `tests/` automate the capture of OpenFlow tables. For traffic logs (iperf/ping), please follow the redirection instructions within the Mininet CLI or the script output.


### Wrap Up
When finished testing, return to Terminal 2 (Mininet CLI) and type `exit`. To stop the controller in Terminal 1, press `Ctrl+C`.

