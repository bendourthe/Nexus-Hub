---
template_id: SKILL
template_name: Optimize-Context-Usage - Generic
version: 1.0.0
last_updated: 2025-12-03
language: Generic
category: skills
phase: optimize-context-usage
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tags:

  - skills
  - generic
---
# optimize-context-usage

---
category: security-quality
priority: MEDIUM
languages: [all]
requires_user_input: false
estimated_duration: 1-3 hours
---

## Overview

Optimize token usage and context management in Claude Code interactions to reduce costs, improve response times, and work within token limits while maintaining effectiveness.

## When to Use This Skill

- Hitting context length limits frequently
- High token costs in production
- Slow response times due to large contexts
- Need to process large codebases
- Multiple iterations required on same task
- Long-running conversations with Claude

## Prerequisites

- Understanding of tokenization
- Access to token counting tools
- Knowledge of context window limits
- Familiarity with Claude's capabilities
- Understanding of your codebase structure

## Step-by-Step Instructions

### Phase 1: Assessment

#### Step 1: Measure Current Token Usage

**Token counting tools:**

```python
# token_counter.py
"""
Count tokens in text using tiktoken (OpenAI's tokenizer).
Claude uses a similar tokenization approach.
"""
import tiktoken
from pathlib import Path
from typing import Dict, List
import json

class TokenCounter:
    """Count and analyze token usage."""

    def __init__(self, encoding_name: str = "cl100k_base"):
        """Initialize with tokenizer."""
        self.encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def count_tokens_in_file(self, filepath: str) -> int:
        """Count tokens in file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.count_tokens(content)

    def analyze_codebase(self, directory: str) -> Dict:
        """Analyze token usage across codebase."""
        results = {
            'files': {},
            'total_tokens': 0,
            'total_files': 0,
            'large_files': [],  # Files > 4000 tokens
            'by_extension': {}
        }

        for filepath in Path(directory).rglob('*'):
            if filepath.is_file() and not self._should_skip(filepath):
                try:
                    tokens = self.count_tokens_in_file(str(filepath))
                    relative_path = str(filepath.relative_to(directory))

                    results['files'][relative_path] = tokens
                    results['total_tokens'] += tokens
                    results['total_files'] += 1

                    # Track large files
                    if tokens > 4000:
                        results['large_files'].append({
                            'file': relative_path,
                            'tokens': tokens
                        })

                    # Track by extension
                    ext = filepath.suffix or 'no_extension'
                    results['by_extension'][ext] = results['by_extension'].get(ext, 0) + tokens

                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

        # Sort large files by token count
        results['large_files'].sort(key=lambda x: x['tokens'], reverse=True)

        return results

    def _should_skip(self, filepath: Path) -> bool:
        """Check if file should be skipped."""
        skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}
        skip_extensions = {'.pyc', '.pyo', '.so', '.dll', '.exe', '.png', '.jpg', '.pdf'}

        # Skip if in excluded directory
        if any(part in skip_dirs for part in filepath.parts):
            return True

        # Skip if excluded extension
        if filepath.suffix in skip_extensions:
            return True

        return False

    def generate_report(self, results: Dict, output_file: str = 'token_usage.json'):
        """Generate token usage report."""
        # Calculate statistics
        if results['total_files'] > 0:
            avg_tokens = results['total_tokens'] / results['total_files']
        else:
            avg_tokens = 0

        report = {
            'summary': {
                'total_files': results['total_files'],
                'total_tokens': results['total_tokens'],
                'average_tokens_per_file': avg_tokens,
                'large_files_count': len(results['large_files']),
                'estimated_context_windows': results['total_tokens'] / 100000  # Assuming 100k window
            },
            'large_files': results['large_files'][:20],  # Top 20
            'by_extension': results['by_extension'],
            'files': results['files']
        }

        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Print summary
        self._print_summary(report)

        return report

    def _print_summary(self, report: Dict):
        """Print report summary."""
        summary = report['summary']

        print("\n" + "="*60)
        print("TOKEN USAGE ANALYSIS")
        print("="*60)
        print(f"\nTotal files analyzed: {summary['total_files']}")
        print(f"Total tokens: {summary['total_tokens']:,}")
        print(f"Average tokens per file: {summary['average_tokens_per_file']:.0f}")
        print(f"Large files (>4k tokens): {summary['large_files_count']}")
        print(f"Estimated context windows needed: {summary['estimated_context_windows']:.1f}")

        if report['large_files']:
            print("\n📊 Largest files (top 10):")
            for item in report['large_files'][:10]:
                print(f"  {item['file']}: {item['tokens']:,} tokens")

        print("\n📊 Token distribution by file type:")
        sorted_ext = sorted(
            report['by_extension'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for ext, tokens in sorted_ext[:5]:
            print(f"  {ext}: {tokens:,} tokens")

# Usage
if __name__ == '__main__':
    counter = TokenCounter()
    results = counter.analyze_codebase('src/')
    counter.generate_report(results)
```

