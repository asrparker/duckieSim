#!/usr/bin/env python3
import gym_duckietown
from gym_duckietown.simulator import Simulator
import time
from pyglet.window import key
from pyglet import app

print("Initializing Duckietown Simulator...")

# Define the key press/release functions WITHOUT the decorators initially
# These functions will be registered as event handlers later
def on_key_press(symbol, modifiers):
    if symbol == key.ESCAPE:
        env.close()
        app.exit()
    elif symbol == key.UP:
        env.robot.set_right_wheel_velocity(1.0) # CORRECTED LINE
        env.robot.set_left_wheel_velocity(1.0)  # CORRECTED LINE
    elif symbol == key.DOWN:
        env.robot.set_right_wheel_velocity(-1.0) # CORRECTED LINE
        env.robot.set_left_wheel_velocity(-1.0)  # CORRECTED LINE
    elif symbol == key.LEFT:
        env.robot.set_right_wheel_velocity(1.0) # CORRECTED LINE
        env.robot.set_left_wheel_velocity(0.0)  # CORRECTED LINE
    elif symbol == key.RIGHT:
        env.robot.set_right_wheel_velocity(0.0) # CORRECTED LINE
        env.robot.set_left_wheel_velocity(1.0)  # CORRECTED LINE

def on_key_release(symbol, modifiers):
    if symbol == key.UP or symbol == key.DOWN or \
       symbol == key.LEFT or symbol == key.RIGHT:
        env.robot.set_right_wheel_velocity(0.0) # CORRECTED LINE
        env.robot.set_left_wheel_velocity(0.0)  # CORRECTED LINE

# Instantiate the Simulator with your chosen parameters
env = Simulator(
    seed=123,
    map_name="plus_map",
    max_steps=500001,
    domain_rand=0,
    camera_width=640,
    camera_height=480,
    accept_start_angle_deg=4,
    full_transparency=True,
    distortion=False,
)

# Reset and render the environment to create the window
env.reset()
env.render() # <-- The window is created here

# NOW, push the handlers to the window's event stack
env.unwrapped.window.push_handlers(on_key_press)
env.unwrapped.window.push_handlers(on_key_release)

# Run the simulation
app.run()
