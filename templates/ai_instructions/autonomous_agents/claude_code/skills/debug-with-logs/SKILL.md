---
name: debug-with-logs
description: Systematic debugging using strategic logging and log analysis techniques
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Workflow
tags: [workflow, debugging, logging, troubleshooting, best-practice]
priority: HIGH
---

# Debug with Logs

Master systematic debugging through strategic logging and log analysis. Learn to add effective logging statements, analyze log output, and solve problems efficiently without relying solely on debuggers.

## When to Use This Skill

Use this skill when:

- Investigating production issues where debuggers aren't available

- Debugging intermittent or timing-dependent bugs

- Understanding code flow in complex systems

- Troubleshooting integration issues between components

- Analyzing performance bottlenecks

- Debugging multithreaded or concurrent code

- Working with legacy code without test coverage

- Investigating issues in distributed systems

- Debugging issues that only occur in specific environments

- Learning unfamiliar codebases

**Logging is especially valuable when**:

- Issue only reproduces in production

- Debugger affects timing/behavior

- Multiple components interact

- Root cause is unclear

- Need historical context for debugging

## What This Skill Does

This skill provides a systematic approach to debugging that:

### 1. Strategic Logging
- Add meaningful log statements at critical points

- Use appropriate log levels (DEBUG, INFO, WARN, ERROR)

- Log contextual information (variables, state, timing)

- Avoid log spam and noise

### 2. Log Analysis
- Read and interpret log output effectively

- Identify patterns and anomalies

- Trace execution flow through logs

- Correlate events across components

### 3. Problem Solving
- Form hypotheses based on log evidence

- Validate assumptions with targeted logging

- Narrow down root cause systematically

- Document findings for future reference

### 4. Best Practices
- Structured logging for easier parsing

- Performance-conscious logging

- Security-aware logging (no sensitive data)

- Production-ready logging strategies

## Why Logging for Debugging Works

**Debugger-Only Approach** (Traditional):
```
Developer: *sets breakpoint*
Developer: *runs debugger*
Developer: *steps through code line by line*
Result:

- ❌ Debugger unavailable in production

- ❌ Changes program timing (hides race conditions)

- ❌ Slow iteration cycle (stop, inspect, repeat)

- ❌ No historical context

- ❌ Difficult for distributed systems

- ❌ Can't easily share debugging session
```

**Log-Based Debugging** (Modern):
```
Developer: *adds strategic log statements*
Developer: *runs application normally*
Developer: *analyzes log output*
Developer: *refines hypothesis and adds more logs*
Result:

- ✅ Works in any environment (dev, staging, prod)

- ✅ Captures real timing and behavior

- ✅ Fast iteration (just re-run)

- ✅ Historical record of events

- ✅ Perfect for distributed systems

- ✅ Logs can be shared with team
```

**Best Approach** (Combined):
```
Use debuggers for:

- Understanding code structure

- Exploring object state

- Local development

Use logging for:

- Production debugging

- Integration issues

- Performance analysis

- Long-term monitoring
```

## Benefits of Log-Based Debugging

### Production-Ready
- Works in environments where debuggers aren't available

- Doesn't require stopping or restarting services

- Minimal performance impact when done correctly

- Can be enabled/disabled dynamically

### Historical Context
- Logs provide timeline of events

- Can analyze multiple runs

- Identify patterns over time

- Correlate with monitoring metrics

### Collaboration
- Logs can be shared with team

- Provide evidence for bug reports

- Document reproduction steps

- Enable async debugging

### Comprehensive View
- See interactions between components

- Track data flow through system

- Identify side effects

- Understand system state changes

## Prerequisites

### Required
- Understanding of log levels (DEBUG, INFO, WARN, ERROR)

- Basic knowledge of logging frameworks

- Ability to read and interpret log output

- Access to application logs

### Recommended
- Log aggregation tool (ELK, Splunk, CloudWatch, etc.)

- Log viewer with search/filter capabilities

- Basic understanding of structured logging

- Familiarity with log rotation and retention

### Knowledge
- Programming concepts (variables, functions, control flow)

- Basic debugging principles

- Understanding of your logging framework

- Awareness of log performance implications

## Instructions

### Step 1: Understand the Problem

Before adding logs, clearly define what you're debugging:

**Ask yourself**:

- What is the expected behavior?

- What is the actual behavior?

- When does the problem occur?

- What are the symptoms?

- What do I need to learn?

**Example Problem**: "User reports that order confirmation emails are not being sent"

**Questions to answer**:

