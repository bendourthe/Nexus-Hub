---
template_id: SKILL
template_name: Code-Complexity-Analysis - Generic
version: 1.0.0
last_updated: 2025-12-03
language: Generic
category: skills
phase: code-complexity-analysis
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tags:

  - skills

  - generic
---
# code-complexity-analysis

---
category: security-quality
priority: MEDIUM
languages: [python, javascript, typescript, java, csharp, go, rust]
requires_user_input: false
estimated_duration: 30min-2 hours
---

## Overview

Analyze code complexity using multiple metrics (cyclomatic, cognitive, halstead), identify problematic areas, and provide actionable refactoring recommendations to improve maintainability.

## When to Use This Skill

- Code reviews revealing difficult-to-understand code

- High bug rates in certain modules

- Onboarding new developers struggling with codebase

- Pre-refactoring assessment needed

- Technical debt analysis

- Code quality gates for CI/CD

## Prerequisites

- Access to codebase

- Static analysis tools installed

- Understanding of complexity metrics

- Ability to refactor code (if implementing fixes)

## Step-by-Step Instructions

### Phase 1: Analysis Setup

#### Step 1: Install Complexity Analysis Tools

**Python:**

```bash
# Install complexity analysis tools
pip install radon          # Cyclomatic complexity
pip install mccabe         # McCabe complexity
pip install cognitive-complexity  # Cognitive complexity
pip install lizard         # Multi-language analyzer
pip install wily           # Track complexity over time

# Install code quality tools
pip install pylint flake8 bandit
```

**JavaScript/TypeScript:**

```bash
# Install ESLint with complexity plugins
npm install --save-dev eslint
npm install --save-dev eslint-plugin-complexity
npm install --save-dev typescript-eslint

# Install specialized tools
npm install --save-dev complexity-report
npm install --save-dev plato
npm install --save-dev jscpd  # Copy-paste detector
```

**Multi-language:**

```bash
# Lizard supports many languages
pip install lizard

# SonarQube for comprehensive analysis
docker run -d --name sonarqube -p 9000:9000 sonarqube:latest
```

#### Step 2: Run Initial Complexity Scan

**Python with Radon:**

```bash
# Cyclomatic complexity
radon cc src/ -a -s

# Output:
# src/order_service.py
#     M 156:4 OrderService.process_order - B (13)
#     M 201:4 OrderService.validate_payment - A (5)
#     C 45:0 OrderProcessor - B (9)

# Maintainability index
radon mi src/ -s

# Complexity trend over time
wily build src/
wily report src/ -m cyclomatic.complexity
```

**JavaScript with ESLint:**

```bash
# Run complexity analysis
npx eslint src/ --ext .js,.ts \
  --rule 'complexity: ["error", 10]' \
  --rule 'max-depth: ["error", 3]' \
  --rule 'max-nested-callbacks: ["error", 3]' \
  --format json > complexity-report.json

# Generate HTML report
npx complexity-report src/ --output complexity-report.html
```

**Cross-language with Lizard:**

```bash
# Analyze entire project
lizard src/ -l python -l javascript -o complexity-report.html

# Filter by complexity threshold
lizard src/ -C 15 -w

# Output:
# File: src/order_processor.py
#   Function: process_complex_order at line 145
#   Cyclomatic Complexity: 18
#   Lines of Code: 87
#   Token Count: 342
```

### Phase 2: Metrics Analysis

#### Step 3: Understanding Complexity Metrics

**Cyclomatic Complexity (McCabe):**

