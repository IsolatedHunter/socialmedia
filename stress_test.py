import requests
import random
import string
import time
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://127.0.0.1:5000"

def generate_random_name():
    # Generates a random base name (e.g., Bot_A1B2C3)
    return "Bot_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def simulate_user(user_id):
    # A Session automatically stores and sends cookies (like the login session)
    session = requests.Session()
    base_username = generate_random_name()
    
    try:
        # 1. Register the user (your app automatically logs them in upon registration)
        session.post(f"{BASE_URL}/register", data={
            "username": base_username,
            "password": "password123",
            "venmo_handle": ""
        })
        
        # 2. Post a status update
        session.post(f"{BASE_URL}/", data={
            "content": f"Stress test post from bot #{user_id}! The server is working hard.",
            "location": "The Matrix"
        })
        
        # 3. Load the home feed
        response = session.get(f"{BASE_URL}/")
        
        if response.status_code == 200:
            print(f"[SUCCESS] Bot {user_id} ({base_username}) finished.")
        else:
            print(f"[ERROR] Bot {user_id} hit a wall. HTTP Status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"[FAILED] Bot {user_id} could not connect: {e}")

def run_stress_test(total_users):
    print(f"Launching {total_users} simulated users at {BASE_URL}...\n")
    start_time = time.time()
    
    # ThreadPoolExecutor runs the simulate_user function concurrently
    with ThreadPoolExecutor(max_workers=total_users) as executor:
        for i in range(total_users):
            executor.submit(simulate_user, i)
            
    elapsed = time.time() - start_time
    print(f"\nStress test finished in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    # Change this number to simulate more or fewer concurrent users
    run_stress_test(1000)