# Pagination & limits

## Pagination

- Default + maximum page size: **30 records**
- Use `offset` and `limit` parameters to page

```graphql
sessions(filter: {...}, offset: 0, limit: 30) { id }
```

## Query complexity

Complexity limits enforced to protect platform stability. Large or deeply nested queries may fail.

**Best practice:**

- Split large data requests into smaller queries
- Avoid requesting full metrics across many sessions in one query
- Page through sessions, then fetch metrics per page
