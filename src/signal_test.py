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

# --- Feedback Window Class ---
class FeedbackWindow(pyglet.window.Window):
    def __init__(self, width, height, title='Feedback', feedback_duration=0.1, blink_interval=0.3):
        super().__init__(width, height, caption=title, resizable=False)
        self.feedback_active = False
        self.feedback_start_time = 0.0
        self.feedback_duration = feedback_duration # Duration of each individual blink (on-time)
        self.blink_interval = blink_interval     # Pause duration between blinks (off-time)

        self.current_blink_count = 0 # How many blinks have been completed so far
        self.total_blinks_requested = 0 # Total number of blinks for the current sequence
        self.next_state_change_time = 0.0 # When the current blink/pause should end

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
        self.current_blink_count = 0 # Reset count for new sequence
        self.total_blinks_requested = num_blinks
        self.feedback_color = color
        
        # Immediately start the first blink
        self.next_state_change_time = time.time() + self.feedback_duration 
        # The first blink is "on" immediately, and will turn off after feedback_duration
        
        # Increment current_blink_count to mark that the first blink has started
        self.current_blink_count = 1


    def on_draw(self):
        """Drawing logic for the feedback window."""
        self.clear() # Clear this window's content
        current_time = time.time()

        if not self.feedback_active:
            return # No feedback sequence is active

        # If we are currently displaying a blink (rectangle is ON)
        if self.current_blink_count > 0 and current_time < self.next_state_change_time:
            # Draw the rectangle
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
        
        # If we are NOT currently displaying a blink (rectangle is OFF or blink just ended)
        else:
            # Check if it's time to transition to the next state (either start next blink or end sequence)
            if current_time >= self.next_state_change_time:
                # If there are more blinks left to do
                if self.current_blink_count < self.total_blinks_requested:
                    # Start the next blink (transition from OFF to ON)
                    self.current_blink_count += 1
                    self.next_state_change_time = current_time + self.feedback_duration
                    # No drawing here, it will be drawn in the next on_draw call when current_time < next_state_change_time
                # If all blinks have been displayed
                else:
                    self.feedback_active = False # End the entire feedback sequence
            # Else (current_time < self.next_state_change_time), we are in the "off" (pause) period between blinks
            # So, do nothing (don't draw)
            
# --- Key press/release functions ---
def on_key_press(symbol, modifiers):
    global action
    if symbol == key.ESCAPE:
        env.close()
        feedback_win.close() 
        app.exit()
    # --- Duckiebot Driving Controls (Arrow Keys) ---
    elif symbol == key.UP:
        action = np.array([0.5, 0.5])
    elif symbol == key.DOWN:
        action = np.array([-0.5, -0.5])
    elif symbol == key.LEFT:
        action = np.array([-0.2, 0.2])
    elif symbol == key.RIGHT:
        action = np.array([0.2, -0.2])
    # --- Feedback Blink Controls (A, S, D keys) ---
    elif symbol == key.A:
        feedback_win.activate_feedback(1, color=(1.0, 1.0, 1.0, 1.0)) # 1 blink, white
    elif symbol == key.S:
        feedback_win.activate_feedback(2, color=(1.0, 1.0, 1.0, 1.0)) # 2 blinks, white
    elif symbol == key.D:
        feedback_win.activate_feedback(3, color=(1.0, 1.0, 1.0, 1.0)) # 3 blinks, white

def on_key_release(symbol, modifiers):
    global action
    if symbol == key.UP or symbol == key.DOWN or \
       symbol == key.LEFT or symbol == key.RIGHT:
        action = np.array([0.0, 0.0])


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


# Push key event handlers to the SIMULATOR'S window
env.unwrapped.window.push_handlers(on_key_press)
env.unwrapped.window.push_handlers(on_key_release)

# Define an update function that pyglet will call periodically (for simulation steps)
def update(dt):
    global action
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
