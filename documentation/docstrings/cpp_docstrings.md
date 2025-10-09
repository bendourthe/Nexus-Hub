# C++ Documentation Comments (Doxygen)

## Objective
Generate comprehensive, standards-compliant Doxygen documentation comments for all public interfaces (namespaces, classes, templates, functions) that clearly document purpose, parameters, return values, and provide usage examples following Doxygen conventions for modern C++ code.

## Implementation Checklist

### File/Header Documentation
- [ ] File purpose and scope clearly explained
- [ ] Key classes and templates listed
- [ ] Dependencies and requirements noted
- [ ] Usage examples provided
- [ ] Author and version information included

### Class/Template Documentation
- [ ] Class purpose and responsibility documented
- [ ] Template parameters documented
- [ ] All public members described
- [ ] Constructor/destructor behavior explained
- [ ] Move/copy semantics documented
- [ ] Exception safety guarantees noted

### Function/Method Documentation
- [ ] Function purpose clearly stated
- [ ] All parameters documented with @param/@tparam
- [ ] Return values documented with @return
- [ ] Exceptions documented with @throws/@exception
- [ ] Noexcept guarantees documented
- [ ] SFINAE/concepts requirements explained

### Special Member Documentation
- [ ] Constructor initialization documented
- [ ] Move semantics explained
- [ ] Copy behavior documented
- [ ] Operator overloads clearly explained
- [ ] Template specializations documented

### Documentation Style
- [ ] Consistent Doxygen style throughout codebase
- [ ] Proper use of Doxygen commands
- [ ] C++11/14/17/20 features documented
- [ ] Modern C++ idioms explained

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ Doxygen Documentation Generation Request

Please generate comprehensive Doxygen documentation for this C++ project following this protocol:

## Phase 1: Analysis & Modern C++ Review

1. **Analyze Existing Code**
   - Inventory all namespaces, classes, templates, and functions
   - Identify existing documentation patterns
   - Note C++ standard version used (C++11/14/17/20/23)
   - Check for existing Doxyfile configuration

2. **Review C++ Documentation Needs**
   - Template parameter documentation
   - Move/copy semantics
   - Exception safety guarantees
   - RAII patterns
   - Concept requirements (C++20)
   - Coroutine documentation (C++20)

3. **Check Project Structure**
   - Verify header organization
   - Identify public API vs implementation details
   - Note namespace hierarchy
   - Document build requirements

## Phase 2: File and Namespace Documentation

### File Documentation Template
```cpp
/**
 * @file processor.hpp
 * @brief Advanced data processing with modern C++ features.
 *
 * This header provides a comprehensive template-based interface for processing
 * data with compile-time type safety, move semantics, and zero-cost abstractions.
 * It leverages modern C++ features for performance and expressiveness.
 *
 * @section features Key Features
 * - Template-based generic programming
 * - Move semantics for efficient resource management
 * - RAII for automatic cleanup
 * - Exception-safe guarantee (strong or no-throw)
 * - Constexpr support for compile-time evaluation
 * - Concept constraints (C++20) for clear error messages
 *
 * @section usage Usage Example
 * @code{.cpp}
 * #include <processor.hpp>
 * #include <vector>
 * #include <iostream>
 *
 * int main() {
 *     // Create processor with move semantics
 *     auto options = processing::Options{}
 *         .set_mode(processing::Mode::Strict)
 *         .set_workers(10)
 *         .set_timeout(std::chrono::seconds{30});
 *
 *     processing::Processor<std::string> processor{std::move(options)};
 *
 *     // Process data using ranges (C++20)
 *     std::vector<std::string> data = {"item1", "item2", "item3"};
 *     auto result = processor.process(data | std::views::filter(is_valid));
 *
 *     std::cout << "Processed: " << result.count() << " items\n";
 *     return 0;
 * }
 * @endcode
 *
 * @section threading Thread Safety
 * All classes are thread-safe unless explicitly documented otherwise.
 * Const methods can be called concurrently. Non-const methods require
 * external synchronization or use internal locking.
 *
 * @section exceptions Exception Safety
 * - Strong guarantee: Operations complete successfully or leave objects unchanged
 * - No-throw guarantee: Clearly marked with noexcept
 * - Basic guarantee: Objects remain in valid (but unspecified) state
 *
 * @section memory Memory Management
 * - RAII patterns for automatic resource management
 * - Move semantics for efficient transfers
 * - Smart pointers preferred over raw pointers
 * - No manual delete needed for managed resources
 *
 * @author John Doe <john.doe@example.com>
 * @version 2.0.0
 * @date 2024-01-15
 * @copyright MIT License
 *
 * @see processor_impl.hpp
 * @see processor_traits.hpp
 *
 * @since 1.0.0 (C++11)
 * @since 2.0.0 (C++20 with concepts)
 */

#ifndef PROCESSING_PROCESSOR_HPP
#define PROCESSING_PROCESSOR_HPP

#include <concepts>
#include <memory>
#include <chrono>
```

