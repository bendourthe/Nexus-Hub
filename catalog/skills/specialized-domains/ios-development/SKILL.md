---
name: ios-development
description: iOS native development expertise with Swift, SwiftUI, UIKit, and modern Apple platform patterns. Use when building iOS applications, designing UI with SwiftUI, implementing MVVM architecture, or integrating Apple frameworks.
summary_l0: "Build iOS apps with Swift, SwiftUI, UIKit, and modern Apple platform patterns"
overview_l1: "This skill provides iOS native development expertise covering Swift, SwiftUI, UIKit, and modern Apple platform patterns. Use it when building iOS apps, designing declarative UI with SwiftUI, implementing MVVM or clean architecture, integrating Apple frameworks (SwiftData, HealthKit, MapKit, StoreKit 2, App Intents), persisting data with Core Data, networking with async/await, writing tests, or bridging UIKit and SwiftUI in brownfield projects. Key capabilities include Xcode and Swift Package Manager configuration, SwiftUI view composition with property wrappers, NavigationStack routing, UIKit lifecycle and diffable data sources, MVVM with @Observable and dependency injection, persistence with SwiftData and Keychain, async/await networking with Codable, Apple framework integration, and testing with XCTest and XCUITest. The expected output is production-quality Swift following Apple Human Interface Guidelines with proper architecture, error handling, and test coverage. Trigger phrases: iOS app, SwiftUI view, UIKit controller, MVVM iOS, SwiftData, HealthKit, StoreKit, App Intents, XCTest, XCUITest, NavigationStack, @Observable, Keychain, push notification."
---

# iOS Development

Structured guidance for building native iOS applications with Swift, SwiftUI, UIKit, and modern Apple platform patterns. Covers project setup, declarative UI, navigation, UIKit interop, architecture, data persistence, networking, Apple framework integration, and testing strategies for production iOS applications.

## When to Use This Skill

Use this skill for:

- Setting up a new iOS project with proper Xcode configuration and Swift Package Manager dependencies
- Building declarative user interfaces with SwiftUI views, modifiers, and state management
- Implementing navigation with NavigationStack, sheets, alerts, and deep linking
- Working with UIKit view controllers, table views, collection views, and Auto Layout
- Designing MVVM architecture with @Observable, coordinators, and dependency injection
- Persisting data with SwiftData, Core Data, UserDefaults, or Keychain
- Building async/await networking layers with URLSession and Codable serialization
- Integrating Apple frameworks such as HealthKit, MapKit, StoreKit 2, or App Intents
- Writing unit tests, UI tests, and snapshot tests for iOS applications

**Trigger phrases**: "iOS app", "SwiftUI", "UIKit", "Swift Package Manager", "MVVM iOS", "SwiftData", "Core Data", "HealthKit", "MapKit", "StoreKit", "App Intents", "XCTest", "XCUITest", "NavigationStack", "async await networking", "Codable", "@Observable", "@State", "@Binding", "UICollectionView", "diffable data source", "Keychain", "push notification", "background task"

## What This Skill Does

Provides iOS development patterns including:

- **Project Setup**: Xcode project configuration, Swift Package Manager, module organization, build settings, Info.plist
- **SwiftUI Fundamentals**: Views, modifiers, property wrappers, @State/@Binding/@Observable, previews
- **Layouts and Navigation**: VStack/HStack/ZStack, LazyStacks, NavigationStack, sheets, alerts, deep linking
- **UIKit Patterns**: View controller lifecycle, diffable data sources, Auto Layout, UIKit-SwiftUI interop
- **Architecture**: MVVM with @Observable, Coordinator pattern, dependency injection, Repository pattern
- **Data and Networking**: SwiftData, Core Data, Keychain, URLSession async/await, Codable
- **Apple Frameworks**: Notifications, background tasks, HealthKit, MapKit, StoreKit 2, App Intents
- **Testing**: XCTest, Swift Testing, XCUITest, snapshot testing, async test patterns, protocol-based mocking

## Instructions

### Step 1: Project Structure and Configuration

Full walkthrough: [step-1-project-structure-and-configuration.md](references/step-1-project-structure-and-configuration.md) (load this step when you reach it).

### Step 2: SwiftUI Fundamentals

Full walkthrough: [step-2-swiftui-fundamentals.md](references/step-2-swiftui-fundamentals.md) (load this step when you reach it).

### Step 3: SwiftUI Layouts and Navigation

