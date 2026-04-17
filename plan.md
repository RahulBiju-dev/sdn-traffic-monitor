# SDN Traffic Monitoring and Statistics Project – Implementation Plan

**Problem Statement**
Build a controller module that collects and displays traffic statistics. The solution must retrieve flow statistics, display packet and byte counts, perform periodic monitoring, and generate simple reports using an SDN-based approach with Mininet and an OpenFlow controller.

**Assignment Problem (Orange):** Controller–switch interaction, flow rule design (match–action), and network behavior observation using Mininet + Ryu controller.

**Evaluation Mapping:**

| Phase | Marks Component |
|---|---|
| Phase 1–2 | Problem Understanding & Setup (4 marks) |
| Phase 3 | SDN Logic & Flow Rule Implementation (6 marks) |
| Phase 4–5 | Functional Correctness / Demo (6 marks) |
| Phase 6 | Performance Observation & Analysis (5 marks) |
| Phase 7 | Explanation, Viva & Validation (4 marks) |

All work must be version-controlled and submitted via a **public GitHub repository**. Commit to Git at the end of every phase with a meaningful commit message describing what was completed.

---

## Repository Structure (Target)

The final repository should contain the following layout:

- `topology/topo.py` — Mininet custom topology script
- `controller/traffic_monitor.py` — Ryu controller application (single file containing all controller logic)
- `tests/test_scenario_1.sh` — automated normal traffic test
- `tests/test_scenario_2.sh` — automated blocked traffic test
- `logs/` — created at runtime; holds per-switch statistics log files
- `screenshots/` — evidence folder: flow tables, iperf results, ping output
- `README.md` — full project documentation

---

## Phase 1: Environment Setup

**Goal:** Provision a working Linux environment with Mininet and Ryu installed, verified, and under version control.

1. Provision an Ubuntu 20.04 or 22.04 LTS virtual machine with at least 2 vCPUs and 2 GB RAM.
2. Update all system packages before installing anything else.
3. Install Mininet using the system package manager. After installation, verify by checking its version from the terminal — the command should print a version string without errors.
4. Install the Ryu SDN framework using pip3. If pip3 is not available, install it first via the package manager. After installation, verify by checking Ryu's version from the terminal.
5. Install supporting network tools: iperf3, Wireshark, tcpdump, and net-tools. These will be needed for traffic generation and evidence capture in later phases.
6. Create the project directory, initialise a Git repository inside it, create the subdirectories listed in the repository structure above, and make an initial commit.
7. Create a public repository on GitHub named `sdn-traffic-monitor`, add it as a remote, and push the initial commit. Verify the repository is accessible without login by opening it in a private browser window.

**Phase 1 is complete when:** Both Mininet and Ryu report their version strings cleanly, the directory structure exists, and the initial commit is visible on GitHub.

---

## Phase 2: Topology Design

**Goal:** A Mininet topology with 2 switches and 4 hosts, bandwidth-constrained links, and a remote controller connection.

### Topology Specification (`topology/topo.py`)

- Define a custom Mininet topology class that inherits from `Topo`.
- Add two OpenFlow switches named `s1` and `s2`.
- Add four hosts: `h1` and `h2` connected to `s1`; `h3` and `h4` connected to `s2`. Assign static IPs in the `10.0.0.0/24` range (h1=.1, h2=.2, h3=.3, h4=.4).
- Connect all hosts to their respective switches and connect `s1` to `s2` using bandwidth-limited links at 10 Mbps on every link. Use Mininet's `TCLink` class to enforce this.
- Enable `autoSetMacs=True` so each host gets a deterministic MAC address based on its number (h1 = `00:00:00:00:00:01`, h2 = `00:00:00:00:00:02`, etc.). These MAC addresses will be needed in Phase 3 to define blocking rules.
- Configure the topology to connect to a `RemoteController` at `127.0.0.1` on port `6633`.
- The script should have a `run()` function that builds the network, starts it, opens the Mininet CLI, and cleanly stops the network on exit.
- Include a `if __name__ == '__main__'` guard that sets the log level to `info` and calls `run()`.

### Validation

Before integrating the controller, run a quick connectivity check using Mininet's built-in default controller to confirm the topology is wired correctly and all four hosts can reach each other. This is a pre-controller sanity check only — the default controller is not used in the final project.

**Phase 2 is complete when:** The custom topology launches, all four hosts can ping each other with 0% loss, and the file is committed to Git.

---

## Phase 3: Controller Development – Core Logic

**Goal:** A single Ryu application file that handles switch handshake, installs a table-miss flow entry, and processes `packet_in` events with a learning-switch forwarding behaviour plus explicit match–action flow rule installation.

### File: `controller/traffic_monitor.py`

This file contains the entire controller. Organise it into the following logical sections, each implemented as a method of the main Ryu app class.

