# Viva Notes: SDN Traffic Monitoring and Statistics

## 1. Problem Statement Detailed Analysis
**The Core Problem:** "Controller–switch interaction, flow rule design, and network behaviour observation using Mininet + Ryu controller."

**What does this actually mean?**
The objective is to practically demonstrate the fundamental principles of a Software-Defined Network (SDN). In legacy networks, physical hardware like switches and routers contain both the "brain" (Control Plane - routing logic, firewall policies) and the "brawn" (Data Plane - literal packet forwarding). This project asks us to decouple them. 

**Deconstructing the Requirements:**
1. **Controller-Switch Interaction:** We must establish a secure OpenFlow 1.3 channel between a dumb hardware abstraction (the Mininet Open vSwitch) and an intelligent central brain (the Ryu Python script), proving they can pass messages back and forth.
2. **Flow Rule Design (Match-Action Rules):** The core of OpenFlow. We must program logic into Ryu that looks at packet headers (Match, e.g., "Source MAC is X, Destination MAC is Y") and assigns an operation (Action, e.g., "Output to Port 2" or "Drop").
3. **Network Behavior Observation:** A system is only as good as its observability. We must verify our rules work by explicitly testing throughput (using `iperf3`) and generating quantitative evidence (extracting live byte/packet counts via OpenFlow polling) to prove the controller has total visibility over the network data plane.

## 2. Core Technologies Deep Dive

* **SDN (Software-Defined Networking):** A paradigm shift in telecommunications that introduces programmability to the network. By moving all routing and security logic to a centralized tier, network administrators can deploy changes via software APIS globally across thousands of switches instantly, rather than logging into each device via SSH.
* **OpenFlow 1.3:** The communication protocol standard that controls the interface between the control and forwarding layers of an SDN architecture. It gives access to the forwarding plane of a network switch or router over the network.
* **Ryu Controller:** A Python-based, component-oriented SDN framework. It handles the low-level OpenFlow socket connections and gives us an API (`ryu.app.manager`) so we can write Python logic triggered by network events (Event-Driven Architecture).
* **Mininet:** A network emulator that utilizes Linux network namespaces to realistically simulate switches, routers, and hosts on a single CPU. It is crucial because testing SDN controller code on a physical $10,000 Cisco switch is risky and difficult; Mininet provides an identical software testbed.
* **iperf (iperf3):** An active measurement tool for characterizing maximum achievable bandwidth on IP networks. We use `iperf` rather than `ping` because `ping` uses tiny ICMP packets that only test latency and connectivity, whereas `iperf` saturates the link with TCP streams to prove our 10 Mbps topology constraint.

## 3. Implementation Blueprint

Our solution marries a custom Mininet script with a customized Ryu application.

1. **Topology Orchestration:** We spin up a custom Python Mininet script explicitly defining two Open vSwitches (`s1`, `s2`), four hosts, and a backbone. We use `TCLink` (Traffic Control Link) to simulate real-world constraints: a hard 10 Mbps limit.
2. **The "Learning Switch" Algorithm:** Switches boot up knowing nothing about the network. When `h1` pings `h3`:
   - The switch (`s1`) receives the packet. It has an empty table.
   - It hits the "Table-Miss" rule and forwards the packet directly to the Ryu Controller via `packet_in`.
   - Ryu inspects the Ethernet header. It records: "MAC address for `h1` is on port 1 of `s1`".
3. **Proactive OpenFlow Rule Installation:** Once the controller identifies the destination MAC, it doesn't just forward the packet; it sends an `OFPFlowMod` message back to the switch. This tells the switch datapath: "For the next 30 seconds, if you see traffic bound for this MAC, forward it out this specific port automatically." This priority 5 rule bypasses the controller for future packets, ensuring high throughput.
4. **Hardcoded Security Constraints (Firewalling):** The problem implies restricting interactions. We hardcoded a Layer 2 Firewall constraint blocking host 2 (`h2`) from communicating with host 3 (`h3`). During the `packet_in` event, if Ryu spots these two specific MAC addresses interacting, it injects a priority 10 `DROP` rule (an OpenFlow rule with an empty instruction set).
5. **Continuous Async Statistics Polling:** To observe network behavior mathematically, a background Greenlet thread is spawned in Ryu (`hub.spawn`). It wakes up every 10 seconds and blasts an `OFPFlowStatsRequest` to every switch it controls. Switches respond with `OFPFlowStatsReply`. Ryu parses the byte count and packet count fields for every active rule, writing them to a log.

