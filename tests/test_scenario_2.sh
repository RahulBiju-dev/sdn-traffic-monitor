#!/bin/bash
# test_scenario_2.sh - Automates evidence capture for Scenario 2 (Blocked Traffic)

echo "SDN Traffic Monitor - Scenario 2 Evidence Capture"
echo "------------------------------------------------"

# Check if screenshots directory exists
mkdir -p screenshots

echo "[1/2] Capturing DROP flow entry from s1..."
# Filtering for priority 10 which is our DROP rule
sudo ovs-ofctl -O OpenFlow13 dump-flows s1 | grep "priority=10" > screenshots/scenario2_flow_table.txt

if [ -s screenshots/scenario2_flow_table.txt ]; then
    echo "Success: DROP rule captured in screenshots/scenario2_flow_table.txt"
else
    echo "Warning: No DROP rule (priority 10) found. Did you trigger a block (h2 ping h3)?"
fi

echo "[2/2] Note: Please save your ping outputs manually to screenshots/scenario2_ping.txt"
echo "Example: h2 ping -c 4 h3 > screenshots/scenario2_ping.txt (run this inside Mininet node or Terminal 3)"

echo "------------------------------------------------"
echo "Scenario 2 capture complete."
