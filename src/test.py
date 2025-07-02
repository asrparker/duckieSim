import gym_duckietown
from gym_duckietown.simulator import Simulator
import gym
import numpy as np # Needed for actions

print("gym_duckietown imported successfully!")

# --- Running Simulator (with graphics) ---
print("\n--- Running Duckietown Simulator with Graphics ---")
try:
    env = Simulator(
        seed=123,
        map_name="loop_empty", # A simple, empty loop map
        max_steps=500001,
        domain_rand=0,
        camera_width=640,
        camera_height=480,
        accept_start_angle_deg=4,
        # draw_curve=True,  # Optional: Draws the ideal path
        # draw_bbox=True,   # Optional: Draws bounding boxes around objects
        # frame_rate=30     # Optional: Limit the simulation frame rate
    )
    print("Duckietown simulator environment created successfully!")

    # Reset the environment to get initial observation
    obs = env.reset()

    # Simple loop to step through the environment and render
    # The Duckiebot will just drive straight
    for step in range(300): # Run for 300 simulation steps
        action = np.array([0.5, 0.0]) # [forward_velocity, steering_angle] - 0.5 m/s forward, no steering
        obs, reward, done, info = env.step(action)
        env.render() # IMPORTANT: This is what makes the window appear!

        if done: # Check if the episode is finished (e.g., crashed, fell off map)
            print(f"Episode finished after {step+1} steps.")
            break

    env.close() # Close the simulator window
    print("Simulator environment closed.")

except Exception as e:
    print(f"Error running Duckietown simulator with rendering: {e}")

# --- (Original non-visual test, keeping for completeness but not the focus) ---
print("\n--- Testing Registered Gym Environment (non-visual - for internal check) ---")
try:
    env_gym = gym.make("Duckietown-small_loop-v0")
    print("Registered Gym environment 'Duckietown-small_loop-v0' created successfully!")
    env_gym.close()
    print("Registered environment closed.")
except Exception as e:
    print(f"Error creating registered Gym environment: {e}")
    