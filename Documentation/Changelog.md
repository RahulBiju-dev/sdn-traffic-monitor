# Agent-Oriented Project Changelog

Project Status: **Phase 2 Complete**
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

## Implementation Context for Phase 3 (Next)
- **Target:** `controller/traffic_monitor.py`
- **Required Logic:** 
    - MAC learning switch.
    - Match-action flows (Forwarding + Drop).
    - Hard-coded blocking of `h2` to `h3` traffic.
- **Agent Action:** `@sdn_dev` to implement `traffic_monitor.py`.
