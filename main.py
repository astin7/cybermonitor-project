import sys
import os
import ctypes
import psutil
import eel
import wmi 
import json
import time 
import hashlib 
import pythoncom 
import winreg
import secrets_config

# CONFIGURATION
# Anyone can use this key for 20 minutes (1200 seconds)
UNIVERSAL_TRIAL_KEY = "CYBER-TRIAL-LIMITED" 

# Hardware Lock Secrets
PERM_SALT = secrets_config.PERM_SALT
TRIAL_SALT = secrets_config.TRIAL_SALT
LICENSE_FILE = "license_tracker.json"
REG_PATH = r"Software\CyberMonitor"

# Global State
CURRENT_USER_KEY = None
DETECTED_BASE_CLOCK = 0
last_cpu_mhz = 0
last_gpu_mhz = 0
wmi_obj = None

def get_resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except: base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 0)
    sys.exit()

# HARDWARE SECURITY
def get_system_hwid():
    """Gets the unique Motherboard UUID"""
    try:
        pythoncom.CoInitialize() 
        c = wmi.WMI()
        uuid = c.Win32_ComputerSystemProduct()[0].UUID
        return uuid.strip()
    except:
        return "UNKNOWN-ID"

def verify_key_math(user_key, hwid, salt):
    """Checks if key matches the math for a specific salt"""
    try:
        combined = hwid + salt
        hashed = hashlib.sha256(combined.encode()).hexdigest().upper()
        expected_key = hashed[:8]
        expected_formatted = f"{expected_key[:4]}-{expected_key[4:]}"
        return user_key == expected_formatted
    except:
        return False

# HARDWARE INIT
from pythonnet import load
try: load("netfx")
except: pass

import clr 
try:
    clr.AddReference(get_resource_path("LibreHardwareMonitorLib.dll"))
    from LibreHardwareMonitor.Hardware import Computer
except: pass

computer = Computer()
computer.IsCpuEnabled = True
computer.IsGpuEnabled = True 
computer.IsMemoryEnabled = False 
computer.Open()

try:
    wmi_obj = wmi.WMI()
    proc_info = wmi_obj.Win32_Processor()[0]
    DETECTED_BASE_CLOCK = int(proc_info.MaxClockSpeed)
except Exception: pass

eel.init('web')

# License logic 
def load_license_data():
    """Reads license dictionary from the Windows Registry"""
    try:
        # Open the key for reading
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        
        # Retrieve the data
        value, _ = winreg.QueryValueEx(key, "LicenseInfo")
        winreg.CloseKey(key)
        return json.loads(value)
    except (FileNotFoundError, OSError):
        # If the key doesn't exist yet, return empty
        return {}
    except Exception as e:
        print(f"Registry Load Error: {e}")
        return {}

def save_license_data(data):
    """Saves license dictionary to the Windows Registry"""
    try:
        # Create or open the registry key
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        
        # Convert dictionary to JSON string for storage
        json_str = json.dumps(data)
        
        # Store it as a string value named 'LicenseInfo'
        winreg.SetValueEx(key, "LicenseInfo", 0, winreg.REG_SZ, json_str)
        winreg.CloseKey(key) #
    except Exception as e:
        print(f"Registry Save Error: {e}")

@eel.expose
def get_hwid_frontend():
    return get_system_hwid()

@eel.expose
def validate_key(user_key):
    global CURRENT_USER_KEY
    
    my_hwid = get_system_hwid()

    # Check universal trial 
    if user_key == UNIVERSAL_TRIAL_KEY:
        data = load_license_data()
        
        # If this computer has never used the universal key, give 1200s (20 mins)
        if user_key not in data:
            data[user_key] = 1200 
            save_license_data(data)
            CURRENT_USER_KEY = user_key
            return "success"
        
        # Check if they have time left
        seconds_left = data[user_key]
        if seconds_left > 0:
            CURRENT_USER_KEY = user_key
            return "success"
        else:
            return "expired"

    # Check permanent formula
    if verify_key_math(user_key, my_hwid, PERM_SALT):
        CURRENT_USER_KEY = "PERMANENT-OWNER"
        return "success"
    
    # Check generated trial formula (1 Hour Specific)
    if verify_key_math(user_key, my_hwid, TRIAL_SALT):
        data = load_license_data()
        if user_key not in data:
            data[user_key] = 3600
            save_license_data(data)
            CURRENT_USER_KEY = user_key
            return "success"
        
        seconds_left = data[user_key]
        if seconds_left > 0:
            CURRENT_USER_KEY = user_key
            return "success"
        else:
            return "expired"

    return "invalid"