### Namespace Documentation Template
```cpp
/**
 * @namespace processing
 * @brief Data processing functionality with modern C++ idioms.
 *
 * This namespace contains classes and functions for data processing operations.
 * It provides a type-safe, efficient API leveraging C++17/20 features.
 *
 * @section organization Namespace Organization
 * - processing::detail - Implementation details (do not use directly)
 * - processing::traits - Type traits and metaprogramming utilities
 * - processing::literals - User-defined literals for configuration
 *
 * @section concepts Key Concepts (C++20)
 * - Processable: Types that can be processed
 * - ProcessorCallable: Valid processing function objects
 * - ResultType: Valid result types
 */
namespace processing {

/**
 * @namespace processing::literals
 * @brief User-defined literals for convenient configuration.
 *
 * This namespace provides literal operators for creating duration and
 * size values with clear units.
 *
 * @code{.cpp}
 * using namespace processing::literals;
 * auto timeout = 30_sec;  // std::chrono::seconds{30}
 * auto buffer = 1_MB;     // 1048576 bytes
 * @endcode
 */
namespace literals {
    // Literal operator implementations
}

} // namespace processing
```

## Phase 3: Class and Template Documentation

### Class Template Documentation
```cpp
/**
 * @class Processor
 * @brief Generic data processor with compile-time type safety.
 *
 * Processor provides a type-safe, efficient interface for processing data
 * of any type that satisfies the Processable concept. It uses move semantics
 * for optimal performance and RAII for resource management.
 *
 * @tparam T The type of data to process. Must satisfy the Processable concept,
 *           which requires T to be move-constructible and have a valid() method.
 * @tparam Allocator The allocator type for internal storage.
 *                   Defaults to std::allocator<T>.
 *
 * @section lifecycle Object Lifecycle
 * - Constructed with Options (moved for efficiency)
 * - Movable but not copyable (unique ownership)
 * - Automatically cleaned up on destruction (RAII)
 *
 * @section thread_safety Thread Safety
 * - Const methods are thread-safe and can be called concurrently
 * - Non-const methods require external synchronization
 * - Internal state protected by mutex for concurrent process() calls
 *
 * @section exception_safety Exception Safety
 * - Constructor: Strong guarantee (throws on failure)
 * - process(): Strong guarantee (original data unchanged on failure)
 * - Destructor: No-throw guarantee (noexcept)
 * - Move operations: No-throw guarantee (noexcept)
 *
 * @code{.cpp}
 * // Create processor with custom allocator
 * processing::Processor<std::string, CustomAllocator<std::string>> processor{
 *     processing::Options{}
 *         .set_mode(processing::Mode::Strict)
 *         .set_workers(std::thread::hardware_concurrency())
 * };
 *
 * // Process data (move semantics)
 * std::vector<std::string> data = load_data();
 * auto result = processor.process(std::move(data));
 *
 * // Chaining with ranges (C++20)
 * auto filtered_result = processor.process(
 *     data | std::views::filter([](auto& item) { return item.size() > 10; })
 * );
 * @endcode
 *
 * @note This class is move-only to enforce unique ownership of resources.
 * @warning Do not use after move. Moved-from objects are in valid but
 *          unspecified state (can only be destroyed or assigned to).
 *
 * @see Options
 * @see Result
 * @see Processable concept
 *
 * @since 1.0.0
 * @since 2.0.0 Added concept constraints
 */
template <Processable T, typename Allocator = std::allocator<T>>
class Processor {
public:
    /// Type alias for processed data type
    using value_type = T;
    /// Type alias for allocator
    using allocator_type = Allocator;
    /// Type alias for result type
    using result_type = Result<T>;

    // Class implementation
};
```

