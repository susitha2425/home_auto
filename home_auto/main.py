# main.py

from intent_semantic import detect_intents

print("Home Automation Intent Model Ready!\n")

while True:
    user = input("Enter command: ")

    if user.lower() in ["exit", "quit", "stop"]:
        break

    result = detect_intents(user)
    print("Output:", result)