```python
# Example function with complexity 1 (simplest)
def simple_function(x):
    return x + 1

# Complexity 2 (one decision point)
def with_if(x):
    if x > 0:
        return x
    return 0

# Complexity 4 (three decision points)
def multiple_conditions(x, y):
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x
    else:
        return y

# Complexity 10 (many branches)
def high_complexity(order):
    """High cyclomatic complexity - needs refactoring."""
    if not order:
        return None

    if order.status == "pending":
        if order.payment_verified:
            if order.items_available:
                if order.shipping_valid:
                    return process_order(order)
                else:
                    return "Invalid shipping"
            else:
                return "Items unavailable"
        else:
            return "Payment not verified"
    elif order.status == "processing":
        return check_processing_status(order)
    elif order.status == "shipped":
        return track_shipment(order)
    else:
        return "Unknown status"

# Calculate complexity
from radon.complexity import cc_visit

complexity = cc_visit("""
def high_complexity(order):
    # ... function code here ...
""")

print(f"Complexity: {complexity[0].complexity}")
```

**Cognitive Complexity:**

```python
# Cyclomatic: 4, Cognitive: 7 (harder to understand)
def cognitive_example(items):
    total = 0
    for item in items:          # +1
        if item.is_valid:       # +2 (nested)
            if item.in_stock:   # +3 (nested)
                total += item.price
            else:
                notify_out_of_stock(item)
        elif item.is_backorder:  # +1
            schedule_backorder(item)
    return total

# Lower cognitive complexity (same logic)
def refactored_example(items):
    total = 0
    for item in items:              # +1
        total += process_item(item) # Extracted complexity
    return total

def process_item(item):
    if not item.is_valid:
        return 0
    if not item.in_stock:
        notify_out_of_stock(item)
        return 0
    if item.is_backorder:
        schedule_backorder(item)
    return item.price
```

**Maintainability Index:**

```python
# Formula: MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
# HV = Halstead Volume
# CC = Cyclomatic Complexity
# LOC = Lines of Code

# Good maintainability (MI > 65)
def well_maintained_function(data):
    """Clear, simple function."""
    if not data:
        return []
    return [item for item in data if item.is_valid]

# Poor maintainability (MI < 65)
def poorly_maintained_function(data, config, options, flags, handlers):
    """Complex function with many parameters and logic."""
    results = []
    for item in data:
        if config['mode'] == 'strict':
            if item.validate(options):
                if flags.get('process', True):
                    try:
                        processed = handlers['processor'](item, config, options)
                        if processed and processed.is_valid():
                            results.append(processed)
                    except Exception as e:
                        if flags.get('continue_on_error', False):
                            log_error(e, item, config)
                        else:
                            raise
    return results
```

#### Step 4: Generate Complexity Report

```python
# generate_complexity_report.py
"""
Generate comprehensive complexity report for codebase.
"""
import os
import json
from radon.complexity import cc_visit
from radon.metrics import mi_visit, h_visit
from pathlib import Path

class ComplexityAnalyzer:
    def __init__(self, source_dir):
        self.source_dir = Path(source_dir)
        self.results = {
            'high_complexity': [],
            'moderate_complexity': [],
            'low_maintainability': [],
            'summary': {}
        }

    def analyze_file(self, filepath):
        """Analyze single Python file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()

        # Cyclomatic complexity
        cc_results = cc_visit(code)
        mi_result = mi_visit(code, False)

        for item in cc_results:
            complexity_data = {
                'file': str(filepath),
                'name': item.name,
                'line': item.lineno,
                'complexity': item.complexity,
                'rank': item.letter,
                'type': item.classname or 'function'
            }

            # Categorize by complexity
            if item.complexity > 15:
                self.results['high_complexity'].append(complexity_data)
            elif item.complexity > 10:
                self.results['moderate_complexity'].append(complexity_data)

        # Maintainability index
        if mi_result < 65:
            self.results['low_maintainability'].append({
                'file': str(filepath),
                'mi_score': mi_result
            })

    def analyze_directory(self):
        """Analyze all Python files in directory."""
        for filepath in self.source_dir.rglob('*.py'):
            if 'test' not in str(filepath) and '__pycache__' not in str(filepath):
                try:
                    self.analyze_file(filepath)
                except Exception as e:
                    print(f"Error analyzing {filepath}: {e}")

        # Generate summary
        self.results['summary'] = {
            'total_high_complexity': len(self.results['high_complexity']),
            'total_moderate_complexity': len(self.results['moderate_complexity']),
            'total_low_maintainability': len(self.results['low_maintainability']),
            'files_analyzed': len(list(self.source_dir.rglob('*.py')))
        }

    def generate_report(self, output_file='complexity_report.json'):
        """Generate JSON report."""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        # Print summary
        print("\n" + "="*60)
        print("CODE COMPLEXITY ANALYSIS REPORT")
        print("="*60)
        print(f"\nFiles analyzed: {self.results['summary']['files_analyzed']}")
        print(f"High complexity functions: {self.results['summary']['total_high_complexity']}")
        print(f"Moderate complexity functions: {self.results['summary']['total_moderate_complexity']}")
        print(f"Low maintainability files: {self.results['summary']['total_low_maintainability']}")

        if self.results['high_complexity']:
            print("\n⚠️  HIGH COMPLEXITY FUNCTIONS (CC > 15):")
            for item in sorted(self.results['high_complexity'],
                             key=lambda x: x['complexity'],
                             reverse=True)[:10]:
                print(f"  {item['file']}:{item['line']}")
                print(f"    {item['name']} - Complexity: {item['complexity']} (Rank: {item['rank']})")

        print("\nReport saved to:", output_file)

# Usage
if __name__ == '__main__':
    analyzer = ComplexityAnalyzer('src/')
    analyzer.analyze_directory()
    analyzer.generate_report()
```

