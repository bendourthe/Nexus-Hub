---
name: init-java-project
description: Initialize complete Java project with Spring Boot, Maven/Gradle build tools, testing framework, and production-ready configuration
version: 1.0.0
author: Benjamin Dourthe
language: Java
category: Project Initialization
tags: [java, spring-boot, maven, gradle, initialization, setup, project-structure]
priority: MEDIUM
template_source: agent_prompts/autonomous_agents/claude_code/java/
---

# Initialize Java Project

Create a complete, production-ready Java project with Spring Boot, Maven or Gradle build tools, comprehensive testing framework, and documentation in minutes. Supports REST APIs, microservices, and enterprise applications.

## When to Use This Skill

Use this skill when you need to:
- ✅ Start a new Java project from scratch
- ✅ Set up Spring Boot application
- ✅ Initialize Maven or Gradle build configuration
- ✅ Establish standard project structure quickly
- ✅ Configure testing framework (JUnit 5, Mockito)
- ✅ Set up Spring Security basics
- ✅ Create Docker configuration
- ✅ Initialize OpenAPI/Swagger documentation
- ✅ Set up CI/CD with GitHub Actions

## What This Skill Does

Creates a complete Java project structure following industry best practices:

### 1. Directory Structure

#### Spring Boot with Maven
```
project-name/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/
│   │   │       └── company/
│   │   │           └── project/
│   │   │               ├── ProjectApplication.java
│   │   │               ├── config/
│   │   │               │   ├── SecurityConfig.java
│   │   │               │   ├── SwaggerConfig.java
│   │   │               │   └── WebConfig.java
│   │   │               ├── controller/
│   │   │               │   └── HealthController.java
│   │   │               ├── service/
│   │   │               ├── repository/
│   │   │               ├── model/
│   │   │               │   ├── entity/
│   │   │               │   └── dto/
│   │   │               ├── exception/
│   │   │               │   ├── GlobalExceptionHandler.java
│   │   │               │   └── ResourceNotFoundException.java
│   │   │               └── util/
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── application-dev.yml
│   │       ├── application-prod.yml
│   │       ├── db/
│   │       │   └── migration/
│   │       └── static/
│   └── test/
│       ├── java/
│       │   └── com/
│       │       └── company/
│       │           └── project/
│       │               ├── controller/
│       │               ├── service/
│       │               ├── repository/
│       │               └── integration/
│       └── resources/
│           └── application-test.yml
├── target/                     # Maven build output
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .gitignore
├── pom.xml
├── CHANGELOG.md
├── DEVLOG.md
├── README.md
└── CLAUDE.md
```

#### Spring Boot with Gradle
```
project-name/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── [same structure as Maven]
│   │   └── resources/
│   │       └── [same structure as Maven]
│   └── test/
│       ├── java/
│       │   └── [same structure as Maven]
│       └── resources/
├── build/                      # Gradle build output
├── gradle/
│   └── wrapper/
│       ├── gradle-wrapper.jar
│       └── gradle-wrapper.properties
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .gitignore
├── build.gradle
├── settings.gradle
├── gradlew
├── gradlew.bat
├── CHANGELOG.md
├── DEVLOG.md
├── README.md
└── CLAUDE.md
```

### 2. Configuration Files
- **pom.xml / build.gradle**: Dependencies and build configuration
- **application.yml**: Application configuration (dev, test, prod profiles)
- **SecurityConfig.java**: Spring Security configuration
- **SwaggerConfig.java**: OpenAPI documentation setup
- **.gitignore**: Comprehensive Java ignore patterns
- **Dockerfile**: Container configuration
- **docker-compose.yml**: Multi-container setup

### 3. Documentation
- **README.md**: Installation, usage, and feature documentation
- **CHANGELOG.md**: Version history following Keep a Changelog format
- **DEVLOG.md**: Development task list and decision log
- **CLAUDE.md**: Claude Code project guidelines
- **Swagger UI**: Interactive API documentation

