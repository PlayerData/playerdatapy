# FAQ

### Which authentication method should I use?

- **Authorisation Code Grant** — user-facing apps, or when mutations are required
- **Client Credentials Grant** — backend, read-only integrations

Full decision guide: [Choosing a grant type](auth.md#choosing-a-grant-type).

### Why can't I access a club's data?

Under the Authorisation Code Grant, the authenticated user is not listed as staff for that club — contact the club administrator. Under Client Credentials, the service account has not been granted access to that organisation — contact `support@playerdata.com`.

For the exact response shapes, see [Troubleshooting](#troubleshooting) below.

### Can I write or update data (mutate) via the API?

Yes, but only under the Authorisation Code Grant. Client credentials cannot write under any configuration.

Note that `createSession` only creates the session record — attaching data needs a second call to `upsertDataRecordings`.

### Is the GraphiQL Playground safe to use?

Yes — but mutations run against **real production data**.

### How long do tokens last?

Access tokens expire after **2 hours**. Authorisation Code Grant issues refresh tokens; Client Credentials Grant does not (re-run the flow).

### Where do I get credentials?

Contact your PlayerData representative or `support@playerdata.com`.

### Why is this metric null / zero?

A null means "not recorded"; a zero means "recorded, and the value was zero". Most nulls reflect club or device configuration rather than a fault — see [Expected nulls and zeros](#expected-nulls-and-zeros) below.

### Why does a participation have no data at all?

Read the participation's `diagnosticWarnings` before raising a ticket — the API explains the cause and the remedy itself:

```graphql
query ParticipationDiagnostics($id: ID!) {
  trainingSession(id: $id) {
    sessionParticipations {
      athlete { name }
      diagnosticWarnings {
        errorType
        shortMessage
        outcome
        remediation
      }
    }
  }
}
```

`errorType` covers the common physical causes — `NO_GPS_DATA`, `GPS_QUALITY`, `UNIT_NOT_WORN`, `UNIT_SWITCHED_OFF`, `BATTERY_DEPLETION`, `DATA_OUTSIDE_TIME_WINDOW`, `DATA_OVERWRITTEN`, `PITCH_LOCATION_ERROR`. `outcome` describes the impact on the data and `remediation` lists what prevents it recurring. `Session.aggregatedDiagnosticWarnings` rolls the same warnings up across every participation in a session.

A participation with no data and no warnings is worth reporting to `support@playerdata.com`.

### What is `percentageMaxSpeedKph` a percentage of?

The athlete's own personal best max speed — not the session's top speed, and not a club or positional maximum. See [Metrics](metrics.md#speed).

## Expected nulls and zeros

Most metric fields are nullable, and a null is usually a statement about metric configuration rather than a fault.

A null means *"not recorded"*. A zero means *"recorded, and the value was zero"*. Treat the two differently — averaging a zero that means "no IMU device" will quietly skew a report.

### Commonly reported, working as intended

| Field | What the value means | What to do |
|---|---|---|
| `Athlete.labelledAccelzonesLowerBoundsMs2.absolute` | Null when the athlete has no absolute overrides set, so platform defaults are in use | Nothing. Read `relative` for the derived per-athlete bounds, or treat null as "defaults" |
| `SessionParticipation.filteredDataFileUrl` | Always null. Retired field, kept for compatibility | Use `datafiles` for the participation's data recordings |
| `activeMinutes` | `0.0` when the club does not record IMU data | Zero here means "not recorded", not an inactive athlete. Confirm the club has IMU-capable devices before treating it as a real measurement |
| IMU-derived fields | Empty or null without supporting device firmware | Check firmware support with the club before building on these |
| Heart-rate fields (`avgHeartrateBpm`, `maxHeartrateBpm`, `zone*HeartrateDurationS`) | Empty when no heart-rate strap was paired for that participation | Check `DataRecording.hasHeartrateData` before reading them |
| `Athlete.shirtNumber` | Commonly null — optional, and many clubs never fill it in | Do not use as a join key or a display fallback |
| `Athlete.customId` | Commonly null — optional external identifier, populated only by clubs that use one | Fall back to `Athlete.id`, which is always present |

## Troubleshooting

### Authentication and access

| Symptom | Likely cause | Fix |
|---|---|---|
| `invalid_client` from `/oauth/token` | Wrong client ID or secret, or the client is not provisioned for the grant type you asked for | Confirm the credentials, then confirm the client is enabled for that grant — a client provisioned for authorisation code will reject `grant_type=client_credentials` |
| `200` with `{"data": {"organisations": []}}` | The service account authenticated, but has not been granted access to any organisation | Access is granted by PlayerData, not self-served. Contact `support@playerdata.com` with your client ID and the organisation you need |
| `200` with `errors[].extensions.permissionError: true` | Under the authorisation code grant, the signed-in user is not staff on the club you queried. Under client credentials, the service account has not been granted access to that organisation | This is the expected error shape, not a bug. See [Permissions](auth.md#permissions) for which applies to your grant |
| Empty `500` on a mutation, with a client-credentials token | Client credentials cannot write | Use the [authorisation code grant](auth.md#choosing-a-grant-type) for anything that mutates. Contact support if you need to change your credential type |

Authenticating successfully tells you nothing about whether you can see a given club's data — the two are separate checks.

### Checking what a token can actually see

Before debugging a specific query, confirm what the token is scoped to:

```graphql
query WhoAmI {
  organisations {
    id
    name
    clubs { id name }
  }
}
```

An empty list means the grant is the problem, not the query.

## Still stuck?

Reach out to `support@playerdata.com`. Include your client ID (never the secret), the grant type, the query, and the full response body including `errors[].extensions`.
