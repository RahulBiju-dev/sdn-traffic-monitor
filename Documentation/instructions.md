# Project Demo Guide

This file outlines the sequential commands to run a full demonstration of the SDN Traffic Monitor project. This workflow will launch the controller, build the custom topology, verify switch connectivity, generate traffic, test firewall controls, and inspect OpenFlow flow tables.

### 1. Start the Controller

Open **Terminal 1** and start the Ryu application:

```bash
cd ~/Projects/sdn-traffic-monitor
ryu-manager controller/traffic_monitor.py
```

*Note: Leave this terminal running to observe proactive logging every 10 seconds.*

### 2. Start the Mininet Topology

Open **Terminal 2** and launch the custom Mininet topology script:

```bash
cd ~/Projects/sdn-traffic-monitor
sudo python3 topology/topo.py
```

*Wait for the `mininet>` prompt to appear. The switches are now establishing an OpenFlow 1.3 connection with the Ryu controller.*

---

## 3. Traffic and Firewall Demonstration

Inside the Mininet CLI (`mininet>`), run the following commands sequentially:

**Step A: Verify End-to-End Connectivity and Firewall Rules**
Run a full ping test across all hosts:
```bash
mininet> pingall
```
*Expected Result: All pings should succeed EXCEPT for `h2` communicating with `h3`. The controller dynamically drops their packets (X).*

**Step B: Test Blocked Traffic (h2 to h3)**
Perform an explicit ping test for the prohibited host pair:
```bash
mininet> h2 ping -c 4 h3
```
*Expected Result: 100% packet loss.*

**Step C: Test Allowed Traffic (h1 to h3)**
Perform a ping test for a permitted host pair to prove routing works:
```bash
mininet> h1 ping -c 4 h3
```
*Expected Result: 0% packet loss.*

**Step D: Measure Throughput (h1 to h4)**
Run a 15-second multi-stream TCP bandwidth test from `h1` to `h4`:
```bash
mininet> h4 iperf3 -s &
mininet> h1 iperf3 -c 10.0.0.4 -t 15
```
*Expected Result: A bandwidth capacity close to the topology's 10 Mbps configured link limit.*

---

## 4. Flow Table Verification

Open **Terminal 3** to inspect the OpenFlow tables injected into the OVS switches by our Ryu application. 

**Step A: Inspect Switch 1 (s1)**
Look at the flow priorities and matching rules:
```bash
sudo ovs-ofctl dump-flows s1 -O OpenFlow13
```
*Expected Result: You should see the default table-miss entry (priority 0), successfully cached MAC forwarding flows (priority 5), and the explicit drop rule for `h2` and `h3` (priority 10 with no output actions).*

**Step B: Inspect Switch 2 (s2)**
```bash
sudo ovs-ofctl dump-flows s2 -O OpenFlow13
```
*Expected Result: Similar dynamically learned forwarding flows based on source and destination MACs.*

---

### 5. Wrap Up

Once the demonstration is complete:
1. In **Terminal 2** (Mininet CLI), type `exit` to close Mininet.
2. In **Terminal 1**, press `Ctrl+C` to terminate the Ryu controller.
3. If necessary, clean up lingering Mininet processes:
   ```bash
   sudo mn -c
   ```