- Is the order being created successfully?

- Is the email service being called?

- Are there any errors during email sending?

- What's the timing of each step?

### Step 2: Identify Key Points for Logging

Identify where to add log statements:

**Entry and Exit Points**:
```python
# Log when entering/exiting functions
def process_order(order_id):
    logger.info(f"Processing order {order_id}")
    # ... processing logic ...
    logger.info(f"Completed processing order {order_id}")
```

**Decision Points**:
```python
# Log branch decisions
if user.is_premium():
    logger.debug(f"User {user.id} is premium, applying discount")
    apply_discount(order)
else:
    logger.debug(f"User {user.id} is standard, no discount applied")
```

**Error Conditions**:
```python
# Log errors with context
try:
    result = external_api.call()
except APIException as e:
    logger.error(f"API call failed for user {user_id}: {e}", exc_info=True)
```

**State Changes**:
```python
# Log important state transitions
logger.info(f"Order {order_id} status changed: {old_status} -> {new_status}")
```

**Integration Points**:
```python
# Log external calls
logger.debug(f"Calling payment gateway for order {order_id}")
response = payment_gateway.charge(amount)
logger.debug(f"Payment gateway response: {response.status}")
```

### Step 3: Use Appropriate Log Levels

Choose the right log level for each message:

| Level | Usage | Example |
|-------|-------|---------|
| **DEBUG** | Detailed diagnostic info | Variable values, loop iterations |
| **INFO** | General informational messages | Service started, user logged in |
| **WARN** | Warning messages, potentially harmful | Deprecated API used, high memory |
| **ERROR** | Error events but app still running | Failed API call, validation error |
| **CRITICAL** | Severe errors requiring attention | Database down, system crash |

**Python Example**:
```python
import logging

logger = logging.getLogger(__name__)

def process_payment(order_id, amount):
    # INFO: Important business event
    logger.info(f"Processing payment for order {order_id}, amount: ${amount}")

    # DEBUG: Detailed diagnostic info
    logger.debug(f"Payment details: order={order_id}, amount={amount}, currency=USD")

    # WARN: Potential issue
    if amount > 10000:
        logger.warning(f"High value transaction detected: ${amount} for order {order_id}")

    try:
        result = payment_gateway.charge(amount)
        # INFO: Success
        logger.info(f"Payment successful for order {order_id}, transaction_id: {result.id}")
        return result
    except PaymentDeclinedException as e:
        # ERROR: Recoverable error
        logger.error(f"Payment declined for order {order_id}: {e}")
        raise
    except PaymentGatewayException as e:
        # CRITICAL: System-level failure
        logger.critical(f"Payment gateway failure: {e}", exc_info=True)
        raise
```

### Step 4: Log Contextual Information

Include relevant context in log messages:

**What to Log**:

- **Identifiers**: User ID, order ID, request ID, correlation ID

- **Values**: Input parameters, calculated values, return values

- **Timing**: Timestamps, duration, elapsed time

- **State**: Current state, previous state, transitions

- **Environment**: Server name, environment (dev/prod), version

**Python Example**:
```python
import time

def calculate_order_total(order_id, items):
    start_time = time.time()

    # Log entry with context
    logger.info(f"Calculating total for order {order_id}, {len(items)} items")

    subtotal = sum(item.price * item.quantity for item in items)
    logger.debug(f"Order {order_id} subtotal: ${subtotal:.2f}")

    tax = calculate_tax(subtotal)
    logger.debug(f"Order {order_id} tax: ${tax:.2f}")

    total = subtotal + tax

    elapsed = time.time() - start_time
    # Log result with timing
    logger.info(
        f"Order {order_id} total calculated: ${total:.2f} "
        f"(subtotal: ${subtotal:.2f}, tax: ${tax:.2f}) in {elapsed:.3f}s"
    )

    return total
```

**JavaScript Example**:
```javascript
function processUserLogin(userId, loginSource) {
    const startTime = Date.now();

    // Log entry with context
    logger.info(`User login attempt`, {
        userId,
        loginSource,
        timestamp: new Date().toISOString()
    });

    try {
        const user = getUserById(userId);
        logger.debug(`User retrieved`, { userId, username: user.username });

        updateLastLogin(userId);
        logger.debug(`Last login updated`, { userId });

        const session = createSession(user);
        logger.info(`User login successful`, {
            userId,
            sessionId: session.id,
            duration: Date.now() - startTime
        });

        return session;
    } catch (error) {
        logger.error(`User login failed`, {
            userId,
            error: error.message,
            stack: error.stack,
            duration: Date.now() - startTime
        });
        throw error;
    }
}
```

