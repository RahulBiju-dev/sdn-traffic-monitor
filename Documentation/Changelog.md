# Agent-Oriented Project Changelog

Project Status: **Phase 7 Complete**
Target Environment: **Ubuntu VM (SDN-ready)**
Agent Context: **@sdn_dev, @documenter, @professor**

---

## Phase 1: Environment Provisioning & Git Initialisation
- **Status:** [x] Verified
- **Date:** 2026-04-17
- **Technical State:**
    - Directory structure defined: `topology/`, `controller/`, `tests/`, `logs/`, `screenshots/`.
    - Tools installed: `mininet`, `ryu`, `iperf3`, `tcpdump`.
    - Git Repo: Linked to `RahulBiju-dev/sdn-traffic-monitor`.
- **Global Constraints:** 
    - Use Python 3.
    - OpenFlow version 1.3 only.

---

## Phase 2: Topology Architecture (`topology/topo.py`)
- **Status:** [x] Code Complete | [ ] Manual Verification (User-side)
- **Files Modified:**
    - `[NEW] topology/topo.py`
- **Architecture State:**
    - **Backbone:** 2 Switches (`s1`, `s2`) connected via a 10 Mbps `TCLink`.
    - **Endpoints:**
        - `h1` (10.0.0.1), `h2` (10.0.0.2) -> `s1`
        - `h3` (10.0.0.3), `h4` (10.0.0.4) -> `s2`
    - **Link Parameters:** All links forced to 10 Mbps (`bw=10`, `TCLink`).
    - **Logic:** `autoSetMacs=True` ensures `h1` MAC is `00:00:00:00:00:01`, etc.
    - **Controller:** Configured for `RemoteController` at `127.0.0.1:6633`.
- **Agent Instructions:** 
    - **Testing:** Future agents must prompt the user to run: `sudo mn --custom topology/topo.py --topo TwoSwitchTopo --link tc --controller default --test pingall` to verify the topology before proceeding to Phase 3.
    - **Compatibility:** Ensure any controller logic (Phase 3) matches the 10.0.0.0/24 subnet and deterministic MAC addresses.

---

## Phase 3 & 4: Controller Logic & Monitoring (`controller/traffic_monitor.py`)
- **Status:** [x] Code Complete | [ ] Awaiting Manual Verification
- **Date:** 2026-04-18
- **Files Modified:**
    - `[NEW] controller/traffic_monitor.py`
    - `[NEW] logs/.gitkeep`
    - `[NEW] Documentation/instructions.md`
- **Architecture State:**
    - **Learning Switch:** MAC-to-port mapping logic implemented.
    - **Firewall Rules:** Hardcoded constraint explicitly dropping packets where `src_mac=00:00:00:00:00:02` (h2) and `dst_mac=00:00:00:00:00:03` (h3).
    - **Monitoring Subsystem:** Ryu `hub` green thread spawns dynamically tracking all active datapaths, fetching matching and flow statistics, saving it out to `logs/stats_<dpid>.log` every 10 seconds.
    - **Bug Fix:** Fixed issue where disconnected switches were not removed from `self.datapaths`. Added `DEAD_DISPATCHER` handler.
- **Agent Instructions:** 
    - **Testing:** The `@documenter` profile has emitted a new validation guide located in `Documentation/instructions.md`.
    - **Next Phase:** The user will manually deploy the instances into Mininet. Once they report successful operations from Scenario 1 and 2, phase 5 testing handles saving packet captures and performance data for `@professor` analysis!

---

## Phase 5: Testing and Validation
- **Status:** [x] Code Complete | [ ] Awaiting Final Demo
- **Date:** 2026-04-18
- **Files Modified:**
    - `[NEW] tests/test_scenario_1.sh`
    - `[NEW] tests/test_scenario_2.sh`
- **Technical State:**
    - Automated scripts created to capture snapshots of flow tables for both Scenarios.
    - Instruction manual updated with specific evidence capture workflows.
    - Verified `logs/controller.log` redirection using `tee`.
- **Agent Instructions:** 
    - **Viva Preparation:** Move to `@professor` profile to generate viva questions once the user has confirmed the test results.
    - **Analysis:** Proceed to Phase 6 (Performance Observation) after verification.

---

## Phase 6: Performance Observation & Analysis
- **Status:** [x] Scripts Ready | [ ] Awaiting User Measurements on VM
- **Date:** 2026-04-18
- **Files Modified:**
    - `[NEW] tests/test_phase6_perf.sh`
- **Technical State:**
    - Helper script created to capture before/after flow tables and produce diffs.
    - `Documentation/instructions.md` updated with step-by-step Phase 6 measurement commands.
    - Performance results table added to `README.md` with placeholder values for the user to fill in after running measurements.
- **Agent Instructions:**
    - **User Action Required:** Run the Phase 6 steps in `Documentation/instructions.md` on the VM, capture screenshots, and fill in the performance results table in `README.md`.

---

## Phase 7: Documentation & Submission
- **Status:** [x] README Complete | [ ] Awaiting Final Push
- **Date:** 2026-04-18
- **Files Modified:**
    - `[MODIFIED] README.md` — Full rewrite with all 8 required sections.
    - `[MODIFIED] Documentation/instructions.md` — Phase 6 & 7 instructions added.
    - `[MODIFIED] Documentation/Changelog.md` — Updated to reflect all phases.
- **Technical State:**
    - README contains: Problem Statement, Architecture (ASCII diagram), Setup Steps, Expected Output, Test Scenarios, Performance Results (placeholder), Screenshots/Logs index, References.
    - Final submission checklist included in `Documentation/instructions.md`.
- **Agent Instructions:**
    - **User Action Required:** Fill in the performance results table in `README.md` after completing Phase 6 measurements, then run the final commit and push.
