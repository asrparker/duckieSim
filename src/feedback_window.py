import pyglet
import time

class FeedbackWindow(pyglet.window.Window):
    """
    A Pyglet window to display visual feedback (blinking or solid color).

    It can display a blinking rectangle for specific feedback IDs (num_blinks 1, 2, 3)
    or a solid colored rectangle for a continuous signal (num_blinks 0).
    """
    def __init__(self, width, height, title, feedback_duration, blink_interval):
        """
        Initializes the FeedbackWindow.

        Args:
            width (int): The width of the feedback window.
            height (int): The height of the feedback window.
            title (str): The title of the feedback window.
            feedback_duration (float): How long a blinking feedback (for num_blinks > 0)
                                       should remain active in seconds.
            blink_interval (float): The interval (in seconds) at which the blinking
                                    rectangle toggles visibility.
        """
        super().__init__(width, height, title)
        self.feedback_duration = feedback_duration
        self.blink_interval = blink_interval
        self.active_num_blinks = None  # Stores the currently active feedback ID (0, 1, 2, or 3)
        self.feedback_start_time = 0   # Timestamp when the current feedback started
        self.blink_state = True        # True for visible, False for hidden during blinking
        self.last_blink_toggle_time = 0 # Timestamp of the last blink state toggle
        self.feedback_color = (1.0, 1.0, 1.0, 1.0) # Default color (RGBA: white)

        # Flag to indicate if solid color mode is active (when num_blinks is 0)
        self.is_solid_color_mode = False 

    def activate_feedback(self, num_blinks, color=(1.0, 1.0, 1.0, 1.0)):
        # If num_blinks is None, deactivate feedback
        if num_blinks is None:
            self.active_num_blinks = None
            self.is_solid_color_mode = False
            return # Exit the function, no need to set other properties

        self.active_num_blinks = num_blinks
        self.feedback_start_time = time.time()
        self.feedback_color = color
        self.blink_state = True 
        self.last_blink_toggle_time = time.time()

        if num_blinks == 0:
            self.is_solid_color_mode = True
        else:
            self.is_solid_color_mode = False 

    def on_draw(self):
        """
        Pyglet's drawing event handler. Clears the window and draws the feedback.
        """
        self.clear() # Clear the window content

        if self.active_num_blinks is not None:
            current_time = time.time()

            if self.is_solid_color_mode:
                # If in solid color mode (num_blinks = 0), always draw the rectangle
                pyglet.gl.glColor4f(*self.feedback_color)
                pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                                     ('v2f', (0, 0, self.width, 0, self.width, self.height, 0, self.height)))
            else:
                # Logic for blinking feedback (num_blinks 1, 2, 3)
                # Check if the feedback duration has passed
                if current_time - self.feedback_start_time < self.feedback_duration:
                    # Toggle blink state if blink_interval has passed
                    if current_time - self.last_blink_toggle_time > self.blink_interval:
                        self.blink_state = not self.blink_state
                        self.last_blink_toggle_time = current_time

                    # Draw the rectangle only if blink_state is True (visible)
                    if self.blink_state:
                        pyglet.gl.glColor4f(*self.feedback_color)
                        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                                             ('v2f', (0, 0, self.width, 0, self.width, self.height, 0, self.height)))
                else:
                    # If duration passed for blinking IDs, deactivate the feedback
                    self.active_num_blinks = None 

    def close(self):
        """
        Closes the feedback window.
        """
        super().close()