### 4. Testing Framework
- JUnit 5 for unit testing
- Mockito for mocking
- Spring Boot Test for integration tests
- Test containers for database testing
- Code coverage with JaCoCo

### 5. Development Tools
- Spring Boot DevTools for hot reload
- Lombok for boilerplate reduction
- MapStruct for object mapping
- Flyway or Liquibase for database migrations
- Spring Boot Actuator for monitoring

## Prerequisites

- Java 17+ (JDK)
- Maven 3.8+ or Gradle 8+
- Docker (optional, for containerization)
- git (version control)
- (Optional) Claude Code for AI assistance

## Instructions

### Step 1: Define Project Requirements

Gather this information before initialization:

**Project Details**:
- **Name**: Project identifier (kebab-case)
- **Group ID**: com.company.domain
- **Artifact ID**: project-name
- **Description**: One-line summary of purpose
- **Type**: REST API / Microservice / Web Application
- **Build Tool**: Maven / Gradle
- **Database**: PostgreSQL / MySQL / MongoDB / H2

**Dependencies**:
- Core dependencies (e.g., Spring Web, Spring Data JPA)
- Security requirements
- Database drivers
- Additional features (Redis, Kafka, etc.)

**Features**:
- Key capabilities to document
- Initial version number (default: 0.1.0)

### Step 2: Invoke the Skill

#### Example: Spring Boot REST API with Maven
```
"Use the init-java-project skill to create a new Spring Boot REST API project.

Project Details:
- Name: task-management-api
- Group ID: com.company.taskmanager
- Artifact ID: task-management-api
- Description: RESTful API for task management with Spring Boot
- Type: REST API
- Build Tool: Maven
- Database: PostgreSQL
- Java Version: 17

Dependencies:
- Spring Web (REST endpoints)
- Spring Data JPA (database access)
- Spring Security (authentication)
- Spring Validation (input validation)
- PostgreSQL Driver
- Flyway (database migrations)
- Lombok (code generation)

Features:
- User authentication with JWT
- Task CRUD operations
- Task categorization
- RESTful API design
- OpenAPI documentation

Please initialize the complete project structure with all configurations."
```

#### Example: Microservice with Gradle
```
"Use the init-java-project skill to create a new microservice project.

Project Details:
- Name: user-service
- Group ID: com.company.microservices
- Artifact ID: user-service
- Description: User management microservice
- Type: Microservice
- Build Tool: Gradle
- Database: MongoDB
- Java Version: 21

Dependencies:
- Spring Web
- Spring Data MongoDB
- Spring Cloud (service discovery)
- Spring Boot Actuator
- Resilience4j (circuit breaker)
- Micrometer (metrics)

Features:
- User registration and management
- Service discovery integration
- Health checks and monitoring
- Circuit breaker patterns
- Distributed tracing

Please initialize the complete project structure with Gradle."
```

### Step 3: Review Generated Structure

The skill will create all files and directories. Verify:

```bash
# Check structure
tree task-management-api/

# Navigate to project
cd task-management-api

# Verify build file
cat pom.xml
# or
cat build.gradle
```

### Step 4: Build the Project

#### Using Maven
```bash
# Clean and compile
./mvnw clean compile

# Run tests
./mvnw test

# Package application
./mvnw package

# Skip tests during build
./mvnw package -DskipTests
```

#### Using Gradle
```bash
# Clean and build
./gradlew clean build

# Run tests
./gradlew test

# Build without tests
./gradlew build -x test

# Generate test report
./gradlew test jacocoTestReport
```

### Step 5: Set Up Environment

Create `src/main/resources/application-local.yml`:

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/taskdb
    username: postgres
    password: password
    driver-class-name: org.postgresql.Driver

  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: true
    properties:
      hibernate:
        format_sql: true

  flyway:
    enabled: true
    baseline-on-migrate: true

jwt:
  secret: your-secret-key-here
  expiration: 86400000

