
import os

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
skills_dir = os.path.join(repo_root, 'catalog', 'skills')
commands_dir = os.path.join(repo_root, 'catalog', 'commands')

SKILL_APPEND_TEXT = """

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
"""

COMMAND_APPEND_TEXT = """

## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1.  **Analyze**: Look at the generated output.
    *   Is it complete?
    *   Are there any obvious errors?
    *   Does it meet the user's requirements?
2.  **Refine**:
    *   Fix any issues found.
    *   Add missing components.
3.  **Stop**:
    *   If you are confident the result is excellent.
    *   OR if you have reached the maximum iteration count.
"""

def update_file(filepath, app_text):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if "Iterative Refinement" in content:
            print(f"Skipping {filepath} (already updated)")
            return

        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(app_text)
        print(f"Updated {filepath}")
    except Exception as e:
        print(f"Error updating {filepath}: {e}")

def process_dir(directory, text):
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                update_file(os.path.join(root, file), text)

if __name__ == "__main__":
    print("Updating Skills...")
    process_dir(skills_dir, SKILL_APPEND_TEXT)

    print("\nUpdating Commands...")
    process_dir(commands_dir, COMMAND_APPEND_TEXT)
