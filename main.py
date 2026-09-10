# Recognizes hand gestures from a M5StickC Plus2 and controls a WiZ bulb.
# Listens for IMU packets on UDP port 5005, classifies 0.5 s windows with
# the forest trained by model_train.py, and sends the matching lamp command.
# Needs model.joblib next to this file and the stick powered on the same network.

import pandas as pd
import asyncio
from pywizlight import wizlight, PilotBuilder
import time
import socket
import joblib

# Address of the WiZ bulb on the local network - change to your own
LAMP_IP = "192.168.100.24"

# Feature order must match model_train.py exactly
# fmt: off
names = ["mean_ax", "mean_ay", "mean_az", "mean_gx", "mean_gy", "mean_gz",
         "std_ax", "std_ay", "std_az", "std_gx", "std_gy", "std_gz",
         "dif_ax", "dif_ay", "dif_az", "dif_gx", "dif_gy", "dif_gz",
         "label", "record"]
# fmt: on
model = joblib.load("model.joblib")


# Modes 0-2 are custom white settings, the rest map to built-in WiZ scenes (1-32)
async def mode_to_lamp(scene, mode, bright, lamp):
    if mode == "swipe_ud":
        scene = scene + 1
    elif mode == "swipe_lr":
        scene = scene - 1
    else:
        await lamp.turn_on(PilotBuilder(brightness=bright, scene=4))
        return scene
    # Swipes move through the ring of modes, % wraps it around
    scene %= 30
    if scene == 0:
        await lamp.turn_on(PilotBuilder(brightness=bright, colortemp=4000))
    elif scene == 1:
        await lamp.turn_on(PilotBuilder(brightness=bright, cold_white=255))
    elif scene == 2:
        await lamp.turn_on(PilotBuilder(brightness=bright, warm_white=255))
    else:
        await lamp.turn_on(PilotBuilder(brightness=bright, scene=scene + 2))
    return scene


async def main():
    lamp = wizlight(LAMP_IP)
    scene = 0
    buffer = list()
    counter = 0
    candidate = ""
    same_count = 0
    last_fire = 0
    brightness = 200

    print("Listening on UDP port 5005")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 5005))

    start = time.time()
    while time.time() - start < 240:
        # One packet is "micros,ax,ay,az,gx,gy,gz"
        data, addr = sock.recvfrom(1024)
        line = data.decode().strip().split(",")
        if len(line) != 7:
            continue
        line2 = []
        if len(buffer) >= 50:
            # Predict every 25 packets, about 4 times per second
            if counter % 25 == 0:
                buffer_df = pd.DataFrame(buffer, columns=["ax", "ay", "az", "gx", "gy", "gz"])
                x = pd.DataFrame([list(buffer_df.mean()) + list(buffer_df.std()) + list(buffer_df.max() - buffer_df.min())], columns=names[:18])
                pred2 = model.predict(x)
                pred_proba = model.predict_proba(x)
                conf = max(pred_proba[0])
                answer = pred2[0]
                # Low confidence is treated as no gesture
                if conf < 0.85:
                    answer = "nothing"
                if candidate == answer:
                    same_count += 1
                else:
                    same_count = 1
                print(answer, conf)
                # Fire only after 3 identical predictions in a row, then wait 1 s
                if same_count == 3 and answer != "nothing" and time.time() - last_fire > 1:
                    print("GESTURE:", answer)
                    # Tilt sets brightness for the next 4 seconds
                    if answer == "rotate":
                        cnt = 0
                        rotate_start = time.time()
                        while time.time() - rotate_start < 4:
                            data, addr = sock.recvfrom(1024)
                            line3 = data.decode().strip()
                            parts = line3.split(",")
                            if len(parts) != 7:
                                continue
                            brightness = int((float(parts[1]) + 1) * 127)
                            brightness = max(10, min(255, brightness))
                            if cnt % 10 == 0:
                                await lamp.turn_on(PilotBuilder(brightness=brightness))
                            cnt += 1
                        buffer.clear()
                        same_count = 0
                    elif answer == "shake":
                        await lamp.turn_off()
                    else:
                        scene = await mode_to_lamp(scene, answer, brightness, lamp)
                    last_fire = time.time()
                candidate = answer
            # Drop the oldest sample to keep the window sliding
            if buffer:
                buffer.pop(0)
        for i in range(1, 7):
            line2.append(float(line[i]))
        buffer.append(line2)
        counter += 1

    print("Session finished")
    sock.close()


asyncio.run(main())
