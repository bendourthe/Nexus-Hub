### Step 5: Architecture Patterns

A clean architecture separates UI, business logic, and data access into distinct layers. On iOS, MVVM with @Observable provides the best balance of testability and SwiftUI integration.

**MVVM with @Observable**:

```swift
import Foundation
import Observation

// MARK: - Protocol for dependency injection and testing

protocol TransactionRepositoryProtocol: Sendable {
    func fetchTransactions(for accountID: Account.ID) async throws -> [Transaction]
    func deleteTransaction(id: Transaction.ID) async throws
}

// MARK: - ViewModel

@Observable
@MainActor
final class TransactionListViewModel {
    private(set) var transactions: [Transaction] = []
    private(set) var isLoading = false
    private(set) var error: AppError?

    private let repository: TransactionRepositoryProtocol
    private let accountID: Account.ID

    init(accountID: Account.ID, repository: TransactionRepositoryProtocol) {
        self.accountID = accountID
        self.repository = repository
    }

    func loadTransactions() async {
        isLoading = true
        error = nil

        do {
            transactions = try await repository.fetchTransactions(for: accountID)
        } catch {
            self.error = AppError(underlying: error)
        }

        isLoading = false
    }

    func deleteTransaction(at offsets: IndexSet) async {
        let idsToDelete = offsets.map { transactions[$0].id }

        // Optimistic UI update
        var removedTransactions: [(Int, Transaction)] = []
        for offset in offsets.sorted().reversed() {
            removedTransactions.append((offset, transactions[offset]))
            transactions.remove(at: offset)
        }

        do {
            for id in idsToDelete {
                try await repository.deleteTransaction(id: id)
            }
        } catch {
            // Rollback on failure
            for (index, transaction) in removedTransactions.reversed() {
                transactions.insert(transaction, at: index)
            }
            self.error = AppError(underlying: error)
        }
    }
}

// MARK: - View

struct TransactionListView: View {
    @State private var viewModel: TransactionListViewModel

    init(accountID: Account.ID, repository: TransactionRepositoryProtocol) {
        _viewModel = State(initialValue: TransactionListViewModel(
            accountID: accountID,
            repository: repository
        ))
    }

    var body: some View {
        Group {
            if viewModel.isLoading && viewModel.transactions.isEmpty {
                ProgressView("Loading transactions...")
            } else if let error = viewModel.error, viewModel.transactions.isEmpty {
                ContentUnavailableView {
                    Label("Unable to Load", systemImage: "exclamationmark.triangle")
                } description: {
                    Text(error.userMessage)
                } actions: {
                    Button("Retry") {
                        Task { await viewModel.loadTransactions() }
                    }
                }
            } else {
                List {
                    ForEach(viewModel.transactions) { transaction in
                        TransactionRow(transaction: transaction)
                    }
                    .onDelete { offsets in
                        Task { await viewModel.deleteTransaction(at: offsets) }
                    }
                }
                .refreshable {
                    await viewModel.loadTransactions()
                }
            }
        }
        .task { await viewModel.loadTransactions() }
        .navigationTitle("Transactions")
    }
}
```

**Coordinator Pattern for Navigation**:

```swift
import UIKit

protocol Coordinator: AnyObject {
    var childCoordinators: [any Coordinator] { get set }
    var navigationController: UINavigationController { get }
    func start()
}

final class AppCoordinator: Coordinator {
    var childCoordinators: [any Coordinator] = []
    let navigationController: UINavigationController
    private let dependencyContainer: DependencyContainer

    init(navigationController: UINavigationController, dependencyContainer: DependencyContainer) {
        self.navigationController = navigationController
        self.dependencyContainer = dependencyContainer
    }

    func start() {
        let homeCoordinator = HomeCoordinator(
            navigationController: navigationController,
            dependencyContainer: dependencyContainer
        )
        homeCoordinator.delegate = self
        childCoordinators.append(homeCoordinator)
        homeCoordinator.start()
    }
}

extension AppCoordinator: HomeCoordinatorDelegate {
    func homeCoordinatorDidRequestTransactionDetail(_ coordinator: HomeCoordinator, transactionID: Transaction.ID) {
        let detailCoordinator = TransactionDetailCoordinator(
            navigationController: navigationController,
            transactionID: transactionID,
            dependencyContainer: dependencyContainer
        )
        childCoordinators.append(detailCoordinator)
        detailCoordinator.start()
    }
}
```

**Dependency Container**:

```swift
import Foundation

@MainActor
final class DependencyContainer: Sendable {
    private let apiClient: APIClient
    private let modelContainer: ModelContainer

    init(apiClient: APIClient, modelContainer: ModelContainer) {
        self.apiClient = apiClient
        self.modelContainer = modelContainer
    }

    func makeTransactionRepository() -> TransactionRepositoryProtocol {
        TransactionRepository(apiClient: apiClient, modelContainer: modelContainer)
    }

    func makeAuthService() -> AuthServiceProtocol {
        AuthService(apiClient: apiClient)
    }

    func makeTransactionListViewModel(accountID: Account.ID) -> TransactionListViewModel {
        TransactionListViewModel(
            accountID: accountID,
            repository: makeTransactionRepository()
        )
    }
}
```

**Key Architecture Principles**:

- Define protocols for all services and repositories. View models depend on protocols, not concrete types, enabling test doubles
- Mark view models `@MainActor` and `@Observable`. The `@MainActor` annotation guarantees all property updates happen on the main thread, which SwiftUI requires
- Use optimistic UI updates for delete and toggle operations, rolling back if the server call fails
- Use the `.task` modifier to kick off async work when a view appears. SwiftUI cancels the task automatically when the view disappears
- The Coordinator pattern is most valuable in UIKit-heavy apps. In pure SwiftUI apps, the Router pattern from Step 3 serves the same purpose with less boilerplate