### Phase 3: Refactoring Strategies

#### Step 5: Reduce Cyclomatic Complexity

**Strategy 1: Extract Methods**

```python
# BEFORE: High complexity (CC = 12)
def process_order(order):
    if not order:
        return None

    if order.status != "pending":
        return {"error": "Invalid status"}

    if not validate_customer(order.customer_id):
        return {"error": "Invalid customer"}

    if not check_inventory(order.items):
        return {"error": "Insufficient inventory"}

    payment_result = process_payment(order.payment_info)
    if not payment_result.success:
        return {"error": "Payment failed"}

    shipping_result = arrange_shipping(order.shipping_info)
    if not shipping_result.success:
        return {"error": "Shipping failed"}

    order.status = "confirmed"
    save_order(order)
    send_confirmation_email(order)

    return {"success": True, "order_id": order.id}

# AFTER: Lower complexity (CC = 3 for each function)
def process_order(order):
    """Process order with validation."""
    if not order:
        return None

    validation_error = validate_order(order)
    if validation_error:
        return validation_error

    return execute_order(order)

def validate_order(order):
    """Validate order can be processed."""
    if order.status != "pending":
        return {"error": "Invalid status"}

    if not validate_customer(order.customer_id):
        return {"error": "Invalid customer"}

    if not check_inventory(order.items):
        return {"error": "Insufficient inventory"}

    return None

def execute_order(order):
    """Execute order processing steps."""
    payment_result = process_payment(order.payment_info)
    if not payment_result.success:
        return {"error": "Payment failed"}

    shipping_result = arrange_shipping(order.shipping_info)
    if not shipping_result.success:
        rollback_payment(payment_result.transaction_id)
        return {"error": "Shipping failed"}

    finalize_order(order)
    return {"success": True, "order_id": order.id}

def finalize_order(order):
    """Finalize order and notify customer."""
    order.status = "confirmed"
    save_order(order)
    send_confirmation_email(order)
```

**Strategy 2: Replace Conditional with Polymorphism**

