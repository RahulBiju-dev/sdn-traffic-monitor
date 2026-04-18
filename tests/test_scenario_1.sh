#!/bin/bash
# test_scenario_1.sh - Automates evidence capture for Scenario 1 (Normal Traffic)

echo "SDN Traffic Monitor - Scenario 1 Evidence Capture"
echo "------------------------------------------------"

# Check if screenshots directory exists
mkdir -p screenshots

echo "[1/2] Dumping flow tables for s1 and s2..."
sudo ovs-ofctl -O OpenFlow13 dump-flows s1 > screenshots/scenario1_flow_table.txt
sudo ovs-ofctl -O OpenFlow13 dump-flows s2 >> screenshots/scenario1_flow_table.txt

echo "[2/2] Checking if iperf data exists (you should run iperf in Mininet first)..."
if [ -f "iperf_temp.txt" ]; then
    mv iperf_temp.txt screenshots/scenario1_iperf.txt
    echo "Summary: iperf results saved."
else
    echo "Warning: iperf_temp.txt not found. Please run iperf in Mininet and save output to iperf_temp.txt if you want automated capture."
fi

echo "------------------------------------------------"
echo "Scenario 1 capture complete. Check screenshots/ folder."
