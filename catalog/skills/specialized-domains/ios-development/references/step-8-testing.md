### Step 8: Testing

Comprehensive testing on iOS combines unit tests with XCTest or Swift Testing, UI tests with XCUITest, and protocol-based mocking for dependency isolation.

**Unit Tests with Swift Testing Framework**:

```swift
import Testing
@testable import MyApp

@Suite("TransactionListViewModel")
struct TransactionListViewModelTests {
    let mockRepository: MockTransactionRepository

    init() {
        mockRepository = MockTransactionRepository()
    }

    @Test("loads transactions on initial fetch")
    @MainActor
    func loadTransactions() async {
        let expected = [
            Transaction.preview(merchantName: "Coffee Shop", amount: -4.50),
            Transaction.preview(merchantName: "Salary", amount: 5000.00),
        ]
        mockRepository.stubbedTransactions = expected

        let viewModel = TransactionListViewModel(
            accountID: UUID(),
            repository: mockRepository
        )

        await viewModel.loadTransactions()

        #expect(viewModel.transactions.count == 2)
        #expect(viewModel.transactions[0].merchantName == "Coffee Shop")
        #expect(viewModel.isLoading == false)
        #expect(viewModel.error == nil)
    }

    @Test("sets error state when fetch fails")
    @MainActor
    func loadTransactionsFailure() async {
        mockRepository.stubbedError = APIError.networkError(URLError(.notConnectedToInternet))

        let viewModel = TransactionListViewModel(
            accountID: UUID(),
            repository: mockRepository
        )

        await viewModel.loadTransactions()

        #expect(viewModel.transactions.isEmpty)
        #expect(viewModel.error != nil)
        #expect(viewModel.isLoading == false)
    }

    @Test("deletes transaction with optimistic update")
    @MainActor
    func deleteTransaction() async {
        let transactions = [
            Transaction.preview(merchantName: "Item 1"),
            Transaction.preview(merchantName: "Item 2"),
            Transaction.preview(merchantName: "Item 3"),
        ]
        mockRepository.stubbedTransactions = transactions

        let viewModel = TransactionListViewModel(
            accountID: UUID(),
            repository: mockRepository
        )
        await viewModel.loadTransactions()

        await viewModel.deleteTransaction(at: IndexSet(integer: 1))

        #expect(viewModel.transactions.count == 2)
        #expect(viewModel.transactions.contains(where: { $0.merchantName == "Item 2" }) == false)
    }

    @Test("rolls back optimistic delete on failure")
    @MainActor
    func deleteTransactionRollback() async {
        let transactions = [
            Transaction.preview(merchantName: "Item 1"),
            Transaction.preview(merchantName: "Item 2"),
        ]
        mockRepository.stubbedTransactions = transactions
        mockRepository.stubbedDeleteError = APIError.serverError(statusCode: 500)

        let viewModel = TransactionListViewModel(
            accountID: UUID(),
            repository: mockRepository
        )
        await viewModel.loadTransactions()

        await viewModel.deleteTransaction(at: IndexSet(integer: 0))

        #expect(viewModel.transactions.count == 2, "Transaction should be restored after failed delete")
        #expect(viewModel.error != nil)
    }
}
```

**Protocol-Based Mocking**:

```swift
@testable import MyApp

final class MockTransactionRepository: TransactionRepositoryProtocol, @unchecked Sendable {
    var stubbedTransactions: [Transaction] = []
    var stubbedError: Error?
    var stubbedDeleteError: Error?
    var fetchCallCount = 0
    var deletedIDs: [Transaction.ID] = []

    func fetchTransactions(for accountID: Account.ID) async throws -> [Transaction] {
        fetchCallCount += 1
        if let error = stubbedError {
            throw error
        }
        return stubbedTransactions
    }

    func deleteTransaction(id: Transaction.ID) async throws {
        if let error = stubbedDeleteError {
            throw error
        }
        deletedIDs.append(id)
    }
}

final class MockAPIClient: APIClientProtocol, @unchecked Sendable {
    var stubbedResponses: [String: Any] = [:]
    var stubbedErrors: [String: Error] = [:]
    var requestLog: [(path: String, method: HTTPMethod)] = []

    func request<T: Decodable>(_ endpoint: Endpoint) async throws -> T {
        requestLog.append((path: endpoint.path, method: endpoint.method))

        if let error = stubbedErrors[endpoint.path] {
            throw error
        }
        guard let response = stubbedResponses[endpoint.path] as? T else {
            throw APIError.decodingError(
                DecodingError.dataCorrupted(.init(codingPath: [], debugDescription: "No stub"))
            )
        }
        return response
    }
}
```

