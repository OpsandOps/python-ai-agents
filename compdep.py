#conmposition
class Animal:
    def sound(self):
        return "loud sounds"

    def move(self):
        return "moves fast"

class Dog(Animal):
   def __init__(self):
    super().__init__()
    self.noise = Animal()
    self.motion = Animal()

# dog = Dog()
# print(dog.motion.move())
# print(dog.sound())
# print(dog.move())

# ============================================================================
# EXAMPLE 2: DEPENDENCY INJECTION
# ============================================================================
# print("\n" + "=" * 70)
# print("EXAMPLE 2: DEPENDENCY INJECTION")
# print("=" * 70)
# print("\nDependency Injection = Passing dependencies FROM OUTSIDE")
# print("Instead of creating inside, we inject from outside\n")

# # --- Different Email Services ---
# class EmailService:
#     def send(self, message):
#         return f"📧 Sending via Email: {message}"


# class SMSService:
#     def send(self, message):
#         return f"📱 Sending via SMS: {message}"


# # --- Bad Design: Hard-Coded Dependency ---
# class NotificationBad:
#     """
#     ❌ BAD: Creates EmailService inside the class
#     Problem: Can't swap to SMS without changing code
#     """
#     def __init__(self):
#         self.service = EmailService()  # Hard-coded dependency!
    
#     def notify(self, message):
#         return self.service.send(message)


# # --- Good Design: Dependency Injection ---
# class Notification:
#     """
#     ✅ GOOD: Service is INJECTED from outside
#     We can pass ANY service that has a send() method
#     """
#     def __init__(self, service):
#         self.service = service  # Injected dependency!
    
#     def notify(self, message):
#         return self.service.send(message)


# # --- Demonstration ---
# print("Creating notification with INJECTED email service:")
# email_service = EmailService()
# notifier1 = Notification(email_service)  # Inject EmailService
# print(f"  {notifier1.notify('Hello World')}")

# print("\nNow switching to SMS (no code change needed!):")
# sms_service = SMSService()
# notifier2 = Notification(sms_service)    # Inject SMSService
# print(f"  {notifier2.notify('Hello World')}")

# print("\nWhy dependency injection is better:")
# print("  ✅ Can swap services without changing Notification class")
# print("  ✅ Easy to test with mock services")
# print("  ✅ More flexible and maintainable")


# # ============================================================================
# # BONUS: COMBINING BOTH PATTERNS
# # ============================================================================
# print("\n" + "=" * 70)
# print("BONUS: COMPOSITION + DEPENDENCY INJECTION TOGETHER")
# print("=" * 70)
# print("\nThis is exactly what fileExplorerAgent3.py does!\n")

# class Logger:
#     def log(self, message):
#         return f"[LOG] {message}"


# class Database:
#     def save(self, data):
#         return f"[DB] Saved: {data}"


# class UserService:
#     """
#     Uses BOTH patterns:
#     - Dependency Injection: logger and db are injected
#     - Composition: UserService HAS-A logger and HAS-A db
#     """
#     def __init__(self, logger, database):
#         self.logger = logger      # Injected + Composition
#         self.database = database  # Injected + Composition
    
#     def create_user(self, username):
#         # Delegates to injected dependencies
#         log_msg = self.logger.log(f"Creating user: {username}")
#         db_msg = self.database.save({"user": username})
#         return f"{log_msg}\n  {db_msg}"


# # --- Demonstration ---
# print("Creating services:")
# logger = Logger()
# database = Database()

# print("\nInjecting dependencies into UserService:")
# user_service = UserService(logger, database)

# print("\nUsing the service:")
# result = user_service.create_user("Alice")
# print(f"  {result}")

# print("\n" + "=" * 70)
# print("HOW THIS RELATES TO fileExplorerAgent3.py")
# print("=" * 70)
# print("""
# In fileExplorerAgent3.py:

#     agent = Agent(
#         goals=goals,
#         agent_language=AgentFunctionCallingActionLanguage(),  # ← Injected
#         action_registry=registry,                             # ← Injected
#         environment=Environment()                             # ← Injected
#     )

# Agent uses:
# - COMPOSITION: Agent HAS-A language, HAS-A registry, HAS-A environment
# - DEPENDENCY INJECTION: These are passed in from outside

# Benefits:
# ✅ Can swap AgentLanguage implementations
# ✅ Can test with mock environment
# ✅ Each class has single responsibility
# ✅ Loose coupling, high flexibility
# """)



## understanding the getattr and the setattr
## allows you to access object attribute dynamically as names
class Person:
    def __init__(self):
        self.name = "Prosper"
        self.age = 30

# print(Person.__static_attributes__)
# person = Person()
# print(person.__static_attributes__)
# print(getattr(person, "name"))

def getname(person: Person):
    if not person:
        return None
    try:
        return getattr(person, "school")
    except AttributeError:
        setattr(person, "school", "Vaatia Colege")

    return person.school

getname(Person)

print(Person.school)

# a function that takes another fn as an argument
##V
# def decorated_function(name=None):
#     def decorator(fn):
#         return fn.__dict__.update(name)
#     return decorator

# @decorated_function(name={"prosper"})
# def usingDecorator(_):
#     pass
    
# usingDecorator()
# print(decorated_function)

def read_file(file_name)-> List[str]:
    pass