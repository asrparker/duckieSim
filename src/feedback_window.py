# feedback_window.py

import pyglet
from pyglet import gl
import time

class FeedbackWindow(pyglet.window.Window):
    """
    A Pyglet window dedicated to displaying blinking visual feedback.
    This class is separated from the main simulation logic for better code organization.
    """
    def __init__(self, width, height, title='Feedback', feedback_duration=0.1, blink_interval=0.3):
        super().__init__(width, height, caption=title, resizable=False)
        
        self.feedback_active = False
        self.feedback_duration = feedback_duration
        self.blink_interval = blink_interval

        self.current_blink_number = 0
        self.total_blinks_requested = 0
        self.last_state_change_time = 0.0
        self.is_blinking_on_state = False

        self.set_location(100, 100)

        self.rect_width = self.width * 0.8
        self.rect_height = self.height * 0.8
        self.rect_x = (self.width - self.rect_width) / 2
        self.rect_y = (self.height - self.rect_height) / 2
        
        self.feedback_color = (1.0, 1.0, 1.0, 1.0)

    def activate_feedback(self, num_blinks, color=(1.0, 1.0, 1.0, 1.0)):
        """
        Method to be called by the main script to start a new blink sequence.
        num_blinks: The total number of times the rectangle should blink.
        color: The RGB or RGBA tuple for the blink color.
        """
        self.feedback_active = True
        self.total_blinks_requested = num_blinks
        self.feedback_color = color
        
        self.current_blink_number = 1
        self.is_blinking_on_state = True
        self.last_state_change_time = time.time()

    def on_draw(self):
        """
        Pyglet's drawing event handler for this window.
        """
        self.clear()
        current_time = time.time()

        if not self.feedback_active:
            return

        time_in_current_state = current_time - self.last_state_change_time

        if self.is_blinking_on_state:
            if time_in_current_state < self.feedback_duration:
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
                if self.current_blink_number < self.total_blinks_requested:
                    self.is_blinking_on_state = False
                    self.last_state_change_time = current_time
                else:
                    self.feedback_active = False

        else:
            if time_in_current_state < self.blink_interval:
                pass
            else:
                self.current_blink_number += 1
                self.is_blinking_on_state = True
                self.last_state_change_time = current_time
                