#### Step 2: Identify Optimization Opportunities

**Analysis questions:**

```python
"""
Token Optimization Checklist

1. Large Files
   - Which files exceed 4,000 tokens?
   - Can they be split into smaller modules?
   - Are there redundant sections?

2. Redundant Context
   - Are we sending the same code repeatedly?
   - Can we cache common components?
   - Are we including unnecessary imports?

3. Documentation Overhead
   - Are docstrings too verbose?
   - Can we summarize instead of including full docs?
   - Are comments necessary for Claude's task?

4. Test Files
   - Do we need to include tests in context?
   - Can we reference test patterns instead?

5. Generated Code
   - Are we including auto-generated files?
   - Can we exclude build artifacts?

6. Historical Context
   - Are we carrying too much conversation history?
   - Can we summarize previous exchanges?

Optimization Potential Score:
- 0-5 files >4k tokens: LOW (10-20% reduction possible)
- 6-15 files >4k tokens: MEDIUM (20-40% reduction possible)
- 16+ files >4k tokens: HIGH (40-60% reduction possible)
"""
```

### Phase 2: Optimization Strategies

#### Step 3: Implement File Chunking

```python
# context_optimizer.py
"""
Optimize context by chunking and summarizing code.
"""
from typing import List, Dict, Tuple
import ast

class ContextOptimizer:
    """Optimize code context for Claude."""

    def __init__(self, max_tokens_per_chunk: int = 4000):
        self.max_tokens = max_tokens_per_chunk
        self.token_counter = TokenCounter()

    def chunk_large_file(self, filepath: str) -> List[Dict]:
        """
        Split large file into logical chunks.

        Strategies:
        1. Split by class boundaries
        2. Split by function boundaries
        3. Keep related code together
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try to parse as Python
        try:
            tree = ast.parse(content)
            return self._chunk_by_ast(content, tree, filepath)
        except SyntaxError:
            # Fall back to simple line-based chunking
            return self._chunk_by_lines(content, filepath)

    def _chunk_by_ast(self, content: str, tree: ast.AST, filepath: str) -> List[Dict]:
        """Chunk Python file by AST nodes (classes, functions)."""
        chunks = []
        lines = content.split('\n')

        # Extract top-level definitions
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                # Get source code for this definition
                start_line = node.lineno - 1
                end_line = node.end_lineno

                chunk_content = '\n'.join(lines[start_line:end_line])
                tokens = self.token_counter.count_tokens(chunk_content)

                chunks.append({
                    'file': filepath,
                    'type': type(node).__name__,
                    'name': node.name,
                    'start_line': start_line + 1,
                    'end_line': end_line,
                    'content': chunk_content,
                    'tokens': tokens
                })

        return chunks

    def _chunk_by_lines(self, content: str, filepath: str) -> List[Dict]:
        """Chunk file by line count when AST parsing fails."""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        start_line = 1

        for i, line in enumerate(lines, 1):
            line_tokens = self.token_counter.count_tokens(line)

            if current_tokens + line_tokens > self.max_tokens and current_chunk:
                # Save current chunk
                chunks.append({
                    'file': filepath,
                    'type': 'lines',
                    'start_line': start_line,
                    'end_line': i - 1,
                    'content': '\n'.join(current_chunk),
                    'tokens': current_tokens
                })

                # Start new chunk
                current_chunk = [line]
                current_tokens = line_tokens
                start_line = i
            else:
                current_chunk.append(line)
                current_tokens += line_tokens

        # Add final chunk
        if current_chunk:
            chunks.append({
                'file': filepath,
                'type': 'lines',
                'start_line': start_line,
                'end_line': len(lines),
                'content': '\n'.join(current_chunk),
                'tokens': current_tokens
            })

        return chunks

    def create_file_summary(self, filepath: str) -> Dict:
        """
        Create concise summary of file instead of including full content.

        Useful for providing context without using many tokens.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            tree = ast.parse(content)
            return self._summarize_from_ast(tree, filepath)
        except SyntaxError:
            return self._summarize_from_text(content, filepath)

    def _summarize_from_ast(self, tree: ast.AST, filepath: str) -> Dict:
        """Create summary from AST."""
        summary = {
            'file': filepath,
            'classes': [],
            'functions': [],
            'imports': []
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [
                    m.name for m in node.body
                    if isinstance(m, ast.FunctionDef)
                ]
                summary['classes'].append({
                    'name': node.name,
                    'methods': methods
                })

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Only top-level functions (not methods)
                if not any(node in cls.body for cls in ast.walk(tree) if isinstance(cls, ast.ClassDef)):
                    summary['functions'].append({
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args]
                    })

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        summary['imports'].append(alias.name)
                else:
                    summary['imports'].append(f"{node.module}.{node.names[0].name}")

        return summary

    def _summarize_from_text(self, content: str, filepath: str) -> Dict:
        """Create basic summary from text."""
        lines = content.split('\n')

        return {
            'file': filepath,
            'line_count': len(lines),
            'estimated_tokens': self.token_counter.count_tokens(content),
            'type': 'text'
        }

    def create_context_package(
        self,
        files: List[str],
        max_total_tokens: int = 50000
    ) -> Dict:
        """
        Create optimized context package from file list.

        Strategy:
        1. Summarize large files
        2. Include full content for small files
        3. Chunk medium files
        4. Stay within token budget
        """
        package = {
            'full_files': [],
            'summaries': [],
            'chunks': [],
            'total_tokens': 0
        }

        for filepath in files:
            tokens = self.token_counter.count_tokens_in_file(filepath)

            if tokens < 1000:
                # Small file - include in full
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                if package['total_tokens'] + tokens <= max_total_tokens:
                    package['full_files'].append({
                        'file': filepath,
                        'content': content,
                        'tokens': tokens
                    })
                    package['total_tokens'] += tokens

            elif tokens < 4000:
                # Medium file - include if room, otherwise summarize
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                if package['total_tokens'] + tokens <= max_total_tokens:
                    package['full_files'].append({
                        'file': filepath,
                        'content': content,
                        'tokens': tokens
                    })
                    package['total_tokens'] += tokens
                else:
                    # Summarize instead
                    summary = self.create_file_summary(filepath)
                    summary_tokens = 200  # Estimate
                    package['summaries'].append(summary)
                    package['total_tokens'] += summary_tokens

            else:
                # Large file - chunk or summarize
                summary = self.create_file_summary(filepath)
                summary_tokens = 200
                package['summaries'].append(summary)
                package['total_tokens'] += summary_tokens

        return package

    def format_context_for_claude(self, package: Dict) -> str:
        """Format context package for Claude."""
        parts = []

        # Add full files
        if package['full_files']:
            parts.append("=== Complete Files ===\n")
            for item in package['full_files']:
                parts.append(f"\nFile: {item['file']}")
                parts.append(f"```\n{item['content']}\n```\n")

        # Add summaries
        if package['summaries']:
            parts.append("\n=== File Summaries ===\n")
            for summary in package['summaries']:
                parts.append(f"\nFile: {summary['file']}")

                if 'classes' in summary:
                    parts.append("Classes:")
                    for cls in summary['classes']:
                        parts.append(f"  - {cls['name']}")
                        parts.append(f"    Methods: {', '.join(cls['methods'])}")

                    parts.append("Functions:")
                    for func in summary['functions']:
                        parts.append(f"  - {func['name']}({', '.join(func['args'])})")

        parts.append(f"\nTotal tokens: {package['total_tokens']:,}")

        return '\n'.join(parts)

# Usage example
if __name__ == '__main__':
    optimizer = ContextOptimizer(max_tokens_per_chunk=4000)

    # Analyze and chunk large file
    chunks = optimizer.chunk_large_file('large_module.py')
    print(f"Split into {len(chunks)} chunks")

    # Create optimized context package
    files = ['service.py', 'models.py', 'utils.py', 'large_file.py']
    package = optimizer.create_context_package(files, max_total_tokens=50000)

    print(f"\nContext package:")
    print(f"  Full files: {len(package['full_files'])}")
    print(f"  Summaries: {len(package['summaries'])}")
    print(f"  Total tokens: {package['total_tokens']:,}")

    # Format for Claude
    formatted = optimizer.format_context_for_claude(package)
    print(f"\nFormatted context: {len(formatted)} characters")
```