### Regular Class Documentation
```cpp
/**
 * @class Options
 * @brief Configuration options for Processor creation.
 *
 * Options uses the builder pattern for fluent configuration. All setters
 * return *this to allow method chaining.
 *
 * @section defaults Default Values
 * - mode: Mode::Strict
 * - workers: std::thread::hardware_concurrency()
 * - timeout: 30 seconds
 * - retry_attempts: 3
 *
 * @section example Usage Example
 * @code{.cpp}
 * auto options = processing::Options{}
 *     .set_mode(processing::Mode::Lenient)
 *     .set_workers(16)
 *     .set_timeout(std::chrono::minutes{5})
 *     .set_retry_attempts(5);
 * @endcode
 *
 * @note Options objects are copyable and movable.
 * @note All setters perform validation and may throw std::invalid_argument.
 */
class Options {
public:
    /**
     * @brief Constructs Options with default values.
     *
     * Creates an Options object with sensible defaults suitable for most
     * use cases. Customize using setter methods.
     *
     * @throws Never throws (noexcept).
     */
    Options() noexcept = default;

    // Method declarations
};
```

### Interface/Abstract Class Documentation
```cpp
/**
 * @class IHandler
 * @brief Abstract interface for event handlers.
 *
 * IHandler defines the contract for handling events. Implementations must
 * be thread-safe as handle() may be called concurrently from multiple threads.
 *
 * @section implementing Implementing IHandler
 * 1. Inherit from IHandler
 * 2. Implement handle() with thread-safe logic
 * 3. Ensure handle() provides exception safety guarantees
 * 4. Make handle() noexcept if guaranteed not to throw
 *
 * @code{.cpp}
 * class LogHandler : public IHandler {
 * public:
 *     void handle(const Event& event) override {
 *         std::lock_guard lock{mutex_};
 *         log_ << event.to_string() << std::endl;
 *     }
 *
 * private:
 *     mutable std::mutex mutex_;
 *     std::ofstream log_;
 * };
 * @endcode
 *
 * @note Pure virtual destructor ensures proper cleanup in derived classes.
 * @note Use smart pointers (std::unique_ptr, std::shared_ptr) for ownership.
 */
class IHandler {
public:
    /**
     * @brief Virtual destructor for proper polymorphic deletion.
     *
     * @throws Never throws (noexcept).
     */
    virtual ~IHandler() noexcept = default;

    /**
     * @brief Handles a single event.
     *
     * Implementations must be thread-safe. This method may be called
     * concurrently from multiple threads.
     *
     * @param event The event to handle. Passed by const reference for
     *              efficiency. Handler must not modify the event.
     *
     * @throws std::exception derived types on error. Implementations should
     *         document specific exception types.
     *
     * @note Must be thread-safe.
     * @note Should complete quickly (< 100ms typical).
     */
    virtual void handle(const Event& event) = 0;
};
```

## Phase 4: Function and Method Documentation