### Step 5: Use Structured Logging

Use structured logging for easier analysis:

**Python Example** (with structlog):
```python
import structlog

logger = structlog.get_logger()

def process_order(order_id, user_id):
    # Bind context once
    log = logger.bind(order_id=order_id, user_id=user_id)

    log.info("order_processing_started")

    order = get_order(order_id)
    log.info("order_retrieved", items_count=len(order.items))

    total = calculate_total(order)
    log.info("total_calculated", amount=total)

    try:
        payment = process_payment(order_id, total)
        log.info("payment_processed", transaction_id=payment.id)
    except Exception as e:
        log.error("payment_failed", error=str(e), error_type=type(e).__name__)
        raise
```

**JSON Output** (easy to parse):
```json
{
  "event": "order_processing_started",
  "order_id": "ORD-12345",
  "user_id": "USR-789",
  "timestamp": "2025-10-20T14:30:00Z",
  "level": "info"
}
{
  "event": "payment_processed",
  "order_id": "ORD-12345",
  "user_id": "USR-789",
  "transaction_id": "TXN-54321",
  "timestamp": "2025-10-20T14:30:05Z",
  "level": "info"
}
```

### Step 6: Analyze Log Output

Read and interpret logs systematically:

**Techniques**:

1. **Follow the Flow**:
```
Start with entry log -> trace through execution -> find where it diverges
```

2. **Look for Gaps**:
```
Expected log message missing? -> That code wasn't executed
```

3. **Check Timing**:
```
Compare timestamps -> identify delays or bottlenecks
```

4. **Correlate Events**:
```
Use request IDs to follow flow across services
```

**Example Analysis**:
```
10:00:00.100 INFO  Order processing started [order=ORD-123]
10:00:00.150 DEBUG Retrieved order items [order=ORD-123, items=3]
10:00:00.200 DEBUG Calculated total [order=ORD-123, total=$150.00]
10:00:00.250 DEBUG Calling payment gateway [order=ORD-123]
--- No payment response log! ---
10:00:30.500 ERROR Payment timeout [order=ORD-123]

Analysis:

- Order retrieval works (logs present)

- Total calculation works (logs present)

- Payment gateway call initiated (log present)

- No response received from gateway (log missing)

- Timeout after 30 seconds (from timestamps)
Hypothesis: Payment gateway not responding -> Add network-level logging
```

### Step 7: Refine and Iterate

Based on log analysis, refine your logging:

**Add More Specific Logs**:
```python
# Initial logging
logger.info("Sending email")

# After analysis - need more detail
logger.info(f"Sending email to {email_address} with template {template_id}")
logger.debug(f"Email content: subject={subject}, recipient={email_address}")

# Send email...

logger.info(f"Email sent successfully, message_id={message_id}")
```

**Remove Unnecessary Logs**:
```python
# Too verbose - remove after debugging
# logger.debug(f"Loop iteration {i}")
# logger.debug(f"Variable x = {x}")
```

**Adjust Log Levels**:
```python
# Too noisy at INFO
# logger.info(f"Cache hit for key {key}")

# Better at DEBUG
logger.debug(f"Cache hit for key {key}")
```

### Step 8: Clean Up Temporary Logs

After debugging, clean up temporary logging:

**Keep**:

- Error logging

- Important business events

- Performance metrics

- Security events

- Integration points

**Remove**:

- Verbose debug statements

- Loop iteration logs

- Temporary diagnostic logs

- Excessive variable dumps

**Example Cleanup**:
```python
# Before (debugging)
def process_items(items):
    logger.debug(f"Starting process_items with {len(items)} items")  # REMOVE
    for i, item in enumerate(items):
        logger.debug(f"Processing item {i}: {item}")  # REMOVE
        result = process_item(item)
        logger.debug(f"Item {i} result: {result}")  # REMOVE
        logger.debug(f"Memory usage: {get_memory_usage()}")  # REMOVE
    logger.debug("Finished process_items")  # REMOVE

# After (production)
def process_items(items):
    logger.info(f"Processing {len(items)} items")  # KEEP - business event

    for item in items:
        try:
            result = process_item(item)
        except ProcessingError as e:
            logger.error(f"Failed to process item {item.id}: {e}")  # KEEP - error
            raise

    logger.info(f"Completed processing {len(items)} items")  # KEEP - completion
```

## Common Logging Patterns

### Pattern 1: Request/Response Logging

