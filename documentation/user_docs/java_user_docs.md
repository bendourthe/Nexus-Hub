# Java User Documentation

## Objective
Create clear, comprehensive user-facing documentation that enables users of all skill levels to quickly understand, install, configure, and effectively use the Java software using Maven/Gradle ecosystem.

## Output Directory Structure

All documentation outputs should be saved in organized directories:

```
documentation/
└── user_docs/
    ├── generated_docs/
    ├── templates/
    ├── assets/
    └── exports/
```

**Directory Setup**:

- Create `documentation/user_docs/` directory in repository root if it doesn't exist

- All documentation files, templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `generated_docs/` - Generated documentation files (HTML, MD, PDF)

- `templates/` - Documentation templates and examples

- `assets/` - Images, diagrams, supplementary files

- `exports/` - Published documentation, release artifacts

## Implementation Checklist

### README Structure
- [ ] Compelling project overview and value proposition
- [ ] Key features highlighted
- [ ] Installation instructions complete and tested
- [ ] Quick start guide for immediate success
- [ ] Usage examples for common scenarios
- [ ] Links to detailed documentation

### Installation Guides
- [ ] Prerequisites clearly listed (JDK version, Maven/Gradle)
- [ ] Step-by-step installation process
- [ ] Platform-specific instructions (Windows, macOS, Linux)
- [ ] Troubleshooting common installation issues
- [ ] Verification steps to confirm successful installation

### Quick Start Guides
- [ ] Minimal example to first success
- [ ] Common use cases covered
- [ ] Progressive complexity (simple to advanced)
- [ ] Expected output shown
- [ ] Next steps guidance

### Usage Examples
- [ ] Real-world scenarios
- [ ] Complete, runnable code
- [ ] Input/output examples
- [ ] Edge cases and limitations
- [ ] Best practices demonstrated

### FAQ and Troubleshooting
- [ ] Common questions answered
- [ ] Error messages explained
- [ ] Debugging guidance
- [ ] Known limitations documented
- [ ] Where to get help

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Java User Documentation Request

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

Please create comprehensive user documentation for this Java project following this protocol:

## Phase 1: Audience Analysis & Documentation Planning