### Template Function Documentation
```cpp
/**
 * @brief Processes a range of items using parallel execution.
 *
 * This function template processes all items in the given range concurrently,
 * distributing work across multiple threads. It returns a vector of results
 * corresponding to each input item.
 *
 * @tparam Range The range type. Must satisfy std::ranges::range concept and
 *               contain elements of type T that satisfy Processable.
 * @tparam Func The callable type for processing. Must be invocable with
 *              range value_type and return a Result<T>.
 *
 * @param range The input range to process. Passed by forwarding reference
 *              to support both lvalues and rvalues efficiently.
 * @param func The processing function to apply to each element. Must be
 *             thread-safe as it will be called concurrently.
 * @param workers Number of worker threads. Must be positive.
 *                Defaults to std::thread::hardware_concurrency().
 *
 * @return std::vector<Result<T>> containing results for each input item,
 *         in the same order as the input range.
 *
 * @throws std::invalid_argument if workers is zero or negative.
 * @throws std::bad_alloc if memory allocation fails.
 * @throws Exception types from Func if processing fails in Strict mode.
 *
 * @par Complexity
 * - Time: O(n/p) where n = range size, p = workers (assuming balanced load)
 * - Space: O(n) for result storage
 *
 * @par Exception Safety
 * Strong guarantee: If an exception is thrown, the input range is unchanged
 * and all resources are properly cleaned up.
 *
 * @par Thread Safety
 * This function is thread-safe. Multiple threads can call process_parallel()
 * concurrently. The func parameter must be thread-safe.
 *
 * @code{.cpp}
 * // Process vector with default workers
 * std::vector<int> numbers = {1, 2, 3, 4, 5};
 * auto results = process_parallel(numbers, [](int n) {
 *     return Result{n * n};
 * });
 *
 * // Process range with custom worker count
 * auto filtered = numbers | std::views::filter([](int n) { return n % 2 == 0; });
 * auto results = process_parallel(filtered, processor, 8);
 *
 * // Process with move semantics
 * auto results = process_parallel(std::move(numbers), processor);
 * // numbers is now moved-from (don't use)
 * @endcode
 *
 * @note Func must be thread-safe if workers > 1.
 * @note Input range is consumed if passed as rvalue.
 * @warning Range iterators must remain valid during processing.
 *
 * @see Processor
 * @see Result
 * @see Processable
 *
 * @since 2.0.0 (C++20)
 */
template <std::ranges::range Range, std::invocable<std::ranges::range_value_t<Range>> Func>
    requires Processable<std::ranges::range_value_t<Range>>
auto process_parallel(Range&& range, Func&& func, size_t workers = 0)
    -> std::vector<Result<std::ranges::range_value_t<Range>>>;
```

### Member Function Documentation
```cpp
/**
 * @brief Processes a collection of items.
 *
 * Processes all items using configured settings. In parallel mode, distributes
 * work across worker threads. In strict mode, fails immediately on error.
 *
 * @param items The items to process. Passed by const reference; original
 *              collection is not modified.
 *
 * @return Result object containing processing outcomes and statistics.
 *
 * @throws ProcessingException if processing fails in Strict mode.
 * @throws std::bad_alloc if memory allocation fails.
 *
 * @par Exception Safety
 * Strong guarantee: On exception, processor state is unchanged.
 *
 * @par Thread Safety
 * This method is thread-safe and can be called concurrently from multiple
 * threads on the same Processor instance.
 *
 * @code{.cpp}
 * std::vector<std::string> items = {"a", "b", "c"};
 * try {
 *     auto result = processor.process(items);
 *     std::cout << "Success: " << result.succeeded() << std::endl;
 * } catch (const ProcessingException& e) {
 *     std::cerr << "Error: " << e.what() << std::endl;
 * }
 * @endcode
 */
[[nodiscard]] auto process(const std::vector<T>& items) const -> Result<T>;
```

### Constructor Documentation
```cpp
/**
 * @brief Constructs a Processor with the given options.
 *
 * Initializes internal resources including thread pool and work queues.
 * The options parameter is moved for efficiency; the source Options object
 * is left in a valid but unspecified state.
 *
 * @param options Configuration options. Moved into the processor.
 *                After this call, options is moved-from.
 *
 * @throws std::invalid_argument if options contains invalid values.
 * @throws std::system_error if thread creation fails.
 * @throws std::bad_alloc if memory allocation fails.
 *
 * @par Exception Safety
 * Strong guarantee: If construction fails, all resources are cleaned up
 * and no Processor object is created.
 *
 * @code{.cpp}
 * auto options = Options{}.set_workers(10);
 * Processor<int> proc{std::move(options)};
 * // options is now moved-from (don't use)
 * @endcode
 *
 * @note This constructor is explicit to prevent implicit conversions.
 * @note Options are moved, not copied, for efficiency.
 */
explicit Processor(Options&& options);

/**
 * @brief Copy constructor is deleted.
 *
 * Processor manages unique resources (thread pool, queues) that cannot
 * be safely copied. Use std::move() to transfer ownership or std::shared_ptr
 * for shared ownership.
 *
 * @code{.cpp}
 * Processor<int> p1{options};
 * // Processor<int> p2 = p1;  // ERROR: copy is deleted
 * Processor<int> p2 = std::move(p1);  // OK: move is allowed
 * @endcode
 */
Processor(const Processor&) = delete;

/**
 * @brief Move constructor.
 *
 * Transfers ownership of resources from other to this. After the move,
 * other is left in a valid but unspecified state and should only be
 * destroyed or assigned to.
 *
 * @param other The processor to move from.
 *
 * @throws Never throws (noexcept).
 *
 * @par Exception Safety
 * No-throw guarantee.
 *
 * @code{.cpp}
 * Processor<int> p1{options};
 * Processor<int> p2 = std::move(p1);
 * // p1 is now moved-from (can only destroy or assign)
 * // p2 owns all resources
 * @endcode
 */
Processor(Processor&& other) noexcept;
```

