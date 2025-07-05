#!/usr/bin/env python3
import gym_duckietown
from gym_duckietown.simulator import Simulator
import numpy as np
import time
import random # For random state selection
import math   # For softmax exponentiation
from pyglet.window import key
from pyglet import app
from pyglet import clock
from pyglet import gl
import pyglet.window

print("Initializing Duckietown Simulator with Q-Learning Agent...")

# Global action variable for the Duckiebot (human control)
action = np.array([0.0, 0.0])

# Global dictionary to track pressed keys for human control
keys_pressed = {}

# --- Feedback Window Class (No Changes Here) ---
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
            
# --- Key press/release functions (Human Control) ---
def on_key_press(symbol, modifiers):
    keys_pressed[symbol] = True
    if symbol == key.ESCAPE:
        env.close()
        feedback_win.close() 
        app.exit()

def on_key_release(symbol, modifiers):
    keys_pressed[symbol] = False

# --- Q-Learning Agent Setup ---
NUM_STATES = 12 # As per your definition (0-11)
NUM_ACTIONS = 3 # Blink 1, Blink 2, Blink 3

Q_table = np.zeros((NUM_STATES, NUM_ACTIONS))

ALPHA = 0.1       # Learning rate
GAMMA = 0.99      # Discount factor
TEMPERATURE = 1.0 # Softmax temperature (higher = more exploration, lower = more exploitation)
                  # You'll want to decay this over time for better learning

NUM_EPISODES = 500 # Number of training episodes
current_episode = 0

# State tracking for Q-learning within an episode
current_agent_state = None      # The state (0-11) for the agent's decision in current episode
prev_agent_state = None         # State where agent took action
prev_agent_action = None        # Action agent took
signaled_this_episode = False   # Flag to ensure agent signals only once at intersection

# --- Map Definitions for Plus Map ---
# These are the coordinates for the ends of the four arms of the '+' map
ARM_END_TILES = {
    "Top": (0, 2),
    "Right": (2, 0),
    "Bottom": (0, -2),
    "Left": (-2, 0)
}
ALL_ARM_NAMES = list(ARM_END_TILES.keys())

# Map agent_state (0-11) to (start_arm_name, target_arm_name) for episode setup
STATE_ID_TO_EPISODE_GOAL = {}
current_state_id_counter = 0
for start_arm in ALL_ARM_NAMES:
    for target_arm in ALL_ARM_NAMES:
        if start_arm != target_arm: # Cannot start and end at the same arm
            STATE_ID_TO_EPISODE_GOAL[current_state_id_counter] = (start_arm, target_arm)
            current_state_id_counter += 1

assert current_state_id_counter == NUM_STATES, "Error: Mismatch in NUM_STATES and STATE_ID_TO_EPISODE_GOAL mapping."

# --- Softmax Action Selection Function ---
def softmax_action_selection(state, q_table, temperature):
    """
    Selects an action using softmax probabilities based on Q-values.
    """
    if temperature <= 0: # Avoid division by zero or negative temperature
        return np.argmax(q_table[state, :]) # Fallback to greedy if temp is zero or negative

    q_values = q_table[state, :]
    
    # Subtract max Q-value for numerical stability (prevents overflow with large exponents)
    # This doesn't change the probabilities
    max_q = np.max(q_values)
    exp_q = np.exp((q_values - max_q) / temperature)
    
    probabilities = exp_q / np.sum(exp_q)
    
    # Handle potential NaN if sum is zero (e.g., all Q-values are -inf)
    if np.sum(exp_q) == 0:
        probabilities = np.ones(NUM_ACTIONS) / NUM_ACTIONS # Uniform probability if all Qs are very low

    action_idx = np.random.choice(NUM_ACTIONS, p=probabilities)
    return action_idx

# --- Main Simulator Setup ---
env = Simulator(
    seed=123,
    map_name="plus_map",
    max_steps=500001,
    domain_rand=0,
    camera_width=640,
    camera_height=480,
    accept_start_angle_deg=360, # Allows random start angle for Duckiebot
    full_transparency=False,
    distortion=False,
)

env.reset() # Initial reset to create the window
env.render()

# Create the Feedback Window
feedback_win = FeedbackWindow(width=200, height=100, title='Duckiebot Feedback', 
                              feedback_duration=0.1, blink_interval=0.3)
# Position the feedback window next to the simulator window
sim_x, sim_y = env.unwrapped.window.get_location()
feedback_win.set_location(sim_x + env.unwrapped.window.width + 20, sim_y)

# Activate the simulator window to give it focus
env.unwrapped.window.activate() 

# Push key event handlers to the SIMULATOR'S window
env.unwrapped.window.push_handlers(on_key_press)
env.unwrapped.window.push_handlers(on_key_release)

