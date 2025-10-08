# System Prompt Template Generation Guide

This document provides detailed specifications for creating language-specific system prompts based on the Python template structure.

---

## Completed Templates

### JavaScript/TypeScript ✓
**Location**:
- `autonomous_agents/claude_code/javascript/`
- `coding_assistants/javascript/`

**Files Created**:
- CLAUDE_comprehensive_35k.md
- CLAUDE_condensed_20k.md
- GLOBAL_comprehensive_35k.md
- GLOBAL_condensed_15k.md

---

## Remaining Languages to Complete

### 1. Java (Spring Boot Focus)

#### Key Adaptations Required

**Project Structure**:
```
project_name/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/company/project/
│   │   │       ├── Application.java
│   │   │       ├── controller/
│   │   │       ├── service/
│   │   │       ├── repository/
│   │   │       ├── model/
│   │   │       └── config/
│   │   └── resources/
│   │       ├── application.properties
│   │       └── application.yml
│   └── test/
│       └── java/
├── target/
├── pom.xml (Maven) or build.gradle (Gradle)
├── CHANGELOG.md
├── README.md
└── DEVLOG.md
```

**Build Tools**:
- Maven: `mvn clean install`, `mvn test`, `mvn spring-boot:run`
- Gradle: `./gradlew build`, `./gradlew test`, `./gradlew bootRun`

**Code Standards**:
```java
// Naming conventions
public class UserService { }      // PascalCase for classes
private static final int MAX = 100;  // UPPER_CASE for constants
public void getUserById() { }     // camelCase for methods
private String userName;          // camelCase for variables

// Annotations
@Service
@Transactional
public class UserServiceImpl implements UserService {

    @Autowired
    private UserRepository userRepository;

    @Override
    public User findById(Long id) {
        return userRepository.findById(id)
            .orElseThrow(() -> new UserNotFoundException(id));
    }
}
```

**Testing Framework**:
- JUnit 5
- Mockito
- Spring Boot Test
- AssertJ

**Documentation**:
- JavaDoc for all public methods
- README with Maven/Gradle setup
- application.properties configuration

**Package Management**:
- Maven dependencies in pom.xml
- Gradle dependencies in build.gradle
- Version management with dependency management

---

### 2. C# (.NET Focus)

#### Key Adaptations Required

**Project Structure**:
```
ProjectName/
├── src/
│   └── ProjectName/
│       ├── Controllers/
│       ├── Services/
│       ├── Models/
│       ├── Data/
│       ├── Program.cs
│       └── ProjectName.csproj
├── tests/
│   └── ProjectName.Tests/
│       └── ProjectName.Tests.csproj
├── ProjectName.sln
├── CHANGELOG.md
├── README.md
└── DEVLOG.md
```

**Build Tools**:
- .NET CLI: `dotnet build`, `dotnet test`, `dotnet run`
- NuGet package manager

**Code Standards**:
```csharp
// Naming conventions
public class UserService { }           // PascalCase for classes
private const int MaxUsers = 100;      // PascalCase for constants
public User GetUserById() { }          // PascalCase for methods
private string _userName;              // _camelCase for private fields

// Modern C# features
public class UserService
{
    private readonly IUserRepository _repository;

    public UserService(IUserRepository repository)
    {
        _repository = repository ?? throw new ArgumentNullException(nameof(repository));
    }

    public async Task<User?> GetUserByIdAsync(int id)
    {
        return await _repository.FindByIdAsync(id);
    }
}

// Records for DTOs (C# 9+)
public record UserDto(int Id, string Name, string Email);

// Pattern matching
public string GetUserStatus(User user) => user switch
{
    { IsActive: true, LastLogin: var login } when login > DateTime.Now.AddDays(-7) => "Active",
    { IsActive: true } => "Inactive",
    _ => "Disabled"
};
```

**Testing Framework**:
- xUnit or NUnit
- Moq for mocking
- FluentAssertions

**Documentation**:
- XML documentation comments
- README with .NET SDK requirements
- appsettings.json configuration

**Package Management**:
- NuGet packages in .csproj
- PackageReference format

---

### 3. Go (Standard Library Focus)

#### Key Adaptations Required

**Project Structure**:
```
project_name/
├── cmd/
│   └── app/
│       └── main.go
├── internal/
│   ├── handler/
│   ├── service/
│   ├── repository/
│   └── model/
├── pkg/
│   └── utils/
├── test/
├── go.mod
├── go.sum
├── CHANGELOG.md
├── README.md
└── DEVLOG.md
```

**Build Tools**:
- Go CLI: `go build`, `go test`, `go run`
- Go modules for dependency management