### Destructor Documentation
```cpp
/**
 * @brief Destructor that cleanly shuts down processor.
 *
 * Stops all worker threads, completes pending work, and releases all
 * resources. Blocks until all threads have terminated.
 *
 * @throws Never throws (noexcept).
 *
 * @par Exception Safety
 * No-throw guarantee. All cleanup operations are performed even if
 * internal errors occur.
 *
 * @note This is a RAII class. Destructor is called automatically when
 *       the object goes out of scope.
 * @warning Do not call explicitly (delete ptr). Use smart pointers or
 *          stack allocation for automatic cleanup.
 */
~Processor() noexcept;
```

### Operator Overload Documentation
```cpp
/**
 * @brief Function call operator for convenient processing.
 *
 * Provides function-like syntax for processing. Equivalent to calling
 * process(items).
 *
 * @param items The items to process.
 * @return Result object with processing outcomes.
 *
 * @throws Same exceptions as process().
 *
 * @code{.cpp}
 * Processor<int> proc{options};
 * std::vector<int> data = {1, 2, 3};
 *
 * // Both are equivalent
 * auto result1 = proc.process(data);
 * auto result2 = proc(data);  // Function call syntax
 * @endcode
 */
[[nodiscard]] auto operator()(const std::vector<T>& items) const -> Result<T>;

/**
 * @brief Move assignment operator.
 *
 * Assigns other to this by transferring ownership. The current object's
 * resources are cleaned up first, then other's resources are moved.
 *
 * @param other The processor to move from.
 * @return Reference to this.
 *
 * @throws Never throws (noexcept).
 *
 * @par Exception Safety
 * No-throw guarantee.
 *
 * @code{.cpp}
 * Processor<int> p1{options1};
 * Processor<int> p2{options2};
 * p1 = std::move(p2);  // p1 now owns p2's resources
 * @endcode
 */
auto operator=(Processor&& other) noexcept -> Processor&;
```

## Phase 5: C++ Specific Documentation

### Concept Documentation (C++20)
```cpp
/**
 * @concept Processable
 * @brief Defines requirements for types that can be processed.
 *
 * A type T is Processable if it:
 * - Is move-constructible
 * - Has a valid() member function returning bool
 * - Is destructible
 *
 * @tparam T The type to check.
 *
 * @code{.cpp}
 * struct MyData {
 *     std::string value;
 *     bool valid() const { return !value.empty(); }
 * };
 * static_assert(Processable<MyData>);  // Compiles
 * @endcode
 *
 * @see Processor
 * @since 2.0.0
 */
template <typename T>
concept Processable = std::move_constructible<T> &&
    requires(const T& t) {
        { t.valid() } -> std::convertible_to<bool>;
    };
```

### Smart Pointer Return Documentation
```cpp
/**
 * @brief Creates a new processor instance.
 *
 * Factory function that returns a unique pointer to a newly created processor.
 * Uses perfect forwarding to construct the processor with given arguments.
 *
 * @tparam T The data type to process.
 * @tparam Args Constructor argument types (deduced).
 *
 * @param args Arguments forwarded to Processor constructor.
 *
 * @return std::unique_ptr<Processor<T>> owning the new processor.
 *
 * @throws Same exceptions as Processor constructor.
 *
 * @code{.cpp}
 * auto proc = make_processor<int>(Options{}.set_workers(10));
 * auto result = proc->process(data);
 * // proc automatically cleaned up
 * @endcode
 *
 * @note Returns unique_ptr for clear ownership semantics.
 * @see Processor::Processor()
 */
template <typename T, typename... Args>
[[nodiscard]] auto make_processor(Args&&... args) -> std::unique_ptr<Processor<T>>;
```

