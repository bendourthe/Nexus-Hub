### Step 3: Generate the Minimal Reproduction Test

Build the test that demonstrates the bug with the least amount of code possible.

**Python: Reproduction test generator**

```python
def generate_python_reproduction_test(spec: TestSpecification) -> str:
    """Generate a Python reproduction test from the specification."""
    test_name = generate_test_name(spec)
    imports = []
    setup_lines = []
    act_lines = []
    assert_lines = []

    # Determine imports
    if spec.module_under_test:
        module = spec.module_under_test.replace(".py", "")
        if spec.function_under_test:
            imports.append(f"from {module} import {spec.function_under_test}")
        else:
            imports.append(f"import {module}")

    if spec.error_type:
        imports.append("import pytest")

    # Build setup section
    for key, value in spec.input_values.items():
        setup_lines.append(f"    {key} = {repr(value)}")

    if not setup_lines:
        setup_lines.append("    # TODO: Add the specific input values from the bug report")

    # Build act section
    if spec.function_under_test:
        if spec.error_type:
            act_lines.append(f"    with pytest.raises({spec.error_type}):")
            act_lines.append(f"        {spec.function_under_test}()")
            act_lines.append(f"        # TODO: Add the arguments that trigger the bug")
        else:
            act_lines.append(f"    result = {spec.function_under_test}()")
            act_lines.append(f"    # TODO: Add the arguments that trigger the bug")
    else:
        act_lines.append("    # TODO: Call the function that triggers the bug")
        act_lines.append("    result = None")

    # Build assert section
    if spec.expected_output and not spec.error_type:
        assert_lines.append(f"    # Bug: actual output was: {spec.actual_output}")
        assert_lines.append(f"    # Expected: {spec.expected_output}")
        assert_lines.append(f"    assert result == {repr(spec.expected_output)}")
    elif not spec.error_type:
        assert_lines.append(f"    # TODO: Assert the expected behavior")
        assert_lines.append(f"    # Before fix: this assertion should FAIL")
        assert_lines.append(f"    # After fix: this assertion should PASS")
        assert_lines.append(f"    assert result is not None")

    # Compose the test
    parts = []
    if imports:
        parts.append("\n".join(imports))
        parts.append("")

    parts.append("")
    parts.append(f"def {test_name}():")
    parts.append(f'    """Reproduction test for bug{" " + spec.bug_id if spec.bug_id else ""}.')
    parts.append(f"")
    if spec.title:
        parts.append(f"    {spec.title}")
    if spec.actual_output:
        parts.append(f"    Bug: {spec.actual_output}")
    if spec.expected_output:
        parts.append(f"    Expected: {spec.expected_output}")
    parts.append(f'    """')

    parts.append("    # Arrange")
    parts.extend(setup_lines)
    parts.append("")
    parts.append("    # Act")
    parts.extend(act_lines)
    parts.append("")

    if assert_lines:
        parts.append("    # Assert")
        parts.extend(assert_lines)

    return "\n".join(parts) + "\n"
```

**JavaScript: Reproduction test generator**

