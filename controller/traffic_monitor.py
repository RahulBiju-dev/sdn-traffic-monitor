import logging
import time
import datetime
import os

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import hub

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

class TrafficMonitorApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TrafficMonitorApp, self).__init__(*args, **kwargs)
        
        # Phase 3: Mac to port mapping (learning switch)
        self.mac_to_port = {}
        
        # Phase 3 & 4: Track connected datapaths
        self.datapaths = {}
        
        # Phase 3: Blocked MAC address pairs (src_mac, dst_mac)
        # Block h2 -> h3 traffic
        self.blocked_pairs = {("00:00:00:00:00:02", "00:00:00:00:00:03")}
        
        # Phase 4: Start background monitoring thread
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info(f'Switch connected: {datapath.id}')
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info(f'Switch disconnected: {datapath.id}')
                del self.datapaths[datapath.id]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        self.datapaths[datapath.id] = datapath

        # Phase 3: Install table-miss flow entry (Priority 0)
        # Action: Send to controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, idle_timeout=0, hard_timeout=0):
        # Phase 3: Helper function to install a flow rule
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst,
                                idle_timeout=idle_timeout,
                                hard_timeout=hard_timeout)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # Ignore LLDP packets
            return
            
        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})

        # Phase 3: Learn the MAC address to avoid FLOOD next time
        self.mac_to_port[dpid][src] = in_port

        # Phase 3: Block specific pairs (h2 -> h3)
        if (src, dst) in self.blocked_pairs:
            self.logger.info(f"Blocking traffic from {src} to {dst}")
            match = parser.OFPMatch(eth_src=src, eth_dst=dst)
            actions = [] # Empty actions list causes DROP
            self.add_flow(datapath, 10, match, actions) # Priority 10 for DROP
            return # Don't forward this packet

        # Phase 3: Forwarding Decision
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Phase 3: Install a flow to avoid packet_in next time (only if we know destination)
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # Verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 5, match, actions) # Priority 5 for Forwarding
                return
            else:
                self.add_flow(datapath, 5, match, actions) # Priority 5 for Forwarding

        # Transmit the initial packet outwards since switch couldn't earlier
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    # Phase 4: Monitoring System
    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

    def _request_stats(self, datapath):
        self.logger.debug(f'Send stats request: {datapath.id}')
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        log_file_path = os.path.join(LOG_DIR, f'stats_{dpid}.log')
        
        self.logger.info(f'--- Stats Report --- {current_time} | Switch: s{dpid} ---')
        
        with open(log_file_path, 'a') as f:
            for stat in sorted([flow for flow in body if flow.priority > 0],
                               key=lambda flow: (flow.match.get('in_port', 0), flow.match.get('eth_dst', ''))):
                
                # Format to print to controller output
                match_str = str(dict(stat.match.items()))
                report_line = (f"Match: {match_str} | Priority: {stat.priority} | "
                               f"Packets: {stat.packet_count} | Bytes: {stat.byte_count}")
                self.logger.info(report_line)
                
                # Append to file strictly separated by commas
                file_record = (f"{current_time},s{dpid},{match_str},{stat.priority},"
                               f"{stat.packet_count},{stat.byte_count},{stat.duration_sec}\n")
                f.write(file_record)
        self.logger.info('-' * 50)
