import gym_duckietown
from gym_duckietown.simulator import Simulator
import gym

print("gym_duckietown imported successfully!")

try:
    # Try to create a basic simulator environment
    env = Simulator(
        seed=123,
        map_name="loop_empty", # A simple, empty loop map
        max_steps=500001,
        domain_rand=0,
        camera_width=640,
        camera_height=480,
        accept_start_angle_deg=4,
    )
    print("Duckietown simulator environment created successfully!")
    env.close() # Close the environment
    print("Environment closed.")
except Exception as e:
    print(f"Error creating Duckietown simulator environment: {e}")

# Try a standard gym.make for a registered environment (though Simulator is more direct)
try:
    env_gym = gym.make("Duckietown-small_loop-v0")
    print("Registered Gym environment 'Duckietown-small_loop-v0' created successfully!")
    env_gym.close()
    print("Registered environment closed.")
except Exception as e:
    print(f"Error creating registered Gym environment: {e}")
    