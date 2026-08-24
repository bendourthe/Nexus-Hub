### Step 2: SwiftUI Fundamentals

SwiftUI uses a declarative syntax where views are lightweight value types that describe the desired UI state. The framework diffs the view hierarchy and updates only what changed.

**View Composition and Modifiers**:

```swift
import SwiftUI

struct TransactionRow: View {
    let transaction: Transaction
    @Environment(\.dynamicTypeSize) private var typeSize

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: transaction.category.iconName)
                .font(.title2)
                .foregroundStyle(transaction.category.color)
                .frame(width: 40, height: 40)
                .background(transaction.category.color.opacity(0.12))
                .clipShape(Circle())

            VStack(alignment: .leading, spacing: 2) {
                Text(transaction.merchantName)
                    .font(.body)
                    .fontWeight(.medium)
                    .lineLimit(1)

                Text(transaction.date.formatted(date: .abbreviated, time: .shortened))
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Text(transaction.amount, format: .currency(code: transaction.currencyCode))
                .font(.body.monospacedDigit())
                .foregroundStyle(transaction.amount < 0 ? .primary : .green)
        }
        .padding(.vertical, 4)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(transaction.merchantName), \(transaction.amount.formatted(.currency(code: transaction.currencyCode))), \(transaction.date.formatted(date: .abbreviated, time: .shortened))")
    }
}
```

**State Management with @State, @Binding, and @Observable**:

```swift
import SwiftUI
import Observation

@Observable
final class AuthViewModel {
    var email = ""
    var password = ""
    var isLoading = false
    var errorMessage: String?

    private let authService: AuthServiceProtocol

    init(authService: AuthServiceProtocol) {
        self.authService = authService
    }

    func signIn() async {
        guard !email.isEmpty, !password.isEmpty else {
            errorMessage = "Email and password are required."
            return
        }

        isLoading = true
        errorMessage = nil

        do {
            try await authService.signIn(email: email, password: password)
        } catch let error as AuthError {
            errorMessage = error.userFacingMessage
        } catch {
            errorMessage = "An unexpected error occurred. Please try again."
        }

        isLoading = false
    }
}

struct SignInView: View {
    @State private var viewModel: AuthViewModel

    init(authService: AuthServiceProtocol) {
        _viewModel = State(initialValue: AuthViewModel(authService: authService))
    }

    var body: some View {
        Form {
            Section {
                TextField("Email", text: $viewModel.email)
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)

                SecureField("Password", text: $viewModel.password)
                    .textContentType(.password)
            }

            if let errorMessage = viewModel.errorMessage {
                Section {
                    Label(errorMessage, systemImage: "exclamationmark.triangle")
                        .foregroundStyle(.red)
                }
            }

            Section {
                Button {
                    Task { await viewModel.signIn() }
                } label: {
                    if viewModel.isLoading {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Text("Sign In")
                            .frame(maxWidth: .infinity)
                    }
                }
                .disabled(viewModel.isLoading)
            }
        }
        .navigationTitle("Sign In")
    }
}
```

**Custom Property Wrapper for UserDefaults**:

```swift
import SwiftUI

@propertyWrapper
struct AppStorage<Value: Codable> {
    private let key: String
    private let defaultValue: Value
    private let store: UserDefaults

    init(wrappedValue: Value, _ key: String, store: UserDefaults = .standard) {
        self.key = key
        self.defaultValue = wrappedValue
        self.store = store
    }

    var wrappedValue: Value {
        get {
            guard let data = store.data(forKey: key),
                  let decoded = try? JSONDecoder().decode(Value.self, from: data) else {
                return defaultValue
            }
            return decoded
        }
        set {
            if let data = try? JSONEncoder().encode(newValue) {
                store.set(data, forKey: key)
            }
        }
    }
}
```

**SwiftUI Previews with Sample Data**:

```swift
#Preview("Transaction Row - Expense") {
    List {
        TransactionRow(transaction: .preview(
            merchantName: "Whole Foods Market",
            amount: -87.32,
            category: .groceries
        ))
        TransactionRow(transaction: .preview(
            merchantName: "Monthly Salary",
            amount: 5200.00,
            category: .income
        ))
    }
}

extension Transaction {
    static func preview(
        merchantName: String = "Preview Merchant",
        amount: Double = -25.00,
        category: TransactionCategory = .general,
        currencyCode: String = "USD"
    ) -> Transaction {
        Transaction(
            id: UUID(),
            merchantName: merchantName,
            amount: Decimal(amount),
            currencyCode: currencyCode,
            category: category,
            date: .now
        )
    }
}
```

**Key SwiftUI Principles**:

- Use `@Observable` (iOS 17+) instead of `ObservableObject`/`@Published` for simpler, more efficient observation with fine-grained tracking
- Keep views small and composable. Extract subviews when a view exceeds 40 lines or when a section is reused
- Always provide accessibility labels for non-text elements and use `.accessibilityElement(children: .combine)` for composite rows
- Use `@State` for view-local state, `@Binding` for child-to-parent communication, and `@Environment` for shared values
- Prefer the `format:` parameter on `Text` for locale-aware formatting of numbers, dates, and currencies