logging:
  level:
    com.company.taskmanager: DEBUG
    org.springframework.web: DEBUG
```

### Step 6: Run the Application

#### Development Mode
```bash
# Using Maven
./mvnw spring-boot:run -Dspring-boot.run.profiles=local

# Using Gradle
./gradlew bootRun --args='--spring.profiles.active=local'

# With hot reload (DevTools)
./mvnw spring-boot:run
```

#### Using Docker
```bash
# Build Docker image
docker build -t task-management-api:latest -f docker/Dockerfile .

# Run with docker-compose
cd docker
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Step 7: Verify Setup

```bash
# Check application health
curl http://localhost:8080/actuator/health

# Access Swagger UI
open http://localhost:8080/swagger-ui.html

# Run all tests with coverage
./mvnw clean verify jacoco:report

# View coverage report
open target/site/jacoco/index.html
```

### Step 8: Initialize Git Repository

```bash
# Initialize git
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial project structure

- Spring Boot application setup
- Maven/Gradle build configuration
- Testing framework configured
- Docker configuration included
- OpenAPI documentation setup

Generated with init-java-project skill"

# (Optional) Add remote and push
git remote add origin <your-repo-url>
git push -u origin main
```

### Step 9: Start Development

Your project is now ready! Begin developing:

```bash
# Run in development mode
./mvnw spring-boot:run

# Run tests continuously
./mvnw test -Dtest="*Test" -DfailIfNoTests=false

# Format code (if using Spotless)
./mvnw spotless:apply

# Build for production
./mvnw clean package -Pprod
```

## Generated File Contents

### pom.xml (Maven)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>

    <groupId>com.company.taskmanager</groupId>
    <artifactId>task-management-api</artifactId>
    <version>0.1.0</version>
    <name>task-management-api</name>
    <description>RESTful API for task management with Spring Boot</description>

    <properties>
        <java.version>17</java.version>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <springdoc.version>2.3.0</springdoc.version>
    </properties>

    <dependencies>
        <!-- Spring Boot Starters -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>

        <!-- Database -->
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>

        <dependency>
            <groupId>org.flywaydb</groupId>
            <artifactId>flyway-core</artifactId>
        </dependency>

        <!-- JWT -->
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId>
            <version>0.12.3</version>
        </dependency>

        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-impl</artifactId>
            <version>0.12.3</version>
            <scope>runtime</scope>
        </dependency>

        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-jackson</artifactId>
            <version>0.12.3</version>
            <scope>runtime</scope>
        </dependency>

        <!-- Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>

        <!-- OpenAPI Documentation -->
        <dependency>
            <groupId>org.springdoc</groupId>
            <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
            <version>${springdoc.version}</version>
        </dependency>

        <!-- Development Tools -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-devtools</artifactId>
            <scope>runtime</scope>
            <optional>true</optional>
        </dependency>

        <!-- Testing -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>

        <dependency>
            <groupId>org.springframework.security</groupId>
            <artifactId>spring-security-test</artifactId>
            <scope>test</scope>
        </dependency>

        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </exclude>
                    </excludes>
                </configuration>
            </plugin>

            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>0.8.11</version>
                <executions>
                    <execution>
                        <goals>
                            <goal>prepare-agent</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>report</id>
                        <phase>test</phase>
                        <goals>
                            <goal>report</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

