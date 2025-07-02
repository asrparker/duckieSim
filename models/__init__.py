# This file defines data models used in the simulation, including classes that represent different entities within the Duckietown environment.

class Duckie:
    def __init__(self, id, position, velocity):
        self.id = id
        self.position = position
        self.velocity = velocity

class Lane:
    def __init__(self, id, width):
        self.id = id
        self.width = width

class TrafficLight:
    def __init__(self, id, state):
        self.id = id
        self.state = state

class Vehicle:
    def __init__(self, id, position, speed):
        self.id = id
        self.position = position
        self.speed = speed