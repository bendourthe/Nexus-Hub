### Step 6: Data Persistence and Networking

iOS apps typically need local persistence for offline support and caching, secure storage for credentials, and a networking layer for API communication.

**SwiftData Model and CRUD Operations**:

```swift
import Foundation
import SwiftData

@Model
final class Transaction {
    @Attribute(.unique) var id: UUID
    var merchantName: String
    var amount: Decimal
    var currencyCode: String
    var category: TransactionCategory
    var date: Date
    var note: String?

    @Relationship(deleteRule: .nullify, inverse: \Account.transactions)
    var account: Account?

    init(
        id: UUID = UUID(),
        merchantName: String,
        amount: Decimal,
        currencyCode: String,
        category: TransactionCategory,
        date: Date,
        note: String? = nil
    ) {
        self.id = id
        self.merchantName = merchantName
        self.amount = amount
        self.currencyCode = currencyCode
        self.category = category
        self.date = date
        self.note = note
    }
}

@Model
final class Account {
    @Attribute(.unique) var id: UUID
    var name: String
    var balance: Decimal
    var currencyCode: String
    var lastUpdated: Date

    @Relationship(deleteRule: .cascade)
    var transactions: [Transaction] = []

    init(id: UUID = UUID(), name: String, balance: Decimal, currencyCode: String) {
        self.id = id
        self.name = name
        self.balance = balance
        self.currencyCode = currencyCode
        self.lastUpdated = .now
    }
}

// SwiftData queries in SwiftUI
struct TransactionListSwiftDataView: View {
    @Query(
        filter: #Predicate<Transaction> { $0.amount < 0 },
        sort: \Transaction.date,
        order: .reverse
    )
    private var expenses: [Transaction]

    @Environment(\.modelContext) private var modelContext

    var body: some View {
        List {
            ForEach(expenses) { transaction in
                TransactionRow(transaction: transaction)
            }
            .onDelete(perform: deleteTransactions)
        }
    }

    private func deleteTransactions(at offsets: IndexSet) {
        for index in offsets {
            modelContext.delete(expenses[index])
        }
    }
}
```

**Keychain Wrapper for Secure Storage**:

```swift
import Foundation
import Security

enum KeychainError: Error {
    case duplicateItem
    case itemNotFound
    case unexpectedStatus(OSStatus)
    case invalidData
}

struct KeychainManager {
    static func save(_ data: Data, for key: String, accessGroup: String? = nil) throws {
        var query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrAccount: key,
            kSecValueData: data,
            kSecAttrAccessible: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
        ]
        if let accessGroup {
            query[kSecAttrAccessGroup] = accessGroup
        }

        let status = SecItemAdd(query as CFDictionary, nil)
        if status == errSecDuplicateItem {
            let updateQuery: [CFString: Any] = [
                kSecClass: kSecClassGenericPassword,
                kSecAttrAccount: key,
            ]
            let updateAttributes: [CFString: Any] = [kSecValueData: data]
            let updateStatus = SecItemUpdate(updateQuery as CFDictionary, updateAttributes as CFDictionary)
            guard updateStatus == errSecSuccess else {
                throw KeychainError.unexpectedStatus(updateStatus)
            }
        } else if status != errSecSuccess {
            throw KeychainError.unexpectedStatus(status)
        }
    }

    static func load(for key: String) throws -> Data {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrAccount: key,
            kSecReturnData: true,
            kSecMatchLimit: kSecMatchLimitOne,
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess else {
            if status == errSecItemNotFound {
                throw KeychainError.itemNotFound
            }
            throw KeychainError.unexpectedStatus(status)
        }
        guard let data = result as? Data else {
            throw KeychainError.invalidData
        }
        return data
    }

    static func delete(for key: String) throws {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrAccount: key,
        ]
        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw KeychainError.unexpectedStatus(status)
        }
    }
}
```

**Async/Await Networking Layer**:

