# Core concepts

Core objects exposed by the API.

| Object | Description |
|--------|-------------|
| `Organisation` | Top-level entity containing one or more clubs |
| `Club` | Team within an organisation; athletes + staff granted access |
| `Person` | User account, may map to one or more athlete/staff profiles |
| `Athlete` | User profile that participates in sessions; sees only own data |
| `Staff` | User profile that creates, manages, views sessions + all athlete data within a club |
| `Session` | Scheduled activity — Training, Match, or Match with Extra Time |
| `SessionParticipation` | Record of an athlete's involvement in a session |
| `Segment` | Defined time period within a session |
| `SegmentParticipation` | Record of an athlete's involvement in a segment |
| `Survey` | Athlete-reported form data, session-linked or standalone |

## Session subtypes

Two concrete implementations:

- `TrainingSession`
- `MatchSession`

Distinguish via `__typename`:

```graphql
{
  session(id: "...") {
    __typename
    ... on TrainingSession { ... }
    ... on MatchSession { ... }
  }
}
```