### build.gradle (Gradle)
```gradle
plugins {
    id 'java'
    id 'org.springframework.boot' version '3.2.0'
    id 'io.spring.dependency-management' version '1.1.4'
    id 'jacoco'
}

group = 'com.company.taskmanager'
version = '0.1.0'
sourceCompatibility = '17'

configurations {
    compileOnly {
        extendsFrom annotationProcessor
    }
}

repositories {
    mavenCentral()
}

ext {
    set('springdocVersion', '2.3.0')
    set('jjwtVersion', '0.12.3')
}

dependencies {
    // Spring Boot Starters
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.boot:spring-boot-starter-security'
    implementation 'org.springframework.boot:spring-boot-starter-validation'
    implementation 'org.springframework.boot:spring-boot-starter-actuator'

    // Database
    runtimeOnly 'org.postgresql:postgresql'
    implementation 'org.flywaydb:flyway-core'

    // JWT
    implementation "io.jsonwebtoken:jjwt-api:${jjwtVersion}"
    runtimeOnly "io.jsonwebtoken:jjwt-impl:${jjwtVersion}"
    runtimeOnly "io.jsonwebtoken:jjwt-jackson:${jjwtVersion}"

    // Lombok
    compileOnly 'org.projectlombok:lombok'
    annotationProcessor 'org.projectlombok:lombok'

    // OpenAPI Documentation
    implementation "org.springdoc:springdoc-openapi-starter-webmvc-ui:${springdocVersion}"

    // Development Tools
    developmentOnly 'org.springframework.boot:spring-boot-devtools'

    // Testing
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.security:spring-security-test'
    testRuntimeOnly 'com.h2database:h2'
}

tasks.named('test') {
    useJUnitPlatform()
    finalizedBy jacocoTestReport
}

jacoco {
    toolVersion = "0.8.11"
}

jacocoTestReport {
    dependsOn test
    reports {
        xml.required = true
        html.required = true
    }
}
```

### application.yml
```yaml
spring:
  application:
    name: task-management-api

  profiles:
    active: dev

  jpa:
    open-in-view: false
    hibernate:
      ddl-auto: validate
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect

server:
  port: 8080
  error:
    include-message: always
    include-binding-errors: always

springdoc:
  api-docs:
    path: /api-docs
  swagger-ui:
    path: /swagger-ui.html
    operations-sorter: method
    tags-sorter: alpha

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      show-details: when-authorized

logging:
  level:
    root: INFO
    com.company.taskmanager: INFO
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} - %msg%n"
```

### ProjectApplication.java
```java
package com.company.taskmanager;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Main application class for Task Management API.
 *

 * @author Your Name (your.email@example.com)
 */
@SpringBootApplication
public class ProjectApplication {

    public static void main(String[] args) {
        SpringApplication.run(ProjectApplication.class, args);
    }
}
```

### HealthController.java
```java
package com.company.taskmanager.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.Map;

/**
 * Health check controller for monitoring application status.
 *

 * @author Your Name (your.email@example.com)
 */
@RestController
@RequestMapping("/api/v1")
public class HealthController {

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
            "status", "UP",
            "timestamp", Instant.now(),
            "version", "0.1.0"
        ));
    }
}
```

### GlobalExceptionHandler.java
```java
package com.company.taskmanager.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Global exception handler for centralized error handling.
 *

 * @author Your Name (your.email@example.com)
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<Object> handleResourceNotFoundException(
            ResourceNotFoundException ex, WebRequest request) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("timestamp", Instant.now());
        body.put("status", HttpStatus.NOT_FOUND.value());
        body.put("error", "Not Found");
        body.put("message", ex.getMessage());
        body.put("path", request.getDescription(false));

        return new ResponseEntity<>(body, HttpStatus.NOT_FOUND);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Object> handleGlobalException(
            Exception ex, WebRequest request) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("timestamp", Instant.now());
        body.put("status", HttpStatus.INTERNAL_SERVER_ERROR.value());
        body.put("error", "Internal Server Error");
        body.put("message", ex.getMessage());
        body.put("path", request.getDescription(false));

        return new ResponseEntity<>(body, HttpStatus.INTERNAL_SERVER_ERROR);
    }
}
```

### Dockerfile
```dockerfile
# Build stage
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

# Runtime stage
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app

COPY --from=build /app/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: taskdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:

      - "5432:5432"
    volumes:

      - postgres_data:/var/lib/postgresql/data
    networks:

      - app-network

  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:

      - "8080:8080"
    environment:
      SPRING_PROFILES_ACTIVE: prod
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/taskdb
      SPRING_DATASOURCE_USERNAME: postgres
      SPRING_DATASOURCE_PASSWORD: password
    depends_on:

      - postgres
    networks:

      - app-network

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
```