```swift
import Foundation

enum HTTPMethod: String {
    case get = "GET"
    case post = "POST"
    case put = "PUT"
    case delete = "DELETE"
}

struct Endpoint {
    let path: String
    let method: HTTPMethod
    let queryItems: [URLQueryItem]?
    let body: (any Encodable)?
    let headers: [String: String]

    init(
        path: String,
        method: HTTPMethod = .get,
        queryItems: [URLQueryItem]? = nil,
        body: (any Encodable)? = nil,
        headers: [String: String] = [:]
    ) {
        self.path = path
        self.method = method
        self.queryItems = queryItems
        self.body = body
        self.headers = headers
    }
}

enum APIError: Error, LocalizedError {
    case invalidURL
    case httpError(statusCode: Int, data: Data)
    case decodingError(DecodingError)
    case networkError(URLError)
    case unauthorized
    case serverError(statusCode: Int)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid request URL."
        case .httpError(let code, _):
            return "Server returned status \(code)."
        case .decodingError:
            return "Failed to parse server response."
        case .networkError(let urlError):
            return urlError.localizedDescription
        case .unauthorized:
            return "Your session has expired. Please sign in again."
        case .serverError(let code):
            return "Server error (\(code)). Please try again later."
        }
    }
}

actor APIClient {
    private let baseURL: URL
    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder
    private let tokenProvider: TokenProviderProtocol

    init(
        baseURL: URL,
        session: URLSession = .shared,
        tokenProvider: TokenProviderProtocol
    ) {
        self.baseURL = baseURL
        self.session = session
        self.tokenProvider = tokenProvider

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder = decoder

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.keyEncodingStrategy = .convertToSnakeCase
        self.encoder = encoder
    }

    func request<T: Decodable>(_ endpoint: Endpoint) async throws -> T {
        var components = URLComponents(url: baseURL.appending(path: endpoint.path), resolvingAgainstBaseURL: false)
        components?.queryItems = endpoint.queryItems

        guard let url = components?.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = endpoint.method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let token = try await tokenProvider.currentToken()
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        for (key, value) in endpoint.headers {
            request.setValue(value, forHTTPHeaderField: key)
        }

        if let body = endpoint.body {
            request.httpBody = try encoder.encode(body)
        }

        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await session.data(for: request)
        } catch let error as URLError {
            throw APIError.networkError(error)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidURL
        }

        switch httpResponse.statusCode {
        case 200..<300:
            break
        case 401:
            throw APIError.unauthorized
        case 500..<600:
            throw APIError.serverError(statusCode: httpResponse.statusCode)
        default:
            throw APIError.httpError(statusCode: httpResponse.statusCode, data: data)
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch let error as DecodingError {
            throw APIError.decodingError(error)
        }
    }
}
```

**Repository Pattern Combining Remote and Local Data**:

```swift
import Foundation
import SwiftData

struct TransactionRepository: TransactionRepositoryProtocol {
    private let apiClient: APIClient
    private let modelContainer: ModelContainer

    init(apiClient: APIClient, modelContainer: ModelContainer) {
        self.apiClient = apiClient
        self.modelContainer = modelContainer
    }

    func fetchTransactions(for accountID: Account.ID) async throws -> [Transaction] {
        // Try network first, fall back to cache
        do {
            let response: TransactionsResponse = try await apiClient.request(
                Endpoint(path: "/accounts/\(accountID)/transactions")
            )
            try await cacheTransactions(response.transactions, for: accountID)
            return response.transactions
        } catch is APIError {
            return try await loadCachedTransactions(for: accountID)
        }
    }

    @ModelActor
    private actor DataStoreActor {
        func cacheTransactions(_ transactions: [Transaction], for accountID: Account.ID) throws {
            for transaction in transactions {
                modelContext.insert(transaction)
            }
            try modelContext.save()
        }

        func loadCachedTransactions(for accountID: Account.ID) throws -> [Transaction] {
            let descriptor = FetchDescriptor<Transaction>(
                predicate: #Predicate { $0.account?.id == accountID },
                sortBy: [SortDescriptor(\.date, order: .reverse)]
            )
            return try modelContext.fetch(descriptor)
        }
    }

    private func cacheTransactions(_ transactions: [Transaction], for accountID: Account.ID) async throws {
        let actor = DataStoreActor(modelContainer: modelContainer)
        try await actor.cacheTransactions(transactions, for: accountID)
    }

    private func loadCachedTransactions(for accountID: Account.ID) async throws -> [Transaction] {
        let actor = DataStoreActor(modelContainer: modelContainer)
        return try await actor.loadCachedTransactions(for: accountID)
    }
}
```

**Key Persistence and Networking Principles**:

- Use SwiftData for structured local persistence. It integrates with SwiftUI via `@Query` and `@Model`, providing automatic change tracking
- Store authentication tokens and sensitive credentials in the Keychain, never in UserDefaults or plain files
- Make the `APIClient` an actor to ensure thread-safe access to mutable state such as token refresh logic
- Use the Repository pattern to abstract whether data comes from the network or local cache. Views and view models never call the API client directly
- Configure `JSONDecoder` with `.convertFromSnakeCase` and `JSONEncoder` with `.convertToSnakeCase` once at the client level to avoid per-endpoint boilerplate
