# C API Documentation

## Objective
Create complete API documentation for C libraries and HTTP clients, enabling developers to understand function signatures, usage patterns, memory management, and error handling.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/api_docs/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/api_docs/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Function Documentation

- [ ] All public functions documented with signatures

- [ ] Parameter descriptions with types

- [ ] Return values explained

- [ ] Error codes documented

- [ ] Memory ownership clarified

### Data Structures

- [ ] All public structs documented

- [ ] Field descriptions provided

- [ ] Alignment/packing notes if relevant

- [ ] Initialization requirements explained

### Error Handling

- [ ] Error codes enumerated

- [ ] Error messages documented

- [ ] Error handling patterns shown

- [ ] Common error scenarios covered

### Memory Management

- [ ] Allocation patterns documented

- [ ] Deallocation requirements explained

- [ ] Memory ownership rules clarified

- [ ] Resource cleanup shown

### Examples

- [ ] Complete working examples

- [ ] HTTP client usage (libcurl, etc.)

- [ ] Error handling examples

- [ ] Memory management examples

## Prompt Template

~~~markdown
# C API Documentation Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/api_docs"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**

- All generated files should be saved with the `${OUTPUT_DIR}/` prefix

- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Phase 1: Library API Documentation

### Public Header (mylib.h)
```c
/**
 * @file mylib.h
 * @brief Main API for MyLib
 * @author Your Name
 * @version 1.0.0
 */

#ifndef MYLIB_H
#define MYLIB_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Error codes */
typedef enum {
    MYLIB_OK = 0,                /**< Success */
    MYLIB_ERR_INVALID_ARG = -1,  /**< Invalid argument */
    MYLIB_ERR_NO_MEMORY = -2,    /**< Out of memory */
    MYLIB_ERR_NOT_INIT = -3,     /**< Library not initialized */
    MYLIB_ERR_IO = -4            /**< I/O error */
} mylib_error_t;

/** Configuration structure */
typedef struct {
    size_t buffer_size;          /**< Buffer size in bytes */
    int enable_logging;          /**< Enable logging (0/1) */
} mylib_config_t;

/** Opaque handle type */
typedef struct mylib_context mylib_context_t;

/**
 * @brief Initialize the library
 *
 * This function must be called before any other library functions.
 * Resources allocated by this function must be freed using mylib_cleanup().
 *
 * @param config Pointer to configuration structure
 * @param ctx Output parameter for context handle
 * @return MYLIB_OK on success, error code on failure
 *
 * @note The caller retains ownership of the config parameter.
 * @note The ctx parameter will be set to NULL on failure.
 *
 * @see mylib_cleanup()
 */
int mylib_init(const mylib_config_t *config, mylib_context_t **ctx);

/**
 * @brief Process input data
 *
 * @param ctx Context handle from mylib_init()
 * @param input Input string (NULL-terminated)
 * @param output Output buffer (caller-allocated)
 * @param output_size Size of output buffer
 * @return Number of bytes written, or negative error code
 *
 * @note Output buffer must be at least as large as input
 * @note Function is thread-safe if contexts don't overlap
 */
int mylib_process(mylib_context_t *ctx, const char *input,
                  char *output, size_t output_size);

/**
 * @brief Get error message for error code
 *
 * @param error Error code
 * @return Human-readable error message (static string)
 */
const char* mylib_strerror(int error);

/**
 * @brief Cleanup and free resources
 *
 * @param ctx Context handle to cleanup (can be NULL)
 *
 * @note After calling this function, the context is invalid
 */
void mylib_cleanup(mylib_context_t *ctx);

#ifdef __cplusplus
}
#endif

#endif /* MYLIB_H */
```

### Usage Example
```c
#include "mylib.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    /* Initialize library */
    mylib_config_t config = {
        .buffer_size = 1024,
        .enable_logging = 1
    };

    mylib_context_t *ctx = NULL;
    int result = mylib_init(&config, &ctx);
    if (result != MYLIB_OK) {
        fprintf(stderr, "Init failed: %s\n", mylib_strerror(result));
        return 1;
    }

    /* Process data */
    const char *input = "test data";
    char output[1024];

    result = mylib_process(ctx, input, output, sizeof(output));
    if (result < 0) {
        fprintf(stderr, "Process failed: %s\n", mylib_strerror(result));
        mylib_cleanup(ctx);
        return 1;
    }

    printf("Processed %d bytes: %s\n", result, output);

    /* Cleanup */
    mylib_cleanup(ctx);
    return 0;
}
```

## Phase 2: HTTP Client Examples

