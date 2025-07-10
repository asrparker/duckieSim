#!/usr/bin/env python3
import pyglet # Added to fix NameError for pyglet.clock and pyglet.app
from gym_duckietown.simulator import Simulator 
# REMOVED: from gym_duckietown.envs import DuckietownEnv # Not used for env instantiation here
import numpy as np
import time
from pyglet.window import key
from pyglet import app, clock, window # These specific imports are redundant if 'import pyglet' is used, but harmless.
import math 
import os 
import yaml 
# REMOVED: import pyglet.gl as gl (no longer needed for explicit clearing)
from PIL import Image # Added for screenshot functionality from the working code
import sys # Added for sys.exit(0) for clean shutdown

# Import FeedbackWindow from the separate file (assumes feedback_window.py exists)
from feedback_window import FeedbackWindow 

print("Initializing Duckietown Simulator (removing reward prints)...")

# ==============================================================================
# CUSTOM MAP PATH (Assumes 'plus_map.yaml' is in the gym_duckietown/maps directory)
# ==============================================================================
# CUSTOM_PLUS_MAP_PATH = "/home/adam/Workspace/work/projects/signalling/code/sim/maps/plus_map.yaml"

# ==============================================================================
# CONFIGURATION AND GLOBAL VARIABLES
# ==============================================================================

# Global action variable for the Duckiebot.
# NOTE: This global 'action' is now primarily for the KEY_VELOCITIES logic
# The 'action' array inside update(dt) will be a local variable.
action = np.array([0.0, 0.0]) 

# Define wheel velocity contributions for each key press
# These are [left_wheel_vel, right_wheel_vel]
KEY_VELOCITIES = {
    key.UP: np.array([0.5, 0.5]),          # Both wheels forward
    key.DOWN: np.array([-0.5, -0.5]),       # Both wheels backward
    key.LEFT: np.array([-0.2, 0.2]),       # Left wheel backward, right wheel forward (turn left on spot)
    key.RIGHT: np.array([0.2, -0.2]),      # Left wheel forward, right wheel backward (turn right on spot)
}


# ==============================================================================
# KEYBOARD EVENT HANDLERS
# ==============================================================================

# Initialize Pyglet's KeyStateHandler to track continuous key presses.
key_handler = key.KeyStateHandler()

# MODIFIED: on_key_press - Removed glClear calls, changed app.exit to sys.exit
def on_key_press(symbol, modifiers):
    global action # Declare global to modify the 'action' variable
    
    if symbol == key.ESCAPE:
        env.close()
        feedback_win.close()
        sys.exit(0) # MODIFIED: Changed app.exit() to sys.exit(0) for cleaner shutdown
    
    # Driving keys: add their corresponding velocities to the global action array
    if symbol in KEY_VELOCITIES:
        action += KEY_VELOCITIES[symbol]
    
    # Feedback window keys
    elif symbol == key.A: feedback_win.activate_feedback(1, color=(1.0, 1.0, 1.0, 1.0))
    elif symbol == key.S: feedback_win.activate_feedback(2, color=(1.0, 1.0, 1.0, 1.0)) 
    elif symbol == key.D: feedback_win.activate_feedback(3, color=(1.0, 1.0, 1.0, 1.0)) 
    
    # Manual reset key
    elif symbol == key.BACKSPACE or symbol == key.SLASH:
        print("RESET (manual key press)")
        env.reset() 
        # REMOVED: Explicit OpenGL clear calls
        env.render() 
    
    # Pass the event to the key_handler for other keys (like A,S,D)
    key_handler.on_key_press(symbol, modifiers)

# MODIFIED: on_key_release - No change needed here for glClear
def on_key_release(symbol, modifiers):
    global action # Declare global to modify the 'action' variable
    
    # Driving keys: subtract their corresponding velocities from the global action array
    if symbol in KEY_VELOCITIES:
        action -= KEY_VELOCITIES[symbol]
    
    # Pass the event to the key_handler for other keys
    key_handler.on_key_release(symbol, modifiers)