# --- Update Function (Main Loop for Simulation and Q-Learning) ---
def update(dt):
    global action, current_episode, current_agent_state, prev_agent_state, prev_agent_action, signaled_this_episode, TEMPERATURE, Q_table
    
    # --- Human Driving Control ---
    linear_vel = 0.0
    angular_vel = 0.0
    base_speed = 0.5
    turn_rate = 0.2 

    if keys_pressed.get(key.UP, False) and not keys_pressed.get(key.DOWN, False):
        linear_vel = base_speed
    elif keys_pressed.get(key.DOWN, False) and not keys_pressed.get(key.UP, False):
        linear_vel = -base_speed
    if keys_pressed.get(key.LEFT, False) and not keys_pressed.get(key.RIGHT, False):
        angular_vel = turn_rate
    elif keys_pressed.get(key.RIGHT, False) and not keys_pressed.get(key.LEFT, False):
        angular_vel = -turn_rate
    action = np.array([linear_vel - angular_vel, linear_vel + angular_vel])

    # --- Environment Step ---
    obs, reward_env, done, info = env.step(action) 
    env.render() 
    env.unwrapped.window.flip() 

    # --- Q-Learning Logic within Episode ---
    if current_episode < NUM_EPISODES:
        # Episode Initialization / Reset
        if done or current_episode == 0: # If episode just finished or it's the very first run
            if current_episode > 0: # Don't print for initial reset
                # --- Reward Calculation and Q-Table Update for previous episode ---
                final_tile_coords = info['tile'] # Final tile where done=True
                
                # Get the expected target tile for the current episode's state
                # This needs to be derived from the 'current_agent_state' which was set at the start of the episode
                # STATE_ID_TO_EPISODE_GOAL[current_agent_state] gives (start_arm_name, target_arm_name)
                # Then use ARM_END_TILES to get the actual coordinates
                
                # Check if current_agent_state is valid (should be if episode ran)
                if current_agent_state is not None and current_agent_state != -1:
                    _, expected_target_arm_name = STATE_ID_TO_EPISODE_GOAL[current_agent_state]
                    expected_target_tile_coords = ARM_END_TILES[expected_target_arm_name]
                    
                    episode_reward = 0
                    if final_tile_coords == expected_target_tile_coords:
                        episode_reward = 10.0 # Positive reward for reaching correct endpoint
                        print(f"Episode {current_episode}: SUCCESS! Reached correct endpoint {expected_target_tile_coords}. Reward: {episode_reward:.1f}")
                    elif final_tile_coords in ARM_END_TILES.values(): # Reached an incorrect endpoint
                        episode_reward = -10.0 # Negative reward for reaching incorrect endpoint
                        print(f"Episode {current_episode}: FAILURE! Reached incorrect endpoint {final_tile_coords}. Correct was {expected_target_tile_coords}. Reward: {episode_reward:.1f}")
                    else: # Done due to timeout or other reason, not reaching an end tile
                        episode_reward = -5.0 # Penalty for not reaching a specific endpoint
                        print(f"Episode {current_episode}: TIMEOUT/OTHER. Final tile {final_tile_coords}. Reward: {episode_reward:.1f}")

                    # Q-learning update (if an action was taken in this episode)
                    if prev_agent_state is not None and prev_agent_action is not None:
                        # For terminal states, next_Q is 0.
                        next_Q_max = 0 
                        
                        old_q_value = Q_table[prev_agent_state, prev_agent_action]
                        Q_table[prev_agent_state, prev_agent_action] = old_q_value + ALPHA * (episode_reward + GAMMA * next_Q_max - old_q_value)
                        
                        print(f"Q-Update: State {prev_agent_state}, Action {prev_agent_action}, Old Q: {old_q_value:.2f}, New Q: {Q_table[prev_agent_state, prev_agent_action]:.2f}")
                        print(f"Q-Table row for state {prev_agent_state}: {np.round(Q_table[prev_agent_state, :], 2)}")
                else:
                    print(f"Episode {current_episode}: No valid agent state for reward calculation.")

            # --- Start New Episode ---
            current_episode += 1
            if current_episode > NUM_EPISODES:
                print("\n--- Training complete! ---")
                print("Final Q-Table:")
                print(np.round(Q_table, 2))
                # Optionally save Q-table to a file
                # np.save('q_table.npy', Q_table)
                app.exit() # Exit the app after training

            # Randomly select a new agent state (0-11) for the next episode
            current_agent_state = random.randint(0, NUM_STATES - 1)
            
            # Get the corresponding initial and target tiles for the environment
            start_arm_name, target_arm_name = STATE_ID_TO_EPISODE_GOAL[current_agent_state]
            initial_tile_coords = ARM_END_TILES[start_arm_name]
            target_tile_coords = ARM_END_TILES[target_arm_name]
            
            print(f"\n--- Starting Episode {current_episode}/{NUM_EPISODES} ---")
            print(f"Agent State: {current_agent_state} (Goal: Drive from {start_arm_name} to {target_arm_name})")
            
            # Reset environment with new initial and target tiles
            env.reset(options={'initial_tile': initial_tile_coords, 'target_tile': target_tile_coords})
            
            # Reset Q-learning state for new episode
            signaled_this_episode = False
            prev_agent_state = None
            prev_agent_action = None
            # Optionally decay temperature here for exploration-exploitation trade-off
            # TEMPERATURE = max(0.1, TEMPERATURE * 0.99) 
            # Or use a schedule: TEMPERATURE = initial_temp * (1 - current_episode / NUM_EPISODES)


        # --- Agent Decision Point (at central intersection) ---
        current_duckiebot_tile = info['tile']
        
        # Check if the Duckiebot is at the central intersection (0,0) and agent hasn't signaled yet
        if current_duckiebot_tile == (0,0) and not signaled_this_episode:
            # Agent chooses an action (blink signal) based on the current_agent_state
            chosen_action_idx = softmax_action_selection(current_agent_state, Q_table, TEMPERATURE)
            
            # Execute the blink action (action_idx 0->1 blink, 1->2 blinks, 2->3 blinks)
            feedback_win.activate_feedback(chosen_action_idx + 1, color=(1.0, 1.0, 1.0, 1.0))
            
            # Store for Q-learning update at episode end
            prev_agent_state = current_agent_state
            prev_agent_action = chosen_action_idx
            signaled_this_episode = True # Mark that agent has signaled for this episode
            print(f"Agent signaled: {chosen_action_idx + 1} blinks for state {current_agent_state}")

# Schedule the update function to run at a regular interval
clock.schedule_interval(update, 1.0 / env.unwrapped.frame_rate)

# Run the Pyglet application loop (manages both windows)
app.run()