## 4. Code Locations and Logic Breakdown

* **Topology (`topology/topo.py`)**
    * *Core Class:* `MyTopo(Topo)`
    * *Logic:* Instantiates nodes via `self.addSwitch('s1', protocols='OpenFlow13')`. We linked nodes using `self.addLink(..., bw=10)` to apply bandwidth limitations.
    * *Execution:* Handled by Mininet's `net.start()`.

* **Controller Applicaton (`controller/traffic_monitor.py`)**
    * *Core Class:* `TrafficMonitorApp(app_manager.RyuApp)`
    * *Key Event Handlers:*
        * `@set_ev_cls(ofp_event.EventOFPSwitchFeatures...)`: Triggers on initial switch handshake. Installs the critical Priority 0 Table-Miss entry.
        * `@set_ev_cls(ofp_event.EventOFPPacketIn...)`: The brain of the app. It's invoked whenever a switch encounters an unknown frame. Handles the MAC-to-Port dictionary mapping, the Firewall Drop injections, and the Forwarding Rule injections.
        * `@set_ev_cls(ofp_event.EventOFPFlowStatsReply...)`: The telemetry engine. Receives the raw byte buffer from the switch, unpacks the matching fields, extracts `stat.packet_count` and `stat.byte_count`, and writes to `logs/`.

## 5. Potential Examiner Questions & Solutions (Comprehensive)

**Q1. What is the fundamental difference between the Control Plane and the Data Plane?**
* **Solution:** The Control Plane is the "brain"—it runs the routing algorithms, makes the decisions about where traffic should go, and handles security policies. The Data Plane (or Forwarding Plane) is the "brawn"—it executes the rule, actually moving bits from an ingress port to an egress port purely in hardware. In SDN, they are physically separated.

**Q2. Why does the first ping take significantly longer than the subsequent pings?**
* **Solution:** The first ping causes a "cache miss" on the switch’s OpenFlow table. This triggers a slow process: the switch encapsulates the packet inside an OpenFlow `packet_in` message, sends it over the network to the Ryu controller, Ryu calculates the path, and Ryu sends an `OFPFlowMod` (plus `packet_out`) back. Subsequent pings hit the newly cached hardware rule directly on the switch, drastically lowering latency.

**Q3. How did you specifically enforce the firewall rule blocking h2 and h3?**
* **Solution:** In the Ryu `_packet_in_handler` function, we extract the `eth_src` and `eth_dst` from the Ethernet header of incoming packets. We added a conditional `if` statement checking for the exact MAC addresses of `h2` and `h3` (bidirectionally). If matched, we instruct the switch to install a flow rule with a higher priority (10) and an *empty output action list*. In OpenFlow, empty actions mean drop the packet.

**Q4. What is a "Table-Miss Entry" and why must it be at Priority 0?**
* **Solution:** It is the fallback/catch-all rule installed when the switch boots. If an incoming packet fails to match any specific, high-priority rules (like priority 5 forwarding or priority 10 drops), it falls down to Priority 0. The action for the Table-Miss entry is to output the packet to the `CONTROLLER` port. Without it, the switch would simply drop unknown packets, and the network would fail to learn.

**Q5. Explain the difference between `packet_in` and `packet_out` in the OpenFlow specification.**
* **Solution:** `packet_in` goes from Switch $\rightarrow$ Controller; it is the switch saying "I don't know what to do with this packet, please tell me." `packet_out` goes from Controller $\rightarrow$ Switch; it is the controller saying "Take this specific unstructured packet data and push it out of this specific Physical Port on the switch right now."

**Q6. What is `OFPFlowMod` and how does it differ from a `packet_out`?**
* **Solution:** `OFPFlowMod` (Flow Modification) alters the long-term state of the switch by adding, modifying, or deleting rules in the switch's hardware flow tables. It affects *future* packets. `packet_out` is a one-time instruction to eject a single, specific packet.

