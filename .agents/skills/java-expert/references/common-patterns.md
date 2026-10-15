## Common Patterns

### Pattern 1: Repository with Specification

```java
public interface UserRepository extends JpaRepository<UserEntity, Long>,
                                        JpaSpecificationExecutor<UserEntity> {}

// Dynamic queries with Specifications
public class UserSpecifications {

    public static Specification<UserEntity> hasName(String name) {
        return (root, query, cb) -> cb.equal(root.get("name"), name);
    }

    public static Specification<UserEntity> emailContains(String fragment) {
        return (root, query, cb) -> cb.like(
            cb.lower(root.get("email")),
            "%" + fragment.toLowerCase() + "%"
        );
    }

    public static Specification<UserEntity> joinedAfter(LocalDate date) {
        return (root, query, cb) -> cb.greaterThan(root.get("joinDate"), date);
    }
}

// Usage
List<UserEntity> results = userRepository.findAll(
    hasName("Alice").and(joinedAfter(LocalDate.of(2024, 1, 1)))
);
```

### Pattern 2: Event-Driven with Spring ApplicationEvent

```java
// Domain event
public record OrderPlacedEvent(String orderId, String userId, BigDecimal total) {}

// Publishing
@Service
public class OrderService {
    private final ApplicationEventPublisher eventPublisher;

    public OrderService(ApplicationEventPublisher eventPublisher) {
        this.eventPublisher = eventPublisher;
    }

    @Transactional
    public Order placeOrder(CreateOrderRequest request) {
        Order order = createAndSave(request);
        eventPublisher.publishEvent(new OrderPlacedEvent(order.id(), order.userId(), order.total()));
        return order;
    }
}

// Listening
@Component
public class OrderEventListener {

    @EventListener
    public void onOrderPlaced(OrderPlacedEvent event) {
        // Send confirmation email, update inventory, etc.
    }

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void afterOrderCommitted(OrderPlacedEvent event) {
        // Only fires after the transaction commits successfully
    }
}
```