**HTTP API Example**:
```python
import uuid

def handle_request(request):
    # Generate correlation ID
    request_id = str(uuid.uuid4())

    # Log request
    logger.info(
        "Incoming request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.path,
            "user_id": request.user.id if request.user else None,
            "ip_address": request.remote_addr
        }
    )

    try:
        response = process_request(request)

        # Log response
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration": response.elapsed
            }
        )

        return response
    except Exception as e:
        # Log error
        logger.error(
            "Request failed",
            extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise
```

### Pattern 2: Performance Logging

**Timing Decorator Example**:
```python
import time
import functools

def log_performance(func):
    """Decorator to log function performance."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        logger.debug(f"Starting {func.__name__}")

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            logger.info(
                f"{func.__name__} completed in {elapsed:.3f}s",
                extra={"function": func.__name__, "duration": elapsed}
            )

            # Warn if slow
            if elapsed > 5.0:
                logger.warning(
                    f"{func.__name__} took {elapsed:.3f}s (threshold: 5.0s)"
                )

            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {elapsed:.3f}s: {e}",
                exc_info=True
            )
            raise

    return wrapper

@log_performance
def complex_calculation(data):
    # Expensive operation
    return process_data(data)
```

### Pattern 3: State Transition Logging

**State Machine Example**:
```python
class Order:
    def __init__(self, order_id):
        self.order_id = order_id
        self.state = "created"
        logger.info(f"Order {order_id} created")

    def transition_to(self, new_state, reason=None):
        old_state = self.state

        # Validate transition
        if not self._is_valid_transition(old_state, new_state):
            logger.error(
                f"Invalid state transition for order {self.order_id}: "
                f"{old_state} -> {new_state}"
            )
            raise ValueError(f"Cannot transition from {old_state} to {new_state}")

        # Log transition
        logger.info(
            f"Order {self.order_id} state transition: {old_state} -> {new_state}",
            extra={
                "order_id": self.order_id,
                "old_state": old_state,
                "new_state": new_state,
                "reason": reason
            }
        )

        self.state = new_state
```

### Pattern 4: Error Context Logging

**Exception Handling with Context**:
```python
def process_user_order(user_id, order_data):
    log = logger.bind(user_id=user_id)

    try:
        # Validate user
        user = get_user(user_id)
        if not user:
            log.error("User not found", user_id=user_id)
            raise UserNotFoundError(f"User {user_id} not found")

        log.info("User validated", username=user.username)

        # Validate order data
        if not validate_order_data(order_data):
            log.error("Invalid order data", order_data=order_data)
            raise ValidationError("Order data validation failed")

        log.info("Order data validated", items=len(order_data['items']))

        # Process order
        order = create_order(user, order_data)
        log.info("Order created", order_id=order.id)

        return order

    except UserNotFoundError as e:
        log.error("User lookup failed", error=str(e))
        raise
    except ValidationError as e:
        log.error("Validation failed", error=str(e))
        raise
    except DatabaseError as e:
        log.critical("Database error during order processing", error=str(e))
        raise
    except Exception as e:
        log.critical("Unexpected error", error=str(e), error_type=type(e).__name__)
        raise
```

## Language-Specific Examples

### Python with logging Module

**Setup**:
```python
import logging
import logging.config

# Configure logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s %(filename)s:%(lineno)d: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': 'app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file']
    }
})

logger = logging.getLogger(__name__)

# Usage
def process_data(data_id):
    logger.info(f"Processing data {data_id}")

    try:
        result = expensive_operation(data_id)
        logger.debug(f"Operation result for {data_id}: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to process {data_id}: {e}", exc_info=True)
        raise
```

### JavaScript with Winston

**Setup**:
```javascript
const winston = require('winston');

// Configure logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'user-service' },
  transports: [
    // Write to console
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    }),
    // Write to file
    new winston.transports.File({
      filename: 'error.log',
      level: 'error'
    }),
    new winston.transports.File({
      filename: 'combined.log'
    })
  ]
});

// Usage
function processOrder(orderId, userId) {
  logger.info('Processing order', { orderId, userId });

  try {
    const order = getOrder(orderId);
    logger.debug('Order retrieved', { orderId, itemCount: order.items.length });

    const total = calculateTotal(order);
    logger.info('Order total calculated', { orderId, total });

    return { order, total };
  } catch (error) {
    logger.error('Order processing failed', {
      orderId,
      userId,
      error: error.message,
      stack: error.stack
    });
    throw error;
  }
}
```

### Java with SLF4J and Logback

