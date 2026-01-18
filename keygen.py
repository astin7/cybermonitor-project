import hashlib

# --- CONFIGURATION ---
PERM_SALT = "CYBER-2077-TOP-SECRET"   # Generates Lifetime Keys
TRIAL_SALT = "CYBER-TRIAL-LIMITED"    # Generates 1-Hour Keys

def generate_key(hardware_id, salt):
    """Generates a key based on ID + Specific Salt"""
    combined = hardware_id.strip() + salt
    hashed = hashlib.sha256(combined.encode()).hexdigest().upper()
    final_key = hashed[:8]
    return f"{final_key[:4]}-{final_key[4:]}"

print("--- CYBER MONITOR KEY GENERATOR ---")

while True:
    print("\n--------------------------------")
    hwid = input("Enter Friend's HWID: ").strip()
    
    if not hwid: continue

    print("\nSelect Key Type:")
    print("1. Permanent (Lifetime)")
    print("2. Trial (1 Hour)")
    choice = input("Choice (1/2): ")

    if choice == "1":
        key = generate_key(hwid, PERM_SALT)
        print(f"\n>>> PERMANENT KEY: {key}")
    elif choice == "2":
        key = generate_key(hwid, TRIAL_SALT)
        print(f"\n>>> TRIAL KEY (1 HR): {key}")
    else:
        print("Invalid choice.")