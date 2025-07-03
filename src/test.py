#!/usr/bin/env python3
import gym_duckietown
from gym_duckietown.simulator import Simulator
import time # Import time for potential future use, though not directly used in this loop

print("Initializing Duckietown Simulator...")

# Instantiate the Simulator with your chosen parameters
env = Simulator(
    seed=123,  # random seed
    map_name="loop_empty",
    max_steps=500001,  # we don't want the gym to reset itself automatically too soon
    domain_rand=0,
    camera_width=640,
    camera_height=480,
    accept_start_angle_deg=4,  # start close to straight
    full_transparency=True,
    distortion=False,
)

print("Simulator initialized. Starting continuous simulation loop...")
print("Press Ctrl+C in the terminal to stop the simulation.")

try:
    # Reset the environment to get initial observation and setup the first frame
    observation = env.reset()

    while True:
        action = [0.1, 0.1] # Example action: move forward slightly, no turn
        observation, reward, done, misc = env.step(action)
        env.render() # This command should attempt to open and update the graphical window

        if done:
            print("Episode finished. Resetting environment...")
            env.reset()

except KeyboardInterrupt:
    # This block will execute when you press Ctrl+C
    print("\nSimulation interrupted by user (Ctrl+C).")
except Exception as e:
    print(f"An error occurred during simulation: {e}")
    import traceback
    traceback.print_exc() # Print full traceback for more info
finally:
    # Ensure the environment is closed cleanly
    env.close()
    print("Simulator environment closed.")
