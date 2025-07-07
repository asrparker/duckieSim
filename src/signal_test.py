#!/usr/bin/env python3
import gym_duckietown
from gym_duckietown.simulator import Simulator
import numpy as np
import time
from pyglet.window import key
from pyglet import app
from pyglet import clock
# Removed pyglet.gl as it's only used in FeedbackWindow now
import pyglet.window # Explicitly importing pyglet.window for clarity
import math # Required for math.pi to define angles

# NEW: Import FeedbackWindow from the new file
from feedback_window import FeedbackWindow 

print("Initializing Duckietown Simulator...")

# ==============================================================================
# GLOBAL VARIABLES
# These variables are accessible and modifiable from anywhere in the script.
# ==============================================================================

# Global action variable for the Duckiebot.
# This array holds the left and right wheel velocities for the robot.
action = np.array([0.0, 0.0]) # [left_wheel_velocity, right_wheel_velocity]

# Global dictionary to track which keyboard keys are currently pressed.
# Stores key symbols as keys and True/False as values.
keys_pressed = {} # Stores {key_symbol: True/False}

# Map Definitions and Fixed Initial Pose
# These are the (row, column) tile coordinates for the ends of the four arms of the '+' map.
# Based on a 7x7 map where the junction is at (3,3).
ARM_END_TILES = {
    "Top": (1, 3),    # Row 1, Column 3
    "Right": (3, 5),  # Row 3, Column 5
    "Bottom": (5, 3), # Row 5, Column 3 - Our fixed starting point
    "Left": (3, 1)    # Row 3, Column 1
}

# Define the standard size of a Duckietown road tile in meters.
# CORRECTED: Updated TILE_SIZE to match the map file's 0.585.
TILE_SIZE = 0.585

# Define the fixed initial pose (position and angle) for the Duckiebot.
# This ensures it always starts at the bottom arm facing towards the intersection.
# 'pos': (x, y, z) where x, z are map coordinates, y is height (usually 0.0).
# The calculation converts the (row, column) tile index to precise (x, z) world coordinates
# by multiplying by TILE_SIZE and adding TILE_SIZE/2 to get the center of the tile.
# IMPORTANT: In Duckietown's 3D world, the X-coordinate corresponds to the tile's COLUMN index,
# and the Z-coordinate corresponds to the tile's ROW index.
FIXED_INITIAL_POSE = {
    'pos': np.array([ARM_END_TILES["Bottom"][1] * TILE_SIZE + TILE_SIZE/2, 0.0, ARM_END_TILES["Bottom"][0] * TILE_SIZE + TILE_SIZE/2]),
    'angle': math.pi / 2 # Face North (towards the intersection)
}


# ==============================================================================
# KEYBOARD EVENT HANDLERS
# Functions that respond to keyboard presses and releases.
# ==============================================================================

def on_key_press(symbol, modifiers):
    """
    Called by Pyglet when a keyboard key is pressed down.
    symbol: The key symbol (e.g., key.UP, key.ESCAPE).
    modifiers: Modifier keys (e.g., key.MOD_SHIFT).
    """
    keys_pressed[symbol] = True # Mark the key as currently pressed.

    # Handle ESCAPE key to exit the application.
    if symbol == key.ESCAPE:
        env.close() # Close the Duckietown simulator window.
        feedback_win.close() # Close the feedback window.
        app.exit() # Exit the Pyglet application loop.
    # Handle A, S, D keys to manually activate blinking feedback (for testing).
    elif symbol == key.A:
        feedback_win.activate_feedback(1, color=(1.0, 1.0, 1.0, 1.0)) # 1 blink, white.
    elif symbol == key.S:
        feedback_win.activate_feedback(2, color=(1.0, 1.0, 1.0, 1.0)) # 2 blinks, white.
    elif symbol == key.D:
        feedback_win.activate_feedback(3, color=(1.0, 1.0, 1.0, 1.0)) # 3 blinks, white.

def on_key_release(symbol, modifiers):
    """
    Called by Pyglet when a keyboard key is released.
    symbol: The key symbol.
    modifiers: Modifier keys.
    """
    keys_pressed[symbol] = False # Mark the key as released.


# ==============================================================================
# ENVIRONMENT SETUP
# Initializes the Duckietown simulator and sets up the windows.
# ==============================================================================

# Initialize the Duckietown Simulator environment.
env = Simulator(
    seed=123, # Random seed for reproducibility of the environment.
    map_name="plus_map", # The specific map to load.
    max_steps=500001, # Maximum number of simulation steps before an episode terminates.
    domain_rand=0, # Level of domain randomization (0 means no randomization).
    camera_width=640, # Width of the camera view.
    camera_height=480, # Height of the camera view.
    # CRITICAL MODIFICATION: Removed accept_start_angle_deg to prevent random angles.
    # This parameter explicitly allows random angles, which conflicts with our goal.
    # The default behavior without this parameter should be more deterministic if user_initial_angle is set.
    full_transparency=False, # Whether to use full transparency for objects.
    distortion=False, # Whether to apply camera distortion.
)

# Initial Fixed Pose Setup for the Simulator (for the very first launch)
# These parameters are read by env.reset() for the initial setup.
env.unwrapped.user_tile_start = ARM_END_TILES["Bottom"] # Sets the starting tile for the simulator's internal logic
env.unwrapped.user_initial_pose = FIXED_INITIAL_POSE['pos'] # Sets the exact 3D position
env.unwrapped.user_initial_angle = FIXED_INITIAL_POSE['angle'] # Sets the exact initial angle