### Phase 3: Smart Context Selection

#### Step 4: Implement Intelligent File Selection

```python
# smart_context.py
"""
Intelligently select which files to include in context based on task.
"""
import re
from typing import List, Set, Dict
from pathlib import Path

class SmartContextSelector:
    """Select relevant files for specific tasks."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.token_counter = TokenCounter()

    def select_files_for_task(
        self,
        task_description: str,
        max_tokens: int = 50000
    ) -> List[str]:
        """
        Select relevant files based on task description.

        Uses heuristics to determine relevance.
        """
        # Extract keywords from task
        keywords = self._extract_keywords(task_description)

        # Find relevant files
        candidates = self._find_candidate_files(keywords)

        # Rank by relevance
        ranked = self._rank_files(candidates, keywords)

        # Select files within token budget
        selected = self._select_within_budget(ranked, max_tokens)

        return selected

    def _extract_keywords(self, task_description: str) -> Set[str]:
        """Extract relevant keywords from task description."""
        # Common programming keywords
        keywords = set()

        # Extract class/function names (CamelCase, snake_case)
        camel_case = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', task_description)
        snake_case = re.findall(r'\b[a-z]+(?:_[a-z]+)+\b', task_description)

        keywords.update(camel_case)
        keywords.update(snake_case)

        # Extract file extensions mentioned
        extensions = re.findall(r'\.([a-z]+)\b', task_description)
        keywords.update(f".{ext}" for ext in extensions)

        # Extract quoted terms
        quoted = re.findall(r'"([^"]+)"', task_description)
        keywords.update(quoted)

        return keywords

    def _find_candidate_files(self, keywords: Set[str]) -> Dict[str, int]:
        """Find files that match keywords."""
        candidates = {}

        for filepath in self.project_root.rglob('*'):
            if filepath.is_file() and self._should_include(filepath):
                score = self._calculate_relevance(filepath, keywords)
                if score > 0:
                    candidates[str(filepath)] = score

        return candidates

    def _should_include(self, filepath: Path) -> bool:
        """Check if file should be considered."""
        # Skip common excluded paths
        exclude = {'.git', '__pycache__', 'node_modules', '.venv', 'dist', 'build'}
        if any(part in exclude for part in filepath.parts):
            return False

        # Include source files only
        include_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx',
            '.java', '.go', '.rs', '.cpp', '.c',
            '.cs', '.rb', '.php'
        }
        return filepath.suffix in include_extensions

    def _calculate_relevance(self, filepath: Path, keywords: Set[str]) -> int:
        """Calculate relevance score for file."""
        score = 0

        # Check filename match
        filename_lower = filepath.name.lower()
        for keyword in keywords:
            if keyword.lower() in filename_lower:
                score += 5

        # Check file content for keywords
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().lower()

            for keyword in keywords:
                count = content.count(keyword.lower())
                score += count

        except Exception:
            pass

        return score

    def _rank_files(
        self,
        candidates: Dict[str, int],
        keywords: Set[str]
    ) -> List[Tuple[str, int, int]]:
        """Rank files by relevance and token count."""
        ranked = []

        for filepath, relevance in candidates.items():
            try:
                tokens = self.token_counter.count_tokens_in_file(filepath)
                ranked.append((filepath, relevance, tokens))
            except Exception:
                continue

        # Sort by relevance (descending)
        ranked.sort(key=lambda x: x[1], reverse=True)

        return ranked

    def _select_within_budget(
        self,
        ranked: List[Tuple[str, int, int]],
        max_tokens: int
    ) -> List[str]:
        """Select files within token budget."""
        selected = []
        total_tokens = 0

        for filepath, relevance, tokens in ranked:
            if total_tokens + tokens <= max_tokens:
                selected.append(filepath)
                total_tokens += tokens

        return selected

    def get_dependencies(self, filepath: str) -> List[str]:
        """
        Get files that this file depends on.

        Useful for including related files in context.
        """
        dependencies = set()

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract Python imports
            import_pattern = r'from\s+([a-zA-Z0-9_.]+)\s+import|import\s+([a-zA-Z0-9_.]+)'
            matches = re.findall(import_pattern, content)

            for match in matches:
                module = match[0] or match[1]

                # Skip standard library
                if not self._is_stdlib(module):
                    # Try to find corresponding file
                    potential_file = self._module_to_file(module)
                    if potential_file and potential_file.exists():
                        dependencies.add(str(potential_file))

        except Exception:
            pass

        return list(dependencies)

    def _is_stdlib(self, module: str) -> bool:
        """Check if module is standard library."""
        stdlib = {
            'os', 'sys', 'json', 're', 'time', 'datetime',
            'pathlib', 'typing', 'collections', 'itertools'
        }
        return module.split('.')[0] in stdlib

    def _module_to_file(self, module: str) -> Path:
        """Convert module path to file path."""
        # Replace dots with path separators
        rel_path = module.replace('.', '/')

        # Try .py file
        py_file = self.project_root / f"{rel_path}.py"
        if py_file.exists():
            return py_file

        # Try __init__.py in package
        init_file = self.project_root / rel_path / '__init__.py'
        if init_file.exists():
            return init_file

        return None

# Usage
if __name__ == '__main__':
    selector = SmartContextSelector('src/')

    task = """
    Review the UserService class for security vulnerabilities.
    Check authentication and authorization logic.
    """

    files = selector.select_files_for_task(task, max_tokens=30000)
    print(f"Selected {len(files)} files for task:")
    for f in files:
        print(f"  - {f}")
```