### .gitignore
```
# Compiled class files
*.class

# Log files
*.log

# Package Files
*.jar
*.war
*.nar
*.ear
*.zip
*.tar.gz
*.rar

# Maven
target/
pom.xml.tag
pom.xml.releaseBackup
pom.xml.versionsBackup
pom.xml.next
release.properties
dependency-reduced-pom.xml
buildNumber.properties
.mvn/timing.properties
.mvn/wrapper/maven-wrapper.jar

# Gradle
.gradle/
build/
!gradle/wrapper/gradle-wrapper.jar
!**/src/main/**/build/
!**/src/test/**/build/

# IDE
.idea/
*.iws
*.iml
*.ipr
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Spring Boot
spring-boot-devtools.properties

# Environment
.env
.env.local
application-local.yml

# JaCoCo
*.exec

# H2 Database
*.db
```

### README.md
```markdown
# Task Management API - v0.1.0

## What's New
- Initial release
- RESTful API with Spring Boot
- User authentication with JWT
- Task CRUD operations
- OpenAPI documentation

## Overview
A production-ready RESTful API for task management built with Spring Boot 3, Spring Security, and PostgreSQL. Provides comprehensive endpoints for user authentication and task management with full OpenAPI documentation.

## Features
- **Authentication**: JWT-based authentication with Spring Security
- **Task Management**: Full CRUD operations for tasks
- **Validation**: Input validation with Bean Validation
- **Documentation**: Interactive API documentation with Swagger UI
- **Monitoring**: Health checks and metrics with Spring Actuator
- **Database Migrations**: Flyway for version-controlled schema changes
- **Containerization**: Docker and docker-compose configuration

## Technology Stack
- Java 17
- Spring Boot 3.2.0
- Spring Security
- Spring Data JPA
- PostgreSQL
- Flyway
- JWT (jjwt)
- Lombok
- SpringDoc OpenAPI

## Installation

### Prerequisites
- Java 17 or higher
- Maven 3.8+ or Gradle 8+
- PostgreSQL 12+ (or Docker)
- Docker (optional)

### Setup

#### Using Maven
```bash
git clone <repository-url>
cd task-management-api

# Build project
./mvnw clean install

# Run application
./mvnw spring-boot:run
```

#### Using Gradle
```bash
git clone <repository-url>
cd task-management-api

# Build project
./gradlew build

# Run application
./gradlew bootRun
```

#### Using Docker
```bash
git clone <repository-url>
cd task-management-api/docker

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Configuration

Create `src/main/resources/application-local.yml`:

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/taskdb
    username: postgres
    password: password

jwt:
  secret: your-secret-key-change-in-production
  expiration: 86400000
```

## Usage

### API Documentation
- **Swagger UI**: http://localhost:8080/swagger-ui.html
- **OpenAPI JSON**: http://localhost:8080/api-docs

### Health Check
```bash
curl http://localhost:8080/actuator/health
```

### Example Endpoints
```
POST   /api/v1/auth/register    - Register new user
POST   /api/v1/auth/login       - Login user
GET    /api/v1/tasks            - Get all tasks
POST   /api/v1/tasks            - Create new task
GET    /api/v1/tasks/{id}       - Get task by ID
PUT    /api/v1/tasks/{id}       - Update task
DELETE /api/v1/tasks/{id}       - Delete task
```

## Development

### Running Tests
```bash
# Maven
./mvnw test

# Gradle
./gradlew test

# With coverage
./mvnw test jacoco:report
./gradlew test jacocoTestReport
```

### Database Migrations
```bash
# Create new migration
# Add file: src/main/resources/db/migration/V2__description.sql

# Migrations run automatically on startup
./mvnw spring-boot:run
```

### Code Quality
```bash
# Format code (if using Spotless)
./mvnw spotless:apply