**Q7. What does "Priority" mean in an OpenFlow rule? Give examples from your topology.**
* **Solution:** Priority dictates the order of operations when a switch evaluates a packet against overlapping rules. Higher numbers denote higher precedence. In our code: Priority 0 is the table-miss (fallback), Priority 5 is for dynamic MAC routing (normal operations), and Priority 10 is for our Firewall Drop rules (overrides normal routing). 

**Q8. Explain what we mean by "Match-Action" logic.**
* **Solution:** Every OpenFlow rule has two halves. The "Match" defines the conditions that must be met in the packet header (like "Source IP is 10.0.0.1", "Destination MAC is X", "Inbound Port is 2"). The "Action" defines what the switch should do if the conditions are met (like "Output to Port 5", "Drop", "Change the IP TTL").

**Q9. How exactly are statistics pulled from the switch? Does the switch tell you, or do you ask it?**
* **Solution:** It is a polling mechanism. The Ryu controller actively requests the data. We utilize a Python Greenlet background thread (`hub.spawn`) that loops indefinitely. Every 10 seconds, it sends an `OFPFlowStatsRequest` to every switch datapath. The switch halts, tallies the internal hardware counters, and replies with an `OFPFlowStatsReply`.

**Q10. Why is periodic statistics monitoring useful in a real production SDN environment?**
* **Solution:** Real-time metrics allow SDN controllers to autonomously detect link congestion. If a flow's byte count spikes aggressively, an application could deduce it's a volumetric DDoS attack and instantly map a new Priority 20 Drop rule to mitigate the attack. It's also utilized for usage-based cloud billing and dynamic load-balancing (rerouting traffic off heavily loaded links).

**Q11. What is MAC Learning? Explain the dictionary variable `self.mac_to_port` in your Ryu app.**
* **Solution:** MAC learning is how Layer 2 switches figure out which physical port a device is plugged into. The controller maintains a dictionary where the keys are the Switch ID (dpid) and the values are sub-dictionaries mapping a `MAC Address` to a `Physical Port`. When a packet arrives, Ryu logs its source MAC and the port it arrived on. When Ryu needs to send a packet to that MAC later, it references this dictionary.

**Q12. What would happen if a broadcast packet (like ARP) entered your topology?**
* **Solution:** The switch doesn't know the destination MAC for a broadcast (it's `ff:ff:ff:ff:ff:ff`), so it goes straight to the controller. The controller's MAC dictionary lookup for the broadcast MAC will fail, defaulting to `OFPP_FLOOD`. The controller tells the switch to flood (broadcast) the packet out of all active ports except the one it arrived on, ensuring ARP resolution succeeds.

**Q13. What happens if the Ryu Controller process crashes while the network is under load?**
* **Solution:** The network will fail-open temporarily but eventually collapse into a "brain dead" state. Existing OpenFlow rules (like priority 5 forwards) will remain cached in the Mininet switches, and traffic hitting those rules will continue line-rate forwarding. However, once those rules expire (via idle timeouts or hard timeouts) or a new unknown flow is generated, the switch will look for the controller. Finding exactly none, those packets will be dropped, halting network access.

**Q14. In Phase 6, we utilized `iperf` instead of `ping`. Why? What is the difference?**
* **Solution:** `ping` uses ICMP, which sends individual 64-byte chunks of data purely to measure the round-trip latency and binary reachability of a host. `iperf` uses continuous multi-threaded TCP/UDP streams to intentionally try and overwhelm the link in order to measure its maximum bandwidth capacity. This was necessary to prove that our Mininet `TCLink(bw=10)` constraints were correctly applied.

**Q15. Suppose you connect `s1` and `s2` with TWO links instead of one, creating a loop. What goes wrong in a basic OpenFlow learning switch?**
* **Solution:** It causes a massive broadcast storm that will crash the topology instantly. Because this basic learning switch does not implement Spanning Tree Protocol (STP), an ARP broadcast packet will flood back and forth infinitely across the two links between `s1` and `s2`. To fix this, we would need to integrate Ryu's `simple_switch_stp_13.py` module to block redundant topology paths.