**XCTest Unit Tests** (for projects not yet on Swift Testing):

```swift
import XCTest
@testable import MyApp

final class APIClientTests: XCTestCase {
    private var sut: APIClient!
    private var mockSession: URLSession!
    private var mockTokenProvider: MockTokenProvider!

    override func setUp() {
        super.setUp()
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [MockURLProtocol.self]
        mockSession = URLSession(configuration: configuration)
        mockTokenProvider = MockTokenProvider(token: "test-token")
        sut = APIClient(
            baseURL: URL(string: "https://api.example.com")!,
            session: mockSession,
            tokenProvider: mockTokenProvider
        )
    }

    override func tearDown() {
        MockURLProtocol.requestHandler = nil
        sut = nil
        super.tearDown()
    }

    func testSuccessfulRequest() async throws {
        let expectedUser = UserDTO(id: "user-1", name: "Alice", email: "alice@example.com")
        let data = try JSONEncoder().encode(expectedUser)

        MockURLProtocol.requestHandler = { request in
            XCTAssertEqual(request.value(forHTTPHeaderField: "Authorization"), "Bearer test-token")
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: 200,
                httpVersion: nil,
                headerFields: nil
            )!
            return (response, data)
        }

        let result: UserDTO = try await sut.request(Endpoint(path: "/users/user-1"))
        XCTAssertEqual(result.id, "user-1")
        XCTAssertEqual(result.name, "Alice")
    }

    func testUnauthorizedThrowsError() async {
        MockURLProtocol.requestHandler = { request in
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: 401,
                httpVersion: nil,
                headerFields: nil
            )!
            return (response, Data())
        }

        do {
            let _: UserDTO = try await sut.request(Endpoint(path: "/me"))
            XCTFail("Expected APIError.unauthorized")
        } catch {
            XCTAssertTrue(error is APIError)
            if case APIError.unauthorized = error { } else {
                XCTFail("Expected .unauthorized, got \(error)")
            }
        }
    }
}

final class MockURLProtocol: URLProtocol {
    nonisolated(unsafe) static var requestHandler: ((URLRequest) throws -> (HTTPURLResponse, Data))?

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        guard let handler = Self.requestHandler else {
            client?.urlProtocol(self, didFailWithError: URLError(.unknown))
            return
        }
        do {
            let (response, data) = try handler(request)
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: data)
            client?.urlProtocolDidFinishLoading(self)
        } catch {
            client?.urlProtocol(self, didFailWithError: error)
        }
    }

    override func stopLoading() {}
}
```

**UI Testing with XCUITest**:

