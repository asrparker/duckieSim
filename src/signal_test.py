#!/usr/bin/env python3
import gym_duckietown
from gym_duckietown.simulator import Simulator
import numpy as np
import time
from pyglet.window import key
from pyglet import app
from pyglet import clock
from pyglet import gl
import pyglet.window # Explicitly importing pyglet.window for clarity

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


# ==============================================================================
# WINDOW CLASSES
# These classes define the custom Pyglet windows used in the application.
# ==============================================================================

# --- Feedback Window Class ---
# This class creates a separate Pyglet window to display blinking signals.
class FeedbackWindow(pyglet.window.Window):
    def __init__(self, width, height, title='Feedback', feedback_duration=0.1, blink_interval=0.3):
        # Initialize the Pyglet window with specified dimensions and title.
        super().__init__(width, height, caption=title, resizable=False)
        
        # State variables for managing the blinking feedback.
        self.feedback_active = False # True if a blink sequence is currently running.
        self.feedback_duration = feedback_duration # Duration (in seconds) that the rectangle is visible (ON state).
        self.blink_interval = blink_interval     # Duration (in seconds) that the rectangle is hidden (OFF state/pause).

        self.current_blink_number = 0 # Tracks which blink in the sequence is currently being displayed (1-indexed).
        self.total_blinks_requested = 0 # Total number of blinks requested for the current sequence.
        self.last_state_change_time = 0.0 # Timestamp when the current blink/pause state began.
        self.is_blinking_on_state = False # True if currently drawing the rectangle, False if in a pause.

        # Set the initial position of the feedback window on the screen.
        self.set_location(100, 100)

        # Calculate dimensions for the blinking rectangle to fit within this window.
        self.rect_width = self.width * 0.8
        self.rect_height = self.height * 0.8
        self.rect_x = (self.width - self.rect_width) / 2
        self.rect_y = (self.height - self.rect_height) / 2
        
        self.feedback_color = (1.0, 1.0, 1.0, 1.0) # Default color for the blinking rectangle (White RGBA).

    def activate_feedback(self, num_blinks, color=(1.0, 1.0, 1.0, 1.0)):
        """
        Method to be called by the main script to start a new blink sequence.
        num_blinks: The total number of times the rectangle should blink.
        color: The RGB or RGBA tuple for the blink color.
        """
        self.feedback_active = True # Activate the feedback sequence.
        self.total_blinks_requested = num_blinks # Set the total number of blinks.
        self.feedback_color = color # Set the color for the current sequence.
        
        # Start the first blink immediately.
        self.current_blink_number = 1
        self.is_blinking_on_state = True
        self.last_state_change_time = time.time() # Record the start time of this first blink.

    def on_draw(self):
        """
        Pyglet's drawing event handler for this window.
        This method is automatically called by Pyglet whenever the window needs to be redrawn.
        It manages the blinking logic based on elapsed time.
        """
        self.clear() # Clear this window's content before drawing.
        current_time = time.time() # Get the current time.

        if not self.feedback_active:
            return # If no feedback sequence is active, do nothing.

        # Calculate how long we've been in the current ON or OFF state.
        time_in_current_state = current_time - self.last_state_change_time

        if self.is_blinking_on_state: # If currently in the "ON" state (drawing the rectangle).
            if time_in_current_state < self.feedback_duration:
                # Still within the ON duration, so draw the rectangle.
                gl.glMatrixMode(gl.GL_PROJECTION)
                gl.glLoadIdentity()
                gl.glOrtho(0, self.width, 0, self.height, -1, 1)

                gl.glMatrixMode(gl.GL_MODELVIEW)
                gl.glLoadIdentity()

                gl.glDisable(gl.GL_DEPTH_TEST) # Disable depth testing for 2D drawing.
                gl.glEnable(gl.GL_BLEND) # Enable blending for transparency (RGBA colors).
                gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA) # Standard alpha blending.

                gl.glColor4f(*self.feedback_color) # Set the color for the rectangle.

                # Draw a filled rectangle using GL_QUADS (four vertices).
                gl.glBegin(gl.GL_QUADS)
                gl.glVertex2f(self.rect_x, self.rect_y)
                gl.glVertex2f(self.rect_x + self.rect_width, self.rect_y)
                gl.glVertex2f(self.rect_x + self.rect_width, self.rect_y + self.rect_height)
                gl.glVertex2f(self.rect_x, self.rect_y + self.rect_height)
                gl.glEnd()

                gl.glDisable(gl.GL_BLEND) # Disable blending after drawing.
                gl.glEnable(gl.GL_DEPTH_TEST) # Re-enable depth testing.
            else:
                # ON duration has passed, transition to OFF state (pause).
                if self.current_blink_number < self.total_blinks_requested:
                    # If more blinks are needed, go into a pause (OFF state).
                    self.is_blinking_on_state = False
                    self.last_state_change_time = current_time # Record start time of pause.
                else:
                    # All blinks completed, end the sequence.
                    self.feedback_active = False

        else: # Currently in the "OFF" state (pause, not drawing).
            if time_in_current_state < self.blink_interval:
                # Still within the OFF duration, so do nothing (don't draw anything).
                pass
            else:
                # OFF duration has passed, transition to ON state for the next blink.
                self.current_blink_number += 1
                self.is_blinking_on_state = True
                self.last_state_change_time = current_time # Record start time of next blink.


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
    accept_start_angle_deg=360, # Allows Duckiebot to start at any angle (randomly chosen).
    full_transparency=False, # Whether to use full transparency for objects.
    distortion=False, # Whether to apply camera distortion.
)

# Reset the environment to its initial state.
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

    # --- Episode Termination Handling ---
    # If the episode is finished (e.g., due to max_steps, crash, or reaching a target).
    if done:
        print("Episode finished. Resetting environment...")
        env.reset() # Reset the environment to its initial state for a new episode.


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
