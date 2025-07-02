import pyglet

print("Attempting to create a Pyglet window...")

try:
    # Create a simple window
    window = pyglet.window.Window(width=640, height=480, caption='Pyglet Test Window')

    @window.event
    def on_draw():
        window.clear()

    # This will keep the window open until manually closed
    print("Pyglet window created. It should be visible. Press ESC or close the window to exit.")
    pyglet.app.run()

except Exception as e:
    print(f"Error creating Pyglet window: {e}")
    import traceback
    traceback.print_exc()

print("Pyglet application finished.")
