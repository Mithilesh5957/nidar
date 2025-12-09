# mission_utils.py
"""MAVLink mission request/upload helpers using pymavlink handshake protocol"""
import time
from pymavlink import mavutil

DEFAULT_TIMEOUT = 8.0

def request_mission(master: mavutil.mavlink_connection, target_system: int, target_component: int = 0, timeout=DEFAULT_TIMEOUT):
    """Request mission from vehicle using MAVLink protocol"""
    master.mav.mission_request_list_send(target_system, target_component)
    start = time.time()
    mission_count = None
    items = {}
    
    while True:
        if time.time() - start > timeout:
            raise TimeoutError("Timeout waiting for mission_count")
        
        msg = master.recv_match(type=['MISSION_COUNT', 'MISSION_ITEM_INT'], blocking=True, timeout=timeout)
        if msg is None:
            continue
        
        t = msg.get_type()
        if t == 'MISSION_COUNT':
            mission_count = msg.count
            if mission_count == 0:
                return []
            master.mav.mission_request_int_send(target_system, target_component, 0)
        elif t == 'MISSION_ITEM_INT':
            seq = msg.seq
            items[seq] = {
                'seq': seq,
                'frame': msg.frame,
                'command': msg.command,
                'param1': msg.param1,
                'param2': msg.param2,
                'param3': msg.param3,
                'param4': msg.param4,
                'x': msg.x / 1e7,
                'y': msg.y / 1e7,
                'z': msg.z
            }
            if mission_count is not None and len(items) < mission_count:
                master.mav.mission_request_int_send(target_system, target_component, seq+1)
            else:
                return [items[i] for i in sorted(items.keys())]

def upload_mission(master: mavutil.mavlink_connection, target_system: int, mission_items: list, target_component: int = 0, timeout=DEFAULT_TIMEOUT):
    """Upload mission to vehicle using MAVLink protocol"""
    count = len(mission_items)
    master.mav.mission_count_send(target_system, target_component, count)
    start = time.time()
    sent = 0
    
    while True:
        if time.time() - start > timeout:
            raise TimeoutError("Timeout waiting for mission_request_int")
        
        req = master.recv_match(type=['MISSION_REQUEST_INT'], blocking=True, timeout=timeout)
        if req is None:
            continue
        
        seq = req.seq
        if seq < 0 or seq >= count:
            raise RuntimeError(f"Invalid seq {seq}")
        
        item = mission_items[seq]
        master.mav.mission_item_int_send(
            target_system,
            target_component,
            seq,
            int(item.get('frame', 0)),
            int(item['command']),
            int(item.get('current', 0)),
            int(item.get('autocontinue', 1)),
            float(item.get('param1', 0)),
            float(item.get('param2', 0)),
            float(item.get('param3', 0)),
            float(item.get('param4', 0)),
            int(round(item['x'] * 1e7)) if item.get('x') is not None else 0,
            int(round(item['y'] * 1e7)) if item.get('y') is not None else 0,
            float(item.get('z', 0))
        )
        sent += 1
        
        if sent >= count:
            ack = master.recv_match(type=['MISSION_ACK'], blocking=True, timeout=timeout)
            if ack and getattr(ack, 'type', None) == 0:
                return True
            else:
                raise RuntimeError(f"Mission upload ack failed: {ack}")