```python
# BEFORE: High complexity due to type checking
def calculate_shipping(order):
    if order.shipping_type == "standard":
        if order.weight < 5:
            return 5.00
        elif order.weight < 10:
            return 8.00
        else:
            return 12.00
    elif order.shipping_type == "express":
        if order.weight < 5:
            return 15.00
        elif order.weight < 10:
            return 20.00
        else:
            return 30.00
    elif order.shipping_type == "overnight":
        if order.weight < 5:
            return 25.00
        elif order.weight < 10:
            return 35.00
        else:
            return 50.00

# AFTER: Polymorphic approach
from abc import ABC, abstractmethod

class ShippingCalculator(ABC):
    @abstractmethod
    def calculate(self, weight):
        pass

class StandardShipping(ShippingCalculator):
    def calculate(self, weight):
        if weight < 5:
            return 5.00
        elif weight < 10:
            return 8.00
        else:
            return 12.00

class ExpressShipping(ShippingCalculator):
    def calculate(self, weight):
        if weight < 5:
            return 15.00
        elif weight < 10:
            return 20.00
        else:
            return 30.00

class OvernightShipping(ShippingCalculator):
    def calculate(self, weight):
        if weight < 5:
            return 25.00
        elif weight < 10:
            return 35.00
        else:
            return 50.00

# Factory to create calculator
shipping_calculators = {
    "standard": StandardShipping(),
    "express": ExpressShipping(),
    "overnight": OvernightShipping()
}

def calculate_shipping(order):
    calculator = shipping_calculators.get(order.shipping_type)
    if not calculator:
        raise ValueError(f"Unknown shipping type: {order.shipping_type}")
    return calculator.calculate(order.weight)
```

**Strategy 3: Use Strategy Pattern**

```python
# BEFORE: Complex conditional logic
def apply_discount(order, customer):
    if customer.loyalty_tier == "gold":
        if order.total > 1000:
            discount = order.total * 0.20
        elif order.total > 500:
            discount = order.total * 0.15
        else:
            discount = order.total * 0.10
    elif customer.loyalty_tier == "silver":
        if order.total > 1000:
            discount = order.total * 0.15
        elif order.total > 500:
            discount = order.total * 0.10
        else:
            discount = order.total * 0.05
    elif customer.loyalty_tier == "bronze":
        if order.total > 1000:
            discount = order.total * 0.10
        else:
            discount = order.total * 0.05
    else:
        discount = 0

    return discount

# AFTER: Strategy pattern
from typing import Protocol

class DiscountStrategy(Protocol):
    def calculate(self, order_total: float) -> float:
        ...

class GoldTierDiscount:
    def calculate(self, order_total: float) -> float:
        if order_total > 1000:
            return order_total * 0.20
        elif order_total > 500:
            return order_total * 0.15
        else:
            return order_total * 0.10

class SilverTierDiscount:
    def calculate(self, order_total: float) -> float:
        if order_total > 1000:
            return order_total * 0.15
        elif order_total > 500:
            return order_total * 0.10
        else:
            return order_total * 0.05

class BronzeTierDiscount:
    def calculate(self, order_total: float) -> float:
        if order_total > 1000:
            return order_total * 0.10
        else:
            return order_total * 0.05

class NoDiscount:
    def calculate(self, order_total: float) -> float:
        return 0

discount_strategies = {
    "gold": GoldTierDiscount(),
    "silver": SilverTierDiscount(),
    "bronze": BronzeTierDiscount(),
    "none": NoDiscount()
}

def apply_discount(order, customer):
    strategy = discount_strategies.get(
        customer.loyalty_tier,
        discount_strategies["none"]
    )
    return strategy.calculate(order.total)
```

#### Step 6: Reduce Cognitive Complexity

**Strategy: Early Returns / Guard Clauses**

```python
# BEFORE: High nesting (high cognitive complexity)
def process_payment(payment_info, order):
    if payment_info:
        if payment_info.card_number:
            if validate_card(payment_info.card_number):
                if payment_info.amount == order.total:
                    if charge_card(payment_info):
                        return {"success": True}
                    else:
                        return {"error": "Charge failed"}
                else:
                    return {"error": "Amount mismatch"}
            else:
                return {"error": "Invalid card"}
        else:
            return {"error": "Missing card number"}
    else:
        return {"error": "Missing payment info"}

# AFTER: Guard clauses (lower cognitive complexity)
def process_payment(payment_info, order):
    """Process payment with guard clauses."""
    if not payment_info:
        return {"error": "Missing payment info"}

    if not payment_info.card_number:
        return {"error": "Missing card number"}

    if not validate_card(payment_info.card_number):
        return {"error": "Invalid card"}

    if payment_info.amount != order.total:
        return {"error": "Amount mismatch"}

    if not charge_card(payment_info):
        return {"error": "Charge failed"}

    return {"success": True}
```