### libcurl Example
```c
#include <curl/curl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/** Response buffer structure */
typedef struct {
    char *data;
    size_t size;
} response_buffer_t;

/** Callback for writing response data */
static size_t write_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    response_buffer_t *buf = (response_buffer_t *)userp;

    char *ptr = realloc(buf->data, buf->size + realsize + 1);
    if (ptr == NULL) {
        fprintf(stderr, "Out of memory\n");
        return 0;
    }

    buf->data = ptr;
    memcpy(&(buf->data[buf->size]), contents, realsize);
    buf->size += realsize;
    buf->data[buf->size] = 0;

    return realsize;
}

/** GET request */
int http_get(const char *url, const char *api_key, response_buffer_t *response) {
    CURL *curl;
    CURLcode res;
    struct curl_slist *headers = NULL;
    char auth_header[256];

    /* Initialize response buffer */
    response->data = malloc(1);
    response->size = 0;

    curl = curl_easy_init();
    if (!curl) {
        return -1;
    }

    /* Set URL */
    curl_easy_setopt(curl, CURLOPT_URL, url);

    /* Set headers */
    snprintf(auth_header, sizeof(auth_header), "Authorization: Bearer %s", api_key);
    headers = curl_slist_append(headers, auth_header);
    headers = curl_slist_append(headers, "Content-Type: application/json");
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

    /* Set callbacks */
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)response);

    /* Set timeout */
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);

    /* Perform request */
    res = curl_easy_perform(curl);

    /* Check for errors */
    if (res != CURLE_OK) {
        fprintf(stderr, "curl_easy_perform() failed: %s\n",
                curl_easy_strerror(res));
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        free(response->data);
        return -1;
    }

    /* Check HTTP status code */
    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    return (int)http_code;
}

/** POST request */
int http_post(const char *url, const char *api_key,
              const char *json_data, response_buffer_t *response) {
    CURL *curl;
    CURLcode res;
    struct curl_slist *headers = NULL;
    char auth_header[256];

    response->data = malloc(1);
    response->size = 0;

    curl = curl_easy_init();
    if (!curl) {
        return -1;
    }

    curl_easy_setopt(curl, CURLOPT_URL, url);

    /* Set headers */
    snprintf(auth_header, sizeof(auth_header), "Authorization: Bearer %s", api_key);
    headers = curl_slist_append(headers, auth_header);
    headers = curl_slist_append(headers, "Content-Type: application/json");
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

    /* Set POST data */
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_data);

    /* Set callbacks */
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)response);

    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);

    res = curl_easy_perform(curl);

    if (res != CURLE_OK) {
        fprintf(stderr, "curl_easy_perform() failed: %s\n",
                curl_easy_strerror(res));
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        free(response->data);
        return -1;
    }

    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    return (int)http_code;
}

/** Usage example */
int main(void) {
    const char *api_key = "your-api-key";
    const char *url = "https://api.example.com/v1/users";
    response_buffer_t response;

    curl_global_init(CURL_GLOBAL_ALL);

    /* GET request */
    int status = http_get(url, api_key, &response);
    if (status == 200) {
        printf("Response: %s\n", response.data);
    } else {
        fprintf(stderr, "Request failed with status %d\n", status);
    }
    free(response.data);

    /* POST request */
    const char *json = "{\"email\":\"test@example.com\",\"name\":\"Test\"}";
    status = http_post(url, api_key, json, &response);
    if (status == 201) {
        printf("Created: %s\n", response.data);
    }
    free(response.data);

    curl_global_cleanup();
    return 0;
}
```

## Phase 3: JSON Parsing (jansson library)

```c
#include <jansson.h>

/** Parse JSON response */
int parse_user_response(const char *json_str) {
    json_error_t error;
    json_t *root = json_loads(json_str, 0, &error);

    if (!root) {
        fprintf(stderr, "JSON parse error: %s\n", error.text);
        return -1;
    }

    json_t *id = json_object_get(root, "id");
    json_t *email = json_object_get(root, "email");
    json_t *name = json_object_get(root, "name");

    if (json_is_integer(id) && json_is_string(email) && json_is_string(name)) {
        printf("ID: %lld\n", json_integer_value(id));
        printf("Email: %s\n", json_string_value(email));
        printf("Name: %s\n", json_string_value(name));
    }

    json_decref(root);
    return 0;
}

/** Create JSON request */
char* create_user_request(const char *email, const char *name) {
    json_t *root = json_object();
    json_object_set_new(root, "email", json_string(email));
    json_object_set_new(root, "name", json_string(name));

    char *json_str = json_dumps(root, JSON_COMPACT);
    json_decref(root);

    return json_str; /* Caller must free */
}
```

## Phase 4: Error Handling Best Practices

```c
/** Error handling example */
int safe_api_call(void) {
    mylib_context_t *ctx = NULL;
    char *output = NULL;
    int result = -1;

    /* Initialize */
    mylib_config_t config = {.buffer_size = 1024};
    if (mylib_init(&config, &ctx) != MYLIB_OK) {
        goto cleanup;
    }

    /* Allocate buffer */
    output = malloc(1024);
    if (output == NULL) {
        goto cleanup;
    }

    /* Perform operation */
    result = mylib_process(ctx, "input", output, 1024);
    if (result < 0) {
        fprintf(stderr, "Error: %s\n", mylib_strerror(result));
        goto cleanup;
    }

    /* Success */
    printf("Result: %s\n", output);
    result = 0;

cleanup:
    free(output);
    mylib_cleanup(ctx);
    return result;
}
```
```

---

## Best Practices

1. **Memory Management**: Always document ownership, use goto for cleanup
2. **Error Handling**: Return error codes, use errno for system errors
3. **Thread Safety**: Document thread safety guarantees
4. **API Design**: Use opaque pointers for handles
5. **Documentation**: Use Doxygen comments extensively
6. **Const Correctness**: Use const for input parameters
7. **NULL Checking**: Always check for NULL returns
8. **Resource Cleanup**: Provide cleanup functions for all resources

---

## Output Format Specifications

The API documentation should:

- Document all public functions with Doxygen comments

- Clarify memory management and ownership

- Show complete working examples with error handling

- Document thread safety characteristics

- Include HTTP client examples using libcurl

- Target C developers with focus on safety

~~~
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**

- [ ] All directories created successfully

- [ ] All files saved in correct subdirectories

- [ ] No files created in repository root

- [ ] Directory structure matches expected layout