**Setup** (logback.xml):
```xml
<configuration>
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>logs/application.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>logs/application-%d{yyyy-MM-dd}.log</fileNamePattern>
            <maxHistory>30</maxHistory>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{50} - %msg%n</pattern>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="STDOUT" />
        <appender-ref ref="FILE" />
    </root>
</configuration>
```

**Usage**:
```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrderService {
    private static final Logger logger = LoggerFactory.getLogger(OrderService.class);

    public Order processOrder(String orderId, String userId) {
        logger.info("Processing order: orderId={}, userId={}", orderId, userId);

        try {
            Order order = orderRepository.findById(orderId);
            logger.debug("Order retrieved: orderId={}, items={}", orderId, order.getItems().size());

            BigDecimal total = calculateTotal(order);
            logger.info("Order total calculated: orderId={}, total={}", orderId, total);

            return order;
        } catch (OrderNotFoundException e) {
            logger.error("Order not found: orderId={}", orderId, e);
            throw e;
        } catch (Exception e) {
            logger.error("Unexpected error processing order: orderId={}, userId={}",
                        orderId, userId, e);
            throw new OrderProcessingException("Failed to process order", e);
        }
    }
}
```

### C# with Serilog

**Setup**:
```csharp
using Serilog;

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Debug()
    .WriteTo.Console()
    .WriteTo.File("logs/application.log",
        rollingInterval: RollingInterval.Day,
        outputTemplate: "{Timestamp:yyyy-MM-dd HH:mm:ss.fff} [{Level}] {Message}{NewLine}{Exception}")
    .CreateLogger();

// Usage
public class OrderService
{
    private readonly ILogger _logger;

    public OrderService()
    {
        _logger = Log.ForContext<OrderService>();
    }

    public Order ProcessOrder(string orderId, string userId)
    {
        _logger.Information("Processing order {OrderId} for user {UserId}", orderId, userId);

        try
        {
            var order = _orderRepository.GetById(orderId);
            _logger.Debug("Order {OrderId} retrieved with {ItemCount} items",
                         orderId, order.Items.Count);

            var total = CalculateTotal(order);
            _logger.Information("Order {OrderId} total calculated: {Total}", orderId, total);

            return order;
        }
        catch (OrderNotFoundException ex)
        {
            _logger.Error(ex, "Order {OrderId} not found", orderId);
            throw;
        }
        catch (Exception ex)
        {
            _logger.Error(ex, "Unexpected error processing order {OrderId}", orderId);
            throw new OrderProcessingException("Failed to process order", ex);
        }
    }
}
```

### Go with logrus

**Setup**:
```go
package main

import (
    "github.com/sirupsen/logrus"
    "os"
)

var log = logrus.New()

func init() {
    // Configure logrus
    log.SetFormatter(&logrus.JSONFormatter{})
    log.SetOutput(os.Stdout)
    log.SetLevel(logrus.InfoLevel)

    // Optional: write to file
    file, err := os.OpenFile("app.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
    if err == nil {
        log.SetOutput(file)
    }
}

// Usage
func processOrder(orderID string, userID string) (*Order, error) {
    log.WithFields(logrus.Fields{
        "order_id": orderID,
        "user_id":  userID,
    }).Info("Processing order")

    order, err := getOrder(orderID)
    if err != nil {
        log.WithFields(logrus.Fields{
            "order_id": orderID,
            "error":    err.Error(),
        }).Error("Failed to retrieve order")
        return nil, err
    }

    log.WithFields(logrus.Fields{
        "order_id":   orderID,
        "item_count": len(order.Items),
    }).Debug("Order retrieved")

    total := calculateTotal(order)

    log.WithFields(logrus.Fields{
        "order_id": orderID,
        "total":    total,
    }).Info("Order total calculated")

    return order, nil
}
```

### C with Custom Logging

