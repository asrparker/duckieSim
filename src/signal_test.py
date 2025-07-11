#!/usr/bin/env python3
import pyglet # Added to fix NameError for pyglet.clock and pyglet.app
from gym_duckietown.simulator import Simulator 
import numpy as np
import time
from pyglet.window import key
from pyglet import app, clock, window 
import math 
import os 
import yaml 
from PIL import Image # Added for screenshot functionality from the working code
import sys # Added for sys.exit(0) for clean shutdown

# Import FeedbackWindow from the separate file (assumes feedback_window.py exists)
from feedback_window import FeedbackWindow 

print("Initializing Duckietown Simulator (consolidating reset logic)...")

# ==============================================================================
# CUSTOM MAP PATH (Assumes 'plus_map.yaml' is in the gym_duckietown/maps directory)
# ==============================================================================
# CUSTOM_PLUS_MAP_PATH = "/home/adam/Workspace/work/projects/signalling/code/sim/maps/plus_map.yaml"

# ==============================================================================
# CONFIGURATION AND GLOBAL VARIABLES
# ==============================================================================

# Global flag for deferred manual reset
manual_reset_pending = False

# Global action variable (no longer directly modified by driving keys in handlers)
# This is kept for consistency but its direct modification for driving is now in update(dt)
action = np.array([0.0, 0.0]) 

# ==============================================================================
# KEYBOARD EVENT HANDLERS
# ==============================================================================

# Initialize Pyglet's KeyStateHandler to track continuous key presses.
key_handler = key.KeyStateHandler()

# MODIFIED: on_key_press - Only handles special keys and defers manual reset
def on_key_press(symbol, modifiers):
    global manual_reset_pending # Declare global to modify the flag
    
    if symbol == key.ESCAPE:
        env.close()
        feedback_win.close()
        sys.exit(0) # Changed app.exit() to sys.exit(0) for cleaner shutdown
    
    # Feedback window keys
    elif symbol == key.A: feedback_win.activate_feedback(1, color=(1.0, 1.0, 1.0, 1.0))
    elif symbol == key.S: feedback_win.activate_feedback(2, color=(1.0, 1.0, 1.0, 1.0)) 
    elif symbol == key.D: feedback_win.activate_feedback(3, color=(1.0, 1.0, 1.0, 1.0)) 
    
    # Manual reset key: set flag, actual reset happens in update(dt)
    elif symbol == key.BACKSPACE or symbol == key.SLASH:
        print("RESET (manual key press - pending)")
        manual_reset_pending = True # Set the flag to trigger reset in update loop
    
    # Pass the event to the key_handler for continuous state tracking of all keys
    key_handler.on_key_press(symbol, modifiers)

# MODIFIED: on_key_release - Only passes to key_handler, no action modification for driving
def on_key_release(symbol, modifiers):
    # Pass the event to the key_handler for continuous state tracking
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
    global manual_reset_pending # Access the global flag
    
    """
    This function is called at every frame to handle
    movement/stepping and redrawing
    """
    # User's EXACT control logic for driving
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

    # The 'action' array passed to env.step() is now [left_wheel_velocity, right_wheel_velocity]
    action_to_step = local_action 

    obs, reward, done, info = env.step(action_to_step) # Pass the calculated action
    
    if key_handler[key.RETURN]:
        im = Image.fromarray(obs)
        im.save("screen.png")

    # CONSOLIDATED RESET LOGIC:
    # If episode is finished OR manual reset is pending, perform reset
    if done or manual_reset_pending:
        if done:
            print(f"Episode finished. Reason: {info.get('reason', 'Unknown')}. Resetting environment randomly...")
        elif manual_reset_pending:
            print("RESET (manual key press - executing deferred reset)")
            
        env.reset()
        env.render() # Render immediately after reset
        manual_reset_pending = False # Reset the flag after handling

    env.render() # Render at the end of every frame

# ==============================================================================
# PYGLET APPLICATION LOOP
# ==============================================================================
pyglet.clock.schedule_interval(update, 1.0 / env.unwrapped.frame_rate) 
pyglet.app.run() 

env.close() # To match manual_control.py's cleanup