#### 3.1 Imports and App Class Declaration

Import the necessary Ryu modules for: app management, OpenFlow event handling, OpenFlow 1.3 protocol constants, packet parsing (ethernet, IPv4, TCP, UDP), the Ryu hub for green threads, and Python's standard `logging`, `time`, and `datetime` modules.

Declare a class that inherits from `RyuApp` and sets `OFP_VERSIONS` to OpenFlow 1.3.

#### 3.2 Initialisation (`__init__`)

In the constructor, initialise the following instance variables:

- `self.mac_to_port` — a dictionary mapping each switch's datapath ID to a nested dictionary of MAC address to port number. This is the learning table.
- `self.datapaths` — a dictionary mapping datapath IDs to datapath objects. Used by the monitoring thread to know which switches to poll.
- `self.blocked_pairs` — a set of (src_mac, dst_mac) tuples that should be dropped. Pre-populate this with one blocking rule for testing: block traffic from h2 to h3 using their deterministic MACs.
- Spawn the background monitoring thread using `hub.spawn`, pointing to the `_monitor` method (defined in Phase 4).

#### 3.3 Switch Features Handler

Register a handler for `EventOFPSwitchFeatures` in the `CONFIG_DISPATCHER` state. This is called when a new switch connects and completes its handshake.

The handler must:
- Store the datapath in `self.datapaths`.
- Install a **table-miss flow entry**: priority = 0, match = any packet, action = send to controller. This ensures all packets without a matching rule are forwarded to the controller for processing.

#### 3.4 `add_flow` Helper Method

Write a generic helper that constructs and sends an `OFPFlowMod` message to a given datapath. It should accept the datapath, priority, match object, action list, and optional `idle_timeout` and `hard_timeout` values. All other controller methods should call this helper instead of constructing `FlowMod` messages directly — this keeps the code clean and modular.

#### 3.5 State Change Handler

Register a handler for `EventOFPStateChange` covering both `MAIN_DISPATCHER` and `CONFIG_DISPATCHER` states. When a switch enters `MAIN_DISPATCHER` (fully connected), add it to `self.datapaths`. When it disconnects, remove it. This keeps the monitoring thread's datapath registry accurate.

#### 3.6 Packet-In Handler

Register a handler for `EventOFPPacketIn` in `MAIN_DISPATCHER`. This is the core forwarding logic and the most important method for marks.

The handler must perform the following steps in order:

1. Parse the incoming packet to extract the source MAC, destination MAC, and ingress port.
2. Ensure the datapath's entry exists in `self.mac_to_port`, then record the source MAC mapped to the ingress port for this switch. This is the learning step.
3. **Blocking check:** If the (src_mac, dst_mac) pair is in `self.blocked_pairs`, install a DROP flow rule with priority 10 and an empty action list (no output action means drop), then return immediately without forwarding the packet.
4. **Forwarding decision:** Look up the destination MAC in the switch's learned MAC table.
   - If found: the output port is the learned port. Install a FORWARD flow rule with priority 5, matching on ingress port and destination MAC, with action OUTPUT to the learned port.
   - If not found: flood the packet out all ports. Do not install a flow rule for flooded traffic.
5. Send the buffered packet out using an `OFPPacketOut` message.

**Priority rationale — important for viva:**
- Table-miss = priority 0 (catch-all, lowest)
- Forwarding rules = priority 5
- DROP rules = priority 10 (must outrank forwarding rules so blocks take effect)

**Phase 3 is complete when:** The controller launches, a switch connects, the table-miss entry is installed, and `pingall` in Mininet succeeds with 0% drop for all non-blocked pairs. Commit to Git.

---

## Phase 4: Statistics Collection and Monitoring

**Goal:** Add a background monitoring thread that periodically polls all connected switches for flow statistics and outputs a formatted report to the terminal and to per-switch log files.

### 4.1 Monitor Thread (`_monitor`)

This is a looping green thread started in `__init__`. Every 10 seconds it iterates over all datapaths in `self.datapaths` and calls the `_request_stats` helper for each one, then sleeps for 10 seconds using `hub.sleep`.

### 4.2 Stats Request Helper (`_request_stats`)

Sends an `OFPFlowStatsRequest` message to the given datapath. This is an asynchronous request — the switch will reply via an event handled by the stats reply handler.

### 4.3 Flow Stats Reply Handler

Register a handler for `EventOFPFlowStatsReply` in `MAIN_DISPATCHER`. This is called when a switch responds to a stats poll.

