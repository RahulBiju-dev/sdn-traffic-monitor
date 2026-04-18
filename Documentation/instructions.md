# Testing Instructions (Phase 3 & 4)

This file contains the step-by-step commands you need to run to verify that the controller and the topology are working as expected. You will need at least three separate terminal windows open on your VM.

### Terminal 1: Start the Controller
First, start the Ryu controller so it acts as the "brain" and listens on port 6633.

```bash
cd ~/Projects/sdn-traffic-monitor
ryu-manager controller/traffic_monitor.py
```

*Note: Leave this terminal running. You should see it periodically outputting stats once switches connect.*

### Terminal 2: Start the Mininet Topology
With the controller running, open a second terminal to start your custom Mininet topology.

```bash
cd ~/Projects/sdn-traffic-monitor
sudo python3 topology/topo.py
```

*Wait for Mininet to start up and drop you into the `mininet>` prompt.*

### Scenario 1: Normal Traffic & Learning Switch
Inside the **Mininet** CLI (Terminal 2), run the following:

1. **Ping All Hosts:**
   ```bash
   pingall
   ```
   *Expected: Everyone should be able to ping each other, EXCEPT h2 to h3 (which we blocked in Phase 3!). If `pingall` shows some dropped packets, it's correct!*

2. **Test Bandwidth (h1 to h3):**
   ```bash
   h1 iperf3 -s &
   h3 iperf3 -c 10.0.0.1 -t 15
   ```
   *Expected: Throughput should be around 10 Mbps (due to `TCLink` limits).*

### Scenario 2: Firewall / Blocked Traffic Test
Inside the **Mininet** CLI (Terminal 2), run:

1. **Allowed Ping (h1 -> h3):**
   ```bash
   h1 ping -c 4 h3
   ```
   *Expected: 4 packets transmitted, 4 received, 0% packet loss.*

2. **Blocked Ping (h2 -> h3):**
   ```bash
   h2 ping -c 4 h3
   ```
   *Expected: 4 packets transmitted, 0 received, 100% packet loss.*

### Terminal 3: Verify Flow Tables & Stats
Open a third terminal alongside your running Mininet and Controller.

1. **Dump Flow Tables for Switch 1 (s1):**
   ```bash
   sudo ovs-ofctl -O OpenFlow13 dump-flows s1
   ```
   *Expected: Look for a flow entry with `priority=10` containing the DROP rule for the h2 MAC -> h3 MAC.*

2. **Verify Background Polling Logs:**
   ```bash
   cat logs/stats_1.log
   cat logs/stats_2.log
   ```
   *Expected: Lines of comma-separated data tracking packets over time.*

### Wrap Up
When finished testing, return to Terminal 2 (Mininet CLI) and type `exit`. To stop the controller in Terminal 1, press `Ctrl+C`.