# Reset the environment to its initial state using the newly set fixed pose.
env.reset()
# Render the initial state of the simulator to its window.
env.render() # This command creates the main simulator window.

# Create an instance of the FeedbackWindow.
feedback_win = FeedbackWindow(width=200, height=100, title='Duckiebot Feedback', 
                              feedback_duration=0.3, blink_interval=0.3)
# Position the feedback window next to the simulator window for convenience.
sim_x, sim_y = env.unwrapped.window.get_location() # Get simulator window's position.
feedback_win.set_location(sim_x + env.unwrapped.window.width + 20, sim_y) # Place feedback window to the right.

# Activate the simulator window to give it focus.
# This is crucial to ensure that keyboard inputs are directed to the driving window upon launch.
env.unwrapped.window.activate() 

# Push (register) the key event handlers to the SIMULATOR'S window.
# This makes the simulator window listen for keyboard input and call on_key_press/release.
env.unwrapped.window.push_handlers(on_key_press)
env.unwrapped.window.push_handlers(on_key_release)


# ==============================================================================
# MAIN UPDATE LOOP (Pyglet Scheduled Function)
# This function runs repeatedly to advance the simulation and handle game logic.
# ==============================================================================

def update(dt):
    """
    This function is called periodically by Pyglet's clock.
    It handles human input, steps the simulator, renders, and manages episode termination.
    """
    global action # Declare 'action' as global to modify it.
    
    # --- Human Driving Control ---
    # Initialize linear (forward/backward) and angular (turning) velocities.
    linear_vel = 0.0
    angular_vel = 0.0

    base_speed = 0.5 # Base speed for forward/backward movement.
    turn_rate = 0.2 # Base rate for turning in place or while moving.

    # Determine linear velocity based on UP/DOWN arrow key presses.
    if keys_pressed.get(key.UP, False) and not keys_pressed.get(key.DOWN, False):
        linear_vel = base_speed
    elif keys_pressed.get(key.DOWN, False) and not keys_pressed.get(key.UP, False):
        linear_vel = -base_speed
    # If both UP and DOWN are pressed, they cancel out, linear_vel remains 0.0.

    # Determine angular velocity based on LEFT/RIGHT arrow key presses.
    if keys_pressed.get(key.LEFT, False) and not keys_pressed.get(key.RIGHT, False):
        angular_vel = turn_rate # Positive angular_vel means turn left.
    elif keys_pressed.get(key.RIGHT, False) and not keys_pressed.get(key.LEFT, False):
        angular_vel = -turn_rate # Negative angular_vel means turn right.
    # If both LEFT and RIGHT are pressed, they cancel out, angular_vel remains 0.0.

    # Convert linear and angular velocities to left and right wheel velocities.
    # This is the action format expected by env.step().
    action = np.array([linear_vel - angular_vel, linear_vel + angular_vel])

    # --- Environment Step ---
    # Advance the simulator by one step using the calculated action.
    # obs: Observation from the environment (e.g., camera image).
    # reward: Reward received from the environment.
    # done: Boolean indicating if the episode has terminated.
    # info: Dictionary containing additional debugging information.
    obs, reward, done, info = env.step(action) 
    
    # Render the current state of the simulator to its window.
    env.render() 
    # Flip the window buffer to display the newly rendered frame.
    env.unwrapped.window.flip() 

    # MODIFIED SECTION: Episode Termination and Fixed Reset Handling
    # If the episode is finished (e.g., due to max_steps, crash, or reaching a target).
    if done:
        # DIAGNOSTIC PRINT: Show current tile and reason for termination
        print(f"Episode finished. Current tile: {info.get('tile', 'N/A')}, Reason: {info.get('reason', 'Unknown')}.")
        print("Resetting environment to fixed bottom arm...")
        
        # Explicitly set the initial pose parameters for the *next* reset.
        # These are the parameters that env.reset() reads.
        env.unwrapped.user_tile_start = ARM_END_TILES["Bottom"]
        env.unwrapped.user_initial_pose = FIXED_INITIAL_POSE['pos']
        env.unwrapped.user_initial_angle = FIXED_INITIAL_POSE['angle']
        
        # Perform the reset. This should clear the screen and place the Duckiebot correctly.
        env.reset() 

        # Render immediately after reset to ensure the display is refreshed.
        env.render()
        env.unwrapped.window.flip()
        
        # DIAGNOSTIC PRINT: Show Duckiebot's position and angle after reset
        print(f"Environment reset complete. Duckiebot's new pose: Pos={env.unwrapped.cur_pos}, Angle={env.unwrapped.cur_angle:.2f} radians.")
        print("Duckiebot should be at the bottom arm, facing north.")
    # END MODIFIED SECTION


# ==============================================================================
# PYGLET APPLICATION LOOP
# Starts the Pyglet event loop, which runs the scheduled update function
# and handles window events.
# ==============================================================================

# Schedule the 'update' function to run at a regular interval.
# The interval is determined by the simulator's frame rate (e.g., 30 times per second).
clock.schedule_interval(update, 1.0 / env.unwrapped.frame_rate)

# Run the Pyglet application loop. This starts all windows and event processing.
app.run()
