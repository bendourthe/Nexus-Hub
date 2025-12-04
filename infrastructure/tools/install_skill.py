"""
Claude Code Skill Installation Tool

Install skills from the AI Templates repository to your local .claude/skills/ directory.

Usage:
    python tools/install_skill.py --skill plan-before-code
    python tools/install_skill.py --category workflow
    python tools/install_skill.py --all
    python tools/install_skill.py --list

Authors:
    - Benjamin Dourthe (benjamin@adonamed.com)
"""
import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


class SkillInstaller:
    """Manage skill installation to .claude/skills/ directory."""

    def __init__(self, repository_root: Optional[Path] = None):
        """Initialize installer with repository paths."""
        if repository_root is None:
            # Assume script is in infrastructure/tools/ directory
            repository_root = Path(__file__).parent.parent.parent

        self.repo_root = repository_root
        self.skills_source = repository_root / 'templates' / 'ai_instructions' / 'autonomous_agents' / 'claude_code' / 'skills'
        self.catalog_path = repository_root / 'catalogs' / 'skills.json'

        # Load catalog
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Skills catalog not found: {self.catalog_path}")

        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            catalog_data = json.load(f)
            self.catalog = catalog_data['skills']
            self.stats = catalog_data['statistics']

    def find_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Find skill in catalog by name."""
        for skill in self.catalog:
            if skill['name'] == skill_name or skill['title'] == skill_name:
                return skill
        return None

    def get_skills_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all skills in a category."""
        category_lower = category.lower()
        return [s for s in self.catalog
                if s['category'].lower() == category_lower]

    def get_skills_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """Get all skills with specific priority."""
        priority_upper = priority.upper()
        return [s for s in self.catalog
                if s['priority'] == priority_upper]

    def get_install_location(self, project_root: Optional[Path] = None) -> Path:
        """Determine installation location for skills."""
        if project_root:
            return project_root / '.claude' / 'skills'

        # Try to find .claude directory in current working directory
        cwd = Path.cwd()

        # Check current directory
        if (cwd / '.claude').exists():
            return cwd / '.claude' / 'skills'

        # Check if we're in a subdirectory of a project with .claude
        for parent in cwd.parents:
            if (parent / '.claude').exists():
                return parent / '.claude' / 'skills'

        # No .claude found, use current directory
        print(f"Warning: No .claude directory found. Creating in current directory: {cwd}")
        return cwd / '.claude' / 'skills'

    def install_skill(self, skill: Dict[str, Any], destination: Path,
                     force: bool = False) -> bool:
        """Install a single skill."""
        skill_name = skill['name']
        source_dir = self.repo_root / skill['path']

        if not source_dir.exists():
            print(f"Error: Skill source not found: {source_dir}")
            return False

        dest_dir = destination / skill_name

        # Check if already installed
        if dest_dir.exists() and not force:
            print(f"⚠️  Skill '{skill_name}' already installed. Use --force to overwrite.")
            return False

        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy skill files
        try:
            if (source_dir / 'SKILL.md').exists():
                shutil.copy2(source_dir / 'SKILL.md', dest_dir / 'SKILL.md')

            # Copy any additional files
            for item in source_dir.iterdir():
                if item.is_file() and item.name != 'SKILL.md':
                    shutil.copy2(item, dest_dir / item.name)

            print(f"✅ Installed: {skill_name}")
            print(f"   Location: {dest_dir}")
            print(f"   Category: {skill['category']}")
            print(f"   Priority: {skill['priority']}")
            if skill['tools_required']:
                print(f"   Tools: {', '.join(skill['tools_required'])}")
            return True

        except Exception as e:
            print(f"❌ Failed to install {skill_name}: {e}")
            return False

    def install_multiple(self, skills: List[Dict[str, Any]], destination: Path,
                        force: bool = False) -> int:
        """Install multiple skills."""
        success_count = 0
        for skill in skills:
            if self.install_skill(skill, destination, force):
                success_count += 1
        return success_count

    def list_skills(self, category: Optional[str] = None,
                   priority: Optional[str] = None):
        """List available skills."""
        skills = self.catalog

        if category:
            skills = self.get_skills_by_category(category)

        if priority:
            skills = self.get_skills_by_priority(priority)

        print(f"\n{'='*80}")
        print(f"Available Skills: {len(skills)}")
        print(f"{'='*80}\n")

        # Group by category
        by_category = {}
        for skill in skills:
            cat = skill['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(skill)

        for cat in sorted(by_category.keys()):
            print(f"\n{cat.upper()}")
            print(f"{'-'*80}")
            for skill in sorted(by_category[cat], key=lambda x: x['name']):
                priority_marker = {
                    'CRITICAL': '[!]',
                    'HIGH': '[*]',
                    'MEDIUM': '[-]',
                    'LOW': '[ ]'
                }.get(skill['priority'], '[-]')

                print(f"  {priority_marker} {skill['name']}")
                print(f"      {skill['description']}")
                if skill['tools_required']:
                    print(f"      Tools: {', '.join(skill['tools_required'])}")
                print()

    def list_categories(self):
        """List all available categories."""
        print(f"\n{'='*80}")
        print("Available Categories")
        print(f"{'='*80}\n")

        for category, count in sorted(self.stats['categories'].items()):
            print(f"  {category:30s} ({count} skills)")

    def show_skill_info(self, skill_name: str):
        """Show detailed information about a skill."""
        skill = self.find_skill(skill_name)
        if not skill:
            print(f"❌ Skill not found: {skill_name}")
            return

        print(f"\n{'='*80}")
        print(f"Skill: {skill['name']}")
        print(f"{'='*80}\n")

        print(f"Description:    {skill['description']}")
        print(f"Category:       {skill['category']}")
        print(f"Priority:       {skill['priority']}")
        print(f"Version:        {skill['version']}")
        print(f"Author:         {skill['author']}")
        print(f"Language:       {skill['language']}")
        print(f"Status:         {skill['status']}")

        if skill['tags']:
            print(f"Tags:           {', '.join(skill['tags'])}")

        if skill['tools_required']:
            print(f"Tools Required: {', '.join(skill['tools_required'])}")

        if skill['based_on']:
            print(f"Based On:       {skill['based_on']}")

        print(f"\nSize:")
        print(f"  Lines:        {skill['size']['lines']:,}")
        print(f"  Characters:   {skill['size']['characters']:,}")
        print(f"  Est. Tokens:  {skill['size']['tokens_estimate']:,}")

        print(f"\nSecurity:")
        print(f"  Structural:   {skill['security']['structural']}/100")
        print(f"  Integrity:    {skill['security']['integrity']}/100")
        print(f"  Semantic:     {skill['security']['semantic']}/100")
        print(f"  Validated:    {'YES' if skill['security']['validated'] else 'NO'}")

        print(f"\nInstallation:")
        print(f"  python tools/install_skill.py --skill {skill_name}")
        print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Install Claude Code skills from AI Templates repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/install_skill.py --list
  python tools/install_skill.py --info plan-before-code
  python tools/install_skill.py --skill plan-before-code
  python tools/install_skill.py --category workflow
  python tools/install_skill.py --priority CRITICAL
  python tools/install_skill.py --all
  python tools/install_skill.py --skill test-driven-development --destination ~/my-project
        """
    )

    parser.add_argument('--skill', '-s', help='Install specific skill by name')
    parser.add_argument('--category', '-c', help='Install all skills in category')
    parser.add_argument('--priority', '-p', help='Install all skills with priority (CRITICAL, HIGH, MEDIUM, LOW)')
    parser.add_argument('--all', '-a', action='store_true', help='Install all skills')
    parser.add_argument('--list', '-l', action='store_true', help='List all available skills')
    parser.add_argument('--categories', action='store_true', help='List all categories')
    parser.add_argument('--info', '-i', help='Show detailed info about a skill')
    parser.add_argument('--destination', '-d', type=Path, help='Installation destination (default: auto-detect .claude/skills)')
    parser.add_argument('--force', '-f', action='store_true', help='Overwrite existing skills')
    parser.add_argument('--repo', type=Path, help='Path to ai_templates repository (default: auto-detect)')

    args = parser.parse_args()

    try:
        installer = SkillInstaller(args.repo)

        # List operations
        if args.list:
            installer.list_skills()
            return 0

        if args.categories:
            installer.list_categories()
            return 0

        if args.info:
            installer.show_skill_info(args.info)
            return 0

        # Install operations
        destination = installer.get_install_location(args.destination)

        if args.skill:
            skill = installer.find_skill(args.skill)
            if not skill:
                print(f"❌ Skill not found: {args.skill}")
                print("\nUse --list to see available skills")
                return 1

            print(f"\nInstalling to: {destination}\n")
            success = installer.install_skill(skill, destination, args.force)
            return 0 if success else 1

        elif args.category:
            skills = installer.get_skills_by_category(args.category)
            if not skills:
                print(f"❌ No skills found in category: {args.category}")
                print("\nUse --categories to see available categories")
                return 1

            print(f"\nInstalling {len(skills)} skills from category '{args.category}'")
            print(f"Destination: {destination}\n")
            count = installer.install_multiple(skills, destination, args.force)
            print(f"\n✅ Successfully installed {count}/{len(skills)} skills")
            return 0

        elif args.priority:
            skills = installer.get_skills_by_priority(args.priority)
            if not skills:
                print(f"❌ No skills found with priority: {args.priority}")
                return 1

            print(f"\nInstalling {len(skills)} skills with priority '{args.priority}'")
            print(f"Destination: {destination}\n")
            count = installer.install_multiple(skills, destination, args.force)
            print(f"\n✅ Successfully installed {count}/{len(skills)} skills")
            return 0

        elif args.all:
            print(f"\nInstalling ALL {len(installer.catalog)} skills")
            print(f"Destination: {destination}\n")
            count = installer.install_multiple(installer.catalog, destination, args.force)
            print(f"\n✅ Successfully installed {count}/{len(installer.catalog)} skills")
            return 0

        else:
            parser.print_help()
            return 1

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
