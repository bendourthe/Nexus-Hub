---
name: cleanup-csharp
description: Remove dead code, consolidate duplicates, and modernize C# codebases for improved maintainability
version: 1.0.0
author: Benjamin Dourthe
language: C#
category: Code Cleanup
priority: MEDIUM
tags: [csharp, dotnet, cleanup, refactoring, modernization, dead-code, linq, async]
template_source: code_cleanup/csharp_cleanup.md
---

# C# Code Cleanup

Systematically identify and remove dead code, consolidate duplicate logic, and modernize legacy C# patterns to maintain a lean, current, and maintainable codebase.

## When to Use This Skill

Use this skill when you need to:
- Remove unused using directives, methods, classes, and properties
- Consolidate duplicate code and near-duplicate implementations
- Modernize legacy patterns (delegates to lambdas, string.Format to interpolation, manual null checks to nullable types)
- Clean up Console.WriteLine and Debug statements
- Optimize using directive organization and code structure
- Prepare codebase for new features or refactoring
- Reduce technical debt before major releases
- Remove unused NuGet packages

## What This Skill Does

This skill performs comprehensive C# code cleanup:

### 1. Dead Code Detection
- **Unused Using Directives**: Identifies and removes unused using statements
- **Unused Methods**: Finds private methods never called
- **Unused Classes**: Detects classes without instantiation
- **Unused Properties/Fields**: Identifies members assigned but never read
- **Unreachable Code**: Finds code after return/break/continue statements
- **Empty Blocks**: Detects empty methods, classes, or catch blocks
- **Unused NuGet Packages**: Identifies packages not used in code

### 2. Duplicate Code Consolidation
- **Exact Duplicates**: Finds identical code blocks for consolidation
- **Near Duplicates**: Detects similar code with minor variations
- **Duplicate Logic**: Identifies functionally equivalent implementations
- **Copy-Paste Detection**: Finds code copied across classes
- **Consolidation Strategy**: Recommends refactoring approach

### 3. Code Modernization (C# 6+)
- **Null-conditional Operators**: Uses `?.` for null checks
- **Null-coalescing Operators**: Uses `??` for defaults
- **String Interpolation**: Replaces string.Format with $""
- **Expression-bodied Members**: Uses `=>` for simple methods
- **Auto-property Initializers**: Initializes properties inline
- **nameof Operator**: Uses nameof() instead of magic strings

### 4. Code Modernization (C# 7+)
- **Out Variables**: Declares out variables inline
- **Discards**: Uses `_` for unused values
- **Local Functions**: Extracts nested functionality
- **Throw Expressions**: Uses throw in expressions
- **Pattern Matching**: Uses pattern matching with is/switch

### 5. Code Modernization (C# 8+)
- **Nullable Reference Types**: Enables and addresses warnings
- **Switch Expressions**: Replaces switch statements
- **Using Declarations**: Replaces using statements
- **Null-coalescing Assignment**: Uses `??=` operator
- **Indices and Ranges**: Uses `^` and `..` for collections