### Coroutine Documentation (C++20)
```cpp
/**
 * @brief Asynchronously processes items using coroutines.
 *
 * This coroutine processes items asynchronously, yielding control back to
 * the caller between items. Useful for UI applications or servers that need
 * to remain responsive.
 *
 * @param items The items to process.
 *
 * @return Task<Result<T>> that can be co_awaited.
 *
 * @throws ProcessingException if processing fails.
 *
 * @code{.cpp}
 * Task<void> process_data() {
 *     std::vector<int> items = {1, 2, 3};
 *     auto result = co_await processor.process_async(items);
 *     std::cout << "Processed: " << result.succeeded() << std::endl;
 * }
 * @endcode
 *
 * @note Requires C++20 coroutine support.
 * @since 2.1.0
 */
[[nodiscard]] auto process_async(std::vector<T> items) -> Task<Result<T>>;
```

### Constexpr Function Documentation
```cpp
/**
 * @brief Computes compile-time processing parameters.
 *
 * This constexpr function computes optimal processing parameters at compile
 * time based on data size and worker count.
 *
 * @param data_size The size of data to process.
 * @param workers The number of workers.
 *
 * @return ProcessingParams with optimal settings.
 *
 * @par Compile-Time Evaluation
 * This function can be evaluated at compile time if all arguments are
 * constant expressions.
 *
 * @code{.cpp}
 * // Computed at compile time
 * constexpr auto params = compute_params(1000, 8);
 * static_assert(params.batch_size == 125);
 *
 * // Can also be used at runtime
 * auto runtime_params = compute_params(data.size(), workers);
 * @endcode
 *
 * @since 2.0.0
 */
[[nodiscard]] constexpr auto compute_params(size_t data_size, size_t workers) noexcept
    -> ProcessingParams;
```

### SFINAE/Enable If Documentation
```cpp
/**
 * @brief Processes integral types with specialized algorithm.
 *
 * This overload is selected when T is an integral type. It uses a
 * specialized algorithm optimized for integers.
 *
 * @tparam T The integral type to process.
 * @tparam Enable SFINAE helper (internal, do not specify).
 *
 * @param value The value to process.
 *
 * @return Processed result.
 *
 * @note This overload is only available for integral types.
 * @note Uses SFINAE for overload resolution.
 *
 * @code{.cpp}
 * auto result1 = process(42);      // Uses this overload
 * auto result2 = process(3.14);    // Uses different overload
 * auto result3 = process("text");  // Uses different overload
 * @endcode
 */
template <typename T, typename Enable = std::enable_if_t<std::is_integral_v<T>>>
[[nodiscard]] auto process(T value) -> Result<T>;
```

## Phase 6: Doxygen Quality Checks for C++

### Completeness
- [ ] All public APIs documented
- [ ] Template parameters with @tparam
- [ ] Concept requirements explained
- [ ] Move/copy semantics documented
- [ ] Exception safety guarantees stated
- [ ] noexcept specifications explained

### Modern C++ Features
- [ ] Move semantics documented
- [ ] Smart pointer ownership clear
- [ ] Concept constraints explained
- [ ] Coroutines documented
- [ ] constexpr usage noted
- [ ] SFINAE/enable_if explained

### C++ Best Practices
- [ ] RAII patterns documented
- [ ] Rule of five/zero noted
- [ ] Exception safety levels stated
- [ ] Thread safety explicitly documented
- [ ] [[nodiscard]] rationale explained

### Clarity
- [ ] Clear, modern C++ terminology
- [ ] STL conventions followed
- [ ] Technical terms explained
- [ ] Examples use modern C++

## Phase 7: Documentation Generation

1. **Configure Doxyfile for C++**
   ```doxyfile
   # C++ specific settings
   PROJECT_NAME = "My C++ Project"
   EXTRACT_ALL = NO
   EXTRACT_PRIVATE = NO
   EXTRACT_STATIC = NO

   # C++ language settings
   OPTIMIZE_OUTPUT_FOR_C = NO
   CPP_CLI_SUPPORT = NO
   EXTENSION_MAPPING = hpp=C++ hxx=C++ h=C++

   # Enable C++ features
   BUILTIN_STL_SUPPORT = YES
   CPP_CLI_SUPPORT = NO
   SIP_SUPPORT = NO
   IDL_PROPERTY_SUPPORT = YES
   DISTRIBUTE_GROUP_DOC = NO

   # Template documentation
   INLINE_SIMPLE_STRUCTS = NO
   TYPEDEF_HIDES_STRUCT = NO
   ```