Full walkthrough: [step-3-swiftui-layouts-and-navigation.md](references/step-3-swiftui-layouts-and-navigation.md) (load this step when you reach it).

### Step 4: UIKit Patterns

Full walkthrough: [step-4-uikit-patterns.md](references/step-4-uikit-patterns.md) (load this step when you reach it).

### Step 5: Architecture Patterns

Full walkthrough: [step-5-architecture-patterns.md](references/step-5-architecture-patterns.md) (load this step when you reach it).

### Step 6: Data Persistence and Networking

Full walkthrough: [step-6-data-persistence-and-networking.md](references/step-6-data-persistence-and-networking.md) (load this step when you reach it).

### Step 7: Apple Frameworks Integration

Full walkthrough: [step-7-apple-frameworks-integration.md](references/step-7-apple-frameworks-integration.md) (load this step when you reach it).

### Step 8: Testing

Full walkthrough: [step-8-testing.md](references/step-8-testing.md) (load this step when you reach it).

## Best Practices

- **Start with SwiftUI, bridge to UIKit when needed**: Use SwiftUI for all new screens. Drop into UIKit only for complex custom layouts, map annotations, or camera integration where UIKit provides capabilities SwiftUI lacks
- **Adopt @Observable over ObservableObject**: The @Observable macro (iOS 17+) provides fine-grained observation without `@Published` wrappers and eliminates unnecessary view re-renders
- **Use Swift concurrency everywhere**: Replace completion handlers, Combine pipelines, and GCD with async/await and structured concurrency. Enable strict concurrency checking to catch data races at compile time
- **Design for offline first**: Cache API responses locally with SwiftData. Show cached data immediately and refresh in the background. Display clear indicators when data is stale
- **Follow the principle of least privilege for permissions**: Request camera, location, notification, and health data permissions at the moment of use with a pre-prompt explaining why the permission is needed
- **Invest in accessibility from day one**: Use semantic SwiftUI modifiers (`.accessibilityLabel`, `.accessibilityHint`, `.accessibilityValue`). Test with VoiceOver enabled during development
- **Keep the main thread free**: Move all I/O, parsing, and heavy computation off the main actor. Use `Task.detached` or custom actors for CPU-intensive work
- **Pin deployment targets explicitly**: Set the minimum iOS version in xcconfig files, not in Xcode project settings, to prevent accidental changes from UI clicks
- **Use SwiftData for new projects, Core Data only for existing ones**: SwiftData is the modern replacement for Core Data with simpler syntax and SwiftUI integration
- **Automate with Xcode Cloud or CI**: Run tests, linting (SwiftLint), and archive builds on every pull request. Catch regressions before they reach the main branch

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll store the auth token in UserDefaults, it's simpler" | UserDefaults is an unencrypted plist any jailbroken device or backup reads in plaintext. Tokens and credentials belong in the Keychain, which is the only Apple-provided encrypted store. |
| "Strong-capturing self in this closure is fine" | A strong self in an escaping closure that the object also retains creates a reference cycle that leaks the view controller forever. Capture `[weak self]` and the Instruments leaks tool stays green. |
| "I'll do the network call on the main thread, it's just one request" | A synchronous request on the main actor blocks the UI and trips the watchdog into a hang termination. async/await off the main actor with a main-actor UI update is the pattern that keeps the app responsive. |
| "SwiftUI previews are nice-to-have, skip them" | Previews are the fastest feedback loop for state and layout bugs; skipping them pushes recomposition and binding errors to device builds that take 10x longer to iterate. |

## Verification

- [ ] The project builds and tests pass: `xcodebuild test -scheme <Scheme> -destination 'platform=iOS Simulator,name=iPhone 15'`
- [ ] No compiler warnings remain in the changed files
- [ ] Instruments Leaks shows no retain cycles in the changed view controllers or view models
- [ ] All credentials and tokens are stored in the Keychain, never in UserDefaults or plist
- [ ] Network calls run off the main actor; UI updates are dispatched back to the main actor
- [ ] SwiftUI views expose a working `#Preview` for the changed screens

## Related Skills

- [[architecture-design]] -- system decomposition and trade-off analysis for complex apps
- [[security-review]] -- security assessment for authentication and data protection
- [[testing-review]] -- test coverage and strategy evaluation
- [[code-quality]] -- code quality metrics and maintainability assessment
- [[android-development]] -- the Android counterpart when the same product targets both platforms

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets are not met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
