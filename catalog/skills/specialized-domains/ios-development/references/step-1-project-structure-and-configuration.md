### Step 1: Project Structure and Configuration

A well-organized iOS project separates features into modules, configures build settings for each environment, and manages dependencies through Swift Package Manager.

**Recommended Project Structure**:

```
MyApp/
  MyApp.xcodeproj
  MyApp/
    App/
      MyAppApp.swift              -- @main entry point
      AppDelegate.swift           -- UIKit lifecycle hooks (if needed)
      Info.plist
    Features/
      Home/
        HomeView.swift
        HomeViewModel.swift
      Settings/
        SettingsView.swift
        SettingsViewModel.swift
    Core/
      Networking/
        APIClient.swift
        Endpoint.swift
      Persistence/
        DataStore.swift
      Models/
        User.swift
        Transaction.swift
    SharedUI/
      Components/
        PrimaryButton.swift
        LoadingOverlay.swift
      Modifiers/
        ShimmerModifier.swift
    Resources/
      Assets.xcassets
      Localizable.xcstrings
  MyAppTests/
    Features/
      HomeViewModelTests.swift
    Core/
      APIClientTests.swift
    Helpers/
      TestFixtures.swift
  MyAppUITests/
    HomeFlowTests.swift
    SettingsFlowTests.swift
  Packages/
    MyAppKit/                     -- local Swift package for shared logic
      Package.swift
      Sources/MyAppKit/
      Tests/MyAppKitTests/
```

**App Entry Point** (SwiftUI lifecycle):

```swift
import SwiftUI
import SwiftData

@main
struct MyAppApp: App {
    private let container: ModelContainer

    init() {
        do {
            let schema = Schema([User.self, Transaction.self])
            let configuration = ModelConfiguration(
                "MyApp",
                schema: schema,
                isStoredInMemoryOnly: false
            )
            container = try ModelContainer(for: schema, configurations: [configuration])
        } catch {
            fatalError("Failed to create ModelContainer: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .modelContainer(container)
        }
    }
}
```

**Swift Package Manager Configuration** (local package):

```swift
// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "MyAppKit",
    platforms: [.iOS(.v17)],
    products: [
        .library(name: "MyAppKit", targets: ["MyAppKit"]),
    ],
    dependencies: [
        .package(url: "https://github.com/pointfreeco/swift-dependencies", from: "1.0.0"),
        .package(url: "https://github.com/apple/swift-algorithms", from: "1.2.0"),
    ],
    targets: [
        .target(
            name: "MyAppKit",
            dependencies: [
                .product(name: "Dependencies", package: "swift-dependencies"),
                .product(name: "Algorithms", package: "swift-algorithms"),
            ]
        ),
        .testTarget(
            name: "MyAppKitTests",
            dependencies: ["MyAppKit"]
        ),
    ]
)
```

**Build Configuration with xcconfig Files**:

```
// Shared.xcconfig
IPHONEOS_DEPLOYMENT_TARGET = 17.0
SWIFT_VERSION = 6.0
SWIFT_STRICT_CONCURRENCY = complete
ENABLE_USER_SCRIPT_SANDBOXING = YES

// Debug.xcconfig
#include "Shared.xcconfig"
SWIFT_OPTIMIZATION_LEVEL = -Onone
SWIFT_ACTIVE_COMPILATION_CONDITIONS = DEBUG
OTHER_SWIFT_FLAGS = -warn-concurrency

// Release.xcconfig
#include "Shared.xcconfig"
SWIFT_OPTIMIZATION_LEVEL = -O
SWIFT_COMPILATION_MODE = wholemodule
ENABLE_TESTABILITY = NO
```

**Info.plist Essentials**:

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
</dict>
<key>NSCameraUsageDescription</key>
<string>We need camera access to scan documents.</string>
<key>NSLocationWhenInUseUsageDescription</key>
<string>We use your location to show nearby results.</string>
<key>UIBackgroundModes</key>
<array>
    <string>fetch</string>
    <string>remote-notification</string>
</array>
```

**Key Project Setup Principles**:

- Set the deployment target to iOS 17+ to use @Observable and SwiftData without backward-compatibility shims
- Enable Swift 6 strict concurrency checking (`SWIFT_STRICT_CONCURRENCY = complete`) from day one to catch data races at compile time
- Use local Swift packages to extract shared logic into testable modules with explicit dependency boundaries
- Keep the main app target thin: it should wire together feature modules but contain minimal logic itself
- Configure separate xcconfig files for Debug and Release to avoid conditional compilation scattered through code
