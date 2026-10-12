class Engine:
    def start(self):
        return "Engine voom"

    def stop(self):
        return "Engine stopped"
  
class Wheels:
    def __init__(self, count=4):
        self.count = count

    def roll(self):
        return f"{self.count} wheels rooling"

class Car:
    def __init__(self, engine: Engine, wheel: Wheels):
        self.engine = Engine()
        self.wheel = Wheels()

print(Car.__dict__)
car = Car(engine=Engine, wheel=Wheels)
print(car.engine.start())
print(car.wheel.roll())