```javascript
function generateJestReproductionTest(spec) {
  const testName = generateTestName(spec);
  const lines = [];

  // Imports
  if (spec.moduleUnderTest) {
    const modulePath = spec.moduleUnderTest.replace(/\.(js|ts)$/, "");
    if (spec.functionUnderTest) {
      lines.push(
        `const { ${spec.functionUnderTest} } = require("./${modulePath}");`
      );
    } else {
      lines.push(`const module = require("./${modulePath}");`);
    }
    lines.push("");
  }

  // Test block
  lines.push(`describe("Bug Reproduction${spec.bugId ? ` #${spec.bugId}` : ""}", () => {`);
  lines.push(`  it("${testName}", () => {`);

  // Documentation
  if (spec.actualOutput) {
    lines.push(`    // Bug: ${spec.actualOutput}`);
  }
  if (spec.expectedOutput) {
    lines.push(`    // Expected: ${spec.expectedOutput}`);
  }
  lines.push("");

  // Arrange
  lines.push("    // Arrange");
  if (Object.keys(spec.inputValues).length > 0) {
    for (const [key, value] of Object.entries(spec.inputValues)) {
      lines.push(`    const ${key} = ${JSON.stringify(value)};`);
    }
  } else {
    lines.push(
      "    // TODO: Add the specific input values from the bug report"
    );
  }
  lines.push("");

  // Act
  lines.push("    // Act");
  if (spec.functionUnderTest) {
    if (spec.errorType) {
      lines.push(
        `    expect(() => ${spec.functionUnderTest}()).toThrow(${spec.errorType});`
      );
      lines.push(
        "    // TODO: Add the arguments that trigger the bug"
      );
    } else {
      lines.push(
        `    const result = ${spec.functionUnderTest}();`
      );
      lines.push(
        "    // TODO: Add the arguments that trigger the bug"
      );
    }
  } else {
    lines.push("    // TODO: Call the function that triggers the bug");
    lines.push("    const result = null;");
  }
  lines.push("");

  // Assert
  if (!spec.errorType) {
    lines.push("    // Assert");
    lines.push("    // Before fix: this assertion should FAIL");
    lines.push("    // After fix: this assertion should PASS");
    if (spec.expectedOutput) {
      lines.push(`    expect(result).toEqual(${JSON.stringify(spec.expectedOutput)});`);
    } else {
      lines.push("    expect(result).not.toBeNull();");
      lines.push("    // TODO: Add specific assertion for expected behavior");
    }
  }

  lines.push("  });");
  lines.push("});");

  return lines.join("\n") + "\n";
}
```

**Java: Reproduction test generator**

```java
public class ReproductionTestGenerator {

    public static String generateJUnit5Test(TestSpecExtractor.TestSpecification spec) {
        String testMethodName = TestSpecExtractor.generateTestMethodName(spec);
        StringBuilder sb = new StringBuilder();

        // Imports
        sb.append("import org.junit.jupiter.api.Test;\n");
        sb.append("import org.junit.jupiter.api.DisplayName;\n");
        if (!spec.errorType().isEmpty()) {
            sb.append("import static org.junit.jupiter.api.Assertions.assertThrows;\n");
        }
        sb.append("import static org.junit.jupiter.api.Assertions.*;\n");
        sb.append("\n");

        // Class
        String className = "Bug" + (spec.bugId().isEmpty() ? "Reproduction" : spec.bugId())
            + "ReproductionTest";
        sb.append("class ").append(className).append(" {\n\n");

        // Test method
        String displayName = "Reproduction: " + (spec.title().isEmpty()
            ? "Bug #" + spec.bugId() : spec.title());
        sb.append("    @Test\n");
        sb.append("    @DisplayName(\"").append(displayName).append("\")\n");
        sb.append("    void ").append(testMethodName).append("() {\n");

        // Documentation
        if (!spec.actualOutput().isEmpty()) {
            sb.append("        // Bug: ").append(spec.actualOutput()).append("\n");
        }
        if (!spec.expectedOutput().isEmpty()) {
            sb.append("        // Expected: ").append(spec.expectedOutput()).append("\n");
        }
        sb.append("\n");

        // Arrange
        sb.append("        // Arrange\n");
        sb.append("        // TODO: Set up the exact conditions from the bug report\n\n");

        // Act & Assert
        if (!spec.errorType().isEmpty()) {
            sb.append("        // Act & Assert\n");
            sb.append("        assertThrows(").append(spec.errorType()).append(".class, () -> {\n");
            if (!spec.functionUnderTest().isEmpty()) {
                sb.append("            // TODO: Call ").append(spec.functionUnderTest());
                sb.append(" with arguments that trigger the bug\n");
            }
            sb.append("        });\n");
        } else {
            sb.append("        // Act\n");
            if (!spec.functionUnderTest().isEmpty()) {
                sb.append("        // var result = instance.")
                    .append(spec.functionUnderTest()).append("();\n");
                sb.append("        // TODO: Add arguments that trigger the bug\n\n");
            }
            sb.append("        // Assert\n");
            sb.append("        // Before fix: this assertion should FAIL\n");
            sb.append("        // After fix: this assertion should PASS\n");
            if (!spec.expectedOutput().isEmpty()) {
                sb.append("        // assertEquals(\"")
                    .append(spec.expectedOutput()).append("\", result);\n");
            } else {
                sb.append("        // assertNotNull(result);\n");
                sb.append("        // TODO: Add specific assertion for expected behavior\n");
            }
        }

        sb.append("    }\n");
        sb.append("}\n");

        return sb.toString();
    }
}
```
