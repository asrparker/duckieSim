#!/usr/bin/env python3
import gym_duckietown
from gym_duckietown.simulator import Simulator
import time
from pyglet.window import key # NEW: Import key module for keyboard input
from pyglet import app # NEW: Import app for pyglet's event loop (though env.render often handles it)

print("Initializing Duckietown Simulator...")

# Instantiate the Simulator with your chosen parameters
env = Simulator(
    seed=123,
    # MODIFIED: Point to your custom map file using its full path
    map_name="plus_map",
    max_steps=500001,
    domain_rand=0,
    camera_width=640,
    camera_height=480,
    accept_start_angle_deg=4,
    full_transparency=True,
    distortion=False, # Set to False for non-fish-eyed view
)

# --- NEW: Manual Control Setup ---
# Global variables to track key states
forward = False
backward = False
left = False
right = False

# Action variables that will be sent to the robot
speed = 0.0
steering = 0.0

# Function that gets called when a keyboard key is pressed down
def on_key_press(symbol, modifiers):
    global forward, backward, left, right, speed, steering # Access global variables
    if symbol == key.UP:
        forward = True
    elif symbol == key.DOWN:
        backward = True
    elif symbol == key.LEFT:
        left = True
    elif symbol == key.RIGHT:
        right = True
    elif symbol == key.Q: # Press 'Q' key to quit the simulation
        env.close()
        exit(0) # Exit the Python script

# Function that gets called when a keyboard key is released
def on_key_release(symbol, modifiers):
    global forward, backward, left, right # Access global variables
    if symbol == key.UP:
        forward = False
    elif symbol == key.DOWN:
        backward = False
    elif symbol == key.LEFT:
        left = False
    elif symbol == key.RIGHT:
        right = False

# --- End NEW Manual Control Setup ---


print("Simulator initialized. Starting continuous simulation loop...")
print("Press arrow keys to drive. Press 'Q' to quit.")

try:
    # Reset the environment to get initial observation and setup the first frame
    observation = env.reset()

    # NEW: Call render once to make sure the window is created
    env.render()
    # NEW: Attach the keyboard event handlers to the simulator's window
    env.window.on_key_press = on_key_press
    env.window.on_key_release = on_key_release

    while True:
        # NEW: Calculate speed and steering based on current key states
        speed = 0.0
        steering = 0.0

        if forward:
            speed = 0.5 # Forward speed (you can adjust this value)
        if backward:
            speed = -0.3 # Backward speed (you can adjust this value)

        if left:
            steering = +0.8 # Left turn amount (you can adjust this value)
        if right:
            steering = -0.8 # Right turn amount (you can adjust this value)

        # Apply the calculated action to the environment
        action = [speed, steering]
        observation, reward, done, misc = env.step(action)

        # Render the environment - this also typically processes pyglet events (like key presses)
        env.render()

        if done:
            print("Episode finished. Resetting environment...")
            observation = env.reset() # Reset to get new observation after episode ends
            # IMPORTANT: Re-attach handlers after reset, as the window might be recreated
            # or its context refreshed by the reset operation
            env.window.on_key_press = on_key_press
            env.window.on_key_release = on_key_release

except KeyboardInterrupt:
    # This block will execute when you press Ctrl+C in the terminal
    print("\nSimulation interrupted by user (Ctrl+C).")
except Exception as e:
    # Catch any other unexpected errors
    print(f"An error occurred during simulation: {e}")
    import traceback
    traceback.print_exc() # Print full traceback for more info
finally:
    # Ensure the environment is closed cleanly when the script ends
    env.close()
    print("Simulator environment closed.")
