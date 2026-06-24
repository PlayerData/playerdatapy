# Metrics

Non-exhaustive reference. Full set discoverable via [GraphiQL Playground](https://app.playerdata.co.uk/api/graphiql).

## Distance & speed

- `totalDistanceM`
- `avgSpeedKph`
- `maxSpeedKph`
- `metresPerMinute`
- `distanceMAtKph`
- `timeAtKph`

## Intensity & events

- `accelerationEvents`
- `decelerationEvents`
- `highIntensityEvents`
- `sprintEvents`
- `totalHighIntensityDistanceM`
- `totalSprintDistanceM`

## Time-series (5-minute intervals)

- `distanceMOverTime`
- `avgSpeedKphOverTime`

## Raw GPS

Latitude, longitude, speed, timestamps per athlete session participation via dedicated schema fields.

## Configured vs all metrics

**Configured metrics** — club has enabled in the app. Shown to staff + athletes. Queryable at session, participation, segment level.

**All metrics** — calculated for every club regardless of config. Useful for analysis or future enablement. Some may not return values depending on firmware.

**Caveats:**

- **Zonal metrics** (speed, acceleration, heart rate) use zones set at session time or app defaults
- **IMU metrics** only available if club device firmware supports them

**Best practice:**

- Use **configured metrics** when aligning with the PlayerData app UI
- Use **all metrics** for deeper analysis or custom reporting
