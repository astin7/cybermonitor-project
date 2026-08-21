import sys
import os
import ctypes
import clr

# Auto admin check
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("Restarting as Administrator to access hardware...")
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    except Exception as e:
        print(f"Failed to restart as admin: {e} ❌")
    sys.exit()

# Load the driver
from pythonnet import load
try: load("netfx")
except: pass

try:
    # Look for DLL in the current folder
    dll_path = os.path.abspath("LibreHardwareMonitorLib.dll")
    if not os.path.exists(dll_path):
        print(f"DLL NOT FOUND at: {dll_path} ❌")
        print("Make sure probe.py is in the same folder as LibreHardwareMonitorLib.dll")
        input("Press Enter to exit...")
        sys.exit()
        
    clr.AddReference(dll_path)
    from LibreHardwareMonitor.Hardware import Computer
except Exception as e:
    print(f"DLL Error: {e} ❌")
    input("Press Enter to exit...")
    sys.exit()

# Scan hardware
print("SCANNING HARDWARE SENSORS...")
print("=================================")

try:
    computer = Computer()
    computer.IsCpuEnabled = True
    computer.IsGpuEnabled = True
    computer.IsMemoryEnabled = True
    computer.Open()

    for hardware in computer.Hardware:
        hardware.Update()
        print(f"\n[HARDWARE]: {hardware.Name} ({hardware.HardwareType})")
        
        for sensor in hardware.Sensors:
            # Print Name, Type, and Value
            print(f"   - {sensor.Name:<35} | Type: {str(sensor.SensorType):<12} | Value: {sensor.Value}")

except Exception as e:
    print(f"SCAN FAILED: {e} ❌")

print("\n=================================")
print("SCAN COMPLETE. Select the text above, Right-Click to Copy. ✅")
input("Press Enter to close this window...")