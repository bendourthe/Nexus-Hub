### Step 4: Design gRPC APIs

**Protobuf Service Definition**:

```protobuf
// order_service.proto
syntax = "proto3";

package commerce.orders.v1;

option go_package = "github.com/example/commerce/orders/v1;ordersv1";
option java_package = "com.example.commerce.orders.v1";

import "google/protobuf/timestamp.proto";
import "google/protobuf/field_mask.proto";

// OrderService manages the order lifecycle.
service OrderService {
  // CreateOrder creates a new order from the provided line items.
  rpc CreateOrder(CreateOrderRequest) returns (CreateOrderResponse);

  // GetOrder retrieves a single order by ID.
  rpc GetOrder(GetOrderRequest) returns (Order);

  // ListOrders returns a paginated list of orders.
  rpc ListOrders(ListOrdersRequest) returns (ListOrdersResponse);

  // CancelOrder cancels an existing order.
  rpc CancelOrder(CancelOrderRequest) returns (Order);

  // WatchOrderStatus streams order status changes in real time.
  rpc WatchOrderStatus(WatchOrderStatusRequest)
      returns (stream OrderStatusEvent);
}

message Order {
  string id = 1;
  string customer_id = 2;
  OrderStatus status = 3;
  repeated OrderLine lines = 4;
  Money total = 5;
  google.protobuf.Timestamp created_at = 6;
  google.protobuf.Timestamp updated_at = 7;
}

message OrderLine {
  string product_id = 1;
  string product_name = 2;
  Money unit_price = 3;
  int32 quantity = 4;
}

message Money {
  int64 amount = 1;          // Smallest currency unit (cents)
  string currency_code = 2;  // ISO 4217 (e.g., "USD")
}

enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0;
  ORDER_STATUS_DRAFT = 1;
  ORDER_STATUS_PLACED = 2;
  ORDER_STATUS_CONFIRMED = 3;
  ORDER_STATUS_SHIPPED = 4;
  ORDER_STATUS_DELIVERED = 5;
  ORDER_STATUS_CANCELLED = 6;
}

message CreateOrderRequest {
  string customer_id = 1;
  repeated CreateOrderLineItem lines = 2;
}

message CreateOrderLineItem {
  string product_id = 1;
  int32 quantity = 2;
}

message CreateOrderResponse {
  Order order = 1;
}

message GetOrderRequest {
  string id = 1;
}

message ListOrdersRequest {
  int32 page_size = 1;      // Max 100
  string page_token = 2;     // Opaque cursor
  OrderStatus status_filter = 3;
  string customer_id_filter = 4;
}

message ListOrdersResponse {
  repeated Order orders = 1;
  string next_page_token = 2;
  int32 total_count = 3;
}

message CancelOrderRequest {
  string order_id = 1;
  string reason = 2;
}

message WatchOrderStatusRequest {
  string order_id = 1;
}

message OrderStatusEvent {
  string order_id = 1;
  OrderStatus previous_status = 2;
  OrderStatus new_status = 3;
  google.protobuf.Timestamp occurred_at = 4;
}
```
