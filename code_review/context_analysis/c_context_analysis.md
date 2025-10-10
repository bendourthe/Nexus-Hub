# C/Embedded Context Analysis

## Objective
Establish comprehensive understanding of the embedded/firmware project before conducting detailed code review. This phase gathers context about target hardware, build system, RTOS configuration, toolchain setup, and current state to inform all subsequent review activities.

## Output Directory Structure

All review outputs should be saved in organized directories:

```
review/
└── context_analysis/
    ├── context_analysis_report.md
    ├── context_analysis_findings.json
    ├── analysis_scripts/
    └── supporting_data/
```

**Directory Setup**:

- Create `review/context_analysis/` directory in repository root if it doesn't exist

- All review outputs (reports, findings, scripts, data) go in the phase-specific directory

**Expected Outputs**:

- `context_analysis_report.md` - Main findings and recommendations

- `context_analysis_findings.json` - Structured data for tooling integration

- `analysis_scripts/` - Any scripts generated during analysis

- `supporting_data/` - Raw data, logs, profiling results, scan outputs

## Analysis Checklist

### Project Understanding
- [ ] Target hardware platform and microcontroller identified
- [ ] Real-time requirements and constraints documented
- [ ] Bare metal vs RTOS architecture clarified
- [ ] Power consumption requirements assessed
- [ ] Safety-critical or certification requirements identified (ISO 26262, IEC 61508, DO-178C)

### Architecture & Structure
- [ ] Entry points and initialization sequence mapped
- [ ] Module organization and layering evaluated
- [ ] Hardware abstraction layers (HAL) identified
- [ ] Interrupt service routines (ISRs) documented
- [ ] Memory map and allocation strategy understood

### Build System & Toolchain
- [ ] Build system documented (Makefile, CMake, custom)
- [ ] Compiler and version identified (GCC, Clang, IAR, Keil)
- [ ] Compiler flags and optimization levels reviewed
- [ ] Linker scripts analyzed
- [ ] Cross-compilation setup verified

### Dependency Analysis
- [ ] External libraries and middleware listed (FreeRTOS, CMSIS, vendor SDKs)
- [ ] Hardware dependencies documented (peripherals, sensors, actuators)
- [ ] Third-party component versions tracked
- [ ] License compatibility verified
- [ ] Vendor SDK versions and update status checked

### Hardware & Resource Constraints
- [ ] Flash/ROM size and usage measured
- [ ] RAM/SRAM allocation analyzed
- [ ] Stack size requirements assessed
- [ ] Clock speeds and timing constraints documented
- [ ] Peripheral usage mapped

### Configuration Management
- [ ] Configuration files identified (config.h, board.h, etc.)
- [ ] Compile-time vs runtime configuration documented
- [ ] Feature flags and conditional compilation reviewed
- [ ] Debug vs release build differences noted

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C/Embedded Project Context Analysis

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Analysis Protocol

Please perform a comprehensive context analysis of this C/embedded project following this protocol:

## Phase 1: Project Discovery

1. **Identify Project Fundamentals**
   - Read and summarize README.md and primary documentation
   - Determine project purpose: firmware, bootloader, device driver, bare metal, RTOS-based
   - Identify target hardware: microcontroller family, board, peripherals
   - Document real-time requirements and constraints
   - Identify safety/certification requirements (automotive, medical, aerospace)

2. **Map Repository Structure**
   ```
   Typical embedded project structure:
   project/
   ├── src/                    # Source files
   │   ├── main.c             # Entry point
   │   ├── drivers/           # Hardware drivers
   │   ├── hal/               # Hardware abstraction layer
   │   ├── app/               # Application logic
   │   └── rtos/              # RTOS configuration
   ├── inc/                   # Header files
   ├── lib/                   # External libraries
   ├── config/                # Configuration files
   ├── linker/                # Linker scripts (.ld)
   ├── tests/                 # Unit/integration tests
   ├── docs/                  # Documentation
   └── Makefile or CMakeLists.txt
   ```
   - Document the actual structure
   - Identify deviations from standard patterns
   - Locate startup code and initialization sequences

3. **Hardware Platform Details**
   - Microcontroller: Family, part number, core (ARM Cortex-M, RISC-V, AVR, etc.)
   - Flash size: Total and available
   - RAM size: Total and available
   - Clock speed: System clock, peripheral clocks
   - Peripherals: UART, SPI, I2C, ADC, timers, DMA, etc.
   - External components: Sensors, displays, communication modules

## Phase 2: Architecture Understanding

1. **System Architecture**
   - Determine architecture type:
     - Bare metal (superloop)
     - RTOS-based (FreeRTOS, Zephyr, ThreadX, etc.)
     - Event-driven
     - State machine-based
   - Map task/thread structure (if RTOS)
   - Identify interrupt priorities and nesting
   - Document communication mechanisms (queues, semaphores, mutexes)

