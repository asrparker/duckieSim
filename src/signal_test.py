#!/usr/bin/env python3
import gym_duckietown
from gym_duckietown.simulator import Simulator
import numpy as np
import time
from pyglet.window import key
from pyglet import app
from pyglet import clock
from pyglet import gl
import pyglet.window

print("Initializing Duckietown Simulator...")

# Global action variable for the Duckiebot
action = np.array([0.0, 0.0])

# --- NEW: Global dictionary to track pressed keys ---
keys_pressed = {} # Stores {key_symbol: True/False}
# --- END NEW ---

# --- Feedback Window Class ---
class FeedbackWindow(pyglet.window.Window):
    def __init__(self, width, height, title='Feedback', feedback_duration=0.1, blink_interval=0.3):
        super().__init__(width, height, caption=title, resizable=False)
        self.feedback_active = False
        self.feedback_duration = feedback_duration # Duration of each individual blink (on-time)
        self.blink_interval = blink_interval     # Pause duration between blinks (off-time)

        self.current_blink_number = 0 # Which blink in the sequence we are currently trying to display (1-indexed)
        self.total_blinks_requested = 0 # Total number of blinks for the current sequence
        self.last_state_change_time = 0.0 # Time when the current blink/pause state began
        self.is_blinking_on_state = False # True if currently drawing the rectangle, False if in a pause

        self.set_location(100, 100) # Initial position for the feedback window

        # Calculate dimensions for the rectangle within this new window
        self.rect_width = self.width * 0.8
        self.rect_height = self.height * 0.8
        self.rect_x = (self.width - self.rect_width) / 2
        self.rect_y = (self.height - self.rect_height) / 2
        
        self.feedback_color = (1.0, 1.0, 1.0, 1.0) # Default to White (RGBA)

    def activate_feedback(self, num_blinks, color=(1.0, 1.0, 1.0, 1.0)):
        """
        Method to be called by the main script to start the blink sequence.
        num_blinks: how many times to blink.
        color: RGB or RGBA tuple for the blink color.
        """
        self.feedback_active = True
        self.total_blinks_requested = num_blinks
        self.feedback_color = color
        
        # Start the first blink immediately
        self.current_blink_number = 1
        self.is_blinking_on_state = True
        self.last_state_change_time = time.time()


    def on_draw(self):
        """Drawing logic for the feedback window."""
        self.clear() # Clear this window's content
        current_time = time.time()

        if not self.feedback_active:
            return # No feedback sequence is active

        # Calculate time elapsed in the current state (on or off)
        time_in_current_state = current_time - self.last_state_change_time

        if self.is_blinking_on_state: # We are in the "ON" state (drawing the rectangle)
            if time_in_current_state < self.feedback_duration:
                # Still within the ON duration, so draw it
                gl.glMatrixMode(gl.GL_PROJECTION)
                gl.glLoadIdentity()
                gl.glOrtho(0, self.width, 0, self.height, -1, 1)

                gl.glMatrixMode(gl.GL_MODELVIEW)
                gl.glLoadIdentity()

                gl.glDisable(gl.GL_DEPTH_TEST) 
                gl.glEnable(gl.GL_BLEND)
                gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

                gl.glColor4f(*self.feedback_color) 

                gl.glBegin(gl.GL_QUADS)
                gl.glVertex2f(self.rect_x, self.rect_y)
                gl.glVertex2f(self.rect_x + self.rect_width, self.rect_y)
                gl.glVertex2f(self.rect_x + self.rect_width, self.rect_y + self.rect_height)
                gl.glVertex2f(self.rect_x, self.rect_y + self.rect_height)
                gl.glEnd()

                gl.glDisable(gl.GL_BLEND)
                gl.glEnable(gl.GL_DEPTH_TEST) 
            else:
                # ON duration has passed, transition to OFF state
                if self.current_blink_number < self.total_blinks_requested:
                    # More blinks to go, so go into a pause (OFF state)
                    self.is_blinking_on_state = False
                    self.last_state_change_time = current_time
                else:
                    # All blinks completed, end the sequence
                    self.feedback_active = False

        else: # self.is_blinking_on_state is False, meaning we are in the "OFF" (pause) state
            if time_in_current_state < self.blink_interval:
                # Still within the OFF duration, so do nothing (don't draw)
                pass
            else:
                # OFF duration has passed, transition to ON state for the next blink
                self.current_blink_number += 1
                self.is_blinking_on_state = True
                self.last_state_change_time = current_time
            