**Setup**:
```c
#include <stdio.h>
#include <time.h>
#include <stdarg.h>

typedef enum {
    LOG_DEBUG,
    LOG_INFO,
    LOG_WARN,
    LOG_ERROR
} LogLevel;

const char* log_level_strings[] = {
    "DEBUG", "INFO", "WARN", "ERROR"
};

static LogLevel current_log_level = LOG_INFO;
static FILE* log_file = NULL;

void log_init(const char* filename, LogLevel level) {
    current_log_level = level;
    if (filename) {
        log_file = fopen(filename, "a");
    }
}

void log_message(LogLevel level, const char* file, int line, const char* format, ...) {
    if (level < current_log_level) {
        return;
    }

    time_t now;
    time(&now);
    char timestamp[64];
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", localtime(&now));

    // Print to console
    fprintf(stderr, "%s [%s] %s:%d: ", timestamp, log_level_strings[level], file, line);

    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);

    fprintf(stderr, "\n");

    // Also write to file if configured
    if (log_file) {
        fprintf(log_file, "%s [%s] %s:%d: ", timestamp, log_level_strings[level], file, line);
        va_start(args, format);
        vfprintf(log_file, format, args);
        va_end(args);
        fprintf(log_file, "\n");
        fflush(log_file);
    }
}

#define LOG_DEBUG(...) log_message(LOG_DEBUG, __FILE__, __LINE__, __VA_ARGS__)
#define LOG_INFO(...) log_message(LOG_INFO, __FILE__, __LINE__, __VA_ARGS__)
#define LOG_WARN(...) log_message(LOG_WARN, __FILE__, __LINE__, __VA_ARGS__)
#define LOG_ERROR(...) log_message(LOG_ERROR, __FILE__, __LINE__, __VA_ARGS__)

// Usage
void process_order(const char* order_id, int user_id) {
    LOG_INFO("Processing order %s for user %d", order_id, user_id);

    Order* order = get_order(order_id);
    if (!order) {
        LOG_ERROR("Order %s not found", order_id);
        return;
    }

    LOG_DEBUG("Order %s retrieved with %d items", order_id, order->item_count);

    double total = calculate_total(order);
    LOG_INFO("Order %s total calculated: $%.2f", order_id, total);

    free_order(order);
}
```

### C++ with spdlog

**Setup**:
```cpp
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/basic_file_sink.h>

class OrderService {
private:
    std::shared_ptr<spdlog::logger> logger;

public:
    OrderService() {
        // Create logger with console and file sinks
        auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
        auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>("logs/app.log", true);

        logger = std::make_shared<spdlog::logger>("OrderService",
            spdlog::sinks_init_list{console_sink, file_sink});

        logger->set_level(spdlog::level::debug);
        logger->set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] %v");
    }

    void processOrder(const std::string& orderId, int userId) {
        logger->info("Processing order {} for user {}", orderId, userId);

        try {
            Order order = getOrder(orderId);
            logger->debug("Order {} retrieved with {} items", orderId, order.items.size());

            double total = calculateTotal(order);
            logger->info("Order {} total calculated: ${:.2f}", orderId, total);

        } catch (const OrderNotFoundException& e) {
            logger->error("Order {} not found: {}", orderId, e.what());
            throw;
        } catch (const std::exception& e) {
            logger->error("Unexpected error processing order {}: {}", orderId, e.what());
            throw;
        }
    }
};
```

## Best Practices

### What to Log

**✅ Always Log**:

- Application startup/shutdown

- User authentication events

- Authorization failures

- Data mutations (create, update, delete)

- External service calls

- Errors and exceptions

- Performance metrics

- Security events

**❌ Never Log**:

- Passwords or credentials

- Credit card numbers

- Social security numbers

- Personal health information

- API keys or secrets

- Session tokens

- Encryption keys

### Performance Considerations

**Efficient Logging**:
```python
# BAD - formats string even if DEBUG disabled
logger.debug(f"Processing {len(items)} items: {expensive_function()}")

# GOOD - only evaluates if DEBUG enabled
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"Processing {len(items)} items: {expensive_function()}")

# BETTER - lazy evaluation
logger.debug("Processing %d items: %s", len(items), lambda: expensive_function())
```

**Avoid Excessive Logging**:
```python
# BAD - logs every iteration
for i in range(10000):
    logger.debug(f"Processing item {i}")  # 10000 log messages!

# GOOD - log summary
logger.debug(f"Processing {len(items)} items")
for i in range(10000):
    process_item(i)
logger.debug("Processing complete")

# BETTER - log periodically
for i in range(10000):
    process_item(i)
    if i % 1000 == 0:
        logger.debug(f"Processed {i}/{10000} items")
```

### Security Considerations

**Sanitize Sensitive Data**:
```python
def log_user_data(user):
    # BAD - logs password
    logger.info(f"User login: {user}")

    # GOOD - exclude sensitive fields
    safe_data = {k: v for k, v in user.items() if k not in ['password', 'ssn']}
    logger.info(f"User login: {safe_data}")

    # BETTER - mask sensitive data
    masked_data = {
        'username': user['username'],
        'email': user['email'],
        'password': '***REDACTED***'
    }
    logger.info(f"User login: {masked_data}")
```

