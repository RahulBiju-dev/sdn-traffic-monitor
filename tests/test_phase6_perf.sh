#!/bin/bash
# test_phase6_perf.sh — Captures before/after flow tables for Phase 6 analysis.
# Usage:
#   BEFORE traffic:  ./tests/test_phase6_perf.sh before
#   AFTER  traffic:  ./tests/test_phase6_perf.sh after
#   DIFF   compare:  ./tests/test_phase6_perf.sh diff

set -e
mkdir -p screenshots

case "$1" in
    before)
        echo "[Phase 6] Capturing BEFORE-traffic flow tables..."
        sudo ovs-ofctl -O OpenFlow13 dump-flows s1 > screenshots/s1_before_traffic.txt
        sudo ovs-ofctl -O OpenFlow13 dump-flows s2 > screenshots/s2_before_traffic.txt
        echo "Saved: screenshots/s1_before_traffic.txt"
        echo "Saved: screenshots/s2_before_traffic.txt"
        ;;
    after)
        echo "[Phase 6] Capturing AFTER-traffic flow tables..."
        sudo ovs-ofctl -O OpenFlow13 dump-flows s1 > screenshots/s1_after_traffic.txt
        sudo ovs-ofctl -O OpenFlow13 dump-flows s2 > screenshots/s2_after_traffic.txt
        echo "Saved: screenshots/s1_after_traffic.txt"
        echo "Saved: screenshots/s2_after_traffic.txt"
        ;;
    diff)
        echo "[Phase 6] Diff: s1 before vs after"
        echo "========================================"
        diff screenshots/s1_before_traffic.txt screenshots/s1_after_traffic.txt || true
        echo ""
        echo "[Phase 6] Diff: s2 before vs after"
        echo "========================================"
        diff screenshots/s2_before_traffic.txt screenshots/s2_after_traffic.txt || true
        ;;
    *)
        echo "Usage: $0 {before|after|diff}"
        exit 1
        ;;
esac