**Code Standards**:
```go
// Naming conventions
type UserService struct { }           // PascalCase (exported)
type userImpl struct { }              // camelCase (private)
const MaxUsers = 100                  // PascalCase (exported)
func GetUserByID() { }                // PascalCase (exported)
func parseUserData() { }              // camelCase (private)

// Interface-based design
type UserRepository interface {
    FindByID(ctx context.Context, id string) (*User, error)
    Create(ctx context.Context, user *User) error
}

type userRepositoryImpl struct {
    db *sql.DB
}

func NewUserRepository(db *sql.DB) UserRepository {
    return &userRepositoryImpl{db: db}
}

// Error handling
func (r *userRepositoryImpl) FindByID(ctx context.Context, id string) (*User, error) {
    var user User
    err := r.db.QueryRowContext(ctx, "SELECT * FROM users WHERE id = $1", id).
        Scan(&user.ID, &user.Name, &user.Email)

    if err != nil {
        if err == sql.ErrNoRows {
            return nil, ErrUserNotFound
        }
        return nil, fmt.Errorf("finding user: %w", err)
    }

    return &user, nil
}

// Defer for cleanup
func ProcessFile(filename string) error {
    file, err := os.Open(filename)
    if err != nil {
        return err
    }
    defer file.Close()

    // Process file
    return nil
}
```

**Testing Framework**:
- Built-in testing package
- testify for assertions
- gomock for mocking

**Documentation**:
- GoDoc comments
- README with Go version requirements
- Example functions

**Package Management**:
- go.mod for dependencies
- Go modules proxy

---

### 4. C (Embedded Systems Focus)

#### Key Adaptations Required

**Project Structure**:
```
project_name/
├── src/
│   ├── main.c
│   ├── drivers/
│   ├── hal/          # Hardware Abstraction Layer
│   └── app/
├── include/
│   ├── config.h
│   └── types.h
├── lib/
├── tests/
├── build/
├── Makefile or CMakeLists.txt
├── CHANGELOG.md
├── README.md
└── DEVLOG.md
```

**Build Tools**:
- Make or CMake
- GCC/Clang compilers
- Platform-specific toolchains (ARM GCC, etc.)

**Code Standards**:
```c
// Naming conventions
typedef struct {
    uint8_t id;
    char name[32];
} user_t;                              // snake_case with _t suffix

#define MAX_USERS 100                  // UPPER_CASE for macros

void user_init(void);                  // snake_case for functions
static void process_data(void);        // static for private functions

// Header guards
#ifndef USER_H
#define USER_H

// Function declarations
void user_init(void);
user_t* user_get_by_id(uint8_t id);

#endif // USER_H

// Embedded-specific patterns
// Volatile for hardware registers
volatile uint32_t* const UART_DATA = (uint32_t*)0x40001000;

// Interrupt service routine
void UART_IRQHandler(void) {
    // Keep ISRs short and fast
    if (*UART_DATA & UART_RX_FLAG) {
        uint8_t data = *UART_DATA & 0xFF;
        // Process or queue data
    }
}

// Memory-efficient structures
#pragma pack(push, 1)
typedef struct {
    uint8_t status;
    uint16_t value;
    uint32_t timestamp;
} __attribute__((packed)) sensor_data_t;
#pragma pack(pop)

// State machines for embedded systems
typedef enum {
    STATE_IDLE,
    STATE_READING,
    STATE_PROCESSING,
    STATE_ERROR
} system_state_t;

static system_state_t current_state = STATE_IDLE;

void state_machine_update(void) {
    switch (current_state) {
        case STATE_IDLE:
            // Handle idle
            break;
        case STATE_READING:
            // Handle reading
            break;
        // ...
    }
}
```

**Testing Framework**:
- Unity (embedded unit testing)
- CMock for mocking
- Ceedling for test automation

**Documentation**:
- Doxygen comments
- Memory map documentation
- Hardware requirements
- Timing diagrams

**Build System**:
- Makefile with cross-compilation support
- CMake for complex projects
- Linker scripts for memory layout

---

### 5. C++ (Modern C++17/20 Focus)

#### Key Adaptations Required

**Project Structure**:
```
project_name/
├── src/
│   ├── main.cpp
│   ├── core/
│   └── utils/
├── include/
│   └── project_name/
├── tests/
├── build/
├── CMakeLists.txt
├── CHANGELOG.md
├── README.md
└── DEVLOG.md
```

**Build Tools**:
- CMake
- Conan or vcpkg for dependencies
- GCC/Clang/MSVC compilers

