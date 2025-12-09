#!/bin/bash
# delivery_start.sh - Start ArduPilot SITL for delivery drone

# Configuration
VPS_IP="YOUR_VPS_IP"
VPS_PORT="5762"
VEHICLE_TYPE="ArduCopter"
FRAME="quad"
INSTANCE=1

echo "Starting Delivery Drone SITL..."
echo "VPS: ${VPS_IP}:${VPS_PORT}"

# Start SITL with TCP output to VPS
cd ~/ardupilot/ArduCopter

# Option 1: Using sim_vehicle.py (recommended for SITL)
~/ardupilot/Tools/autotest/sim_vehicle.py \
    -v ${VEHICLE_TYPE} \
    -f ${FRAME} \
    -I ${INSTANCE} \
    --out tcp:${VPS_IP}:${VPS_PORT} \
    --console \
    --map

# Option 2: Using MAVProxy (if connecting to real hardware)
# mavproxy.py --master=/dev/ttyACM0 --out tcp:${VPS_IP}:${VPS_PORT} --baudrate 57600
