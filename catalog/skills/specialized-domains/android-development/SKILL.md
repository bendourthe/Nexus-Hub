---
name: android-development
description: Android native development expertise with Kotlin, Jetpack Compose, Material Design 3, and modern Android architecture. Use when building Android applications, designing UI with Compose, implementing MVVM/MVI patterns, or configuring Gradle builds.
summary_l0: "Build Android apps with Kotlin, Jetpack Compose, Material Design 3, and modern architecture"
overview_l1: "This skill provides Android native development expertise for building production-quality applications with Kotlin, Jetpack Compose, and modern Android architecture. Use it when creating new Android projects, designing Compose UI with Material Design 3, implementing MVVM or MVI patterns, configuring Gradle builds with version catalogs, setting up Room or Retrofit, handling lifecycle and side effects, implementing type-safe navigation, or writing Android tests. Key capabilities include multi-module Gradle configuration, Compose UI with state hoisting and recomposition optimization, Material Design 3 theming, type-safe Compose Navigation, MVVM with ViewModel, UiState, Repository pattern, and Hilt dependency injection, a data layer with Room, DataStore, Retrofit, and Paging 3, lifecycle-aware coroutine collection and WorkManager, and testing with Compose test rules and Robolectric. The expected output is well-structured, testable Android code following current best practices. Trigger phrases: android app, kotlin android, jetpack compose, material design 3, android viewmodel, room database, hilt injection, android testing, mvvm android, workmanager."
---

# Android Development

Structured guidance for building modern Android applications with Kotlin, Jetpack Compose, Material Design 3, and current Android architecture patterns. Covers project structure, Compose UI development, theming, navigation, architecture, data layer, lifecycle management, and testing strategies specific to production Android applications.

## When to Use This Skill

Use this skill for:

- Setting up a new Android project with multi-module Gradle configuration and version catalogs
- Building UI screens with Jetpack Compose, state hoisting, and recomposition optimization
- Implementing Material Design 3 theming with dynamic color, custom color schemes, and dark theme support
- Setting up Compose Navigation with type-safe routes, nested graphs, and deep links
- Designing MVVM or MVI architecture with ViewModel, UiState, Repository pattern, and Hilt DI
- Implementing the data layer with Room, DataStore, Retrofit or Ktor, and Paging 3
- Handling Android lifecycle, coroutine scoping, side effects, and background work with WorkManager
- Writing unit tests, Compose UI tests, and integration tests for Android components

**Trigger phrases**: "android app", "kotlin android", "jetpack compose", "compose ui", "material design", "material you", "viewmodel", "android navigation", "room database", "hilt", "gradle version catalog", "android testing", "compose preview", "mvvm", "mvi", "datastore", "paging 3", "workmanager", "compose state", "recomposition"

## What This Skill Does

Provides Android development patterns including:

- **Project Structure**: Multi-module Gradle setup, version catalogs, build conventions, ProGuard/R8 configuration
- **Jetpack Compose**: Composable functions, state management, Modifier chains, previews, recomposition optimization
- **Material Design 3**: Dynamic color, custom themes, typography, shapes, dark theme, Material You adaptation
- **Navigation**: Compose Navigation with type-safe routes, nested graphs, bottom navigation, deep links
- **Architecture**: MVVM with ViewModel and UiState, Repository pattern, UseCases, Hilt dependency injection
- **Data Layer**: Room database, DataStore preferences, Retrofit/Ktor networking, offline-first caching, Paging 3
- **Lifecycle**: LaunchedEffect, DisposableEffect, lifecycle-aware Flow collection, WorkManager, foreground services
- **Testing**: JUnit 5 unit tests, Compose testing with ComposeTestRule, Robolectric, Hilt testing, UI automation

## Instructions

### Step 1: Project Structure and Gradle Configuration

Full walkthrough: [step-1-project-structure-and-gradle-configuration.md](references/step-1-project-structure-and-gradle-configuration.md) (load this step when you reach it).

### Step 2: Jetpack Compose Fundamentals

Full walkthrough: [step-2-jetpack-compose-fundamentals.md](references/step-2-jetpack-compose-fundamentals.md) (load this step when you reach it).

