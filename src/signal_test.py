#!/usr/bin/env python3
import gym_duckietown
from gym_duckietown.simulator import Simulator # Using the base Simulator
import numpy as np
import time
from pyglet.window import key
from pyglet import app, clock, window 
import math 

# Import FeedbackWindow from the separate file (assumes feedback_window.py exists)
from feedback_window import FeedbackWindow 

print("Initializing Duckietown Simulator...")

# ==============================================================================
# CONFIGURATION AND GLOBAL VARIABLES
# ==============================================================================

# Global action variable for the Duckiebot.
action = np.array([0.0, 0.0]) 
keys_pressed = {} 

# Map tile definitions for the '+' map.
ARM_END_TILES = {
    "Bottom": (5, 3) # Row 5, Column 3 - Our fixed starting point
}

TILE_SIZE = 0.585 

# Fixed initial pose for the Duckiebot (center of tile (5,3), facing North).
FIXED_INITIAL_POSE = {
    'pos': np.array([ARM_END_TILES["Bottom"][1] * TILE_SIZE + TILE_SIZE/2, 0.0, ARM_END_TILES["Bottom"][0] * TILE_SIZE + TILE_SIZE/2]),
    'angle': math.pi / 2 
}

# ==============================================================================
# KEYBOARD EVENT HANDLERS
# ==============================================================================
def on_key_press(symbol, modifiers):
    keys_pressed[symbol] = True
    if symbol == key.ESCAPE:
        env.close()
        feedback_win.close()
        app.exit()
    elif symbol == key.A: feedback_win.activate_feedback(1, color=(1.0, 1.0, 1.0, 1.0))
    elif symbol == key.S: feedback_win.activate_feedback(2, color=(1.0, 1.0, 1.0, 1.0))
    elif symbol == key.D: feedback_win.activate_feedback(3, color=(1.0, 1.0, 1.0, 1.0))

def on_key_release(symbol, modifiers):
    keys_pressed[symbol] = False

# ==============================================================================
# ENVIRONMENT SETUP
# ==============================================================================
# Initialize the base Duckietown Simulator environment.
env = Simulator( 
    seed=123, # Random seed for reproducibility of the environment.
    map_name="plus_map", # The specific map to load.
    max_steps=500001, # Maximum number of simulation steps before an episode terminates.
    domain_rand=0, # Level of domain randomization (0 means no randomization).
    camera_width=640, # Width of the camera view.
    camera_height=480, # Height of the camera view.
    # Removed accept_start_angle_deg, as it introduces unwanted randomness.
    full_transparency=False, 
    distortion=False, 
)

# Initial Fixed Pose Setup for the Simulator (for the very first launch)
# These parameters are read by env.reset() for the initial setup.
env.unwrapped.user_tile_start = ARM_END_TILES["Bottom"] # Sets the starting tile for the simulator's internal logic
env.unwrapped.user_initial_pose = FIXED_INITIAL_POSE['pos'] # Sets the exact 3D position
env.unwrapped.user_initial_angle = FIXED_INITIAL_POSE['angle'] # Sets the exact initial angle

# Reset the environment to its initial state.
# In this base Simulator, reset() returns only the observation.
obs = env.reset() 
env.render() 
env.unwrapped.window.flip()

# Create an instance of the FeedbackWindow.
feedback_win = FeedbackWindow(width=200, height=100, title='Duckiebot Feedback', 
                              feedback_duration=0.3, blink_interval=0.3)
sim_x, sim_y = env.unwrapped.window.get_location()
feedback_win.set_location(sim_x + env.unwrapped.window.width + 20, sim_y)
env.unwrapped.window.activate() 
env.unwrapped.window.push_handlers(on_key_press, on_key_release)

# ==============================================================================
# MAIN UPDATE LOOP
# ==============================================================================
def update(dt):
    global action
    
    linear_vel = 0.0
    angular_vel = 0.0

    base_speed = 0.5
    turn_rate = 0.2

    if keys_pressed.get(key.UP, False) and not keys_pressed.get(key.DOWN, False): linear_vel = base_speed
    elif keys_pressed.get(key.DOWN, False) and not keys_pressed.get(key.UP, False): linear_vel = -base_speed
    if keys_pressed.get(key.LEFT, False) and not keys_pressed.get(key.RIGHT, False): angular_vel = turn_rate
    elif keys_pressed.get(key.RIGHT, False) and not keys_pressed.get(key.LEFT, False): angular_vel = -turn_rate

    action = np.array([linear_vel - angular_vel, linear_vel + angular_vel])

    obs, reward, done, info = env.step(action) 
    
    env.render() 
    env.unwrapped.window.flip() 

    if done:
        print(f"Episode finished. Current tile: {info.get('tile', 'N/A')}, Reason: {info.get('reason', 'Unknown')}.")
        print("Calling env.reset() (base simulator default behavior)...")
        
        # Call the base Simulator's reset method.
        # This will likely result in inconsistent starting positions for subsequent resets.
        obs = env.reset() 
        
        print(f"Environment reset complete. Duckiebot's new pose: Pos={env.unwrapped.cur_pos}, Angle={env.unwrapped.cur_angle:.2f} radians.")
        print("Observe if the Duckiebot's position and angle are consistent with the initial launch.")

# ==============================================================================
# PYGLET APPLICATION LOOP
# ==============================================================================
clock.schedule_interval(update, 1.0 / env.unwrapped.frame_rate)
app.run()