2. **Generate Documentation**
   ```bash
   doxygen Doxyfile
   ```

3. **Validate C++ Documentation**
   ```bash
   # Check for C++ specific warnings
   doxygen Doxyfile 2>&1 | grep -E "(warning|template|concept)"
   ```

## Output Format

### File-by-File Report
```markdown
## File: include/processor.hpp

### Class Template: Processor<T, Allocator>
[Generated Doxygen comment]

### Method: process
[Generated Doxygen comment]

### Concept: Processable
[Generated Doxygen comment]

---
```

### Summary Report
```markdown
## C++ Doxygen Documentation Summary

**Files Processed**: [count]
**Namespaces Documented**: [count]
**Classes Documented**: [count]
**Templates Documented**: [count]
**Functions Documented**: [count]
**Concepts Documented**: [count] (C++20)

**C++ Features Documented**:
- [ ] Template parameters (@tparam)
- [ ] Move/copy semantics
- [ ] Exception safety
- [ ] noexcept guarantees
- [ ] Concept constraints (C++20)
- [ ] Coroutines (C++20)

**Modern C++ Compliance**:
- [ ] RAII patterns documented
- [ ] Smart pointer ownership clear
- [ ] Rule of five/zero noted
- [ ] [[nodiscard]] usage explained

**Coverage Metrics**:
- Namespace coverage: [X%]
- Class coverage: [X%]
- Function coverage: [X%]
- Overall coverage: [X%]
```

## C++ Documentation Best Practices

1. **Document Template Parameters**
   - Use @tparam for each template parameter
   - Explain constraints and requirements
   - Document SFINAE conditions
   - Note concept requirements (C++20)

2. **Document Move Semantics**
   - State if class is move-only
   - Document moved-from state
   - Note noexcept on move operations
   - Explain resource transfer

3. **Document Exception Safety**
   - State guarantee level (basic/strong/no-throw)
   - List all exceptions that can be thrown
   - Note noexcept specifications
   - Explain rollback behavior

4. **Document Ownership**
   - Clear ownership with smart pointers
   - Document who manages lifetime
   - Note RAII patterns
   - Explain resource cleanup

5. **Use Modern C++ Idioms**
   - Prefer auto and type deduction
   - Use [[nodiscard]] and document why
   - Document constexpr capabilities
   - Explain concept constraints

## Common C++ Documentation Mistakes

1. **Forgetting template parameters**
   - Always use @tparam for templates
   - Document all type requirements
   - Explain SFINAE conditions

2. **Not documenting move semantics**
   - State if move-only
   - Document moved-from state
   - Note noexcept on moves

3. **Missing exception safety**
   - Always state guarantee level
   - Document all thrown exceptions
   - Note noexcept where applicable

4. **Unclear ownership**
   - Use smart pointers
   - Document lifetime management
   - Note RAII patterns

5. **Ignoring modern features**
   - Document concepts (C++20)
   - Note constexpr usage
   - Explain coroutines (C++20)
~~~

## Validation Tools

```cmake
# CMake configuration for Doxygen
find_package(Doxygen REQUIRED)

set(DOXYGEN_GENERATE_HTML YES)
set(DOXYGEN_GENERATE_MAN NO)
set(DOXYGEN_EXTRACT_ALL NO)
set(DOXYGEN_BUILTIN_STL_SUPPORT YES)

doxygen_add_docs(docs
    ${PROJECT_SOURCE_DIR}/include
    ${PROJECT_SOURCE_DIR}/src
    COMMENT "Generate documentation"
)
```

## Output Format Specifications

The generated C++ Doxygen comments should:
- Follow modern C++ conventions and Doxygen standards
- Document all template parameters with @tparam
- State move/copy semantics explicitly
- Document exception safety guarantees
- Note noexcept specifications
- Explain concept requirements (C++20)
- Include runnable modern C++ examples
- Cross-reference with @see and @relates
- Generate well-formatted HTML documentation
- Pass Doxygen validation for C++ code
