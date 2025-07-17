# feedback_window.py

import pyglet
from pyglet import gl
import time

class FeedbackWindow(pyglet.window.Window):
    """
    A Pyglet window dedicated to displaying blinking or solid visual feedback.

    - If activate_feedback(0, color) is called, it displays a solid color continuously.
    - If activate_feedback(None) is called, it turns off any active feedback.
    - If activate_feedback(N, color) where N > 0, it blinks N times (light turns ON N times).
    """
    def __init__(self, width, height, title='Feedback', feedback_duration=0.2, blink_interval=0.2):
        """
        Initializes the FeedbackWindow.

        Args:
            width (int): The width of the feedback window.
            height (int): The height of the feedback window.
            title (str): The title of the feedback window.
            feedback_duration (float): The duration (in seconds) for which the light stays ON
                                       during a single blink cycle. (0.2s as per your original).
            blink_interval (float): The duration (in seconds) for which the light stays OFF
                                    during a single blink cycle. (0.2s as per your original).
        """
        super().__init__(width, height, caption=title, resizable=False)
        
        self.feedback_active = False        # Overall flag: True if any feedback is active (solid or blinking)
        self.feedback_duration = feedback_duration # Duration light is ON for a blink
        self.blink_interval = blink_interval     # Duration light is OFF for a blink

        self.current_blink_number = 0       # Counts how many times the light has turned ON
        self.total_blinks_requested = 0     # The target number of ON states for blinking
        self.last_state_change_time = 0.0   # Timestamp of the last ON/OFF state change
        self.is_blinking_on_state = False   # True if the light should currently be ON (for blinking)

        self.is_solid_on_mode = False       # NEW: True if solid color mode is active (num_blinks = 0)
        
        self.set_location(100, 100) # Default window position

        self.rect_width = self.width * 0.8
        self.rect_height = self.height * 0.8
        self.rect_x = (self.width - self.rect_width) / 2
        self.rect_y = (self.height - self.rect_height) / 2
        
        self.feedback_color = (1.0, 1.0, 1.0, 1.0) # Default color (white)

    def activate_feedback(self, num_blinks, color=(1.0, 1.0, 1.0, 1.0)):
        """
        Activates or deactivates visual feedback.

        Args:
            num_blinks (int or None):
                - None: Deactivates any active feedback (turns off).
                - 0: Activates a continuous solid color.
                - > 0: Activates blinking for this many "ON" cycles.
            color (tuple): RGBA tuple (0.0-1.0) for the feedback color.
        """
        if num_blinks is None:
            # Case 1: Deactivate all feedback
            self.feedback_active = False
            self.is_solid_on_mode = False
            self.current_blink_number = 0
            self.is_blinking_on_state = False # Ensure light is off
            return

        # Common setup for activating any feedback
        self.feedback_active = True
        self.feedback_color = color
        
        if num_blinks == 0:
            # Case 2: Activate solid color mode
            self.is_solid_on_mode = True
            self.total_blinks_requested = 0 # Not relevant for solid mode
            self.current_blink_number = 0
            self.is_blinking_on_state = True # Solid color is always "on"
        else:
            # Case 3: Activate blinking mode (num_blinks > 0)
            self.is_solid_on_mode = False
            # If a new blinking sequence is requested, reset blink counter and state
            if num_blinks != self.total_blinks_requested: # Only reset if different blink count requested
                self.current_blink_number = 0 # Reset count for new sequence
                self.is_blinking_on_state = True # Always start a new blink sequence with light ON
                self.last_state_change_time = time.time() # Reset timer for new sequence
            
            self.total_blinks_requested = num_blinks


    def on_draw(self):
        """
        Pyglet's drawing event handler for this window.
        Handles drawing the rectangle based on the active feedback mode.
        """
        self.clear() # Clear the window content

        if not self.feedback_active:
            return # Nothing to draw if feedback is not active

        current_time = time.time()

        if self.is_solid_on_mode:
            # Draw solid color if in solid mode
            gl.glColor4f(*self.feedback_color)
            gl.glBegin(gl.GL_QUADS)
            gl.glVertex2f(self.rect_x, self.rect_y)
            gl.glVertex2f(self.rect_x + self.rect_width, self.rect_y)
            gl.glVertex2f(self.rect_x + self.rect_width, self.rect_y + self.rect_height)
            gl.glVertex2f(self.rect_x, self.rect_y + self.rect_height)
            gl.glEnd()
        else:
            # Blinking logic for num_blinks > 0
            time_since_last_change = current_time - self.last_state_change_time

            if self.is_blinking_on_state:
                # Light is currently ON
                if time_since_last_change < self.feedback_duration:
                    # Still in the ON phase, so draw it
                    gl.glColor4f(*self.feedback_color)
                    gl.glBegin(gl.GL_QUADS)
                    gl.glVertex2f(self.rect_x, self.rect_y)
                    gl.glVertex2f(self.rect_x + self.rect_width, self.rect_y)
                    gl.glVertex2f(self.rect_x + self.rect_width, self.rect_y + self.rect_height)
                    gl.glVertex2f(self.rect_x, self.rect_y + self.rect_height)
                    gl.glEnd()
                else:
                    # ON phase ended. Check if more blinks are needed.
                    self.current_blink_number += 1 # Increment blink count (light just completed an ON cycle)
                    if self.current_blink_number < self.total_blinks_requested:
                        # More blinks needed, switch to OFF state
                        self.is_blinking_on_state = False
                        self.last_state_change_time = current_time
                    else:
                        # All blinks completed, deactivate feedback
                        self.feedback_active = False
                        self.current_blink_number = 0 # Reset count
                        self.is_blinking_on_state = False # Ensure it's off
            else:
                # Light is currently OFF
                if time_since_last_change < self.blink_interval:
                    # Still in the OFF phase, do nothing (don't draw)
                    pass
                else:
                    # OFF phase ended, switch back to ON state for the next blink
                    self.is_blinking_on_state = True
                    self.last_state_change_time = current_time

        # OpenGL state cleanup (important if other drawing happens)
        gl.glDisable(gl.GL_BLEND)
        gl.glEnable(gl.GL_DEPTH_TEST)


    def close(self):
        """
        Closes the feedback window.
        """
        super().close()
        