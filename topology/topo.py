#!/usr/bin/env python3
"""
topology/topo.py – Phase 2: Custom Mininet Topology
=====================================================
Topology layout:

    h1 (10.0.0.1) ─┐            ┌─ h3 (10.0.0.3)
                    s1 ───────── s2
    h2 (10.0.0.2) ─┘            └─ h4 (10.0.0.4)

All links are capped at 10 Mbps via TCLink.
Connects to a Ryu RemoteController at 127.0.0.1:6633.
MAC addresses are auto-assigned deterministically:
    h1 = 00:00:00:00:00:01, h2 = 00:00:00:00:00:02, etc.
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info


# ---------------------------------------------------------------------------
# Topology definition
# ---------------------------------------------------------------------------

class TwoSwitchTopo(Topo):
    """Two OpenFlow switches, four hosts, 10 Mbps bandwidth on every link."""

    def build(self):
        # ── Link options ────────────────────────────────────────────────────
        link_opts = dict(bw=10)   # Mbps; TCLink enforces this via tc queues

        # ── Switches ────────────────────────────────────────────────────────
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        # ── Hosts ───────────────────────────────────────────────────────────
        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        h3 = self.addHost('h3', ip='10.0.0.3/24')
        h4 = self.addHost('h4', ip='10.0.0.4/24')

        # ── Host → Switch links ──────────────────────────────────────────────
        self.addLink(h1, s1, **link_opts)
        self.addLink(h2, s1, **link_opts)
        self.addLink(h3, s2, **link_opts)
        self.addLink(h4, s2, **link_opts)

        # ── Inter-switch backbone link ───────────────────────────────────────
        self.addLink(s1, s2, **link_opts)


# ---------------------------------------------------------------------------
# Run function
# ---------------------------------------------------------------------------

def run():
    """Build the network, start the CLI, then cleanly stop everything."""

    topo = TwoSwitchTopo()

    net = Mininet(
        topo=topo,
        controller=None,       # controller added explicitly below
        link=TCLink,           # enforce bandwidth constraints
        autoSetMacs=True,      # h1 → 00:00:00:00:00:01, h2 → …:02, etc.
    )

    # Add Ryu remote controller
    net.addController(
        'c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6633,
    )

    info('*** Starting network\n')
    net.start()

    info('*** Running CLI (type "exit" or Ctrl-D to quit)\n')
    CLI(net)

    info('*** Stopping network\n')
    net.stop()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    setLogLevel('info')
    run()
