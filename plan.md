# SDN Traffic Monitoring and Statistics Project – Implementation Plan

**Problem Statement**  
Build a controller module that collects and displays traffic statistics. The solution must retrieve flow statistics, display packet and byte counts, perform periodic monitoring, and generate simple reports using an SDN-based approach with Mininet and an OpenFlow controller.

This document outlines a structured, phased implementation plan. The project remains deliberately straightforward to ensure clarity, modularity, and full compliance with the assignment deliverables and evaluation criteria. All work will be version-controlled and submitted via a public GitHub repository.

## Project Phases

### Phase 1: Environment Setup  
1. Provision a Linux virtual machine (Ubuntu 20.04 or 22.04 recommended).  
2. Install Mininet and the chosen OpenFlow controller (Ryu).  
3. Verify successful installation of both tools.  
4. Create a dedicated project directory and initialise a Git repository.

### Phase 2: Topology Design  
1. Define a simple linear topology consisting of two switches and four hosts.  
2. Ensure appropriate bandwidth settings on links for observable traffic behaviour.  
3. Configure the topology script to connect to a remote controller.  
4. Validate basic connectivity within the Mininet environment (prior to controller integration).

### Phase 3: Controller Development – Core Logic  
1. Create the main controller application using the selected OpenFlow framework.  
2. Implement handling of switch feature negotiation and default flow rules.  
3. Develop packet-in event processing to enable basic forwarding (learning-switch behaviour).  
4. Install explicit match-action flow rules with appropriate priorities.

### Phase 4: Statistics Collection and Monitoring  
1. Add functionality to periodically request flow statistics from active switches.  
2. Process received statistics to extract and display packet and byte counts per flow.  
3. Implement a background monitoring thread that reports data at regular intervals (e.g., every 10 seconds).  
4. Ensure statistics are logged clearly for real-time observation during demonstration.

### Phase 5: Testing and Validation  
1. Execute the controller and Mininet topology in separate terminals.  
2. Demonstrate two distinct test scenarios:  
   - Normal traffic flow with measurable packet/byte increases.  
   - Blocked or filtered traffic showing static or zero statistics for affected flows.  
3. Perform basic validation using ping and iperf to generate traffic.  
4. Capture evidence of flow tables, statistics reports, and performance metrics.

### Phase 6: Performance Observation and Analysis  
1. Measure latency using ping across multiple hosts.  
2. Measure throughput using iperf between selected host pairs.  
3. Record flow-table changes and packet/byte statistics before and after traffic generation.  
4. Document observed behaviour for inclusion in the final report.

### Phase 7: Documentation and Submission  
1. Prepare the source code with modular structure and appropriate comments.  
2. Create a comprehensive README.md file containing:  
   - Problem statement  
   - Setup and execution steps  
   - Expected output examples  
   - Screenshots/logs of flow tables, statistics reports, ping, and iperf results  
   - List of references  
3. Commit all files to the Git repository and push to a public GitHub repository.  
4. Verify that the repository is public and contains all required artefacts for evaluation.

## Final Deliverables Summary  
- Live demonstration in Mininet showing functional correctness.  
- Complete source code on public GitHub repository.  
- Detailed README.md with all specified sections.  
- Proof of execution (screenshots/logs of flow tables, ping/iperf results, and statistics reports).  

This phased approach ensures systematic progress, facilitates clear explanation during viva, and aligns precisely with the evaluation criteria (Problem Understanding & Setup, SDN Logic & Flow Rule Implementation, Functional Correctness, Performance Observation & Analysis, and Explanation & Validation).  

Proceed sequentially through each phase, committing changes to Git after completion of every phase. The resulting implementation will be simple yet fully functional, meeting all project expectations without unnecessary complexity.