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
- `highIntensityEvents`
- `highMetabolicLoadEvents`
- `highSpeedRunEvents`
- `sprintEvents`

### Acceleration & deceleration

- `accelerationEvents`
- `decelerationEvents`
- `maxAcceleration`
- `maxDeceleration`
- `accelerationLoadPerContributingMinutes`

### Heart rate

- `avgHeartrateBpm`
- `maxHeartrateBpm`
- `zoneOneHeartrateDurationS` … `zoneFiveHeartrateDurationS`

### Jump events

- `lowJumpEvents`
- `mediumJumpEvents`
- `highJumpEvents`

## 2. Zonal breakdowns

Every zone metric exists in three shapes — `*DistanceM`, `*DurationS`, `*Events` — and in two scopes:

- **Club zones** — thresholds shared club-wide
- **Individual zones** — per-athlete thresholds

Both scopes are exposed on every athlete. Use whichever matches your analysis.

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

### Acceleration / deceleration bands

Five-band split (One → Five), each in both scopes.

- `clubZoneOneAcceleration*` … `clubZoneFiveAcceleration*`
- `clubZoneOneDeceleration*` … `clubZoneFiveDeceleration*`
- `individualZoneOneAcceleration*` … `individualZoneFiveAcceleration*`
- `individualZoneOneDeceleration*` … `individualZoneFiveDeceleration*`

## 3. Time series

Fields returning `[TimeSeriesData!]`, sampled at 5-minute intervals:

- `distanceMOverTime`
- `avgSpeedKphOverTime`
- `avgHeartrateBpmOverTime`
- `sprintDistanceMOverTime`
- `highIntensityRunDistanceMOverTime`
- `sampledSpeedKphOverTime`

## 4. Raw GPS

Latitude, longitude, speed, timestamps per athlete session participation via dedicated schema fields.

## Configured vs all metrics

**Configured metrics** — club has enabled in the app. Shown to staff + athletes. Queryable at session, participation, segment level.

**All metrics** — calculated for every club regardless of config. Useful for analysis or future enablement. Some may not return values depending on firmware.

**Caveats:**

- **Zonal metrics** (speed, acceleration, heart rate) use zones set for the athlete at an individual and club level
- **IMU metrics** only available if club device firmware supports them

**Best practice:**

- Use **configured metrics** when aligning with the PlayerData app UI
- Use **all metrics** for deeper analysis or custom reporting
