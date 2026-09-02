# Metrics

Per-athlete performance metrics on session, segment, and session-participation objects. Every metric on the `CommonAthleteMetrics` interface is queryable on `MatchSessionAthleteMetricSet`, `TrainingSessionAthleteMetricSet`, and their period/segment variants.

Full schema reference: [`schema/objects/`](schema/objects/index.md). Live exploration: [GraphiQL Playground](https://app.playerdata.co.uk/api/graphiql).

Metrics fall into four shapes:

1. **Totals** — one number per athlete per session/segment (e.g. `totalDistanceM`)
2. **Zonal breakdowns** — totals binned into intensity bands (e.g. `clubZoneSprintDistanceM`)
3. **Time series** — sampled values over time at fixed intervals (e.g. `distanceMOverTime`)
4. **Raw GPS** — per-sample latitude / longitude / speed

## 1. Totals

### Distance & speed

- `totalDistanceM`
- `metresPerMinute`
- `distanceMAtKph` — distance bucketed by speed band
- `timeAtKph` — time bucketed by speed band
- `avgSpeedKph`
- `maxSpeedKph`
- `rawMaxSpeedKph`
- `percentageMaxSpeedKph`
- `percentageRawMaxSpeedKph`
- `ninetyPercentOfMaxSpeedDistanceM`
- `ninetyPercentOfMaxSpeedDurationS`
- `ninetyPercentOfMaxSpeedEvents`

### Intensity totals

- `highSpeedRunDistanceM`
- `totalHighIntensityDistanceM`
- `totalMediumIntensityDistanceM`
- `totalSprintDistanceM`
- `highMetabolicLoadDistanceM`
- `explosiveDistanceM`
- `highIntensityEvents`
- `highMetabolicLoadEvents`
- `highSpeedRunEvents`
- `sprintEvents`

### Acceleration & deceleration

- `accelerationEvents`
- `decelerationEvents`
- `maxAcceleration`
- `maxDeceleration`
- `accelerationLoad`
- `accelerationLoadPerContributingMinutes`

### Heart rate totals

- `avgHeartrateBpm`
- `maxHeartrateBpm`
- `zoneOneHeartrateDurationS` … `zoneFiveHeartrateDurationS`

### Load & effort totals

- `work`
- `workload`
- `activeMinutes` (Only available to IMU users)

### Jump events

- `lowJumpEvents`
- `mediumJumpEvents`
- `highJumpEvents`
- `averageJumpHeightCm`
- `maxJumpHeightCm`

### Other IMU events

Require supporting device firmware.

- `linearAccelerationLowEvents`, `linearAccelerationMediumEvents`, `linearAccelerationHighEvents`
- `lateralAccelerationEvents`
- `verticalAccelerationEvents`

## 2. Zonal breakdowns

Speed and acceleration zone metrics exist in up to three shapes — `*DistanceM`, `*DurationS`, `*Events` — and in two scopes.

These metrics only count a zone once the athlete has held it for at least **0.5 seconds**.

### Zone scopes: club vs individual

Both scopes are exposed on every athlete, always. Picking between them is an analysis decision, not an availability one.

| Scope | Thresholds | Use when |
|---|---|---|
| **Club** (`clubZone*`) | One boundary set shared by the whole team | Comparing athletes against each other, or matching the club's own reporting |
| **Individual** (`individualZone*`) | Per-athlete boundaries | Comparing an athlete against their own capacity |

Individual zones are configured in one of two ways, and the difference is visible in the API:

- **Absolute** — explicit boundaries set for that athlete.
- **Relative** — derived from the athlete's own maximum speed, and re-derived as that maximum changes.

You can read the zone configuration currently in use from the athlete:

```graphql
query AthleteZones($id: ID!) {
  athlete(id: $id) {
    autoUpdateRelativeSpeedzones
    labelledSpeedzonesLowerBoundsKph { absolute { zone1 zone2 zone3 zone4 zone5 }
                                       relative { zone1 zone2 zone3 zone4 zone5 } }
    labelledAccelzonesLowerBoundsMs2 { absolute { zone1 zone2 zone3 zone4 zone5 }
                                       relative { zone1 zone2 zone3 zone4 zone5 } }
  }
}
```

A null `absolute` block means no overrides are set and platform defaults apply.

### Speed / intensity bands

Ascending order: **Jogging → Low intensity → Medium intensity → High intensity → Sprint**. `HighSpeedRunning` is the combined high-intensity + sprint range, not a separate band.

| Band | Club | Individual |
|------|------|------------|
| Jogging | `clubZoneJogging*` | `individualZoneJogging*` |
| Low intensity | `clubZoneLowIntensity*` | `individualZoneLowIntensity*` |
| Medium intensity | `clubZoneMediumIntensity*` | `individualZoneMediumIntensity*` |
| High intensity | `clubZoneHighIntensity*` | `individualZoneHighIntensity*` |
| Sprint | `clubZoneSprint*` | `individualZoneSprint*` |
| High-speed running (combined) | `clubZoneHighSpeedRunning*` | `individualZoneHighSpeedRunning*` |

Default boundaries, used when a club has not configured their own zones. A zone runs from its own lower bound up to the next zone's lower bound, so Jogging is 7.2–10.8 km/h. Speeds below 7.2 km/h fall into no band.

| Label | Zone (km/h) |
|---|---|
| Jogging | 7.2–10.8 |
| Low intensity | 10.8–14.4 |
| Medium intensity | 14.4–19.8 |
| High intensity | 19.8–25.2 |
| Sprint | 25.2 and above |

### Acceleration / deceleration bands

Five-band split (One → Five), each in both scopes.

- `clubZoneOneAcceleration*` … `clubZoneFiveAcceleration*`
- `clubZoneOneDeceleration*` … `clubZoneFiveDeceleration*`
- `individualZoneOneAcceleration*` … `individualZoneFiveAcceleration*`
- `individualZoneOneDeceleration*` … `individualZoneFiveDeceleration*`

Default boundaries, where a club has not configured its own. A zone runs from its own lower bound up to the next zone's lower bound, so Zone 1 is 1–2 m/s².

| Zone | Acceleration | Deceleration |
|---|---|---|
| 1 | 1–2 m/s² | −1 to −2 m/s² |
| 2 | 2–3 m/s² | −2 to −3 m/s² |
| 3 | 3–4 m/s² | −3 to −4 m/s² |
| 4 | 4–5 m/s² | −4 to −5 m/s² |
| 5 | 5 m/s² and above | −5 m/s² and below |

All are configurable per club in zone management, so read the athlete's bounds rather than assuming these.

## 3. Time series

Fields returning `[TimeSeriesData!]`. Each point carries its own `startTime` and `endTime` — read the window from the response rather than assuming a fixed sampling interval:

- `distanceMOverTime`
- `avgSpeedKphOverTime`
- `avgHeartrateBpmOverTime`
- `sprintDistanceMOverTime`
- `highIntensityRunDistanceMOverTime`
- `sampledSpeedKphOverTime`

## 4. Raw GPS

Latitude, longitude, speed, timestamps per athlete session participation via dedicated schema fields.

## What the metrics actually mean

Field names carry units but not definitions. These are the ones that most often get read the wrong way.

### Speed

**`maxSpeedKph`** — peak running speed, found by analysing peak speed data in **0.5-second intervals** and taking the maximum.

**`rawMaxSpeedKph`** — the absolute maximum speed in the session, unsmoothed. Always ≥ `maxSpeedKph`.

**`percentageMaxSpeedKph`** — a percentage of the athlete's **personal best** max speed, recorded across any previous session. This may exceed 100% if an athlete exceeds their previous personal best in the current session.

### Distance and intensity

**`totalDistanceM`** — cumulative distance between successive position measurements.

**`metresPerMinute`** — total distance divided by time spent on the pitch.

**`highMetabolicLoadDistanceM`** — distance covered above the metabolic power threshold of **25.542 W/kg**. `highMetabolicLoadEvents` counts periods spent above that threshold for at least 0.5 s.

**`highSpeedRunDistanceM`** — the high-intensity and sprint zones combined.

### Load and effort

**`workload`** — a **0–10 score**. It is derived from volume and intensity across all of the athlete's sessions in the **last 28 days**, with **5 as the baseline**. Above 5 means the athlete is above their recent norm; below 5 means under it.

**`accelerationLoad`** — a volume metric: acceleration is combined across all 3 axes. An indicator of total physical work.

**`accelerationLoadPerContributingMinutes`** — `accelerationLoad` divided by total contributing minutes.

**`work` (session load in app)** — a cumulative measure of energy exertion during the session.

**`accelerationEvents` / `decelerationEvents`** — counted when acceleration exceeds **2.25 m/s²** (or drops below **−2.25 m/s²**) for at least 0.5 s.

### Heart rate

Default zone boundaries, all configurable per club:

| Zone | Range |
|---|---|
| 1 | 100–120 bpm |
| 2 | 120–140 bpm |
| 3 | 140–160 bpm |
| 4 | 160–180 bpm |
| 5 | 180 bpm and above |

Heart-rate fields are empty without a paired heartrate strap.

## Configured vs all metrics

**Configured metrics** — club has enabled in the app. Shown to staff + athletes. Queryable at session, participation, segment level.

**All metrics** — calculated for every club regardless of config. Useful for analysis or future enablement. Some may not return values depending on firmware.

**Caveats:**

- **Zonal metrics** (speed, acceleration, heart rate) use zones set for the athlete at an individual and club level
- **IMU metrics** only available if club device firmware supports them

**Best practice:**

- Use **configured metrics** when aligning with the PlayerData app UI
- Use **all metrics** for deeper analysis or custom reporting