**Code Standards**:
```cpp
// Naming conventions
class UserService { };                 // PascalCase for classes
constexpr int kMaxUsers = 100;         // kPascalCase for constants
void getUserById() { }                 // camelCase for methods
std::string user_name_;                // snake_case_ for private members

// Modern C++ features
// RAII and smart pointers
class FileHandler {
private:
    std::unique_ptr<std::ifstream> file_;

public:
    explicit FileHandler(const std::string& filename)
        : file_(std::make_unique<std::ifstream>(filename)) {
        if (!file_->is_open()) {
            throw std::runtime_error("Failed to open file");
        }
    }

    // Rule of five (or zero)
    FileHandler(const FileHandler&) = delete;
    FileHandler& operator=(const FileHandler&) = delete;
    FileHandler(FileHandler&&) = default;
    FileHandler& operator=(FileHandler&&) = default;
    ~FileHandler() = default;
};

// Templates and concepts (C++20)
template<typename T>
concept Numeric = std::is_arithmetic_v<T>;

template<Numeric T>
T add(T a, T b) {
    return a + b;
}

// Range-based for loops and structured bindings
std::map<std::string, int> user_ages;
for (const auto& [name, age] : user_ages) {
    std::cout << name << ": " << age << '\n';
}

// std::optional for nullable returns
std::optional<User> findUserById(int id) {
    if (auto it = users.find(id); it != users.end()) {
        return it->second;
    }
    return std::nullopt;
}

// Lambda expressions
auto users = getUsers();
std::sort(users.begin(), users.end(),
    [](const User& a, const User& b) { return a.age < b.age; });
```

**Testing Framework**:
- Google Test (gtest)
- Google Mock (gmock)
- Catch2

**Documentation**:
- Doxygen comments
- README with CMake build instructions
- Modern C++ feature usage

**Build System**:
- CMake with modern targets
- Package managers (Conan/vcpkg)

---

## Template Creation Checklist

For each language, ensure the following sections are adapted:

### Comprehensive Version (~35k tokens)
- [ ] Quick Start section with language commands
- [ ] Project Architecture with standard structure
- [ ] Code Standards with language conventions
- [ ] Documentation Standards with appropriate format
- [ ] Testing Framework with language tools
- [ ] Development Workflow adapted
- [ ] Command Preferences with build tools
- [ ] Version Control section
- [ ] Implementation Examples
- [ ] Quality Checklist

### Condensed Version (~15-20k tokens)
- [ ] Essential quick reference
- [ ] Streamlined project structure
- [ ] Core code standards
- [ ] Basic documentation templates
- [ ] Testing essentials
- [ ] Key commands only
- [ ] Version control basics
- [ ] Quality checklist

---

## Language-Specific Considerations

### Java
- Maven/Gradle build lifecycle
- Spring Boot auto-configuration
- JPA/Hibernate for database
- Lombok for boilerplate reduction
- Stream API for functional programming
- JUnit 5 parameterized tests

### C#
- Dependency injection patterns
- async/await extensively
- Entity Framework Core
- LINQ for queries
- Records and pattern matching (modern C#)
- Minimal APIs (ASP.NET Core)

### Go
- Goroutines and channels
- Context for cancellation
- Table-driven tests
- Error wrapping
- Interface segregation
- Composition over inheritance

### C (Embedded)
- Memory constraints awareness
- Real-time considerations
- Interrupt handling
- DMA configuration
- Power management
- Bootloader considerations
- RTOS integration (FreeRTOS, etc.)

### C++
- RAII principles
- Move semantics
- Template metaprogramming
- STL algorithm usage
- Smart pointer management
- Exception safety guarantees
- Cache-friendly data structures

---

## File Naming Convention

### Autonomous Agents (Claude Code)
- `CLAUDE_comprehensive_35k.md` - Full-featured with all sections
- `CLAUDE_condensed_20k.md` - Streamlined for quick reference

### Coding Assistants (General AI)
- `GLOBAL_comprehensive_35k.md` - Complete guide
- `GLOBAL_condensed_15k.md` - Essential reference

---

## Quality Standards

Each template must:
1. Be language-idiomatic and follow community standards
2. Include practical, runnable code examples
3. Reference official documentation and tools
4. Address security considerations
5. Cover testing approaches
6. Provide clear project initialization steps
7. Include troubleshooting guidance
8. Be token-efficient while comprehensive

---

## Next Steps

1. Use this guide to create remaining templates systematically
2. Follow the same structural pattern as Python/JavaScript templates
3. Adapt all code examples to language syntax
4. Update tool commands and build processes
5. Verify all code examples compile/run
6. Review for language-specific best practices
7. Ensure token counts match target sizes

---