2. **Initialization & Boot Sequence**
   ```c
   // Trace startup sequence:
   1. Reset vector (startup_*.s or startup_*.c)
   2. SystemInit() - Clock and core configuration
   3. __libc_init_array() - C runtime initialization
   4. main() entry
   5. Peripheral initialization
   6. RTOS scheduler start (if applicable)
   7. Application tasks/main loop
   ```

3. **Module Organization**
   - Hardware abstraction: How hardware is abstracted from application
   - Driver organization: Low-level, middleware, high-level
   - Application layers: Business logic separation
   - Module dependencies and coupling
   - Interface design patterns

4. **Memory Architecture**
   ```
   Analyze linker script (.ld file):
   - Code section (.text)
   - Initialized data (.data)
   - Uninitialized data (.bss)
   - Stack allocation
   - Heap allocation (if used)
   - Memory-mapped peripherals
   - Special sections (DMA buffers, shared memory)
   ```

## Phase 3: Build System & Toolchain Analysis

1. **Build Configuration**
   - Build system: Makefile, CMake, IDE project, custom scripts
   - Compiler: GCC, Clang, IAR, Keil, proprietary
   - Compiler version and target architecture
   - Cross-compilation setup (arm-none-eabi-gcc, etc.)

2. **Compiler Flags Review**
   ```bash
   # Check Makefile or build scripts for:

   # Optimization level
   -O0 (debug), -O1, -O2, -O3, -Os (size), -Og (debug-friendly)

   # Target-specific
   -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16

   # Warnings
   -Wall -Wextra -Werror

   # Standards
   -std=c11 -std=c99

   # Debug symbols
   -g -g3 -gdwarf-4

   # Link-time optimization
   -flto
   ```

3. **Linker Script Analysis**
   - Review memory regions (FLASH, RAM, special regions)
   - Check stack size allocation
   - Verify heap configuration
   - Identify custom memory sections
   - Review symbol exports and imports

4. **Build Artifacts**
   - Output formats: .elf, .bin, .hex
   - Map file generation: memory usage report
   - Symbol file for debugging
   - Size reporting: text, data, bss sections

## Phase 4: Dependency & Library Analysis

1. **Third-Party Components**
   - RTOS: FreeRTOS, Zephyr, CMSIS-RTOS, proprietary
   - Vendor HAL/SDK: STM32Cube, ESP-IDF, Nordic SDK, etc.
   - Communication stacks: TCP/IP, USB, Bluetooth, LoRa
   - File systems: FatFS, LittleFS
   - Bootloaders: U-Boot, custom
   - Cryptography: mbedTLS, WolfSSL

2. **Dependency Health Check**
   - Component versions: latest, outdated, obsolete
   - Security advisories: CVEs for embedded libraries
   - Vendor support status: active, legacy, deprecated
   - Update frequency and maintenance status

3. **License Compliance**
   - Component licenses: BSD, MIT, GPL, proprietary
   - License compatibility assessment
   - Attribution requirements
   - GPL contamination risks (especially for commercial products)

## Phase 5: Resource Usage Analysis

1. **Memory Analysis**
   ```bash
   # Examine build output
   arm-none-eabi-size firmware.elf

   # Or parse map file
   grep -A 20 "Memory Configuration" firmware.map

   # Look for:
   - Flash usage: X KB / Y KB (Z%)
   - RAM usage: X KB / Y KB (Z%)
   - Stack allocation
   - Heap allocation (if used)
   ```

2. **Memory Map Review**
   - Code placement in Flash
   - Data sections in RAM
   - DMA buffers: special alignment requirements
   - Memory-mapped peripheral registers
   - Reserved areas: bootloader, configuration, logs

3. **Resource Constraints**
   - Identify memory pressure (>80% Flash or RAM usage)
   - Stack overflow risks
   - Heap fragmentation concerns
   - DMA buffer placement and alignment

## Phase 6: Configuration Management

