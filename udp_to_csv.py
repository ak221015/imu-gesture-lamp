# Records one gesture from the M5StickC Plus2 into a single CSV file.
# Listens on UDP port 5005 and writes 2 seconds of samples after you press Enter.
# Set the output file name below, then run this once per recording.

import time
import socket

# Press Enter to start recording
input()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 5005))

# "x" fails if the file exists, so recordings are never overwritten
with open("nothing1.csv", "x") as f:
    start = time.time()
    print("Recording started")
    # Same column order as the packet format
    f.write("t,ax,ay,az,gx,gy,gz\n")
    # Record for 2 seconds, one gesture per file
    while time.time() - start < 2:
        data, addr = sock.recvfrom(1024)
        line = data.decode().strip()
        f.write(line + "\n")
print("Recording finished")
sock.close()