```swift
import XCTest

final class TransactionFlowUITests: XCTestCase {
    private var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--uitesting"]
        app.launchEnvironment = ["API_BASE_URL": "http://localhost:8080"]
        app.launch()
    }

    func testViewTransactionDetail() {
        // Navigate to transactions tab
        let transactionsTab = app.tabBars.buttons["Transactions"]
        XCTAssertTrue(transactionsTab.waitForExistence(timeout: 5))
        transactionsTab.tap()

        // Wait for list to load
        let firstTransaction = app.cells.firstMatch
        XCTAssertTrue(firstTransaction.waitForExistence(timeout: 10))

        // Tap to view detail
        firstTransaction.tap()

        // Verify detail screen
        let merchantLabel = app.staticTexts["merchantName"]
        XCTAssertTrue(merchantLabel.waitForExistence(timeout: 5))

        let amountLabel = app.staticTexts["amount"]
        XCTAssertTrue(amountLabel.exists)
    }

    func testDeleteTransaction() {
        let transactionsTab = app.tabBars.buttons["Transactions"]
        XCTAssertTrue(transactionsTab.waitForExistence(timeout: 5))
        transactionsTab.tap()

        let firstCell = app.cells.firstMatch
        XCTAssertTrue(firstCell.waitForExistence(timeout: 10))

        let initialCount = app.cells.count

        // Swipe to delete
        firstCell.swipeLeft()
        let deleteButton = app.buttons["Delete"]
        XCTAssertTrue(deleteButton.waitForExistence(timeout: 3))
        deleteButton.tap()

        // Confirm deletion dialog
        let confirmButton = app.buttons["Delete"].firstMatch
        if confirmButton.waitForExistence(timeout: 3) {
            confirmButton.tap()
        }

        // Verify count decreased
        let expectation = XCTNSPredicateExpectation(
            predicate: NSPredicate(format: "count < %d", initialCount),
            object: app.cells
        )
        wait(for: [expectation], timeout: 5)
    }

    func testPullToRefresh() {
        let transactionsTab = app.tabBars.buttons["Transactions"]
        XCTAssertTrue(transactionsTab.waitForExistence(timeout: 5))
        transactionsTab.tap()

        let firstCell = app.cells.firstMatch
        XCTAssertTrue(firstCell.waitForExistence(timeout: 10))

        // Pull to refresh
        firstCell.swipeDown()

        // Verify refresh indicator appeared and data reloaded
        let refreshedCell = app.cells.firstMatch
        XCTAssertTrue(refreshedCell.waitForExistence(timeout: 10))
    }
}
```

**Async Test Patterns**:

```swift
import Testing
@testable import MyApp

@Suite("APIClient Async Patterns")
struct APIClientAsyncTests {
    @Test("cancels in-flight request when task is cancelled")
    func cancellation() async {
        let client = APIClient(
            baseURL: URL(string: "https://api.example.com")!,
            session: .shared,
            tokenProvider: MockTokenProvider(token: "token")
        )

        let task = Task {
            let _: UserDTO = try await client.request(
                Endpoint(path: "/slow-endpoint")
            )
        }

        // Cancel immediately
        task.cancel()

        let result = await task.result
        switch result {
        case .success:
            Issue.record("Expected cancellation error")
        case .failure(let error):
            #expect(error is CancellationError || (error as? URLError)?.code == .cancelled)
        }
    }

    @Test("retries request up to max attempts on transient failure")
    func retryLogic() async throws {
        var attemptCount = 0
        let mockSession = MockRetryURLSession { _ in
            attemptCount += 1
            if attemptCount < 3 {
                throw URLError(.networkConnectionLost)
            }
            return (
                HTTPURLResponse(
                    url: URL(string: "https://api.example.com/data")!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: nil
                )!,
                try JSONEncoder().encode(["status": "ok"])
            )
        }

        // Test with retry-enabled client
        #expect(attemptCount == 0)
        // After performing request with retry logic...
        #expect(attemptCount == 3)
    }
}
```

**Key Testing Principles**:

- Use Swift Testing (`@Test`, `#expect`, `@Suite`) for all new tests. It provides clearer syntax, parameterized tests, and better diagnostics than XCTest
- Mock at the protocol boundary. Define protocols for all external dependencies (network, persistence, system services) and inject mock implementations in tests
- Use `MockURLProtocol` to intercept `URLSession` requests without a real server. This avoids flaky tests caused by network conditions
- Mark tests that mutate `@MainActor`-isolated view models with `@MainActor` to satisfy Swift 6 concurrency requirements
- Keep UI tests focused on critical user flows (three to five scenarios). UI tests are slow and brittle, so cover edge cases with unit tests instead
- Use launch arguments (`--uitesting`) to configure the app for UI testing: stub network responses, seed test data, and disable animations