### Step 3: Material Design 3 Theming

Full walkthrough: [step-3-material-design-3-theming.md](references/step-3-material-design-3-theming.md) (load this step when you reach it).

### Step 4: Navigation

Full walkthrough: [step-4-navigation.md](references/step-4-navigation.md) (load this step when you reach it).

### Step 5: Architecture Patterns

Full walkthrough: [step-5-architecture-patterns.md](references/step-5-architecture-patterns.md) (load this step when you reach it).

### Step 6: Data Layer

Full walkthrough: [step-6-data-layer.md](references/step-6-data-layer.md) (load this step when you reach it).

### Step 7: Lifecycle and Side Effects

Full walkthrough: [step-7-lifecycle-and-side-effects.md](references/step-7-lifecycle-and-side-effects.md) (load this step when you reach it).

### Step 8: Testing

Full walkthrough: [step-8-testing.md](references/step-8-testing.md) (load this step when you reach it).

## Best Practices

- **Compose-first UI**: Build all new screens with Jetpack Compose. Use `ComposeView` to incrementally adopt Compose in existing View-based screens, but avoid mixing Compose and Views within the same screen
- **Single source of truth**: Every piece of data should have exactly one owner. The Room database is the source of truth for cached data; the ViewModel's StateFlow is the source of truth for UI state
- **Unidirectional data flow**: State flows down from ViewModel to UI; events flow up from UI to ViewModel as sealed interface actions. This makes state changes predictable and debuggable
- **Offline-first architecture**: Serve cached data from Room immediately and refresh from the network in the background. Users should always see data, even without connectivity
- **Type safety**: Use Kotlin serialization with `@Serializable` route classes for navigation, sealed interfaces for UI state, and strict Kotlin compiler flags to catch errors at compile time
- **Minimize Android framework coupling**: ViewModels, use cases, and repositories should not depend on Android classes (Context, Activity). Use Hilt to inject platform dependencies behind interfaces

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll hold state inside the Composable, hoisting is overkill" | State held in a Composable is lost on recomposition and rotation, so the user's half-filled form clears on a config change. Hoisting to a ViewModel StateFlow is what survives the lifecycle. |
| "Collecting the Flow with collect() in a coroutine is fine" | A raw collect() keeps running while the screen is in the background, leaking work and crashing on stale UI references. collectAsStateWithLifecycle() (or repeatOnLifecycle) is the only collection that respects the lifecycle. |
| "The ViewModel can take a Context, it's convenient" | A Context reference in a ViewModel outlives the Activity and leaks it across rotation. Injecting platform dependencies behind interfaces via Hilt is what keeps the ViewModel testable and leak-free. |
| "Skipping tests, Compose UI is hard to test anyway" | createComposeRule() with semantics queries makes Compose UI directly testable; skipping it means recomposition and state bugs ship to users instead of failing in CI. |

## Verification

- [ ] The release build succeeds: `./gradlew assembleRelease`
- [ ] Lint is clean: `./gradlew lint` reports no new errors
- [ ] Unit and instrumentation tests pass: `./gradlew test connectedAndroidTest`
- [ ] UI state is hoisted to a ViewModel and exposed as an immutable StateFlow / UiState
- [ ] Every Flow in the UI is collected with `collectAsStateWithLifecycle()` (or `repeatOnLifecycle`)
- [ ] No ViewModel, use case, or repository imports `android.content.Context` or `android.app.Activity` directly
- [ ] Navigation routes are type-safe `@Serializable` classes, not raw strings

## Related Skills

- [[ios-development]] -- the iOS counterpart when the same app targets Apple platforms
- [[mocks-fixtures]] -- build fakes and fixtures for the repository and use-case tests this skill recommends
- [[code-quality]] -- score the resulting Kotlin against SOLID and complexity metrics
- [[async-patterns]] -- structured-concurrency and coroutine patterns behind lifecycle-aware Flow collection
- **Test at every layer**: Unit test ViewModels with Turbine, test Compose screens with ComposeTestRule, test DAOs with in-memory Room databases, and run integration tests with Hilt testing support