### Phase 4: Caching and Reuse

#### Step 5: Implement Context Caching

```python
# context_cache.py
"""
Cache frequently used context to avoid re-sending.
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional

class ContextCache:
    """Cache context chunks to avoid resending."""

    def __init__(self, cache_dir: str = '.context_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_file_hash(self, filepath: str) -> str:
        """Get hash of file content."""
        with open(filepath, 'rb') as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()[:16]

    def cache_context(
        self,
        context_id: str,
        content: str,
        metadata: Dict = None
    ):
        """Cache context with ID."""
        cache_file = self.cache_dir / f"{context_id}.json"

        data = {
            'content': content,
            'metadata': metadata or {},
            'tokens': TokenCounter().count_tokens(content)
        }

        with open(cache_file, 'w') as f:
            json.dump(data, f)

    def get_cached_context(self, context_id: str) -> Optional[Dict]:
        """Retrieve cached context."""
        cache_file = self.cache_dir / f"{context_id}.json"

        if not cache_file.exists():
            return None

        with open(cache_file, 'r') as f:
            return json.load(f)

    def create_reference_context(
        self,
        files: List[str]
    ) -> str:
        """
        Create reference-based context instead of including full content.

        Instead of sending full files, send references to cached content.
        """
        references = []

        for filepath in files:
            file_hash = self.get_file_hash(filepath)

            # Cache if not already cached
            if not self.get_cached_context(file_hash):
                with open(filepath, 'r') as f:
                    content = f.read()
                self.cache_context(file_hash, content, {'file': filepath})

            references.append({
                'file': filepath,
                'cache_id': file_hash,
                'note': 'Full content cached - reference only'
            })

        # Create compact reference context
        context = "=== Cached Files (reference only) ===\n"
        for ref in references:
            context += f"\nFile: {ref['file']} (ID: {ref['cache_id']})\n"

        return context

# Usage
cache = ContextCache()

# Cache common files
common_files = ['models.py', 'utils.py', 'config.py']
reference_context = cache.create_reference_context(common_files)

print("Reference context (very compact):")
print(reference_context)
print(f"\nTokens: {TokenCounter().count_tokens(reference_context)}")
```

