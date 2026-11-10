"""Nut driver test for the SO-101 socket on motor 5 (wrist roll).

Switches motor 5 into continuous-rotation (wheel) mode and lets you drive the
socket from the keyboard while it shows position, turns, speed and load live.

  t      tighten  (stops by itself when the load passes SNUG_LOAD)
  l      loosen
  space  stop
  r      reset the turn counter
  q      quit  (puts motor 5 back into normal position mode)

Only motor 5 is powered by this script - the other joints stay limp,
so rest the arm on something or hold it.

Run from your lerobot folder:  python nut_driver.py
"""
import sys
import time

try:
    import msvcrt  # Windows keyboard input
except ImportError:
    sys.exit("This script uses Windows keyboard input (msvcrt). Run it on your Windows laptop.")

import scservo_sdk as scs

# ---------------- SETTINGS ----------------
PORT = "" #Set to follower arm's connected port
BAUD = 1_000_000
MOTOR_ID = 5

SPEED = 800          # steps/s (4096 steps = 1 turn), 800 ~ 12 rpm
TORQUE_LIMIT = 500   # hard cap on motor torque, 0-1000 (500 = 50%)
SNUG_LOAD = 350      # tightening stops when |load| goes above this (tune it!)
TIGHTEN_DIR = -1     # set for this arm: 't' turns clockwise looking along the socket
MAX_TURNS = 12       # safety stop for one run
STALL_TIME = 1.0     # stop if the socket hasn't moved for this long (s)
STARTUP_IGNORE = 0.3 # ignore the load spike when the motor starts (s)
# ------------------------------------------

# STS3215 register addresses
ADDR_MODE = 33          # 0 = position, 1 = wheel (EEPROM)
ADDR_TORQUE_EN = 40
ADDR_GOAL_POS = 42
ADDR_GOAL_SPEED = 46
ADDR_TORQUE_LIMIT = 48
ADDR_LOCK = 55          # 0 = EEPROM unlocked
ADDR_POS = 56
ADDR_SPEED = 58
ADDR_LOAD = 60

port = scs.PortHandler(PORT)
pk = scs.PacketHandler(0)


def check(result, error, what):
    if result != scs.COMM_SUCCESS:
        raise ConnectionError(f"{what}: {pk.getTxRxResult(result)}")
    if error:
        print(f"\n[motor warning during {what}: {pk.getRxPacketError(error)}]")


def _retry(fn, what, tries=4):
    """Retry a write. EEPROM writes make the motor busy for a moment, so its reply
    can arrive late or get mixed up with the next one - clear the line and retry."""
    for attempt in range(tries):
        r, e = fn()
        if r == scs.COMM_SUCCESS:
            check(r, e, what)
            return
        time.sleep(0.05)
        port.clearPort()
    check(r, e, what)


def w1(addr, val, what="write"):
    _retry(lambda: pk.write1ByteTxRx(port, MOTOR_ID, addr, val), what)


def w2(addr, val, what="write"):
    _retry(lambda: pk.write2ByteTxRx(port, MOTOR_ID, addr, val), what)


def r1(addr):
    for _ in range(4):
        val, r, _ = pk.read1ByteTxRx(port, MOTOR_ID, addr)
        if r == scs.COMM_SUCCESS:
            return val
        time.sleep(0.05)
        port.clearPort()
    return None


def r2(addr):
    val, r, _ = pk.read2ByteTxRx(port, MOTOR_ID, addr)
    return val if r == scs.COMM_SUCCESS else None


def signed(raw, sign_bit):
    """Feetech sign-magnitude: the sign lives in one bit, not two's complement."""
    if raw is None:
        return None
    mag = raw & ((1 << sign_bit) - 1)
    return -mag if raw & (1 << sign_bit) else mag


def set_speed(v):
    raw = min(abs(int(v)), 0x7FFF)
    if v < 0:
        raw |= 0x8000
    w2(ADDR_GOAL_SPEED, raw, "set speed")


