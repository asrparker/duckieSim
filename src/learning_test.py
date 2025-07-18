#!/usr/bin/env python3
import pyglet # Added to fix NameError for pyglet.clock and pyglet.app
from gym_duckietown.simulator import Simulator 
import numpy as np
import time
from pyglet.window import key
from pyglet import app, clock, window 
import math 
import csv
import os
import time
import yaml 
from PIL import Image # Added for screenshot functionality from the working code
import sys # Added for sys.exit(0) for clean shutdown

import Q_learning

# Import FeedbackWindow from the separate file (assumes feedback_window.py exists)
from feedback_window import FeedbackWindow 

print("Initializing Duckietown Simulator (consolidating reset logic)...")

def log_single_row(filepath, data_row, header=None):
    """
    Logs a single row of data to a CSV file.
    If the file doesn't exist, it creates it and writes the header (if provided).
    """
    file_exists = os.path.exists(filepath)
    
    with open(filepath, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        if not file_exists and header:
            writer.writerow(header) # Write header only if file is new
        
        writer.writerow(data_row)

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
    # elif symbol == key.A: feedback_win.activate_feedback(1, color=(1.0, 1.0, 1.0, 1.0))
    # elif symbol == key.S: feedback_win.activate_feedback(2, color=(1.0, 1.0, 1.0, 1.0)) 
    # elif symbol == key.D: feedback_win.activate_feedback(3, color=(1.0, 1.0, 1.0, 1.0)) 
    
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
    max_steps=10000,
    camera_width=640,      
    camera_height=480,     
    full_transparency=False, 
    distortion=False,     
    domain_rand=0,        
    frame_skip=1,         
    camera_rand=False,    
    dynamics_rand=False,  
    #display_debug=False
)

# Initial reset of the environment.
env.reset() 

# Call render() first to ensure the window object is created.
env.render() 
env.unwrapped.window.flip() 

# REMOVED: Explicit OpenGL clear calls from initial setup


# Create an instance of the FeedbackWindow.
sim_x, sim_y = env.unwrapped.window.get_location()
feedback_win = FeedbackWindow(width=200, height=100, title='learner Feedback', 
                              feedback_duration=0.2, blink_interval=0.2)
feedback_win.set_location(sim_x + env.unwrapped.window.width + 20, sim_y)
feedback_win.activate() 

# Activate the main simulation window AFTER the feedback window to ensure it gets focus.
env.unwrapped.window.activate() 

# Push both the KeyStateHandler and the individual key event handlers to the simulator's window.
env.unwrapped.window.push_handlers(key_handler, on_key_press, on_key_release)

learner = Q_learning.QAgent()

# defince tiles by name
junction = (3, 3)
left = (5, 3)
straight = (3, 1)
right = (1, 3)

# Global variables for trial management
signalled = False # Flag to track if a signal has been sent
action = None
learning_trial = False # Flag to indicate if this is a learning trial

trial = 0
total_trials = 30 # Total number of trials to run

q_reward = None

# Global variables for trial timing
episode_start_time = 0.0 # To store the timestamp when the current episode/trial began
signal_start_time = 0.0  # To store the timestamp when the Q-learner activated a signal (blinking)
episide_end_time = 0.0   # To store the timestamp when the current episode/trial ended

# Define your CSV log file path
CSV_LOG_FILE = 'TEST02-B-0718.csv'

# Define the header for your CSV file
# Make sure these strings exactly match your desired column names
csv_header = [
    'Trial Number',
    'Total Time',
    'Time from Signal to Termination',
    'Action Taken',
    'Type of Action', # This might be 'Explore', 'Exploit' or 'Fixed'
    'Termination Location',
    'Termination Reward',
    'Q Table'
]

#if os.path.exists(CSV_LOG_FILE):
#    os.remove(CSV_LOG_FILE) # Optional: Remove old log file to start fresh each run
#    print(f"Removed existing log file: {CSV_LOG_FILE}")

# Log the header row. Pass an empty list for data_row if you only want the header initially.
# Or, if your first trial data is ready immediately, you can log it with the header.
# For simplicity, let's just write the header.
log_single_row(CSV_LOG_FILE, [], header=csv_header) # Pass an empty data_row, header will be written

print(f"CSV logging initialized to {CSV_LOG_FILE} with header.")

