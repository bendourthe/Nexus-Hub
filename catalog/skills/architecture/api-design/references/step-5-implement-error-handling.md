### Step 5: Implement Error Handling

**RFC 7807 Problem Details (REST)**:

```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The request body contains invalid fields.",
  "instance": "/orders/abc-123",
  "errors": [
    {
      "field": "lines[0].quantity",
      "message": "Quantity must be a positive integer.",
      "code": "INVALID_VALUE"
    },
    {
      "field": "customerId",
      "message": "Customer not found.",
      "code": "RESOURCE_NOT_FOUND"
    }
  ]
}
```

**Standard Error Types**:

```
Type URI                                    Status  When to Use
-----------------------------------         ------  -----------
/errors/validation-error                    422     Invalid request body fields
/errors/resource-not-found                  404     Entity does not exist
/errors/conflict                            409     Optimistic lock failure, duplicate
/errors/unauthorized                        401     Missing or invalid credentials
/errors/forbidden                           403     Valid credentials, insufficient permissions
/errors/rate-limited                        429     Too many requests
/errors/internal-error                      500     Unexpected server failure
/errors/service-unavailable                 503     Dependency down, circuit open
```

**Error Handling Implementation (Node.js/Express)**:

```typescript
// middleware/error-handler.ts
import { Request, Response, NextFunction } from "express";

interface ProblemDetail {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  errors?: Array<{ field: string; message: string; code: string }>;
}

export class AppError extends Error {
  constructor(
    public status: number,
    public type: string,
    public title: string,
    public detail: string,
    public fieldErrors?: Array<{ field: string; message: string; code: string }>
  ) {
    super(detail);
  }
}

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  _next: NextFunction
): void {
  if (err instanceof AppError) {
    const problem: ProblemDetail = {
      type: `https://api.example.com/errors/${err.type}`,
      title: err.title,
      status: err.status,
      detail: err.detail,
      instance: req.originalUrl,
    };
    if (err.fieldErrors) {
      problem.errors = err.fieldErrors;
    }
    res.status(err.status)
      .contentType("application/problem+json")
      .json(problem);
    return;
  }

  // Unexpected errors: log full details, return minimal info
  console.error("Unhandled error:", err);
  res.status(500)
    .contentType("application/problem+json")
    .json({
      type: "https://api.example.com/errors/internal-error",
      title: "Internal Server Error",
      status: 500,
      detail: "An unexpected error occurred. Please try again later.",
      instance: req.originalUrl,
    });
}
```