# --- Key press/release functions ---
def on_key_press(symbol, modifiers):
    # Store the key as pressed
    keys_pressed[symbol] = True

    # --- Existing ESCAPE and Feedback Blink Controls (A, S, D keys) ---
    if symbol == key.ESCAPE:
        env.close()
        feedback_win.close() 
        app.exit()
    elif symbol == key.A:
        feedback_win.activate_feedback(1, color=(1.0, 1.0, 1.0, 1.0)) # 1 blink, white
    elif symbol == key.S:
        feedback_win.activate_feedback(2, color=(1.0, 1.0, 1.0, 1.0)) # 2 blinks, white
    elif symbol == key.D:
        feedback_win.activate_feedback(3, color=(1.0, 1.0, 1.0, 1.0)) # 3 blinks, white

def on_key_release(symbol, modifiers):
    # Mark the key as released
    keys_pressed[symbol] = False

# --- Main Simulator Setup ---
env = Simulator(
    seed=123,
    map_name="plus_map",
    max_steps=500001,
    domain_rand=0,
    camera_width=640,
    camera_height=480,
    accept_start_angle_deg=360,
    full_transparency=False,
    distortion=False,
)

env.reset()
env.render() # This creates the simulator's window

# --- Create the Feedback Window ---
feedback_win = FeedbackWindow(width=200, height=100, title='Duckiebot Feedback', 
                              feedback_duration=0.1, blink_interval=0.3)
# Position the feedback window next to the simulator window
sim_x, sim_y = env.unwrapped.window.get_location()
feedback_win.set_location(sim_x + env.unwrapped.window.width + 20, sim_y)

# --- Activate the simulator window to give it focus ---
env.unwrapped.window.activate() 

# Push key event handlers to the SIMULATOR'S window
env.unwrapped.window.push_handlers(on_key_press)
env.unwrapped.window.push_handlers(on_key_release)

# Define an update function that pyglet will call periodically (for simulation steps)
def update(dt):
    global action
    
    # --- NEW: Calculate action based on currently pressed keys ---
    linear_vel = 0.0
    angular_vel = 0.0

    base_speed = 0.5
    turn_rate = 0.2 # For turning in place or while moving

    # Determine linear velocity
    if keys_pressed.get(key.UP, False) and not keys_pressed.get(key.DOWN, False):
        linear_vel = base_speed
    elif keys_pressed.get(key.DOWN, False) and not keys_pressed.get(key.UP, False):
        linear_vel = -base_speed
    # If both UP and DOWN are pressed, they cancel out, linear_vel remains 0.0

    # Determine angular velocity
    if keys_pressed.get(key.LEFT, False) and not keys_pressed.get(key.RIGHT, False):
        angular_vel = turn_rate # Positive angular_vel means turn left
    elif keys_pressed.get(key.RIGHT, False) and not keys_pressed.get(key.LEFT, False):
        angular_vel = -turn_rate # Negative angular_vel means turn right
    # If both LEFT and RIGHT are pressed, they cancel out, angular_vel remains 0.0

    # Convert linear and angular velocities to left and right wheel velocities
    # left_wheel_velocity = linear_velocity - angular_velocity
    # right_wheel_velocity = linear_velocity + angular_velocity
    action = np.array([linear_vel - angular_vel, linear_vel + angular_vel])
    # --- END NEW Action Calculation ---

    obs, reward, done, info = env.step(action) 
    env.render() 
    env.unwrapped.window.flip() 

    if done:
        print("Episode finished. Resetting environment...")
        env.reset()

# Schedule the update function to run at a regular interval
clock.schedule_interval(update, 1.0 / env.unwrapped.frame_rate)

# Run the Pyglet application loop (manages both windows)
app.run()
