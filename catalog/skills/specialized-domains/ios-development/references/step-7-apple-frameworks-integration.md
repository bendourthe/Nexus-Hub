### Step 7: Apple Frameworks Integration

iOS provides specialized frameworks that require careful integration. Each framework has its own permission model, lifecycle requirements, and best practices.

**Push Notifications**:

```swift
import UserNotifications
import UIKit

final class NotificationManager: NSObject, UNUserNotificationCenterDelegate, Sendable {
    static let shared = NotificationManager()

    func requestAuthorization() async throws -> Bool {
        let center = UNUserNotificationCenter.current()
        center.delegate = self
        let granted = try await center.requestAuthorization(options: [.alert, .badge, .sound])
        if granted {
            await MainActor.run {
                UIApplication.shared.registerForRemoteNotifications()
            }
        }
        return granted
    }

    func scheduleLocalNotification(
        title: String,
        body: String,
        triggerDate: Date,
        identifier: String
    ) async throws {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default

        let components = Calendar.current.dateComponents(
            [.year, .month, .day, .hour, .minute],
            from: triggerDate
        )
        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: false)
        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)

        try await UNUserNotificationCenter.current().add(request)
    }

    // Handle notification when app is in foreground
    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        [.banner, .badge, .sound]
    }

    // Handle notification tap
    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse
    ) async {
        let userInfo = response.notification.request.content.userInfo
        // Route to appropriate screen based on notification payload
        if let transactionID = userInfo["transaction_id"] as? String {
            await MainActor.run {
                NotificationCenter.default.post(
                    name: .didTapTransactionNotification,
                    object: nil,
                    userInfo: ["transactionID": transactionID]
                )
            }
        }
    }
}
```

**Background Tasks with BGTaskScheduler**:

```swift
import BackgroundTasks

enum BackgroundTaskIdentifier {
    static let refresh = "com.myapp.refresh"
    static let sync = "com.myapp.datasync"
}

final class BackgroundTaskManager {
    static func registerTasks() {
        BGTaskScheduler.shared.register(
            forTaskWithIdentifier: BackgroundTaskIdentifier.refresh,
            using: nil
        ) { task in
            guard let appRefreshTask = task as? BGAppRefreshTask else { return }
            handleAppRefresh(task: appRefreshTask)
        }

        BGTaskScheduler.shared.register(
            forTaskWithIdentifier: BackgroundTaskIdentifier.sync,
            using: nil
        ) { task in
            guard let processingTask = task as? BGProcessingTask else { return }
            handleDataSync(task: processingTask)
        }
    }

    static func scheduleAppRefresh() {
        let request = BGAppRefreshTaskRequest(identifier: BackgroundTaskIdentifier.refresh)
        request.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60) // 15 minutes
        do {
            try BGTaskScheduler.shared.submit(request)
        } catch {
            // Log scheduling failure; do not crash
        }
    }

    private static func handleAppRefresh(task: BGAppRefreshTask) {
        scheduleAppRefresh() // Schedule the next refresh

        let refreshTask = Task {
            do {
                let repository = DependencyContainer.shared.makeTransactionRepository()
                _ = try await repository.fetchTransactions(for: .currentUser)
                task.setTaskCompleted(success: true)
            } catch {
                task.setTaskCompleted(success: false)
            }
        }

        task.expirationHandler = {
            refreshTask.cancel()
        }
    }

    private static func handleDataSync(task: BGProcessingTask) {
        let syncTask = Task {
            do {
                let syncService = DependencyContainer.shared.makeSyncService()
                try await syncService.performFullSync()
                task.setTaskCompleted(success: true)
            } catch {
                task.setTaskCompleted(success: false)
            }
        }

        task.expirationHandler = {
            syncTask.cancel()
        }
    }
}
```

**StoreKit 2 In-App Purchases**:

