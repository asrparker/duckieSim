#!/usr/bin/env python3
import gym_duckietown
from gym_duckietown.simulator import Simulator
import numpy as np
import time
from pyglet.window import key
from pyglet import app
from pyglet import clock

print("Initializing Duckietown Simulator...")

# Global action variable: [linear_velocity, angular_velocity]
action = np.array([0.0, 0.0])

def on_key_press(symbol, modifiers):
    global action
    if symbol == key.ESCAPE:
        env.close()
        app.exit()
    elif symbol == key.UP:
        action = np.array([1.0, 0.0])
    elif symbol == key.DOWN:
        action = np.array([-1.0, 0.0])
    elif symbol == key.LEFT:
        action = np.array([0.5, 1.0])
    elif symbol == key.RIGHT:
        action = np.array([0.5, -1.0])

def on_key_release(symbol, modifiers):
    global action
    if symbol == key.UP or symbol == key.DOWN or \
       symbol == key.LEFT or symbol == key.RIGHT:
        action = np.array([0.0, 0.0])

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
env.render()

env.unwrapped.window.push_handlers(on_key_press)
env.unwrapped.window.push_handlers(on_key_release)

# Define an update function that pyglet will call periodically
def update(dt):
    global action
    # Corrected unpacking for older Gym API (4 values)
    obs, reward, done, info = env.step(action) # <--- THIS LINE IS CORRECTED
    
    env.render()

    # Check for episode termination using the 'done' flag
    if done: # <--- THIS LINE IS CORRECTED
        print("Episode finished. Resetting environment...")
        env.reset()

# Schedule the update function to run at a regular interval
clock.schedule_interval(update, 1.0 / env.unwrapped.frame_rate)

# Run the Pyglet application loop
app.run()