1. **Identify Target Audience**
   - Primary users: [backend developers/enterprise developers/Android developers/etc.]
   - Technical skill level: [beginner/intermediate/advanced]
   - Use cases: [what problems they're solving]
   - Context: [how they'll use the software]

2. **Document Existing Features**
   - List all major features and capabilities
   - Identify most common use cases
   - Note any complex or non-obvious functionality
   - Document prerequisites and dependencies

3. **Outline Documentation Structure**
   Plan what documentation is needed:
   - [ ] README.md (essential)
   - [ ] INSTALL.md or installation section
   - [ ] QUICKSTART.md or quick start guide
   - [ ] USER_GUIDE.md for detailed usage
   - [ ] EXAMPLES.md with common patterns
   - [ ] FAQ.md for common questions
   - [ ] TROUBLESHOOTING.md for common issues

## Phase 2: README.md - Professional Project Overview

Create a comprehensive README.md that serves as the front door to your project:

### README.md Template

```markdown
# [Project Name]

[![Maven Central](https://img.shields.io/maven-central/v/com.example/package-name.svg)](https://search.maven.org/artifact/com.example/package-name)
[![Java](https://img.shields.io/badge/Java-11%2B-blue)](https://openjdk.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/github/workflow/status/username/project/CI)](https://github.com/username/project/actions)

[One-sentence description of what the project does]

---

## ✨ What's New in v[X.Y.Z]

- 🚀 [New Feature 1]: Brief description
- ⚡ [Performance Improvement]: Specific metric (e.g., "50% faster")
- 🐛 [Important Bug Fix]: What was fixed
- 📝 [Documentation Update]: What was improved

[See full changelog](CHANGELOG.md)

---

## 📋 Overview

[2-3 paragraph description of the project]

**Problem**: [What problem does this solve?]

**Solution**: [How does this project solve it?]

**Benefits**:
- ✅ [Key benefit 1]
- ✅ [Key benefit 2]
- ✅ [Key benefit 3]

---

## 🎯 Key Features

- **[Feature 1]**: Description of what it does and why it matters
- **[Feature 2]**: Highlight unique or powerful capabilities
- **[Feature 3]**: Emphasize ease of use or performance benefits
- **[Feature 4]**: Note integration capabilities or extensibility

---

## 🚀 Quick Start

Get started in less than 5 minutes:

### Installation

**Maven**:
```xml
<dependency>
    <groupId>com.example</groupId>
    <artifactId>package-name</artifactId>
    <version>X.Y.Z</version>
</dependency>
```

**Gradle (Groovy)**:
```groovy
implementation 'com.example:package-name:X.Y.Z'
```

**Gradle (Kotlin DSL)**:
```kotlin
implementation("com.example:package-name:X.Y.Z")
```

### Basic Usage

```java
import com.example.packagename.MainClass;

public class Example {
    public static void main(String[] args) {
        // Simple example showing immediate value
        MainClass instance = new MainClass();
        String result = instance.process("example input");
        System.out.println(result);
        // Output: [expected output]
    }
}
```

**That's it!** You're ready to go. See [Usage Examples](#usage-examples) for more.

---

## 📦 Installation

### Prerequisites

Before installing, ensure you have:
- Java Development Kit (JDK) 11 or higher (17+ recommended)
- Maven 3.6+ or Gradle 7.0+
- [Optional] IDE with Java support (IntelliJ IDEA, Eclipse, VS Code)

### Installation Options

#### Option 1: Maven Central (Recommended)

Add to your `pom.xml`:
```xml
<dependencies>
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>package-name</artifactId>
        <version>X.Y.Z</version>
    </dependency>
</dependencies>
```

#### Option 2: Gradle

Add to your `build.gradle`:
```groovy
dependencies {
    implementation 'com.example:package-name:X.Y.Z'
}
```

Or for Gradle Kotlin DSL (`build.gradle.kts`):
```kotlin
dependencies {
    implementation("com.example:package-name:X.Y.Z")
}
```

#### Option 3: Build from Source

```bash
# Clone repository
git clone https://github.com/username/project.git
cd project

# Build with Maven
mvn clean install

# Or build with Gradle
./gradlew build

# Install to local Maven repository
mvn install -DskipTests
```

### Verify Installation

**Maven**:
```bash
mvn dependency:tree | grep package-name
```

**Gradle**:
```bash
./gradlew dependencies | grep package-name
```

**Troubleshooting**: See [Installation Issues](#installation-issues) if you encounter problems.

---

## 💡 Usage Examples

### Example 1: Basic Usage

[Description of what this example demonstrates]

```java
import com.example.packagename.MainClass;
import com.example.packagename.Options;

public class BasicExample {
    public static void main(String[] args) {
        // Setup
        Options options = Options.builder()
            .option1("value")
            .option2(42)
            .build();

        MainClass instance = new MainClass(options);

        // Perform operation
        String result = instance.process("input data");

        // Display result
        System.out.println("Result: " + result);
    }
}
```

**Output**:
```
Result: processed_data
```

### Example 2: Intermediate Usage with Error Handling

[Description of more complex scenario]

```java
import com.example.packagename.MainClass;
import com.example.packagename.ProcessingException;

public class IntermediateExample {
    public static void main(String[] args) {
        MainClass instance = new MainClass();

        try {
            String result = instance.process("complex input");
            System.out.println("Success: " + result);
        } catch (ProcessingException e) {
            System.err.println("Processing failed: " + e.getMessage());
            // Handle error appropriately
            e.printStackTrace();
        }
    }
}
```

### Example 3: Advanced Usage with Streams

[Description of advanced pattern using Java Streams]

```java
import com.example.packagename.MainClass;
import com.example.packagename.Result;

import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class AdvancedExample {
    public static void main(String[] args) {
        MainClass processor = new MainClass();

        List<String> items = Arrays.asList("item1", "item2", "item3");

        // Process multiple items using streams
        List<Result> results = items.stream()
            .map(processor::process)
            .collect(Collectors.toList());

        // Aggregate results
        long successCount = results.stream()
            .filter(Result::isSuccess)
            .count();

        System.out.println("Processed " + successCount + " items successfully");
    }
}
```

### Example 4: Spring Boot Integration

[Description of framework integration]

```java
import com.example.packagename.MainClass;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.bind.annotation.*;

@SpringBootApplication
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    @Bean
    public MainClass mainClass() {
        return new MainClass();
    }
}

@RestController
@RequestMapping("/api")
class ProcessingController {

    private final MainClass processor;

    public ProcessingController(MainClass processor) {
        this.processor = processor;
    }

    @PostMapping("/process")
    public ResponseEntity<String> process(@RequestBody String input) {
        try {
            String result = processor.process(input);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
```

**More Examples**: See [examples/](examples/) directory for additional use cases.

---

## 🔧 Configuration

### Basic Configuration

```java
import com.example.packagename.MainClass;
import com.example.packagename.Configuration;

public class ConfigExample {
    public static void main(String[] args) {
        Configuration config = Configuration.builder()
            .option1("value1")      // Description of option1
            .option2(42)            // Description of option2
            .debug(false)           // Enable debug output
            .build();

        MainClass instance = new MainClass(config);
    }
}
```

### Configuration File

Alternatively, use a configuration file (application.properties):

```properties
# application.properties
package.option1=value1
package.option2=42
package.debug=false
package.advanced.timeout=30000
package.advanced.retryCount=3
```

```java
import com.example.packagename.MainClass;
import com.example.packagename.ConfigLoader;

public class ConfigFileExample {
    public static void main(String[] args) {
        // Load from file
        Configuration config = ConfigLoader.fromProperties("application.properties");
        MainClass instance = new MainClass(config);
    }
}
```

### Environment Variables

```bash
# Set via environment variables
export PACKAGE_OPTION1="value1"
export PACKAGE_OPTION2="42"
export PACKAGE_DEBUG="false"
```

```java
import com.example.packagename.MainClass;
import com.example.packagename.Configuration;

public class EnvConfigExample {
    public static void main(String[] args) {
        // Automatically loads from environment
        Configuration config = Configuration.fromEnvironment();
        MainClass instance = new MainClass(config);
    }
}
```

---

## 📚 Documentation

- **[User Guide](docs/USER_GUIDE.md)**: Comprehensive usage documentation
- **[Javadoc API Reference](https://javadoc.io/doc/com.example/package-name)**: Complete API documentation
- **[Examples](examples/)**: More code examples and tutorials
- **[FAQ](docs/FAQ.md)**: Frequently asked questions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions

---

## ❓ FAQ

### How do I [common task]?

[Clear, concise answer with code example if relevant]

### What's the difference between [Feature A] and [Feature B]?

[Explanation of differences and when to use each]

### Can I use this with [framework/library]?

[Yes/No with explanation and example if applicable]

### How do I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

**More Questions?** Check the full [FAQ](docs/FAQ.md) or [open an issue](https://github.com/username/project/issues).

---

## 🐛 Troubleshooting

### Installation Issues

**Problem**: `Could not find artifact com.example:package-name:jar:X.Y.Z`

**Solution**: Ensure Maven Central is in your repository list:
```xml
<repositories>
    <repository>
        <id>central</id>
        <url>https://repo.maven.apache.org/maven2</url>
    </repository>
</repositories>
```

### Common Errors

**Error**: `NoClassDefFoundError: com/example/packagename/MainClass`

**Cause**: Missing dependency or classpath issue

**Solution**: Verify dependency is properly added and rebuild:
```bash
# Maven
mvn clean install

# Gradle
./gradlew clean build
```

**More Issues?** See full [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

---

## 🧪 Testing

Run the test suite to verify everything works:

```bash
# Maven
mvn test

# Run with coverage
mvn test jacoco:report

# Run specific test
mvn test -Dtest=ClassName#methodName

# Gradle
./gradlew test

# Run with coverage
./gradlew test jacocoTestReport

# Run specific test
./gradlew test --tests ClassName.methodName
```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick start for contributors:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`mvn test` or `./gradlew test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE) - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- [Contributor/Library]: For [contribution/inspiration]
- [Resource]: For [helpful resource]

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/username/project/issues)
- **Discussions**: [GitHub Discussions](https://github.com/username/project/discussions)
- **Stack Overflow**: Tag with `[package-name]`
- **Documentation**: [https://project-docs.com](https://project-docs.com)

---

## 🗺️ Roadmap

- [ ] v[X+1].0: [Planned major feature]
- [ ] v[X].Y: [Planned minor feature]
- [ ] [Future feature/improvement]

See [ROADMAP.md](ROADMAP.md) for detailed plans.

---

**Made with ❤️ by [Your Name/Organization]**
```

## Phase 3: Installation Guide

Create detailed installation instructions for all platforms and build tools:

### INSTALL.md Template

```markdown
# Installation Guide

Complete installation instructions for [Project Name].

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **JDK**: 11 or higher
- **Build Tool**: Maven 3.6+ or Gradle 7.0+
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 500MB

### Recommended Requirements
- JDK 17 LTS for best performance and support
- Maven 3.8+ or Gradle 7.5+
- 16GB RAM for large projects
- SSD for faster builds

---

## Installation Methods

### Method 1: Maven (Recommended)

Add to your `pom.xml`:

```xml
<dependencies>
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>package-name</artifactId>
        <version>X.Y.Z</version>
    </dependency>
</dependencies>
```

**Verification**:
```bash
mvn dependency:tree | grep package-name
```

### Method 2: Gradle

Add to your `build.gradle`:

**Groovy DSL**:
```groovy
dependencies {
    implementation 'com.example:package-name:X.Y.Z'
}
```

**Kotlin DSL** (`build.gradle.kts`):
```kotlin
dependencies {
    implementation("com.example:package-name:X.Y.Z")
}
```

**Verification**:
```bash
./gradlew dependencies | grep package-name
```

### Method 3: Development Installation

For contributors or users who want the latest code:

#### Windows
```cmd
REM Clone repository
git clone https://github.com/username/project.git
cd project

REM Build with Maven
mvn clean install

REM Or build with Gradle
gradlew.bat build

REM Install to local Maven repository
mvn install -DskipTests
```

#### macOS/Linux
```bash
# Clone repository
git clone https://github.com/username/project.git
cd project

# Build with Maven
mvn clean install

# Or build with Gradle
./gradlew build

# Install to local Maven repository
mvn install -DskipTests
```

### Method 4: Manual JAR Download

For projects without build tool integration:

1. Download JAR from [Maven Central](https://search.maven.org/artifact/com.example/package-name)
2. Add to your project's classpath:
```bash
java -cp "lib/*:package-name-X.Y.Z.jar" com.example.Main
```

---

## Platform-Specific Instructions

### Windows

**Prerequisites**:
1. Install JDK from [AdoptOpenJDK](https://adoptopenjdk.net/) or [Oracle](https://oracle.com/java)
2. Set JAVA_HOME environment variable:
   ```cmd
   setx JAVA_HOME "C:\Program Files\Java\jdk-17"
   setx PATH "%PATH%;%JAVA_HOME%\bin"
   ```
3. Install Maven from [maven.apache.org](https://maven.apache.org) or Gradle from [gradle.org](https://gradle.org)

**Installation**:
```cmd
REM Verify Java installation
java -version
javac -version

REM Create new Maven project
mvn archetype:generate -DgroupId=com.example -DartifactId=myapp

REM Add dependency to pom.xml, then:
mvn clean install
```

**Common Issues**:
- **Error**: "JAVA_HOME is not set"
  - **Fix**: Set JAVA_HOME as shown above
- **Error**: "mvn: command not found"
  - **Fix**: Add Maven bin directory to PATH

### macOS

**Prerequisites**:
1. Install JDK via Homebrew: `brew install openjdk@17`
2. Link JDK: `sudo ln -sfn $(brew --prefix openjdk@17)/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-17.jdk`
3. Install Maven: `brew install maven` or Gradle: `brew install gradle`

**Installation**:
```bash
# Verify Java installation
java -version
javac -version

# Create new Maven project
mvn archetype:generate -DgroupId=com.example -DartifactId=myapp

# Add dependency to pom.xml, then:
mvn clean install
```

**Common Issues**:
- **Error**: "Unable to locate Java"
  - **Fix**: Set JAVA_HOME: `export JAVA_HOME=$(/usr/libexec/java_home -v 17)`
- **Error**: "Permission denied"
  - **Fix**: Use `sudo` or adjust permissions

### Linux

#### Ubuntu/Debian
```bash
# Install OpenJDK
sudo apt update
sudo apt install openjdk-17-jdk

# Install Maven
sudo apt install maven

# Or install Gradle
sudo apt install gradle

# Verify installation
java -version
mvn -version
```

#### Fedora/RHEL/CentOS
```bash
# Install OpenJDK
sudo dnf install java-17-openjdk-devel

# Install Maven
sudo dnf install maven

# Or install Gradle
sudo dnf install gradle
```

#### Arch Linux
```bash
# Install OpenJDK
sudo pacman -S jdk-openjdk

# Install Maven
sudo pacman -S maven

# Or install Gradle
sudo pacman -S gradle
```

---

## Build Tool Comparison

### Maven

**Pros**: Widely adopted, extensive plugin ecosystem, convention over configuration
**Cons**: Verbose XML, slower than Gradle

```xml
<!-- pom.xml -->
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>myapp</artifactId>
    <version>1.0.0</version>

    <dependencies>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>package-name</artifactId>
            <version>X.Y.Z</version>
        </dependency>
    </dependencies>
</project>
```

### Gradle

**Pros**: Faster builds, more flexible, modern DSL
**Cons**: Steeper learning curve, can be complex

```groovy
// build.gradle
plugins {
    id 'java'
}

group = 'com.example'
version = '1.0.0'

repositories {
    mavenCentral()
}

dependencies {
    implementation 'com.example:package-name:X.Y.Z'
}
```

---

## IDE Integration

### IntelliJ IDEA

1. Open project
2. Wait for Maven/Gradle sync
3. Dependencies automatically downloaded

**Manual sync**:
- Maven: Right-click pom.xml → Maven → Reload Project
- Gradle: Right-click build.gradle → Gradle → Refresh Gradle Project

### Eclipse

1. Import as Maven/Gradle project
2. Right-click project → Maven → Update Project
3. Or use Buildship Gradle plugin

### VS Code

1. Install Java Extension Pack
2. Install Maven/Gradle extensions
3. Open project folder
4. Dependencies sync automatically

---

## Verification

### Quick Verification

```bash
# Maven
mvn dependency:tree | grep package-name

# Gradle
./gradlew dependencies --configuration runtimeClasspath | grep package-name
```

### Full Verification

```bash
# Clone repository
git clone https://github.com/username/project.git
cd project

# Run tests
mvn test
# Or
./gradlew test

# Build project
mvn clean package
# Or
./gradlew build
```

### Verify Installation in Code

```java
import com.example.packagename.MainClass;

public class VerifyInstallation {
    public static void main(String[] args) {
        System.out.println("Package version: " + MainClass.getVersion());
    }
}
```

---

## Upgrading

### Upgrade to Latest Version

**Maven**: Update version in `pom.xml`:
```xml
<dependency>
    <groupId>com.example</groupId>
    <artifactId>package-name</artifactId>
    <version>X.Y.Z</version> <!-- Update this -->
</dependency>
```

**Gradle**: Update version in `build.gradle`:
```groovy
implementation 'com.example:package-name:X.Y.Z' // Update this
```

Then rebuild:
```bash
# Maven
mvn clean install

# Gradle
./gradlew clean build
```

### Check for Updates

**Maven**:
```bash
mvn versions:display-dependency-updates
```

**Gradle**:
```bash
./gradlew dependencyUpdates
```

---

## Uninstallation

**Maven**: Remove from `pom.xml` and run:
```bash
mvn clean
```

**Gradle**: Remove from `build.gradle` and run:
```bash
./gradlew clean
```

---

## Troubleshooting Installation

### Common Installation Errors

**Error**: `Could not find artifact`
- **Cause**: Maven Central not configured or network issue
- **Fix**: Check repository configuration and network

**Error**: `JAVA_HOME not set`
- **Cause**: Java environment variable not configured
- **Fix**: Set JAVA_HOME to JDK installation path

**Error**: `Unsupported class file version`
- **Cause**: Library compiled with newer Java than runtime
- **Fix**: Upgrade JDK to version 11 or higher

**Error**: Dependency resolution failures
- **Cause**: Version conflicts or corrupted cache
- **Fix**: Clear cache and rebuild:
  ```bash
  # Maven
  mvn dependency:purge-local-repository

  # Gradle
  ./gradlew clean --refresh-dependencies
  ```

### Getting Help

If installation fails:
1. Check [GitHub Issues](https://github.com/username/project/issues)
2. Review [Troubleshooting Guide](TROUBLESHOOTING.md)
3. Open a new issue with:
   - Your OS and version
   - Java version (`java -version`)
   - Maven/Gradle version
   - Full error message
   - Build file (pom.xml or build.gradle)

---

## Next Steps

After successful installation:
1. Review the [Quick Start Guide](README.md#quick-start)
2. Try the [examples/](examples/) directory
3. Read the [User Guide](USER_GUIDE.md)
4. Check the [Javadoc](https://javadoc.io/doc/com.example/package-name)
```

## Phase 4: Quick Start Guide

Create a focused quick start for immediate success:

### Quick Start Template

```markdown
# Quick Start Guide

Get started with [Project Name] in under 10 minutes.

---

## What You'll Build

By the end of this guide, you'll have:
- ✅ Set up Java project with [Project Name]
- ✅ Run your first example
- ✅ Understanding of core concepts
- ✅ Ready to build your own solution

**Time Required**: ~10 minutes

---

## Prerequisites

- JDK 11+ installed
- Maven or Gradle installed
- Basic Java knowledge
- IDE or text editor

---

## Step 1: Create Project (2 minutes)

**Using Maven**:
```bash
mvn archetype:generate -DgroupId=com.example -DartifactId=myapp \
  -DarchetypeArtifactId=maven-archetype-quickstart -DinteractiveMode=false
cd myapp
```

**Using Gradle**:
```bash
gradle init --type java-application --dsl groovy --test-framework junit
```

---

## Step 2: Add Dependency (1 minute)

**Maven** - Add to `pom.xml`:
```xml
<dependencies>
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>package-name</artifactId>
        <version>X.Y.Z</version>
    </dependency>
</dependencies>
```

**Gradle** - Add to `build.gradle`:
```groovy
dependencies {
    implementation 'com.example:package-name:X.Y.Z'
}
```

---

## Step 3: Your First Program (3 minutes)

Create `src/main/java/com/example/FirstExample.java`:

```java
package com.example;

import com.example.packagename.MainClass;

public class FirstExample {
    public static void main(String[] args) {
        // Create instance with simple configuration
        MainClass processor = new MainClass();

        // Process some data
        String result = processor.process("Hello, World!");

        // Display result
        System.out.println("Result: " + result);
    }
}
```

Build and run:
```bash
# Maven
mvn clean compile exec:java -Dexec.mainClass="com.example.FirstExample"

# Gradle
./gradlew run
```

**Expected Output**:
```
Result: Processed: Hello, World!
```

✅ **Success!** You've run your first program.

---

## Step 4: Understand the Basics (3 minutes)

Let's break down what happened:

1. **Import**: We imported the main class
2. **Instantiate**: We created an instance
3. **Process**: We processed data
4. **Result**: We got a result back

Now try modifying the example:

```java
package com.example;

import com.example.packagename.MainClass;

public class SecondExample {
    public static void main(String[] args) {
        MainClass processor = new MainClass();

        // Try different inputs
        String[] inputs = {"Hello", "World", "Java"};

        for (String text : inputs) {
            String result = processor.process(text);
            System.out.println(text + " -> " + result);
        }
    }
}
```

---

## Step 5: Next Steps

Now that you have the basics:

### Explore More Examples
- **[Example 2: Error Handling](examples/ErrorHandlingExample.java)**: Robust error management
- **[Example 3: Streams API](examples/StreamsExample.java)**: Modern Java patterns
- **[Example 4: Spring Boot](examples/SpringBootExample.java)**: Framework integration

### Read Documentation
- **[User Guide](USER_GUIDE.md)**: Comprehensive usage guide
- **[Javadoc](https://javadoc.io/doc/com.example/package-name)**: API documentation

### Join Community
- **[GitHub Discussions](https://github.com/username/project/discussions)**: Ask questions
- **[Stack Overflow](https://stackoverflow.com/questions/tagged/package-name)**: Community support

---

## Common Next Tasks

### Task: Process Multiple Items

```java
import com.example.packagename.MainClass;
import java.util.Arrays;
import java.util.List;

public class BatchExample {
    public static void main(String[] args) {
        MainClass processor = new MainClass();
        List<String> items = Arrays.asList("item1", "item2", "item3");

        items.stream()
            .map(processor::process)
            .forEach(System.out::println);
    }
}
```

### Task: Add Error Handling

```java
import com.example.packagename.MainClass;
import com.example.packagename.ProcessingException;

public class ErrorHandlingExample {
    public static void main(String[] args) {
        MainClass processor = new MainClass();

        try {
            String result = processor.process("input");
            System.out.println("Success: " + result);
        } catch (ProcessingException e) {
            System.err.println("Processing failed: " + e.getMessage());
        }
    }
}
```

---

## Need Help?

- **Error Messages**: See [Troubleshooting](TROUBLESHOOTING.md)
- **Questions**: Open an [issue](https://github.com/username/project/issues)
- **Examples**: Check [examples/](examples/) directory

**Congratulations!** You're ready to use [Project Name].
```

## Phase 5: FAQ and Troubleshooting

### FAQ.md Template

```markdown
# Frequently Asked Questions

Common questions about [Project Name].

---

## General Questions

### What is [Project Name]?

[Clear, concise explanation of what the project is and what it does]

### Who is this for?

[Target audience and use cases]

### Is it free?

[License and pricing information]

### How do I get support?

[Support channels and resources]

---

## Installation & Setup

### Which Java version do I need?

Java 11 or higher is required. Java 17 LTS is recommended for best performance and long-term support.

### Can I use this with [framework]?

[Framework compatibility information]

### Should I use Maven or Gradle?

Both are fully supported. Choose based on your project:
- **Maven**: Better for traditional enterprise projects, extensive plugin ecosystem
- **Gradle**: Better for modern projects, faster builds, more flexible

---

## Usage Questions

### How do I [common task]?

[Answer with code example]

### What's the difference between [Feature A] and [Feature B]?

[Clear explanation of differences with use case examples]

### Can I use this in production?

[Stability, versioning, and production readiness information]

### How do I handle errors?

Use try-catch blocks with specific exception types:
```java
try {
    String result = processor.process(input);
} catch (ProcessingException e) {
    // Handle processing errors
} catch (ValidationException e) {
    // Handle validation errors
}
```

---

## Troubleshooting

### Why am I getting [common error]?

**Error**: `NoClassDefFoundError`

**Cause**: Missing dependency or classpath issue

**Solution**:
```bash
# Maven - rebuild
mvn clean install

# Gradle - rebuild
./gradlew clean build
```

### The program is slow. How can I improve performance?

[Performance optimization tips]

---

## Contributing

### How can I contribute?

[Contribution process overview]

### I found a bug. What should I do?

[Bug reporting process]

---

[Back to README](../README.md)
```

---

## Output Format

Please provide user documentation in this format:

### Documentation Files Created

```markdown
## README.md
[Generated README content]

---

## INSTALL.md
[Generated installation guide]

---

## QUICKSTART.md
[Generated quick start guide]

---

## FAQ.md
[Generated FAQ]

---
```

### Summary Report

```markdown
## User Documentation Summary

**Files Created**: [count]
- README.md: [Complete/Updated]
- Installation Guide: [Yes/No]
- Quick Start Guide: [Yes/No]
- FAQ: [Yes/No]
- Troubleshooting Guide: [Yes/No]

**Target Audience**: [Beginner/Intermediate/Advanced]

**Content Metrics**:
- Code examples: [count]
- Platform-specific instructions: [Windows/macOS/Linux]
- Build tools documented: [Maven/Gradle]
- FAQ entries: [count]
- Troubleshooting scenarios: [count]

**Quality Checks**:
- [ ] All examples tested and functional
- [ ] Installation instructions verified on all platforms
- [ ] Links working and up-to-date
- [ ] Javadoc references included
- [ ] Accessible to target audience

**Next Steps**:
- [ ] Review documentation for accuracy
- [ ] Test installation on fresh system
- [ ] Get feedback from target users
- [ ] Publish Javadoc to javadoc.io
```

---

## Best Practices

1. **Write for Your Audience**
   - Match technical level to Java developers
   - Explain Maven/Gradle ecosystem concepts
   - Provide context for build tool decisions

2. **Show, Don't Just Tell**
   - Include complete, runnable examples
   - Show both Maven and Gradle syntax
   - Demonstrate Java best practices
   - Include framework integrations

3. **Make It Easy to Find Information**
   - Clear table of contents
   - Good headings and structure
   - Links to Javadoc

4. **Test Your Documentation**
   - Follow your own instructions
   - Test on different JDK versions
   - Verify both Maven and Gradle work

5. **Keep It Updated**
   - Update with code changes
   - Version documentation with releases
   - Address user questions in FAQ

6. **Progressive Disclosure**
   - Start simple, add complexity gradually
   - Quick start for immediate success
   - Detailed docs for advanced users

---

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p documentation/user_docs/generated_docs
mkdir -p documentation/user_docs/templates
mkdir -p documentation/user_docs/assets
mkdir -p documentation/user_docs/exports
```

**Save files as follows**:

- Generated docs → `documentation/user_docs/generated_docs/`

- Templates → `documentation/user_docs/templates/`

- Assets → `documentation/user_docs/assets/`

- Exports → `documentation/user_docs/exports/`

Replace `{phase_name}` with the specific phase (docstrings, comments, user_docs, technical_docs, api_docs, or sbom).

~~~

## Output Format Specifications

The user documentation should:
- Be clear and accessible to Java developers
- Include complete, tested, runnable examples
- Cover Maven and Gradle build tools
- Provide step-by-step instructions with expected outcomes
- Cover multiple platforms where applicable
- Include troubleshooting for common JDK/build tool issues
- Use consistent formatting and structure
- Link to Javadoc and other resources
- Include badges and visual aids where helpful