# ==============================================================================
# ENVIRONMENT SETUP
# ==============================================================================
# Instantiate Simulator directly, passing map_name and seed to constructor.
# Assumes 'plus_map.yaml' is in the gym_duckietown/maps directory.
env = Simulator( 
    seed=123, 
    map_name="plus_map", 
    camera_width=640,      
    camera_height=480,     
    full_transparency=False, 
    distortion=False,     
    domain_rand=0,        
    frame_skip=1,         
    camera_rand=False,    
    dynamics_rand=False,  
)

# Initial reset of the environment.
env.reset() 

# Call render() first to ensure the window object is created.
env.render() 
env.unwrapped.window.flip() 

# REMOVED: Explicit OpenGL clear calls from initial setup


# Create an instance of the FeedbackWindow.
sim_x, sim_y = env.unwrapped.window.get_location()
feedback_win = FeedbackWindow(width=200, height=100, title='Duckiebot Feedback', 
                              feedback_duration=0.2, blink_interval=0.2)
feedback_win.set_location(sim_x + env.unwrapped.window.width + 20, sim_y)
feedback_win.activate() 

# Activate the main simulation window AFTER the feedback window to ensure it gets focus.
env.unwrapped.window.activate() 

# Push both the KeyStateHandler and the individual key event handlers to the simulator's window.
env.unwrapped.window.push_handlers(key_handler, on_key_press, on_key_release)

# ==============================================================================
# MAIN UPDATE LOOP
# ==============================================================================
def update(dt):
    """
    This function is called at every frame to handle
    movement/stepping and redrawing
    """
    wheel_distance = 0.102
    min_rad = 0.08

    # NOTE: 'action' is declared locally here, overriding the global 'action' for this function's scope.
    # This 'action' will be [linear_velocity, angular_velocity] initially.
    local_action = np.array([0.0, 0.0]) 

    if key_handler[key.UP]:
        local_action += np.array([0.3, 0.3]) # Linear velocity forward
    if key_handler[key.DOWN]:
        local_action += np.array([-0.3, -0.3]) # Linear velocity backward
    if key_handler[key.LEFT]:
        local_action += np.array([-0.2, 0.2]) # Angular velocity positive (turn left)
    if key_handler[key.RIGHT]:
        local_action += np.array([0.2, -0.2]) # Angular velocity negative (turn right)
    if key_handler[key.SPACE]:
        local_action = np.array([0, 0]) # Stop

    v1 = local_action[0] # Linear velocity
    v2 = local_action[1] # Angular velocity

    # Limit radius of curvature - this converts linear/angular to left/right wheel velocities
    if v1 == 0 or abs(v2 / v1) > (min_rad + wheel_distance / 2.0) / (min_rad - wheel_distance / 2.0):
        # adjust velocities evenly such that condition is fulfilled
        delta_v = (v2 - v1) / 2 - wheel_distance / (4 * min_rad) * (v1 + v2)
        v1 += delta_v
        v2 -= delta_v

    # The 'action' array passed to env.step() is now [left_wheel_velocity, right_wheel_velocity]
    # after the curvature limit logic.
    action_to_step = np.array([v1, v2]) 

    obs, reward, done, info = env.step(action_to_step) # Pass the converted action
    # REMOVED: print("step_count = %s, reward=%.3f" % (env.unwrapped.step_count, reward))

    if key_handler[key.RETURN]:
        im = Image.fromarray(obs)
        im.save("screen.png")

    if done:
        print("done!")
        env.reset()
        env.render() # Render after reset

    env.render() # Render at the end of every frame

# ==============================================================================
# PYGLET APPLICATION LOOP
# ==============================================================================
pyglet.clock.schedule_interval(update, 1.0 / env.unwrapped.frame_rate) 
pyglet.app.run() 
env.close() 