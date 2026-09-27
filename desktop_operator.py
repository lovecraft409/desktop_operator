import ollama
import subprocess
import json
import shutil
import os
from pathlib import Path

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

def find_folder(name, search_root="~"):
    root = Path(search_root).expanduser()
    matches = [str(p) for p in root.rglob(name) if p.is_dir()]
    return matches if matches else f"No folder named '{name}' found."

def find_file(name, search_root="~"):
    root = Path(search_root).expanduser()
    matches = [str(p) for p in root.rglob(name) if p.is_file()]
    return matches if matches else f"No file named '{name}' found."

def copy_file(source, destination):
    try:
        shutil.copy(source, destination)
        return f"Copied {source} to {destination}"
    except Exception as e:
        return f"Error copying: {e}"

def move_file(source, destination):
    try:
        shutil.move(source, destination)
        return f"Moved {source} to {destination}"
    except Exception as e:
        return f"Error moving: {e}"

home = os.path.expanduser("~")

tools_prompt = f"""
You control a computer. The user's home directory is: {home}

Respond ONLY in this JSON format, nothing else. No explanations, no notes, no placeholder text.

{{"action": "run_command", "command": "..."}}
{{"action": "find_folder", "name": "..."}}
{{"action": "find_file", "name": "..."}}
{{"action": "copy_file", "source": "...", "destination": "..."}}
{{"action": "move_file", "source": "...", "destination": "..."}}
{{"action": "reply", "message": "..."}}

IMPORTANT RULES:
- Never invent placeholder paths like "/path/to/...". If you don't know the exact path, use find_folder or find_file first.
- Only use copy_file/move_file once you have a REAL, exact path (either given by the user, or returned by find_folder/find_file).
- Destination folder paths should be like {home}/Desktop, {home}/Downloads, {home}/Documents.
"""

messages = [{"role": "system", "content": tools_prompt}]

print("Agent ready. Type 'quit' to exit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    messages.append({"role": "user", "content": user_input})

    response = ollama.chat(model='dolphin-mistral:latest', messages=messages)
    reply = response['message']['content']

    try:
        action = json.loads(reply)
    except json.JSONDecodeError:
        print("Agent:", reply)
        messages.append({"role": "assistant", "content": reply})
        continue

    if action["action"] == "run_command":
        cmd = action["command"]
        confirm = input(f"Agent wants to run: {cmd}\nAllow? (y/n): ")
        if confirm.lower() == "y":
            output = run_command(cmd)
            print("Output:", output)
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": f"Command output: {output}"})
        else:
            print("Cancelled.")
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": "Command was not allowed by user."})

    elif action["action"] == "find_folder":
        results = find_folder(action["name"])
        print("Found:", results)
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"Search results: {results}"})

    elif action["action"] == "find_file":
        results = find_file(action["name"])
        print("Found:", results)
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"Search results: {results}"})

    elif action["action"] == "reply":
        print("Agent:", action["message"])
        messages.append({"role": "assistant", "content": reply})

    elif action["action"] == "copy_file":
        confirm = input(f"Agent wants to copy: {action['source']} -> {action['destination']}\nAllow? (y/n): ")
        if confirm.lower() == "y":
            result = copy_file(action["source"], action["destination"])
            print(result)
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": result})
        else:
            print("Cancelled.")
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": "Copy was not allowed by user."})

    elif action["action"] == "move_file":
        confirm = input(f"Agent wants to move: {action['source']} -> {action['destination']}\nAllow? (y/n): ")
        if confirm.lower() == "y":
            result = move_file(action["source"], action["destination"])
            print(result)
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": result})
        else:
            print("Cancelled.")
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": "Move was not allowed by user."})