# ==============================================================================
# MAIN UPDATE LOOP
# ==============================================================================
def update(dt):
    global trial
    global total_trials
    global q_reward

    global manual_reset_pending # Access the global flag
    global signalled # Access the global signalled flag
    global action # Access the global action variable

    global episode_start_time
    global signal_start_time
    global episide_end_time
    
    """
    This function is called at every frame to handle
    movement/stepping and redrawing
    """
    # Control logic for driving
    local_action = np.array([0.0, 0.0]) 

    if key_handler[key.UP]:
        local_action += np.array([0.3, 0.3]) # Linear velocity forward
    if key_handler[key.DOWN]:
        local_action += np.array([-0.3, -0.3]) # Linear velocity backward
    if key_handler[key.LEFT]:
        local_action += np.array([-0.2, 0.2]) # Angular velocity
    if key_handler[key.RIGHT]:
        local_action += np.array([0.2, -0.2]) # Angular velocity
    if key_handler[key.SPACE]:
        local_action = np.array([0, 0]) # Stop

    # The 'action' array passed to env.step() is now [left_wheel_velocity, right_wheel_velocity]
    action_to_step = local_action 

    obs, reward, done, info = env.step(action_to_step) # Pass the calculated action

    current_x, _, current_z = env.unwrapped.cur_pos
    tile_col = int(current_x / env.unwrapped.road_tile_size)
    tile_row = int(current_z / env.unwrapped.road_tile_size)

    # Calculate position relative to the tile's bottom-left corner
    relative_x = current_x - (tile_col * env.unwrapped.road_tile_size)
    relative_z = current_z - (tile_row * env.unwrapped.road_tile_size)

    #print(f"Current Tile: [{tile_row}, {tile_col}], Position within Tile: [{relative_x:.3f}, {relative_z:.3f}]")

    # Put learning stuff here? We have the postion by now
    # Determine the tagid based on the current tile
    current_tile = (tile_row, tile_col)
    tagid = None
    if current_tile == junction:
        tagid = 3
    elif current_tile == left:
        tagid = 0
    elif current_tile == straight:
        tagid = 1
    elif current_tile == right:
        tagid = 2
    
    state = learner.tagid_to_state(tagid)
    #print(f"Current Tile: {current_tile}, Tag ID: {tagid}, State: {state}")

    # use function is_terminal to check if it is a terminal state
    if current_tile == junction and signalled == False:
      # if the tagid shows that the learner is at the intersection point, reset everything to start an episode, and choose an action
      learner.reset()
      if learning_trial:
        action = learner.select_action()
      else:
          action = learner.start_state[0]
      #print(f"Learner at state: {learner.state}, selected action: {action}")
      print(f"Junction reached on trial {trial+1}, {29-trial} remaining! Keep going!")

    elif learner.is_terminal(state) and signalled == True:
      # if the tagid shows that the learner is at the terminal state, update the Q-table, and this should return you an rewar
      q_reward = learner.update(action, tagid)

    #if in the junction, signal using the action
    if current_tile == junction and signalled == False:
        signalled = True
        signal_start_time = time.time() # Record the time the signal was activated
        feedback_win.activate_feedback((action + 1), color=(1.0, 1.0, 1.0, 1.0))
    
    if learner.is_terminal(state) and signalled == True:
        signalled = False
        if q_reward > 0:
            feedback_win.activate_feedback(0, color=(0.0, 1.0, 0.0, 1.0))
        elif q_reward < 0:
            feedback_win.activate_feedback(0, color=(1.0, 0.0, 0.0, 1.0))
        else:
            feedback_win.activate_feedback(None)

    # if in a terminal state, show solid colour depending on the reward

    
    if key_handler[key.RETURN]:
        im = Image.fromarray(obs)
        im.save("screen.png")

    # CONSOLIDATED RESET LOGIC:
    # If episode is finished OR manual reset is pending, perform reset
    if done or manual_reset_pending:
        episide_end_time = time.time() # Capture the end time of the episode
        if done:
            print(f"Episode finished. Reason: {info.get('reason', 'Unknown')}. Resetting environment randomly...")
        elif manual_reset_pending:
            print("RESET (manual key press - executing deferred reset)")
            
        env.reset()
        env.render() # Render immediately after reset
        manual_reset_pending = False # Reset the flag after handling
        feedback_win.activate_feedback(None)

        trial_time = episide_end_time - episode_start_time
        signal_time = episide_end_time - signal_start_time
        
        if learning_trial == False:
            trial_type = 'Fixed'
        elif learner.explore == True:
            trial_type = 'Explore'
        elif learner.explore == False:
            trial_type = 'Exploit'
        
        data_to_log = [
        trial,                                          # 'Trial Number'
        f"{trial_time:.2f}",                            # 'Total Time'
        f"{signal_time:.2f}",                           # 'Time from Signal to Termination'
        action,                                         # 'Action Taken'
        trial_type,                                     # 'Type of Action' (using your new wording)
        current_tile,                                   # 'Termination Location'
        q_reward,                                       # 'Termination Reward'
        learner.Q,                                      # 'Q Table'
        ]   

        log_single_row(CSV_LOG_FILE, data_to_log)

        signalled = False

        episode_start_time = time.time() # Capture the end time of the episode

        trial += 1
        if trial == total_trials:
            print("All trials completed. Exiting. Thank you for participating!")
            env.close()
            feedback_win.close()
            sys.exit(0)

    env.render() # Render at the end of every frame

# ==============================================================================
# PYGLET APPLICATION LOOP
# ==============================================================================
episode_start_time = time.time() # Initialize the start time for the first episode

pyglet.clock.schedule_interval(update, 1.0 / env.unwrapped.frame_rate) 
pyglet.app.run() 

env.close() # To match manual_control.py's cleanup
