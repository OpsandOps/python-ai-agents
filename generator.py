"""
GENERATORS IN PYTHON - A Comprehensive Guide
=============================================

Generators are memory-efficient iterators that produce values on-demand (lazily)
instead of storing everything in memory at once.

Key Concept: They "yield" values one at a time, pausing execution between yields.
"""

# ============================================================================
# 1. THE PROBLEM: Memory-Intensive Lists
# ============================================================================

def get_numbers_list(n):
    """Traditional approach: Creates entire list in memory"""
    result = []
    for i in range(n):
        result.append(i * i)
    return result

# This creates a list with 1 MILLION items in memory at once!
# numbers = get_numbers_list(1_000_000)  # Uses ~8MB+ of RAM


# ============================================================================
# 2. THE SOLUTION: Generator Functions (using yield)
# ============================================================================

def get_numbers_generator(n):
    """Generator approach: Produces values one at a time"""
    for i in range(n):
        yield i * i  # 'yield' instead of 'return'

# This produces values on-demand, minimal memory!
numbers_gen = get_numbers_generator(1_000_000)  # Uses ~128 bytes!

# You can iterate through it:
# for num in numbers_gen:
#     print(num)


# ============================================================================
# 3. GENERATOR EXPRESSIONS (Compact Syntax)
# ============================================================================

# List comprehension (creates full list):
squares_list = [x * x for x in range(10)]
print(f"List: {squares_list}")
print(f"Memory size: {squares_list.__sizeof__()} bytes\n")

# Generator expression (lazy evaluation):
squares_gen = (x * x for x in range(10))  # Note: parentheses, not brackets!
print(f"Generator: {squares_gen}")
print(f"Memory size: {squares_gen.__sizeof__()} bytes")
print(f"Values: {list(squares_gen)}\n")  # Convert to list to see values


# ============================================================================
# 4. REAL-WORLD EXAMPLE: The 'next()' Pattern
# ============================================================================

def find_system_message_traditional(messages):
    """Traditional approach: Loop with break"""
    system = None
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
            break
    return system


def find_system_message_functional(messages):
    """Functional approach: Generator + next()"""
    return next(
        (m["content"] for m in messages if m["role"] == "system"),
        None  # Default if no system message found
    )

# Test data
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "system", "content": "You are helpful"},
    {"role": "assistant", "content": "Hi there!"},
]

print("Traditional:", find_system_message_traditional(messages))
print("Functional:", find_system_message_functional(messages))
print()


# ============================================================================
# 5. GENERATOR STATES: yield pauses execution!
# ============================================================================

def countdown(n):
    """Generator that counts down, pausing at each yield"""
    print(f"Starting countdown from {n}")
    while n > 0:
        print(f"  About to yield {n}")
        yield n  # ← Execution pauses here!
        print(f"  Resumed after yielding {n}")
        n -= 1
    print("Countdown complete!")


print("Creating generator...")
counter = countdown(3)

print("\nCalling next() manually:")
print(f"Got: {next(counter)}")  # Runs until first yield
print(f"Got: {next(counter)}")  # Resumes and runs until next yield
print(f"Got: {next(counter)}")  # Resumes and runs until next yield
# print(next(counter))  # Would raise StopIteration
print()


# ============================================================================
# 6. INFINITE GENERATORS (Impossible with Lists!)
# ============================================================================

def infinite_sequence():
    """Generator that never stops - impossible with a list!"""
    num = 0
    while True:
        yield num
        num += 1


# This would crash if it was a list: infinite_list = [num for num in range(infinity)]
seq = infinite_sequence()
print("First 5 numbers from infinite generator:")
for i in range(5):
    print(next(seq), end=" ")
print("\n")


# ============================================================================
# 7. PRACTICAL USE CASE: File Processing
# ============================================================================

def read_large_file(filepath):
    """
    Generator for reading large files line-by-line
    Memory-efficient for multi-GB files!
    """
    try:
        with open(filepath, 'r') as file:
            for line in file:
                yield line.strip()
    except FileNotFoundError:
        print(f"File {filepath} not found")
        return


# Usage:
# for line in read_large_file('huge_log_file.txt'):
#     if 'ERROR' in line:
#         print(line)


# ============================================================================
# 8. GENERATOR PIPELINE: Chaining Generators
# ============================================================================

def numbers(n):
    """Generate numbers 0 to n-1"""
    for i in range(n):
        yield i


def squares(nums):
    """Square each number"""
    for num in nums:
        yield num * num


def even_only(nums):
    """Filter for even numbers"""
    for num in nums:
        if num % 2 == 0:
            yield num


# Chain them together!
pipeline = even_only(squares(numbers(10)))
print("Pipeline result (even squares):", list(pipeline))
print()

# ============================================================================
# 10. COMMON GOTCHA: Generators Are One-Time Use!
# ============================================================================

gen = (x * x for x in range(5))

print("First iteration:", list(gen))   # [0, 1, 4, 9, 16]
print("Second iteration:", list(gen))  # [] - Empty! Generator exhausted

# To reuse, you must recreate it:
gen = (x * x for x in range(5))
print("Recreated generator:", list(gen))
print()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON: List vs Generator")
    print("="*60 + "\n")
    time_and_memory_comparison()
    
    print("\n" + "="*60)
    print("KEY TAKEAWAY")
    print("="*60)
    print("""
Generators are Python's way of being lazy (in a good way!)
They produce values on-demand, saving memory and improving performance
for large datasets or infinite sequences.

Think of them as a "value factory" that only makes products when requested,
rather than a "warehouse" that stores everything upfront.
    """)