The handler must:
1. Get the current timestamp and the datapath ID from the event.
2. Iterate over all flow stat entries in the reply body.
3. Skip entries with priority 0 (the table-miss entry has no meaningful traffic data).
4. For each remaining entry, extract: match fields, priority, packet count, byte count, and duration in seconds.
5. Print a formatted stats report to the controller terminal using `self.logger.info`. The report should include a header with the timestamp and switch ID, followed by one row per flow entry showing match, priority, packet count, and byte count.
6. Append the same information to a log file at `logs/stats_<dpid>.log`. Each line should be a single-line record with timestamp, DPID, match, packet count, byte count, and duration, so the file can be reviewed after the demo.

The `logs/` directory must exist before the controller runs. Create it in the repository and add a `.gitkeep` file inside it so Git tracks the empty folder.

**Phase 4 is complete when:** The controller prints a stats report every 10 seconds while switches are connected, and the log file grows with each cycle. Commit to Git.

---

## Phase 5: Testing and Validation

**Goal:** Demonstrate two clearly distinct test scenarios showing functional correctness.

### Running the Stack

The controller and topology are always run in two separate terminals. The controller must be started first so it is ready to accept switch connections when Mininet launches.

- **Terminal 1:** Launch the Ryu controller pointing at `controller/traffic_monitor.py`. Redirect output to both the terminal and `logs/controller.log` simultaneously so there is a persistent log of all controller events.
- **Terminal 2:** Launch the Mininet topology by running `topology/topo.py` with superuser privileges.

---

### Scenario 1: Normal Traffic (Allowed Flow)

**Purpose:** Demonstrate learning-switch forwarding, flow rule installation, and increasing packet/byte statistics.

**Steps:**
1. In the Mininet CLI, run `pingall`. All host pairs except the explicitly blocked pair (h2→h3) should succeed with 0% loss.
2. Start an iperf server on `h1` in the background.
3. Run an iperf client from `h3` targeting `h1` for 15 seconds.
4. Wait for two monitoring cycles (approximately 20 seconds) and observe the controller terminal printing stats reports with non-zero and increasing packet and byte counts.
5. In a third terminal, dump the flow tables of both `s1` and `s2` using `ovs-ofctl dump-flows` with the OpenFlow 1.3 flag. Multiple match–action rules should be visible.

**Evidence to save:**
- The flow table dump output saved as `screenshots/scenario1_flow_table.txt`.
- The iperf output saved as `screenshots/scenario1_iperf.txt`.
- A copy or photograph of the controller terminal showing the stats report.

---

### Scenario 2: Blocked Traffic (DROP Rule / Filtering)

**Purpose:** Demonstrate access control — one specific host pair is blocked while all others remain reachable.

**Steps:**
1. In the Mininet CLI, ping from `h1` to `h3` for 4 packets. This should succeed because h1→h3 is not blocked.
2. Ping from `h2` to `h3` for 4 packets. This should result in 100% packet loss because h2→h3 is in `self.blocked_pairs`.
3. Dump the flow table for `s1`. A DROP rule with priority 10 and an empty action list should be visible for the h2→h3 match.
4. Observe the controller stats report — the DROP rule's packet count should be increasing (packets are arriving and being dropped) while h3 receives nothing.

**Evidence to save:**
- Ping output for both h1→h3 (success) and h2→h3 (failure) saved as `screenshots/scenario2_ping.txt`.
- The flow table dump showing the DROP entry saved as `screenshots/scenario2_flow_table.txt`.

---

### Test Scripts

Create two shell scripts in the `tests/` folder. Each script should automate the evidence-capture steps of its scenario: dump flow tables, save the output to the screenshots folder, and print a summary to the terminal. These scripts serve as lightweight regression tests — if the project is re-run later, they should produce the same observable outcomes.

**Phase 5 is complete when:** Both scenarios produce the expected outcomes and all evidence files exist in the `screenshots/` folder. Commit to Git.

---

## Phase 6: Performance Observation and Analysis

**Goal:** Record concrete numbers for latency and throughput, capture before/after flow table states, and document observed behaviour for the README and viva.

### 6.1 Latency Measurement

Run `ping` between `h1` and `h4` for 20 packets. Record the minimum, average, maximum RTT, and packet loss percentage.

Run the same ping a second time immediately after. The second run should show lower average RTT than the first because flow rules are now installed in the switch and packets no longer need to be sent to the controller. This difference illustrates the performance benefit of proactive flow caching and is an important observation to explain during the viva.

Record both sets of numbers.

### 6.2 Throughput Measurement

Run iperf between `h1` and `h4` for 30 seconds with 5-second reporting intervals. Record bandwidth at each interval. The throughput should stabilise around 8–10 Mbps given the 10 Mbps link cap.

Then run iperf between `h1` and `h3` (which crosses the s1→s2 backbone link). Record and compare — traffic crossing switches may show marginally different throughput due to the additional hop.

### 6.3 Flow Table Before and After Traffic