## Expected Outcomes

After optimization:

1. **Reduced token usage**
   - 30-50% reduction in typical cases
   - Stay within context limits
   - Lower API costs

2. **Faster responses**
   - Smaller contexts = faster processing
   - More efficient communication
   - Better user experience

3. **Better context quality**
   - More relevant information included
   - Less noise and redundancy
   - Focused on task at hand

4. **Scalability**
   - Can handle larger codebases
   - Multiple iterations possible
   - Long conversations maintained

## Success Criteria

- [ ] Token usage measured and baselined
- [ ] Large files identified and optimized
- [ ] Chunking strategy implemented
- [ ] Smart file selection working
- [ ] Context summaries created
- [ ] Caching mechanism in place
- [ ] 30%+ token reduction achieved
- [ ] Context quality maintained or improved

## Common Pitfalls

1. **Over-optimization**
   - Don't sacrifice context quality for token count
   - Keep necessary information

2. **Poor chunking**
   - Maintain logical code boundaries
   - Don't break related code apart

3. **Missing dependencies**
   - Include files that are imported
   - Maintain context coherence

4. **Aggressive summarization**
   - Summaries should be informative
   - Don't lose critical details

## Related Skills

- **create-subagent-workflow**: Delegate to specialized agents
- **code-complexity-analysis**: Identify complex code
- **refactor-for-testability**: Simplify code structure

## Additional Resources

### Tools
- **tiktoken**: Token counting for OpenAI models
- **anthropic-sdk**: Official Claude SDK
- **token-count**: CLI tool for counting tokens

### Best Practices
- Prefer summaries for reference code
- Include full content only for code being modified
- Use chunking for large files
- Cache frequently accessed code
- Measure before and after optimization

### Limits
- Claude 3.5 Sonnet: 200K token context window
- Claude 3 Opus: 200K token context window
- Claude 3 Haiku: 200K token context window

---

**Note**: Token optimization is an ongoing process. Regularly review and refine your context management strategies based on usage patterns.
