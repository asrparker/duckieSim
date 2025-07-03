#!/usr/bin/env python3
import gym_duckietown
from gym_duckietown.simulator import Simulator
import time
from pyglet.window import key
from pyglet import app

print("Initializing Duckietown Simulator...")

# Instantiate the Simulator with your chosen parameters
env = Simulator(
    seed=123,
    map_name="plus_map", # Using map_name as the file is now in the default search path
    max_steps=500001,
    domain_rand=0,
    camera_width=640,
    camera_height=480,
    accept_start_angle_deg=4,
    full_transparency=True,
    distortion=False,
)

# Basic control for the Duckiebot
@env.unwrapped.window.event
def on_key_press(symbol, modifiers):
    if symbol == key.ESCAPE:
        env.close()
        app.exit()
    elif symbol == key.UP:
        env.set_right_wheel_velocity(1.0)
        env.set_left_wheel_velocity(1.0)
    elif symbol == key.DOWN:
        env.set_right_wheel_velocity(-1.0)
        env.set_left_wheel_velocity(-1.0)
    elif symbol == key.LEFT:
        env.set_right_wheel_velocity(1.0)
        env.set_left_wheel_velocity(0.0)
    elif symbol == key.RIGHT:
        env.set_right_velocity(0.0) # Corrected to set_right_wheel_velocity
        env.set_left_wheel_velocity(1.0)

@env.unwrapped.window.event
def on_key_release(symbol, modifiers):
    if symbol == key.UP or symbol == key.DOWN or \
       symbol == key.LEFT or symbol == key.RIGHT:
        env.set_right_wheel_velocity(0.0)
        env.set_left_wheel_velocity(0.0)

# Run the simulation
env.reset()
env.render()
app.run()