def decrement_time():
    """No changes needed here, it uses the new load/save functions automatically"""
    if CURRENT_USER_KEY and CURRENT_USER_KEY != "PERMANENT-OWNER":
        data = load_license_data()
        if CURRENT_USER_KEY in data:
            remaining = data[CURRENT_USER_KEY]
            if remaining > 0:
                remaining -= 1
                data[CURRENT_USER_KEY] = remaining
                save_license_data(data)
                return remaining
            else:
                return 0
    return -1

# Dashboard data
@eel.expose
def get_stats():
    global last_cpu_mhz, last_gpu_mhz, DETECTED_BASE_CLOCK

    time_left = -1
    if CURRENT_USER_KEY == "PERMANENT-OWNER":
        time_left = -1
    elif CURRENT_USER_KEY:
        time_left = decrement_time()

    stats = {
        "cpu_name": "CPU", "cpu_usage": 0, "cpu_mhz": last_cpu_mhz, "cpu_temp": 0,
        "ram_usage": 0, "ram_used_gb": 0,
        "gpu_name": "GPU", "gpu_load": 0, "gpu_temp": 0, "gpu_mhz": last_gpu_mhz,
        "processes": [],
        "time_left": time_left
    }

    try:
        ram = psutil.virtual_memory()
        stats['ram_usage'] = int(ram.percent)
        stats['ram_used_gb'] = round(ram.used / (1024**3), 1)

        for hardware in computer.Hardware:
            hardware.Update()
            h_type = str(hardware.HardwareType)
            if h_type == "Cpu":
                stats['cpu_name'] = hardware.Name.replace("AMD", "").replace("Intel", "").replace("Core", "").replace("Processor", "").replace("CPU", "").strip()
                for sensor in hardware.Sensors:
                    if str(sensor.SensorType) == "Load" and "Total" in sensor.Name: stats['cpu_usage'] = int(sensor.Value)
            if "Amd" in h_type or "Radeon" in hardware.Name:
                for sensor in hardware.Sensors:
                    if str(sensor.SensorType) == "Temperature" and "SoC" in sensor.Name: stats['cpu_temp'] = int(sensor.Value)
            if "GpuNvidia" in h_type:
                stats['gpu_name'] = hardware.Name.replace("NVIDIA", "").replace("GeForce", "").strip()
                for sensor in hardware.Sensors:
                    if str(sensor.SensorType) == "Load" and sensor.Name == "GPU Core": stats['gpu_load'] = int(sensor.Value)
                    if str(sensor.SensorType) == "Temperature" and sensor.Name == "GPU Core": stats['gpu_temp'] = int(sensor.Value)
                    if str(sensor.SensorType) == "Clock" and sensor.Name == "GPU Core": 
                         if sensor.Value > 100:
                             stats['gpu_mhz'] = int(sensor.Value)
                             last_gpu_mhz = int(sensor.Value)
    except: pass

    # Turbo Speed
    try:
        if DETECTED_BASE_CLOCK > 0:
            perf_data = wmi_obj.Win32_PerfFormattedData_Counters_ProcessorInformation(Name="_Total")[0]
            real_speed = int((int(perf_data.PercentProcessorPerformance) * DETECTED_BASE_CLOCK) / 100)
            if 400 < real_speed < 10000:
                stats['cpu_mhz'] = real_speed
                last_cpu_mhz = real_speed
    except: pass
    
    if stats['cpu_mhz'] < 100: stats['cpu_mhz'] = last_cpu_mhz

    # Processes
    try:
        procs = []
        for p in psutil.process_iter(['name', 'cpu_percent']):
            if p.info['name'] != "System Idle Process" and p.info['cpu_percent'] > 0.1: procs.append(p.info)
        stats['processes'] = sorted(procs, key=lambda x: x['cpu_percent'], reverse=True)[:5]
    except: pass

    return stats

eel.start('login.html', size=(1200, 800), port=0)
