### Step 4: UIKit Patterns

UIKit remains essential for complex custom layouts, advanced collection view compositions, and brownfield projects. Understanding view controller lifecycle, modern diffable data sources, and UIKit-SwiftUI interop is critical.

**View Controller Lifecycle**:

```swift
import UIKit

final class TransactionsViewController: UIViewController {
    private let viewModel: TransactionsViewModel
    private var collectionView: UICollectionView!
    private var dataSource: UICollectionViewDiffableDataSource<Section, Transaction.ID>!

    enum Section: Int, CaseIterable {
        case pending
        case completed
    }

    init(viewModel: TransactionsViewModel) {
        self.viewModel = viewModel
        super.init(nibName: nil, bundle: nil)
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) {
        fatalError("init(coder:) is not supported")
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Transactions"
        configureCollectionView()
        configureDataSource()
        bindViewModel()
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        Task { await viewModel.loadTransactions() }
    }

    // MARK: - Collection View Setup

    private func configureCollectionView() {
        var configuration = UICollectionLayoutListConfiguration(appearance: .insetGrouped)
        configuration.headerMode = .supplementary
        configuration.trailingSwipeActionsConfigurationProvider = { [weak self] indexPath in
            self?.trailingSwipeActions(for: indexPath)
        }

        let layout = UICollectionViewCompositionalLayout.list(using: configuration)
        collectionView = UICollectionView(frame: .zero, collectionViewLayout: layout)
        collectionView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(collectionView)

        NSLayoutConstraint.activate([
            collectionView.topAnchor.constraint(equalTo: view.topAnchor),
            collectionView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            collectionView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            collectionView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
    }

    private func trailingSwipeActions(for indexPath: IndexPath) -> UISwipeActionsConfiguration? {
        guard let transactionID = dataSource.itemIdentifier(for: indexPath) else {
            return nil
        }
        let deleteAction = UIContextualAction(style: .destructive, title: "Delete") { [weak self] _, _, completion in
            Task {
                await self?.viewModel.deleteTransaction(id: transactionID)
                completion(true)
            }
        }
        return UISwipeActionsConfiguration(actions: [deleteAction])
    }
}
```

**Diffable Data Source with Cell Registration**:

```swift
extension TransactionsViewController {
    private func configureDataSource() {
        let cellRegistration = UICollectionView.CellRegistration<UICollectionViewListCell, Transaction.ID> {
            [weak self] cell, indexPath, transactionID in

            guard let transaction = self?.viewModel.transaction(for: transactionID) else { return }

            var content = cell.defaultContentConfiguration()
            content.text = transaction.merchantName
            content.secondaryText = transaction.amount.formatted(
                .currency(code: transaction.currencyCode)
            )
            content.image = UIImage(systemName: transaction.category.iconName)
            content.imageProperties.tintColor = UIColor(transaction.category.color)
            cell.contentConfiguration = content

            cell.accessories = [.disclosureIndicator()]
        }

        let headerRegistration = UICollectionView.SupplementaryRegistration<UICollectionViewListCell>(
            elementKind: UICollectionView.elementKindSectionHeader
        ) { [weak self] headerView, _, indexPath in
            guard let section = Section(rawValue: indexPath.section) else { return }
            var content = headerView.defaultContentConfiguration()
            content.text = section == .pending ? "Pending" : "Completed"
            headerView.contentConfiguration = content
        }

        dataSource = UICollectionViewDiffableDataSource(collectionView: collectionView) {
            collectionView, indexPath, transactionID in
            collectionView.dequeueConfiguredReusableCell(
                using: cellRegistration, for: indexPath, item: transactionID
            )
        }

        dataSource.supplementaryViewProvider = { collectionView, kind, indexPath in
            collectionView.dequeueConfiguredReusableSupplementary(
                using: headerRegistration, for: indexPath
            )
        }
    }

    private func bindViewModel() {
        viewModel.onTransactionsChanged = { [weak self] pending, completed in
            guard let self else { return }
            var snapshot = NSDiffableDataSourceSnapshot<Section, Transaction.ID>()
            snapshot.appendSections(Section.allCases)
            snapshot.appendItems(pending.map(\.id), toSection: .pending)
            snapshot.appendItems(completed.map(\.id), toSection: .completed)
            self.dataSource.apply(snapshot, animatingDifferences: true)
        }
    }
}
```

**UIKit-SwiftUI Interop with UIHostingController**:

```swift
import SwiftUI
import UIKit

// Embedding SwiftUI in UIKit
final class SettingsHostingController: UIHostingController<SettingsView> {
    init(viewModel: SettingsViewModel) {
        let settingsView = SettingsView(viewModel: viewModel)
        super.init(rootView: settingsView)
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) {
        fatalError("init(coder:) is not supported")
    }
}

// Embedding UIKit in SwiftUI
struct MapViewRepresentable: UIViewRepresentable {
    let region: MKCoordinateRegion
    let annotations: [MKAnnotation]

    func makeUIView(context: Context) -> MKMapView {
        let mapView = MKMapView()
        mapView.delegate = context.coordinator
        return mapView
    }

    func updateUIView(_ mapView: MKMapView, context: Context) {
        mapView.setRegion(region, animated: true)
        mapView.removeAnnotations(mapView.annotations)
        mapView.addAnnotations(annotations)
    }

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    final class Coordinator: NSObject, MKMapViewDelegate {
        func mapView(_ mapView: MKMapView, viewFor annotation: MKAnnotation) -> MKAnnotationView? {
            let identifier = "CustomPin"
            let view = mapView.dequeueReusableAnnotationView(withIdentifier: identifier)
                ?? MKMarkerAnnotationView(annotation: annotation, reuseIdentifier: identifier)
            view.annotation = annotation
            return view
        }
    }
}
```

**Key UIKit Principles**:

- Mark `init(coder:)` as `@available(*, unavailable)` on programmatic view controllers to prevent accidental storyboard instantiation
- Use `UICollectionViewDiffableDataSource` instead of the older `UITableViewDataSource` delegate pattern. Diffable data sources eliminate index-out-of-bounds crashes and provide smooth animations
- Use compositional layout (`UICollectionViewCompositionalLayout`) for all new collection views. It handles complex grid, list, and waterfall layouts without custom `UICollectionViewFlowLayout` subclasses
- Bridge UIKit views into SwiftUI with `UIViewRepresentable` and SwiftUI views into UIKit with `UIHostingController`. Always implement the coordinator pattern for delegate callbacks
