#!/usr/bin/env python3
from gym_duckietown.simulator import Simulator 
import numpy as np
import time
from pyglet.window import key
from pyglet import app, clock, window 
import math 
import os 
import yaml 
import pyglet.gl as gl # RE-ADDED: For explicit OpenGL clearing

# Import FeedbackWindow from the separate file (assumes feedback_window.py exists)
from feedback_window import FeedbackWindow 

print("Initializing Duckietown Simulator (re-introducing explicit OpenGL clearing for clean shutdown)...")

# ==============================================================================
# CUSTOM MAP PATH (Assumes 'plus_map.yaml' is in the gym_duckietown/maps directory)
# ==============================================================================
# CUSTOM_PLUS_MAP_PATH = "/home/adam/Workspace/work/projects/signalling/code/sim/maps/plus_map.yaml"

# ==============================================================================
# CONFIGURATION AND GLOBAL VARIABLES
# ==============================================================================

# Global action variable for the Duckiebot.
# This will be [left_wheel_velocity, right_wheel_velocity] directly,
# modified by key presses and releases.
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

# MODIFIED: on_key_press - Re-added glClear calls
def on_key_press(symbol, modifiers):
    global action # Declare global to modify the 'action' variable
    
    if symbol == key.ESCAPE:
        env.close()
        feedback_win.close()
        app.exit()
    
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
        # RE-ADDED: Explicit OpenGL clear calls
        env.unwrapped.window.switch_to()
        gl.glClearColor(0, 0, 0, 1) # Set clear color to black
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT) # Clear color and depth buffers
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

# RE-ADDED: Explicit OpenGL clear calls from initial setup
env.unwrapped.window.switch_to()
gl.glClearColor(0, 0, 0, 1) # Set clear color to black
gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT) # Clear color and depth buffers


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
    global action # Ensure 'action' is accessible
    
    # Directly use the global 'action' array (which is [left_vel, right_vel])
    obs, reward, done, info = env.step(action) 
    
    # IMPORTANT: This render/flip is for the current frame BEFORE checking 'done'.
    env.render() 
    env.unwrapped.window.flip() 

    # If the episode is finished, reset the environment.
    if done:
        print(f"Episode finished. Reason: {info.get('reason', 'Unknown')}. Resetting environment randomly...")
        env.reset() 
        # RE-ADDED: Explicit OpenGL clear calls from reset logic
        env.unwrapped.window.switch_to()
        gl.glClearColor(0, 0, 0, 1) # Set clear color to black
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT) # Clear color and depth buffers
        env.render() # Immediately render the new state to clear the screen
        print("Environment reset complete. Duckiebot is at a new, random starting position.")
        
# ==============================================================================
# PYGLET APPLICATION LOOP
# ==============================================================================
clock.schedule_interval(update, 1.0 / env.unwrapped.frame_rate)
app.run()