1. **Configuration Files**
   - config.h, board.h, FreeRTOSConfig.h, etc.
   - Feature flags and conditional compilation (#ifdef/#ifndef)
   - Hardware configuration (pin assignments, peripheral config)
   - Build-time vs runtime configuration trade-offs

2. **Conditional Compilation Review**
   ```c
   // Identify patterns like:
   #ifdef ENABLE_FEATURE_X
   #ifndef DEBUG_MODE
   #if defined(BOARD_V2) && !defined(BOOTLOADER)
   ```
   - Feature enabling/disabling
   - Debug vs release differences
   - Platform-specific code
   - Version-specific code

3. **Debug Configuration**
   - Debug interface: SWD, JTAG, UART
   - Debug symbols and optimization
   - Logging/tracing configuration
   - Profiling and instrumentation

## Phase 7: Codebase Metrics

1. **Size & Complexity Metrics**
   ```bash
   # Lines of code (excluding vendor libraries)
   find src/ -name "*.c" -o -name "*.h" | xargs wc -l

   # Complexity (if tools available)
   # Use lizard, pmccabe, or cppcheck
   lizard src/ -l c
   ```

2. **Code Organization Metrics**
   - Number of modules/files
   - Average file size
   - Largest files (potential refactoring candidates)
   - Cyclomatic complexity per function
   - Comment density

3. **Dependency Metrics**
   ```bash
   # Use cflow, egypt, or similar
   cflow -o cflow.txt src/*.c

   # Analyze:
   - Function call depth
   - Circular dependencies
   - Unused functions
   - Global variable usage
   ```

## Phase 8: RTOS Configuration (if applicable)

1. **RTOS Details**
   - RTOS name and version
   - Configuration file (FreeRTOSConfig.h, etc.)
   - Scheduler type: preemptive, cooperative
   - Tick rate configuration

2. **Task/Thread Analysis**
   - Number of tasks/threads
   - Task priorities
   - Stack sizes per task
   - Task communication mechanisms

3. **Synchronization Primitives**
   - Mutexes, semaphores, events
   - Message queues
   - Critical sections
   - Interrupt-safe mechanisms

## Output Format

Please provide a comprehensive context report with the following structure:

### Executive Summary
- **Project Name**: [name]
- **Purpose**: [1-2 sentence description]
- **Target Hardware**: [MCU family and board]
- **Architecture**: [bare metal/RTOS/hybrid]
- **Compiler**: [toolchain and version]
- **Safety/Certification**: [requirements if any]

### Hardware Platform
- **Microcontroller**: [Family, part number, core architecture]
- **Flash Memory**: [size and usage]
- **RAM**: [size and usage]
- **Clock Speed**: [frequencies]
- **Key Peripherals**: [list]
- **External Components**: [sensors, actuators, communication modules]

### Project Structure
```
project/
├── [key directories and their purposes]
├── [entry points and startup files]
├── [linker scripts]
└── [build system files]
```

### Architecture Overview
- **System Type**: [bare metal, RTOS-based, event-driven]
- **Initialization Flow**: [brief description]
- **Module Organization**: [layering and abstraction]
- **Interrupt Handling**: [ISR count and priority scheme]
- **Memory Architecture**: [Flash/RAM organization]

### Build System
| Component | Details |
|-----------|---------|
| Build Tool | [Make, CMake, IDE] |
| Compiler | [name and version] |
| Optimization | [level and flags] |
| Standard | [C99, C11, C17] |
| Key Flags | [important compiler flags] |

### Dependency Summary
| Component | Version | Purpose | Status | License |
|-----------|---------|---------|--------|---------|
| [name] | [version] | [usage] | [current/outdated] | [license] |

### Resource Usage
- **Flash Usage**: [X KB / Y KB (Z%)]
- **RAM Usage**: [X KB / Y KB (Z%)]
- **Stack Allocation**: [size per task/total]
- **Heap Usage**: [size if used]
- **Resource Pressure**: [None/Low/Medium/High]

### RTOS Configuration (if applicable)
- **RTOS**: [name and version]
- **Scheduler**: [type and tick rate]
- **Tasks**: [count and priorities]
- **Stack Sizes**: [per task]
- **Synchronization**: [mechanisms used]

### Codebase Metrics
- **Total Lines**: [number] (excluding vendor code)
- **Source Files**: [count]
- **Average File Size**: [lines]
- **Largest Files**: [list files >500 lines]
- **Function Complexity**: [average cyclomatic complexity]

### Key Findings
1. **Strengths**: [positive observations]
2. **Concerns**: [potential issues to investigate]
3. **Dependencies**: [outdated or problematic components]
4. **Resource Constraints**: [memory pressure, timing concerns]
5. **Build Issues**: [warnings, deprecated features]

### Recommendations for Review Focus
Based on this context, the following review areas should be prioritized:
1. [Area 1] - [reason]
2. [Area 2] - [reason]
3. [Area 3] - [reason]

### Next Steps
- [ ] Proceed with code quality review (MISRA-C, CERT-C compliance)
- [ ] Conduct security audit (buffer overflows, memory safety)
- [ ] Perform performance analysis (timing, resource usage)
- [ ] Review interrupt handling and real-time behavior
- [ ] Assess test coverage (unit tests, hardware-in-the-loop)

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p review/context_analysis/analysis_scripts
mkdir -p review/context_analysis/supporting_data
```

**Save files as follows**:

- Main report → `review/context_analysis/context_analysis_report.md`

- Findings data → `review/context_analysis/context_analysis_findings.json`

- Analysis scripts → `review/context_analysis/analysis_scripts/`

- Supporting data → `review/context_analysis/supporting_data/`

## Notes
- Save this context report - it will inform all subsequent review phases
- Flag any critical resource constraints or hardware limitations
- Document any safety-critical or certification requirements
- Note toolchain-specific issues or vendor SDK quirks
- Identify areas where static analysis tools should focus
~~~