### Structured Logging

**Use Key-Value Pairs**:
```python
# BAD - hard to parse
logger.info(f"User john logged in from 192.168.1.1")

# GOOD - structured
logger.info("User login", extra={
    'username': 'john',
    'ip_address': '192.168.1.1',
    'timestamp': datetime.now().isoformat()
})
```

### Correlation IDs

**Track Requests Across Services**:
```python
import uuid

def handle_request(request):
    # Generate or extract correlation ID
    correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))

    # Bind to logger
    log = logger.bind(correlation_id=correlation_id)

    log.info("Request received")

    # Pass to other services
    response = downstream_service.call(
        headers={'X-Correlation-ID': correlation_id}
    )

    log.info("Request completed")
    return response
```

## Common Pitfalls and Solutions

### Pitfall 1: Logging Too Much

**Problem**: Excessive logging creates noise and impacts performance.

**Solution**:
```python
# Remove noisy logs
# logger.debug(f"Loop iteration {i}")  # Remove
# logger.debug(f"Variable x = {x}")    # Remove

# Keep meaningful logs
logger.info("Processing started")
logger.error("Processing failed", exc_info=True)
```

### Pitfall 2: Logging Too Little

**Problem**: Not enough context to diagnose issues.

**Solution**:
```python
# BAD - not enough context
logger.error("Payment failed")

# GOOD - include context
logger.error(
    "Payment failed",
    extra={
        'order_id': order_id,
        'amount': amount,
        'user_id': user_id,
        'error': str(e)
    }
)
```

### Pitfall 3: Wrong Log Levels

**Problem**: Using inappropriate log levels.

**Solution**:
```python
# BAD - info for debug details
logger.info(f"Variable x = {x}, y = {y}")

# GOOD - debug for details
logger.debug(f"Variable x = {x}, y = {y}")

# BAD - error for expected conditions
logger.error("User not found")

# GOOD - warn or info for expected conditions
logger.warning("User not found", extra={'user_id': user_id})
```

### Pitfall 4: Not Logging Exceptions Properly

**Problem**: Missing stack traces for errors.

**Solution**:
```python
# BAD - loses stack trace
try:
    risky_operation()
except Exception as e:
    logger.error(f"Error: {e}")

# GOOD - includes stack trace
try:
    risky_operation()
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)

# BETTER - structured with context
try:
    risky_operation()
except Exception as e:
    logger.error(
        "Risky operation failed",
        extra={'error_type': type(e).__name__, 'error': str(e)},
        exc_info=True
    )
```

### Pitfall 5: Logging in Loops

**Problem**: Generates too many log messages.

**Solution**:
```python
# BAD - logs every item
for item in items:
    logger.info(f"Processing {item}")
    process(item)

# GOOD - log summary
logger.info(f"Processing {len(items)} items")
for item in items:
    process(item)
logger.info("Processing complete")
```

## Debugging Scenarios

### Scenario 1: Intermittent Bug

**Problem**: Bug only occurs occasionally.

**Approach**:

1. Add logging around suspected area

2. Log all inputs and state

3. Run multiple times to capture failure

4. Analyze failed runs vs successful runs

**Example**:
```python
def process_transaction(transaction_id):
    logger.info(
        "Transaction processing started",
        extra={
            'transaction_id': transaction_id,
            'timestamp': datetime.now().isoformat(),
            'thread_id': threading.get_ident()
        }
    )

    # Log everything that might be relevant
    account = get_account(transaction_id)
    logger.debug(
        "Account retrieved",
        extra={
            'transaction_id': transaction_id,
            'account_balance': account.balance,
            'account_status': account.status
        }
    )

    # ... process transaction ...
```

### Scenario 2: Performance Issue

**Problem**: Application running slow.

**Approach**:

1. Add timing logs around operations

2. Identify bottlenecks

3. Investigate slow components

**Example**:
```python
import time

def slow_operation():
    start = time.time()
    logger.info("Starting slow operation")

    # Step 1
    step1_start = time.time()
    result1 = step_one()
    logger.info(f"Step 1 completed in {time.time() - step1_start:.3f}s")

    # Step 2
    step2_start = time.time()
    result2 = step_two()
    logger.info(f"Step 2 completed in {time.time() - step2_start:.3f}s")

    # Step 3
    step3_start = time.time()
    result3 = step_three()
    logger.info(f"Step 3 completed in {time.time() - step3_start:.3f}s")

    total = time.time() - start
    logger.info(f"Operation completed in {total:.3f}s")
```