### Phase 4: Continuous Monitoring

#### Step 7: Setup Complexity Monitoring

```yaml
# .github/workflows/complexity-check.yml
name: Complexity Check

on: [pull_request]

jobs:
  complexity:
    runs-on: ubuntu-latest
    steps:

    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install tools
      run: |
        pip install radon lizard

    - name: Check complexity
      run: |
        # Fail if any function has complexity > 15
        radon cc src/ -n C -s

    - name: Generate report
      if: always()
      run: |
        radon cc src/ -a -s > complexity-report.txt
        lizard src/ -o complexity-lizard.html

    - name: Upload report
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: complexity-reports
        path: |
          complexity-report.txt
          complexity-lizard.html
```

**Pre-commit hook:**

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Checking code complexity..."

# Check complexity of staged Python files
staged_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -n "$staged_files" ]; then
    for file in $staged_files; do
        # Check if complexity exceeds threshold
        complexity=$(radon cc "$file" -n C -s | grep -c "^")

        if [ "$complexity" -gt 0 ]; then
            echo "❌ High complexity detected in $file"
            radon cc "$file" -n C -s
            echo ""
            echo "Please refactor functions with complexity > 10 before committing."
            exit 1
        fi
    done
fi

echo "✅ Complexity check passed"
```

## Expected Outcomes

After completing this analysis:

1. **Complexity metrics measured**

   - Cyclomatic complexity scores

   - Cognitive complexity analysis

   - Maintainability index calculated

2. **Problem areas identified**

   - High-complexity functions flagged

   - Code smells detected

   - Technical debt quantified

3. **Refactoring roadmap created**

   - Prioritized list of functions to refactor

   - Specific strategies recommended

   - Estimated effort for improvements

4. **Quality gates established**

   - CI/CD checks for complexity

   - Automated monitoring

   - Trending analysis

## Success Criteria

- [ ] Complexity analysis completed for entire codebase

- [ ] All functions with CC > 15 identified

- [ ] Refactoring recommendations provided

- [ ] At least 80% of high-complexity functions refactored

- [ ] Maintainability index improved by 10%

- [ ] Automated complexity checks in CI/CD

- [ ] Team trained on complexity metrics

- [ ] Documentation updated with standards

## Common Pitfalls

1. **Over-optimizing**

   - Don't refactor everything, focus on problem areas

   - Balance complexity reduction with code clarity

2. **Ignoring context**

   - Some complex algorithms are inherently complex

   - Domain complexity may require code complexity

3. **Premature abstraction**

   - Don't add layers just to reduce metrics

   - Keep it simple and readable

## Related Skills

- **refactor-for-testability**: Improve testability

- **add-unit-tests**: Add comprehensive tests

- **setup-python-project**: Project setup

- **code-review**: Review code quality

## Additional Resources

### Tools
- **Radon** (Python): https://radon.readthedocs.io/

- **Lizard** (Multi-language): https://github.com/terryyin/lizard

- **SonarQube**: https://www.sonarqube.org/

- **CodeClimate**: https://codeclimate.com/

### Metrics
- Cyclomatic Complexity: Measures decision points

- Cognitive Complexity: Measures understandability

- Halstead Metrics: Measures program difficulty

- Maintainability Index: Overall maintainability score

### Thresholds
- CC 1-10: Simple, low risk

- CC 11-20: Moderate, medium risk

- CC 21-50: Complex, high risk

- CC 50+: Untestable, very high risk

---

**Note**: Complexity metrics are guidelines, not absolute rules. Use judgment and consider the specific context of your code.
