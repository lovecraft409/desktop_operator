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
        if os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            shutil.copy(source, destination)
        return f"Copied {source} to {destination}"
    except Exception as e:
        return f"Error copying: {e}"

def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"Created folder {path}"
    except Exception as e:
        return f"Error creating folder: {e}"

def move_file(source, destination):
    try:
        shutil.move(source, destination)
        return f"Moved {source} to {destination}"
    except Exception as e:
        return f"Error moving: {e}"

home = os.path.expanduser("~")

tools_prompt = f"""
You control a computer. The user's home directory is: {home}

Respond with exactly ONE JSON object per reply. No explanations, no notes, no extra text.

{{"action": "run_command", "command": "..."}}
{{"action": "find_folder", "name": "..."}}
{{"action": "find_file", "name": "..."}}
{{"action": "copy_file", "source": "...", "destination": "..."}}
{{"action": "move_file", "source": "...", "destination": "..."}}
{{"action": "reply", "message": "..."}}
{{"action": "create_folder", "path": "..."}}

RULES:
- Return only ONE action per response.
- If the user is just chatting, greeting, or asking a question, use "reply".
- Never invent placeholder paths like "/path/to/...". If you don't know the exact path, use find_folder or find_file first.
- Only use copy_file/move_file once you have a REAL, exact path (given by the user or returned by a search).
- Common folders: {home}/Desktop, {home}/Downloads, {home}/Documents.
- Folder names in find_folder are just the name (like "operator"), not a full path.
- Use create_folder to make a new folder. The path must be the full path, like {home}/Desktop/newfolder.

EXAMPLES:
User: hi
{{"action": "reply", "message": "Hey! What do you want me to do?"}}

User: find the folder called operator
{{"action": "find_folder", "name": "operator"}}

User: move the operator folder from Downloads to Desktop
{{"action": "find_folder", "name": "operator"}}

User: Search results: ['{home}/Downloads/operator']
{{"action": "move_file", "source": "{home}/Downloads/operator", "destination": "{home}/Desktop"}}
"""
messages = [{"role": "system", "content": tools_prompt}]

print("Agent ready. Type 'quit' to exit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    messages.append({"role": "user", "content": user_input})
    messages = [messages[0]] + messages[-6:]

    response = ollama.chat(
        model='qwen2.5:3b',
        messages=messages,
        format='json',
        options={'temperature': 0, 'num_ctx': 2048},
        keep_alive='10m'
    )
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

    elif action["action"] == "create_folder":
        confirm = input(f"Agent wants to create folder: {action['path']}\nAllow? (y/n): ")
        if confirm.lower() == "y":
            result = create_folder(action["path"])
            print(result)
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": result})
        else:
            print("Cancelled.")
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": "Creating the folder was not allowed by user."})