### 6. Code Modernization (C# 9-11+)
- **Records**: Replaces simple POCOs (C# 9)
- **Init-only Properties**: Uses init for immutability (C# 9)
- **Target-typed New**: Uses `new()` (C# 9)
- **File-scoped Namespaces**: Removes namespace braces (C# 10)
- **Global Usings**: Moves common usings (C# 10)
- **Required Members**: Uses required keyword (C# 11)
- **Raw String Literals**: Uses raw strings (C# 11)

### 7. Debug Statement Cleanup
- **Console Statements**: Removes debug Console.WriteLine()
- **Debug Statements**: Removes Debug.WriteLine()
- **Commented Code**: Cleans up old commented-out code
- **TODO Comments**: Catalogs and prioritizes TODO items
- **Conditional Compilation**: Reviews #if DEBUG blocks

### 8. Using Directive Organization
- **System Namespaces**: Groups System.* imports
- **Third-Party**: Organizes external dependencies
- **Internal Namespaces**: Structures project imports
- **Unused Removal**: Eliminates unnecessary usings
- **Duplicate Usings**: Consolidates repeated usings

## Prerequisites

- C#/.NET codebase to clean up
- Version control (git) for safe cleanup with rollback capability
- Test suite for regression verification (recommended)
- Backup of codebase or committed state
- .NET SDK installed

## Instructions

### Step 1: Prepare for Cleanup

1. **Commit Current State**:
   ```bash
   git add .
   git commit -m "Pre-cleanup snapshot"
   ```

2. **Create Cleanup Branch** (recommended):
   ```bash
   git checkout -b code-cleanup
   ```

3. **Run Existing Tests**:
   ```bash
   dotnet test
   ```

4. **Run Code Analysis**:
   ```bash
   dotnet format --verify-no-changes
   dotnet build /p:TreatWarningsAsErrors=true
   ```

5. **Create Output Directory**:
   ```bash
   mkdir -p cleanup_report/{templates,assets,exports}
   ```

### Step 2: Invoke the Cleanup Skill

Tell Claude Code to use this skill:

```
"Use the cleanup-csharp skill to analyze and clean up this C# codebase.
Focus on:

1. Removing all unused using directives, methods, and properties
2. Consolidating duplicate code
3. Modernizing to C# 8+ patterns (nullable types, switch expressions, using declarations)
4. Removing Console.WriteLine and Debug statements
5. Organizing using directives properly
6. Identifying unused NuGet packages

Save all reports to cleanup_report/ directory."
```

### Step 3: Review Cleanup Plan

Claude Code will generate a comprehensive cleanup plan including:

1. **Dead Code Candidates** - List of unused code with usage analysis
2. **Duplication Report** - Duplicate code locations with consolidation strategy
3. **Modernization Opportunities** - Legacy patterns to update
4. **Code Smells** - Long methods, god classes, feature envy
5. **Risk Assessment** - Impact analysis for each cleanup operation
6. **Implementation Plan** - Ordered steps with dependencies

**Review the plan before proceeding with changes!**

### Step 4: Execute Cleanup in Phases

**Phase 1: Low-Risk Cleanup**
- Remove unused using directives
- Clean Console.WriteLine/Debug statements
- Remove commented code
- Organize usings

**Phase 2: Code Modernization**
- Apply string interpolation
- Use null-conditional operators
- Apply expression-bodied members
- Use pattern matching
- Apply nullable reference types

**Phase 3: Structural Changes**
- Consolidate duplicates
- Remove dead methods
- Simplify complex code
- Extract constants

**Phase 4: Verification**
- Run tests after each phase
- Run dotnet format
- Verify no functionality changes
- Document any issues

**Phase 5: Multi-Pass Protocol**
- First pass: Apply cleanup across all files
- Verification pass: Check for missed opportunities
- Repeat until complete
- Track statistics for each pass

### Step 5: Test After Cleanup

1. **Run Full Test Suite**:
   ```bash
   dotnet test
   ```

2. **Code Formatting**:
   ```bash
   dotnet format
   dotnet format --verify-no-changes
   ```

3. **Build Verification**:
   ```bash
   dotnet clean
   dotnet build
   ```

4. **Static Analysis** (if configured):
   ```bash
   dotnet build /p:TreatWarningsAsErrors=true
   ```

### Step 6: Review and Commit

1. **Review Changes**:
   ```bash
   git diff
   ```

2. **Stage and Commit** (in logical chunks):
   ```bash
   git add .
   git commit -m "Remove unused using directives and methods"

   git add .
   git commit -m "Modernize to C# 8 nullable reference types and switch expressions"

   git add .
   git commit -m "Consolidate duplicate validation logic"
   ```

3. **Merge to Main** (when satisfied):
   ```bash
   git checkout main
   git merge code-cleanup
   git push
   ```

## Cleanup Categories and Examples

### Category 1: Unused Using Directives
**Before:**
```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

namespace MyApp.Services
{
    public class DataService
    {
        public string ProcessData(string data) => data.ToUpper();
    }
}
```

**After:**
```csharp
namespace MyApp.Services
{
    public class DataService
    {
        public string ProcessData(string data) => data.ToUpper();
    }
}
```

### Category 2: Debug Statements
**Before:**
```csharp
public decimal CalculateTotal(List<Item> items)
{
    Console.WriteLine($"DEBUG: items count = {items.Count}");
    var total = items.Sum(i => i.Price);
    Debug.WriteLine($"DEBUG: total = {total}");
    Console.WriteLine($"Calculation complete");
    return total;
}
```

**After:**
```csharp
public decimal CalculateTotal(List<Item> items)
{
    return items.Sum(i => i.Price);
}
```

### Category 3: String Interpolation and Modern Features
**Before:**
```csharp
string message = string.Format("Hello, {0}! You have {1} messages.", name, count);

public string GetUserName(int userId)
{
    var user = users.FirstOrDefault(u => u.Id == userId);
    if (user != null)
    {
        return user.Name;
    }
    return "Anonymous";
}
```

**After:**
```csharp
string message = $"Hello, {name}! You have {count} messages.";

public string GetUserName(int userId)
{
    return users.FirstOrDefault(u => u.Id == userId)?.Name ?? "Anonymous";
}
```

### Category 4: Pattern Matching and Switch Expressions
**Before:**
```csharp
public string GetShapeDescription(object shape)
{
    if (shape is Circle)
    {
        var circle = (Circle)shape;
        return $"Circle with radius {circle.Radius}";
    }
    else if (shape is Rectangle)
    {
        var rectangle = (Rectangle)shape;
        return $"Rectangle {rectangle.Width}x{rectangle.Height}";
    }
    return "Unknown shape";
}
```

**After (C# 8+)**:
```csharp
public string GetShapeDescription(object shape) => shape switch
{
    Circle c => $"Circle with radius {c.Radius}",
    Rectangle r => $"Rectangle {r.Width}x{r.Height}",
    _ => "Unknown shape"
};
```

### Category 5: Using Declarations
**Before:**
```csharp
public async Task<string> ReadFileAsync(string path)
{
    using (var stream = new FileStream(path, FileMode.Open))
    using (var reader = new StreamReader(stream))
    {
        return await reader.ReadToEndAsync();
    }
}
```

**After (C# 8+)**:
```csharp
public async Task<string> ReadFileAsync(string path)
{
    using var stream = new FileStream(path, FileMode.Open);
    using var reader = new StreamReader(stream);
    return await reader.ReadToEndAsync();
}
```

### Category 6: Records and Init Properties
**Before:**
```csharp
public class Point
{
    public int X { get; set; }
    public int Y { get; set; }

    public Point(int x, int y)
    {
        X = x;
        Y = y;
    }

    public override bool Equals(object obj) { /* ... */ }
    public override int GetHashCode() { /* ... */ }
}
```

**After (C# 9+)**:
```csharp
public record Point(int X, int Y);

// Or with init-only properties:
public record Point
{
    public int X { get; init; }
    public int Y { get; init; }
}
```

### Category 7: File-scoped Namespaces
**Before:**
```csharp
using System;

namespace MyApp.Services
{
    public class DataService
    {
        public string Process(string data)
        {
            return data.ToUpper();
        }
    }
}
```

**After (C# 10+)**:
```csharp
using System;

namespace MyApp.Services;

public class DataService
{
    public string Process(string data)
    {
        return data.ToUpper();
    }
}
```

### Category 8: Duplicate Code Consolidation
**Before:**
```csharp
public bool ValidateUser(User user)
{
    if (string.IsNullOrEmpty(user.Name)) return false;
    if (string.IsNullOrEmpty(user.Email)) return false;
    if (!user.Email.Contains("@")) return false;
    return true;
}

public bool ValidateAdmin(Admin admin)
{
    if (string.IsNullOrEmpty(admin.Name)) return false;
    if (string.IsNullOrEmpty(admin.Email)) return false;
    if (!admin.Email.Contains("@")) return false;
    return true;
}
```

**After:**
```csharp
public interface IAccount
{
    string Name { get; }
    string Email { get; }
}

public bool ValidateAccount(IAccount account)
{
    if (string.IsNullOrEmpty(account.Name)) return false;
    if (string.IsNullOrEmpty(account.Email)) return false;
    if (!account.Email.Contains("@")) return false;
    return true;
}
```

## Output Structure

```
cleanup_report/
├── templates/
│   ├── cleanup_checklist.md
│   ├── modernization_guide.md
│   └── editorconfig.template
├── assets/
│   ├── duplication_graph.png
│   └── complexity_heatmap.png
└── exports/
    ├── cleanup_report.md
    ├── dead_code_list.md
    ├── duplication_analysis.md
    ├── modernization_plan.md
    ├── unused_packages.md
    └── risk_assessment.md
```

## Safety Measures

1. **Version Control Required**
2. **Test Coverage**
3. **Incremental Approach**
4. **Risk Assessment**
5. **Documentation**

## Success Criteria

- [ ] All unused using directives removed
- [ ] No Console.WriteLine/Debug debugging statements
- [ ] No commented-out code
- [ ] Duplicate code consolidated
- [ ] Modern C# patterns applied
- [ ] Using directives organized
- [ ] All tests passing
- [ ] Code builds successfully
- [ ] Cleanup documented

## Tools and Libraries

- **dotnet format**: Code formatting
- **StyleCop**: Style analysis
- **FxCop/Roslyn Analyzers**: Code analysis
- **ReSharper**: Comprehensive analysis
- **NDepend**: Dependency and quality metrics

```bash
# Install analyzers
dotnet add package StyleCop.Analyzers
dotnet add package Microsoft.CodeAnalysis.NetAnalyzers

# Run analysis
dotnet format
dotnet build /p:TreatWarningsAsErrors=true
```

## Additional Resources

- [C# Coding Conventions](https://docs.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- [C# What's New](https://docs.microsoft.com/en-us/dotnet/csharp/whats-new/)
- [.NET Application Architecture](https://dotnet.microsoft.com/learn/dotnet/architecture-guides)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - code_cleanup/csharp_cleanup.md