Before generating any traffic, dump the flow tables of `s1` and `s2` and save as `screenshots/s1_before_traffic.txt` and `screenshots/s2_before_traffic.txt`. At this point only the table-miss entry should exist.

Run `pingall` and iperf to generate traffic, then dump the flow tables again and save as `screenshots/s1_after_traffic.txt` and `screenshots/s2_after_traffic.txt`. Multiple match–action rules with non-zero `n_packets` and `n_bytes` fields should now be visible.

Run a diff between the before and after files to clearly show what was added.

### 6.4 Packet Count Statistics from Controller Log

After two or three monitoring cycles have elapsed, inspect the per-switch log file at `logs/stats_<dpid>.log`. The same flow entries should appear multiple times with increasing packet and byte counts across cycles — this directly demonstrates the periodic monitoring functionality.

Prepare a small summary table for the README listing which flow entry was observed, its packet count at cycle 1, its packet count at cycle 2, and the byte count delta. This is the "simple report" the problem statement requires.

**Phase 6 is complete when:** RTT numbers, iperf bandwidth numbers, before/after flow table files, and the log summary table all exist and are saved. Commit to Git.

---

## Phase 7: Documentation and Submission

**Goal:** Complete `README.md` with all required sections and push the final project to the public GitHub repository.

### README.md Required Sections

The README must contain each of the following sections clearly labelled:

1. **Problem Statement** — Describe the Orange problem in your own words: what the system does, what it demonstrates (controller–switch interaction, match–action rules, traffic monitoring), and why the chosen topology and controller design satisfy the requirements.

2. **Architecture** — Include an ASCII diagram of the topology (h1, h2 → s1 ↔ s2 ← h3, h4), and briefly describe how the controller interacts with switches via OpenFlow 1.3.

3. **Setup and Execution Steps** — Step-by-step instructions for a fresh Ubuntu machine: install dependencies, clone the repo, start the controller in Terminal 1, start the topology in Terminal 2. Must be reproducible by someone who has never seen the project before.

4. **Expected Output** — Show a sample of what the controller terminal should print during a stats cycle, and a sample of what `ovs-ofctl dump-flows` should return after traffic is generated.

5. **Test Scenarios** — Describe Scenario 1 (normal traffic) and Scenario 2 (blocked traffic) with expected outcomes for each.

6. **Performance Results** — A table with the following rows: h1→h4 average RTT (first run), h1→h4 average RTT (second run), h1→h4 throughput, h1→h3 throughput, packet count for a selected flow at cycle 1 and cycle 2.

7. **Screenshots and Logs** — List each file in the `screenshots/` folder with a one-line description of what it shows.

8. **References** — Cite all references used: Ryu documentation, Mininet documentation, OpenFlow 1.3 specification, and any other sources consulted.

### Final Submission Checklist

Before submitting, verify every item below is true:

- Ryu and Mininet both launch without errors.
- `pingall` in Mininet shows 0% loss for all non-blocked pairs.
- h2 ping to h3 shows 100% packet loss.
- The controller terminal prints a formatted stats report every ~10 seconds.
- `logs/stats_<dpid>.log` is populated and shows increasing counts across cycles.
- The `screenshots/` folder contains evidence files for both scenarios and before/after flow tables.
- `README.md` contains all 8 sections listed above.
- The GitHub repository is set to **Public**.
- `git log` shows a clean, phase-by-phase commit history with at least one commit per completed phase.
- The repository is accessible without login from a private browser window.

---

## Notes for Viva

Be prepared to clearly explain the following:

1. **Why OpenFlow 1.3?** — It is the most widely supported version with Ryu and Open vSwitch, supports multiple action types, and is stable enough for academic demonstration.

2. **How does the learning switch work?** — On each `packet_in`, the controller reads the source MAC and records which port it arrived on. Future packets destined for that MAC are forwarded directly to the learned port rather than flooded.

3. **Why are priorities 0, 5, and 10 used?** — Priority 0 is the table-miss catch-all. Priority 5 is for forwarding rules. Priority 10 is for DROP rules so that blocking takes precedence over forwarding when both could match the same packet.

4. **What is the table-miss entry and why is it needed?** — Without it, packets with no matching flow rule are simply discarded by the switch. The table-miss entry ensures they are sent to the controller instead, enabling the learning switch to function before any forwarding rules are installed.

5. **How does the monitoring thread work?** — `hub.spawn` starts a Ryu green thread that loops indefinitely. Every 10 seconds it sends a stats request to each connected switch. The switch replies asynchronously and the reply triggers the `EventOFPFlowStatsReply` handler, which formats and logs the data.

6. **What is the difference between the first and second ping RTT?** — The first ping triggers `packet_in` events and involves round-trips to the controller. Once flow rules are installed in the switch, subsequent packets are handled locally, reducing RTT noticeably.