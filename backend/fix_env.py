
import os

env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    fixed = False
    for line in lines:
        if line.startswith("OPENAI_BASE_URL="):
            # Check for typo
            if "https:/aihubmix.com" in line and "https://aihubmix.com" not in line:
                print(f"Found bad line: {line.strip()}")
                line = line.replace("https:/aihubmix.com", "https://aihubmix.com")
                print(f"Fixed line: {line.strip()}")
                fixed = True
            # Also check generic https:/ case if different domain
            elif "https:/" in line and "https://" not in line:
                 print(f"Found potentially bad line: {line.strip()}")
                 line = line.replace("https:/", "https://")
                 print(f"Fixed line: {line.strip()}")
                 fixed = True
        new_lines.append(line)
        
    if fixed:
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print("Successfully fixed .env file.")
    else:
        print("No issues found or already fixed.")
else:
    print(".env not found")