### Scenario 3: Integration Issue

**Problem**: Communication between services failing.

**Approach**:

1. Log all requests and responses

2. Include correlation IDs

3. Trace flow across services

**Example**:
```python
def call_external_api(request_data):
    correlation_id = str(uuid.uuid4())

    logger.info(
        "Calling external API",
        extra={
            'correlation_id': correlation_id,
            'endpoint': api_endpoint,
            'method': 'POST',
            'request_size': len(json.dumps(request_data))
        }
    )

    try:
        response = requests.post(
            api_endpoint,
            json=request_data,
            headers={'X-Correlation-ID': correlation_id}
        )

        logger.info(
            "API response received",
            extra={
                'correlation_id': correlation_id,
                'status_code': response.status_code,
                'response_size': len(response.content)
            }
        )

        return response
    except requests.RequestException as e:
        logger.error(
            "API call failed",
            extra={
                'correlation_id': correlation_id,
                'error': str(e),
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        raise
```

## Tools for Log Analysis

### Command Line Tools

**grep** - Search logs:
```bash
# Find all errors
grep "ERROR" application.log

# Find specific order
grep "order_id=ORD-123" application.log

# Find with context
grep -C 5 "Payment failed" application.log
```

**awk** - Extract fields:
```bash
# Extract timestamps and messages
awk '{print $1, $2, $NF}' application.log

# Count error types
awk '/ERROR/ {print $5}' application.log | sort | uniq -c
```

**tail** - Follow logs in real-time:
```bash
# Follow log file
tail -f application.log

# Follow with filtering
tail -f application.log | grep ERROR
```

### Log Aggregation Tools

**ELK Stack** (Elasticsearch, Logstash, Kibana):

- Centralized log storage

- Powerful search capabilities

- Visualization and dashboards

- Alerting

**Splunk**:

- Enterprise log management

- Advanced analytics

- Real-time monitoring

- Machine learning

**CloudWatch** (AWS):

- Cloud-native logging

- Integration with AWS services

- Metrics and alarms

- Log insights queries

**Datadog**:

- Unified observability

- Log correlation with metrics

- APM integration

- Alerting and dashboards

## Success Criteria

- [ ] Logs provide enough context to understand issues

- [ ] Log levels are used appropriately

- [ ] No sensitive information in logs

- [ ] Performance impact is minimal

- [ ] Logs are structured and parseable

- [ ] Correlation IDs used for request tracking

- [ ] Errors include stack traces

- [ ] Temporary debug logs removed after debugging

- [ ] Logs help identify root cause quickly

- [ ] Team can understand logs without explanation

## Related Skills

- [`test-driven-development`](../test-driven-development/SKILL.md) - Write tests to complement logging

- [`code-review-security`](../code-review-security/SKILL.md) - Review logs for security issues

- [`dependency-security-audit`](../dependency-security-audit/SKILL.md) - Audit logging libraries

- [`plan-before-code`](../plan-before-code/SKILL.md) - Plan logging strategy upfront

- [`code-commit-workflow`](../code-commit-workflow/SKILL.md) - Commit logging changes properly

## Additional Resources

### Logging Frameworks
- **Python**: [logging](https://docs.python.org/3/library/logging.html), [structlog](https://www.structlog.org/)

- **JavaScript**: [Winston](https://github.com/winstonjs/winston), [Pino](https://getpino.io/)

- **Java**: [SLF4J](http://www.slf4j.org/), [Log4j 2](https://logging.apache.org/log4j/2.x/)

- **C#**: [Serilog](https://serilog.net/), [NLog](https://nlog-project.org/)

- **Go**: [logrus](https://github.com/sirupsen/logrus), [zap](https://github.com/uber-go/zap)

- **C++**: [spdlog](https://github.com/gabime/spdlog), [Boost.Log](https://www.boost.org/doc/libs/release/libs/log/)

### Best Practices
- [12-Factor App: Logs](https://12factor.net/logs) - Logging principles

- [Google SRE Book: Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)

- [The Art of Logging](https://www.codeproject.com/Articles/42354/The-Art-of-Logging)

### Tools
- [ELK Stack](https://www.elastic.co/elastic-stack) - Log aggregation and analysis

- [Splunk](https://www.splunk.com/) - Enterprise log management

- [Datadog](https://www.datadoghq.com/) - Observability platform

- [AWS CloudWatch](https://aws.amazon.com/cloudwatch/) - Cloud logging

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: Industry logging best practices, debugging methodologies