```swift
import StoreKit

@Observable
@MainActor
final class StoreManager {
    private(set) var products: [Product] = []
    private(set) var purchasedProductIDs: Set<String> = []
    private var transactionListener: Task<Void, Never>?

    private let productIDs: Set<String> = [
        "com.myapp.premium.monthly",
        "com.myapp.premium.yearly",
    ]

    init() {
        transactionListener = listenForTransactions()
    }

    deinit {
        transactionListener?.cancel()
    }

    func loadProducts() async {
        do {
            products = try await Product.products(for: productIDs)
                .sorted { $0.price < $1.price }
        } catch {
            products = []
        }
    }

    func purchase(_ product: Product) async throws -> StoreKit.Transaction? {
        let result = try await product.purchase()

        switch result {
        case .success(let verification):
            let transaction = try checkVerified(verification)
            purchasedProductIDs.insert(transaction.productID)
            await transaction.finish()
            return transaction

        case .userCancelled:
            return nil

        case .pending:
            return nil

        @unknown default:
            return nil
        }
    }

    func restorePurchases() async {
        for await result in Transaction.currentEntitlements {
            if let transaction = try? checkVerified(result) {
                purchasedProductIDs.insert(transaction.productID)
            }
        }
    }

    var isPremium: Bool {
        !purchasedProductIDs.isEmpty
    }

    private func listenForTransactions() -> Task<Void, Never> {
        Task.detached { [weak self] in
            for await result in Transaction.updates {
                if let transaction = try? self?.checkVerified(result) {
                    await MainActor.run {
                        self?.purchasedProductIDs.insert(transaction.productID)
                    }
                    await transaction.finish()
                }
            }
        }
    }

    private func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified:
            throw StoreError.failedVerification
        case .verified(let value):
            return value
        }
    }
}

enum StoreError: Error {
    case failedVerification
}
```

**App Intents for Shortcuts**:

```swift
import AppIntents

struct ViewBalanceIntent: AppIntent {
    static let title: LocalizedStringResource = "View Account Balance"
    static let description = IntentDescription("Shows the current balance of a selected account.")

    @Parameter(title: "Account")
    var account: AccountEntity

    func perform() async throws -> some IntentResult & ProvidesDialog {
        let repository = DependencyContainer.shared.makeAccountRepository()
        let balance = try await repository.fetchBalance(for: account.id)
        let formatted = balance.formatted(.currency(code: account.currencyCode))
        return .result(dialog: "Your \(account.name) balance is \(formatted).")
    }
}

struct AccountEntity: AppEntity {
    static let typeDisplayRepresentation = TypeDisplayRepresentation(name: "Account")
    static let defaultQuery = AccountQuery()

    let id: UUID
    let name: String
    let currencyCode: String

    var displayRepresentation: DisplayRepresentation {
        DisplayRepresentation(title: "\(name)")
    }
}

struct AccountQuery: EntityQuery {
    func entities(for identifiers: [UUID]) async throws -> [AccountEntity] {
        let repository = DependencyContainer.shared.makeAccountRepository()
        let accounts = try await repository.fetchAccounts()
        return accounts
            .filter { identifiers.contains($0.id) }
            .map { AccountEntity(id: $0.id, name: $0.name, currencyCode: $0.currencyCode) }
    }

    func suggestedEntities() async throws -> [AccountEntity] {
        let repository = DependencyContainer.shared.makeAccountRepository()
        let accounts = try await repository.fetchAccounts()
        return accounts.map { AccountEntity(id: $0.id, name: $0.name, currencyCode: $0.currencyCode) }
    }
}

struct MyAppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: ViewBalanceIntent(),
            phrases: [
                "Show my balance in \(.applicationName)",
                "Check \(\.$account) balance in \(.applicationName)",
            ],
            shortTitle: "View Balance",
            systemImageName: "dollarsign.circle"
        )
    }
}
```

**Key Framework Integration Principles**:

- Always request permissions at the moment of use, not at app launch. Explain why the permission is needed before showing the system prompt
- Register background tasks in `application(_:didFinishLaunchingWithOptions:)` or early in the app lifecycle. Always reschedule the next occurrence inside the handler
- Use StoreKit 2 (the async/await API) for all new in-app purchase implementations. StoreKit 2 handles receipt validation server-side via `VerificationResult`
- App Intents enable Siri Shortcuts and Spotlight integration. Define intents for the three to five most common actions users perform in your app
- Always listen for `Transaction.updates` on app launch to handle purchases that completed while the app was not running
