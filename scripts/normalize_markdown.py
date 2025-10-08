import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
TARGET_DIRS = [
    ROOT_DIR / "code_review",
    ROOT_DIR / "documentation",
    ROOT_DIR / "test_development",
]

PROMPT_SINGLE_NOTE = "Use the structured prompt below with your coding assistant:"
PROMPT_MULTI_NOTE = (
    "Select the prompt that matches your scenario and run it with your coding assistant."
)


def remove_phase_headings(text: str) -> str:
    text = re.sub(r"^(#{1,6}) Phase \d+:\s*(.+)$", r"\1 \2", text, flags=re.MULTILINE)
    text = re.sub(r"^(#{1,6}) Phase \d+\s*[\u2013-]\s*(.+)$", r"\1 \2", text, flags=re.MULTILINE)
    return text


def remove_time_estimates(text: str) -> str:
    pattern = re.compile(
        r"### Time Estimate\n(?:.*?\n)*?(?=(\n### |\n## |\n---|\Z))",
        re.MULTILINE,
    )
    return pattern.sub("", text)


def replace_prompt_headings(text: str) -> str:
    replacements = {
        "## Copy-Paste Prompt": "## Prompt Template",
        "## Copy the prompt below, then paste it into your coding assistant": "## Prompt Template",
        "## 🎓 Copy-Paste Prompts": "## Prompt Templates",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def replace_phase_language(text: str) -> str:
    text = text.replace("six-phase workflow", "six-step workflow")
    text = text.replace("Six-phase workflow", "Six-step workflow")
    text = re.sub(r"This phase", "This review", text)
    text = re.sub(r"this phase", "this review", text)
    text = re.sub(r"After completing this review, proceed to Phase (\d+): (.+)", r"After completing this review, proceed to the \2.", text)
    text = re.sub(r"After completing this review, proceed to phase (\d+): (.+)", r"After completing this review, proceed to the \2.", text)
    text = re.sub(r"After completing this phase, proceed to Phase (\d+): (.+)", r"After completing this review, proceed to the \2.", text)
    text = re.sub(r"After completing this phase, proceed to phase (\d+): (.+)", r"After completing this review, proceed to the \2.", text)
    text = text.replace("Phase overview", "Review overview")
    text = text.replace("Phase details", "Review details")
    text = text.replace("phase overview", "review overview")
    text = text.replace("phase details", "review details")
    text = text.replace("Phase focus", "Review focus")
    return text


def collapse_blank_lines(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def convert_prompt_blocks(text: str) -> str:
    lines = text.splitlines()
    filtered_lines = [
        line
        for line in lines
        if line.strip() not in {"~~~markdown", "~~~", PROMPT_SINGLE_NOTE, PROMPT_MULTI_NOTE}
    ]
    output: list[str] = []
    i = 0

    def collect_code_block(start_index: int) -> tuple[int, list[str]]:
        nesting: list[str] = []
        collected: list[str] = []
        i_local = start_index + 1
        while i_local < len(filtered_lines):
            current = filtered_lines[i_local]
            stripped_current = current.strip()
            if stripped_current.startswith("```") and len(stripped_current) > 3:
                nesting.append(stripped_current[3:])
                collected.append(current)
                i_local += 1
                continue
            if stripped_current == "```":
                if nesting:
                    nesting.pop()
                    collected.append(current)
                    i_local += 1
                    continue
                return i_local + 1, collected
            collected.append(current)
            i_local += 1
        return i_local, collected

    while i < len(filtered_lines):
        line = filtered_lines[i]
        stripped = line.strip()
        if stripped.startswith("## Prompt Template"):
            output.append("## Prompt Template")
            output.append("")
            output.append(PROMPT_SINGLE_NOTE)
            output.append("")
            i += 1
            pre_block: list[str] = []
            while i < len(filtered_lines) and not filtered_lines[i].strip().startswith("```"):
                pre_block.append(filtered_lines[i])
                i += 1
            if i < len(filtered_lines) and filtered_lines[i].strip().startswith("```"):
                output.append("~~~markdown")
                output.extend(pre_block)
                i, collected = collect_code_block(i)
                output.extend(collected)
                output.append("~~~")
            continue
        if stripped.startswith("## Prompt Templates"):
            output.append("## Prompt Templates")
            output.append("")
            output.append(PROMPT_MULTI_NOTE)
            output.append("")
            i += 1
            continue
        if re.match(r"### Prompt \\d+:", stripped):
            output.append(line)
            output.append("")
            i += 1
            # Append any descriptive text before the code fence
            pre_block = []
            while i < len(filtered_lines) and not filtered_lines[i].strip().startswith("```"):
                pre_block.append(filtered_lines[i])
                i += 1
            if i < len(filtered_lines) and filtered_lines[i].strip().startswith("```"):
                output.append("~~~markdown")
                output.extend(pre_block)
                i, collected = collect_code_block(i)
                output.extend(collected)
                output.append("~~~")
            continue
        output.append(line)
        i += 1
    return "\n".join(output) + "\n"


def process_markdown(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    original = text
    text = remove_phase_headings(text)
    text = replace_phase_language(text)
    text = remove_time_estimates(text)
    text = replace_prompt_headings(text)
    text = convert_prompt_blocks(text)
    text = collapse_blank_lines(text)
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"Updated {path.relative_to(ROOT_DIR)}")


def main() -> None:
    for target in TARGET_DIRS:
        for path in target.rglob("*.md"):
            process_markdown(path)


if __name__ == "__main__":
    main()
