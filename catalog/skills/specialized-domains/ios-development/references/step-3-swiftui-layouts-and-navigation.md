### Step 3: SwiftUI Layouts and Navigation

SwiftUI provides stack-based layouts for composition, lazy containers for performance with large data sets, and NavigationStack for type-safe, path-based navigation.

**Stack-Based Layouts**:

```swift
import SwiftUI

struct DashboardView: View {
    let accounts: [Account]
    let recentTransactions: [Transaction]

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Horizontal scrolling account cards
                ScrollView(.horizontal, showsIndicators: false) {
                    LazyHStack(spacing: 16) {
                        ForEach(accounts) { account in
                            AccountCard(account: account)
                                .containerRelativeFrame(
                                    .horizontal,
                                    count: 1,
                                    spacing: 16
                                )
                        }
                    }
                    .scrollTargetLayout()
                }
                .scrollTargetBehavior(.viewAligned)
                .contentMargins(.horizontal, 20)

                // Recent transactions list
                LazyVStack(alignment: .leading, spacing: 0) {
                    Section {
                        ForEach(recentTransactions) { transaction in
                            TransactionRow(transaction: transaction)
                            if transaction.id != recentTransactions.last?.id {
                                Divider()
                                    .padding(.leading, 52)
                            }
                        }
                    } header: {
                        Text("Recent Transactions")
                            .font(.headline)
                            .padding(.horizontal, 20)
                            .padding(.bottom, 8)
                    }
                }
            }
            .padding(.vertical)
        }
    }
}

struct AccountCard: View {
    let account: Account

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(account.name)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Spacer()
                Image(systemName: account.type.iconName)
                    .foregroundStyle(.secondary)
            }

            Text(account.balance, format: .currency(code: account.currencyCode))
                .font(.title.bold().monospacedDigit())

            Text("Updated \(account.lastUpdated, format: .relative(presentation: .named))")
                .font(.caption2)
                .foregroundStyle(.tertiary)
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
    }
}
```

**NavigationStack with Type-Safe Path-Based Routing**:

```swift
import SwiftUI

enum AppRoute: Hashable {
    case transactionDetail(Transaction.ID)
    case accountDetail(Account.ID)
    case settings
    case profile
}

@Observable
final class Router {
    var path = NavigationPath()

    func navigate(to route: AppRoute) {
        path.append(route)
    }

    func popToRoot() {
        path = NavigationPath()
    }

    func pop() {
        guard !path.isEmpty else { return }
        path.removeLast()
    }
}

struct ContentView: View {
    @State private var router = Router()
    @State private var selectedTab: Tab = .home

    var body: some View {
        TabView(selection: $selectedTab) {
            NavigationStack(path: $router.path) {
                HomeView()
                    .navigationDestination(for: AppRoute.self) { route in
                        switch route {
                        case .transactionDetail(let id):
                            TransactionDetailView(transactionID: id)
                        case .accountDetail(let id):
                            AccountDetailView(accountID: id)
                        case .settings:
                            SettingsView()
                        case .profile:
                            ProfileView()
                        }
                    }
            }
            .tabItem { Label("Home", systemImage: "house") }
            .tag(Tab.home)

            NavigationStack {
                SearchView()
            }
            .tabItem { Label("Search", systemImage: "magnifyingglass") }
            .tag(Tab.search)
        }
        .environment(router)
    }
}
```

**Sheets, Alerts, and Confirmations**:

```swift
import SwiftUI

struct TransactionDetailView: View {
    let transactionID: Transaction.ID
    @State private var showDeleteConfirmation = false
    @State private var showEditSheet = false
    @State private var alertItem: AlertItem?

    var body: some View {
        List {
            // Transaction detail sections...
        }
        .navigationTitle("Transaction")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Menu {
                    Button("Edit", systemImage: "pencil") {
                        showEditSheet = true
                    }
                    Button("Delete", systemImage: "trash", role: .destructive) {
                        showDeleteConfirmation = true
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                }
            }
        }
        .sheet(isPresented: $showEditSheet) {
            EditTransactionView(transactionID: transactionID)
                .presentationDetents([.medium, .large])
                .presentationDragIndicator(.visible)
        }
        .confirmationDialog(
            "Delete Transaction",
            isPresented: $showDeleteConfirmation,
            titleVisibility: .visible
        ) {
            Button("Delete", role: .destructive) {
                Task { await deleteTransaction() }
            }
        } message: {
            Text("This action cannot be undone.")
        }
        .alert(item: $alertItem) { item in
            Alert(
                title: Text(item.title),
                message: Text(item.message),
                dismissButton: .default(Text("OK"))
            )
        }
    }

    private func deleteTransaction() async {
        // deletion logic
    }
}

struct AlertItem: Identifiable {
    let id = UUID()
    let title: String
    let message: String
}
```

**Key Layout and Navigation Principles**:

- Use `LazyVStack` and `LazyHStack` for lists with more than a few dozen items. Lazy stacks create views on demand as they scroll into the viewport
- Use `NavigationStack` with `NavigationPath` for programmatic, type-safe navigation. Avoid the deprecated `NavigationView`
- Centralize routing logic in a `Router` object injected via `@Environment` so that any view can trigger navigation without passing closures through the hierarchy
- Use `.presentationDetents` on sheets to control their height. Half-height sheets (`.medium`) work well for quick forms
- Prefer `confirmationDialog` over `alert` for destructive actions because it presents as an action sheet on iPhone
