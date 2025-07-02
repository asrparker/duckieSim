import gym_duckietown
from gym_duckietown.simulator import Simulator
import gym
import numpy as np
import time

print("gym_duckietown imported successfully!")

# --- Running Simulator (with graphics) ---
print("\n--- Running Duckietown Simulator with Graphics ---")
try:
    env = Simulator(
        seed=123,
        map_name="loop_empty", # A simple, empty loop map
        max_steps=50000,
        domain_rand=0,
        camera_width=640,
        camera_height=480,
        accept_start_angle_deg=4,
        headless=False # Explicitly set to False
    )
    print("Duckietown simulator environment created successfully!")

    # Reset the environment to get initial observation
    obs = env.reset()

    # --- TEMPORARY CHANGE FOR DEBUGGING: Render once and wait ---
    print("Attempting to render one frame and wait for 5 seconds...")
    env.render() # Render the initial frame
    time.sleep(5) # Keep the window open for 5 seconds

    # --- ORIGINAL SIMULATION LOOP (COMMENTED OUT FOR THIS TEST) ---
    # for step in range(500):
    #     action = np.array([0.5, 0.0])
    #     obs, reward, done, info = env.step(action)
    #     env.render()
    #     time.sleep(0.01)
    #
    #     if done:
    #         print(f"Episode finished after {step+1} steps.")
    #         break

    env.close() # Close the simulator window
    print("Simulator environment closed.")

except Exception as e:
    print(f"Error running Duckietown simulator with rendering: {e}")
    import traceback
    traceback.print_exc() # Print full traceback for more info

# --- (Original non-visual test, keeping for completeness but not the focus) ---
print("\n--- Testing Registered Gym Environment (non-visual - for internal check) ---")
try:
    env_gym = gym.make("Duckietown-small_loop-v0")
    print("Registered Gym environment 'Duckietown-small_loop-v0' created successfully!")
    env_gym.close()
    print("Registered environment closed.")
except Exception as e:
    print(f"Error creating registered Gym environment: {e}")
    