# Check code style
./mvnw spotless:check
```

## Production Deployment

### Build for Production
```bash
# Maven
./mvnw clean package -Pprod

# Gradle
./gradlew clean build -Pprod

# Result: target/task-management-api-0.1.0.jar
```

### Run Production Build
```bash
java -jar target/task-management-api-0.1.0.jar \
  --spring.profiles.active=prod \
  --spring.datasource.url=jdbc:postgresql://prod-db:5432/taskdb \
  --spring.datasource.username=prod_user \
  --spring.datasource.password=secure_password \
  --jwt.secret=production-secret-key
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure coverage
5. Submit a pull request

## License
MIT

## Contact
Your Name - your.email@example.com
```

### CHANGELOG.md
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [0.1.0] - 2025-10-21

### Added
- Initial Spring Boot project structure
- User authentication with JWT
- Task CRUD operations
- OpenAPI documentation with Swagger UI
- Global exception handling
- Database migrations with Flyway
- Docker configuration
- Comprehensive test suite
- Health check endpoints
```

### DEVLOG.md
```markdown
# Development Log

## Current Task List

### High Priority
- [ ] Implement user authentication endpoints
- [ ] Create task entity and repository
- [ ] Add task CRUD operations
- [ ] Configure Spring Security

### Medium Priority
- [ ] Add task filtering and sorting
- [ ] Implement pagination
- [ ] Add task categories
- [ ] Create user profile management

### Low Priority
- [ ] Add task search functionality
- [ ] Implement task sharing
- [ ] Add email notifications
- [ ] Create admin dashboard

## Development History

### Project Architecture
- **Design**: RESTful API with Spring Boot
- **Tech Stack**: Java 17, Spring Boot 3, PostgreSQL
- **Pattern**: Layered architecture (Controller-Service-Repository)

### Initial Setup - 2025-10-21
- Created standard Spring Boot project structure
- Configured Maven/Gradle build
- Set up testing framework (JUnit 5)
- Configured OpenAPI documentation
- Initialized Docker configuration

## Troubleshooting History

(Document issues and solutions here as they arise)
```

## Project Types and Variations

### REST API with Database
```
Additional Dependencies:

- Spring Data JPA
- PostgreSQL or MySQL driver
- Flyway or Liquibase
- MapStruct (entity-DTO mapping)
```

### Microservice
```
Additional Dependencies:

- Spring Cloud (Config, Discovery)
- Spring Cloud Gateway
- Resilience4j
- Sleuth (distributed tracing)
```

### Reactive Application
```
Additional Dependencies:

- Spring WebFlux
- R2DBC drivers
- Reactor Test
```

## Success Criteria

After initialization, verify:

- [ ] All directories created correctly
- [ ] Build configuration is valid
- [ ] Application starts successfully
- [ ] Tests run and pass
- [ ] Swagger UI accessible
- [ ] Health endpoint responds
- [ ] Database connection works
- [ ] Docker containers start
- [ ] Documentation complete
- [ ] Ready to begin development

## Related Skills

**Use After Initialization**:
- `setup-java-system-prompt`: Configure Claude Code standards
- `create-claude-md`: Customize project guidelines
- `generate-test-cases`: Add comprehensive tests

**For Development**:
- `plan-before-code`: Plan features before implementing
- `test-driven-development`: Write tests first
- `cleanup-java`: Clean code periodically

## Additional Resources

- [Spring Boot Documentation](https://docs.spring.io/spring-boot/docs/current/reference/)
- [Spring Security Reference](https://docs.spring.io/spring-security/reference/)
- [Spring Data JPA Guide](https://docs.spring.io/spring-data/jpa/docs/current/reference/html/)
- [Maven Getting Started](https://maven.apache.org/guides/getting-started/)
- [Gradle User Manual](https://docs.gradle.org/current/userguide/userguide.html)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - Java Project Standards
**Priority**: MEDIUM - Standard Java/Spring Boot project initialization