def set_mode(mode):
    """Change the mode with the EEPROM LOCKED. With Lock = 1 the motor uses the new
    value straight away but does not save it to flash, so there is no slow flash
    write, and the motor is back in position mode after any power cycle."""
    w1(ADDR_TORQUE_EN, 0, "torque off")
    w1(ADDR_LOCK, 1, "lock")
    time.sleep(0.05)
    seen = []
    for attempt in range(3):
        cur = r1(ADDR_MODE)
        seen.append(cur)
        if cur == mode:
            return
        w1(ADDR_MODE, mode, "set mode")
        time.sleep(0.05)
    seen.append(r1(ADDR_MODE))
    if seen[-1] != mode:
        raise ConnectionError(f"motor {MOTOR_ID} did not switch to mode {mode} "
                              f"(mode read back: {seen})")


def main():
    if not port.openPort():
        sys.exit(f"Could not open {PORT} (is another script using it?)")
    port.setBaudRate(BAUD)
    _, r, _ = pk.ping(port, MOTOR_ID)
    if r != scs.COMM_SUCCESS:
        sys.exit(f"Motor {MOTOR_ID} not responding on {PORT}: check power and cable.")

    try:
        set_mode(1)
        w2(ADDR_TORQUE_LIMIT, TORQUE_LIMIT, "torque limit")
        set_speed(0)
        w1(ADDR_TORQUE_EN, 1, "torque on")
        print(__doc__.split("Only")[0])

        state = "stop"
        run_start = 0.0
        last_pos = r2(ADDR_POS)
        total_steps = 0
        run_start_steps = 0
        last_move = time.time()
        msg = ""

        def drive(new_state):
            nonlocal state, run_start, run_start_steps, last_move, msg
            state = new_state
            run_start = last_move = time.time()
            run_start_steps = total_steps
            if state == "tighten":
                set_speed(TIGHTEN_DIR * SPEED)
            elif state == "loosen":
                set_speed(-TIGHTEN_DIR * SPEED)
            else:
                set_speed(0)
            msg = ""

        while True:
            if msvcrt.kbhit():
                k = msvcrt.getwch().lower()
                if k == "q":
                    break
                if k == "t":
                    drive("tighten")
                elif k == "l":
                    drive("loosen")
                elif k == " ":
                    drive("stop")
                elif k == "r":
                    total_steps = run_start_steps = 0

            pos = r2(ADDR_POS)
            spd = signed(r2(ADDR_SPEED), 15)
            load = signed(r2(ADDR_LOAD), 10)
            now = time.time()

            if pos is not None and last_pos is not None:
                d = pos - last_pos
                if d > 2048:
                    d -= 4096
                elif d < -2048:
                    d += 4096
                total_steps += d
                if abs(d) > 3:
                    last_move = now
                last_pos = pos

            if state != "stop":
                run_turns = abs(total_steps - run_start_steps) / 4096
                settled = now - run_start > STARTUP_IGNORE
                if state == "tighten" and settled and load is not None and abs(load) > SNUG_LOAD:
                    drive("stop"); msg = f"SNUG at load {abs(load)}"
                elif now - last_move > STALL_TIME:
                    drive("stop"); msg = "STALLED (stopped for safety)"
                elif run_turns > MAX_TURNS:
                    drive("stop"); msg = f"MAX_TURNS ({MAX_TURNS}) reached"

            turns = TIGHTEN_DIR * total_steps / 4096
            print(f"\r{state:8s} pos {pos if pos is not None else '----':>4}  "
                  f"turns {turns:+6.2f}  speed {spd if spd is not None else '--':>5}  "
                  f"load {load if load is not None else '--':>5}  {msg:32s}",
                  end="", flush=True)
            time.sleep(0.02)

    finally:
        print("\nRestoring motor 5 to position mode...")
        try:
            set_speed(0)
            set_mode(0)                      # also turns torque off
            pos = r2(ADDR_POS)
            if pos is not None:
                w2(ADDR_GOAL_POS, pos, "goal = current")  # no jump next time torque comes on
            print("Done.")
        except Exception as e:
            print(f"Could not restore cleanly ({e}). Run the script again and press q.")
        port.closePort()


if __name__ == "__main__":
    main()