#!/usr/bin/env python3
import gym_duckietown
from gym_duckietown.simulator import Simulator # Using the base Simulator
import numpy as np
import time
from pyglet.window import key
from pyglet import app, clock, window 
import math # Still needed for math.pi if you want to set initial angle, but removed from FIXED_INITIAL_POSE now

# Import FeedbackWindow from the separate file (assumes feedback_window.py exists)
from feedback_window import FeedbackWindow 

print("Initializing Duckietown Simulator...")

# ==============================================================================
# CONFIGURATION AND GLOBAL VARIABLES
# This section contains only the necessary variables for driving and signaling.
# Reset-related configurations are removed.
# ==============================================================================

# Global action variable for the Duckiebot.
action = np.array([0.0, 0.0]) 
keys_pressed = {} 

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
# This section sets up the base Duckietown Simulator.
# All custom reset logic and fixed pose configurations are removed.
# ==============================================================================
env = Simulator( 
    seed=123, # Random seed for reproducibility of the initial map setup
    map_name="plus_map", # The specific map to load.
    max_steps=500001, # Maximum number of simulation steps before an episode terminates.
    domain_rand=0, # Level of domain randomization (0 means no randomization).
    camera_width=640, # Width of the camera view.
    camera_height=480, # Height of the camera view.
    # Removed accept_start_angle_deg, user_tile_start, user_initial_pose, user_initial_angle
    # to ensure no custom reset attempts are made.
    full_transparency=False, 
    distortion=False, 
)

# Reset the environment to its initial state. This will be the *only* reset.
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
# This loop handles driving and signaling. No reset logic is present.
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

    # Perform a step in the environment.
    # When 'done' becomes True (e.g., off-road, max_steps), the loop will continue
    # but no reset will be explicitly called, and the simulation will effectively stop.
    obs, reward, done, info = env.step(action) 
    
    env.render() 
    env.unwrapped.window.flip() 

    # Removed all 'if done:' reset logic. The simulation will simply stop advancing
    # the Duckiebot when 'done' is True, and you'll need to restart the script.

# ==============================================================================
# PYGLET APPLICATION LOOP
# ==============================================================================
clock.schedule_interval(update, 1.0 / env.unwrapped.frame_rate)
app.run()
