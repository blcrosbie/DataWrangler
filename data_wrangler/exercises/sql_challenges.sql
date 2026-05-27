/*
Codility PostgreSQL SQL practice blocks.

The marked query blocks are intentionally standalone SELECT statements. The
Python harness extracts them by name and executes them against in-memory SQLite
tables, so the query bodies stick to PostgreSQL syntax that is also portable
across SQLite for local smoke testing.
*/

/* -------------------------------------------------------------------------
SqlSum (Elementary)

Expected input table:
  numbers(value INTEGER)

Optimization notes:
  - SUM is a single aggregate scan: O(N) time, O(1) extra memory.
  - SUM ignores NULL values; COALESCE converts all-NULL or zero-row tables to 0.
  - Negative values are included naturally by the aggregate.
------------------------------------------------------------------------- */
-- name: SqlSum
SELECT
    COALESCE(SUM(value), 0) AS total_sum
FROM numbers;
-- end: SqlSum

/* -------------------------------------------------------------------------
SqlEventsDelta (Easy)

Expected input table:
  events(event_type TEXT, event_time TIMESTAMP or INTEGER, value INTEGER)

Result:
  one row per event_type that has at least one non-NULL event_type record:
    event_type, latest_value, previous_value, delta

Optimization notes:
  - ROW_NUMBER() partitions each event type and orders by latest event time.
  - This avoids correlated subqueries and nested scans. With an index on
    (event_type, event_time DESC), the database can evaluate the ranking in
    O(N log N) for the ordering step, or close to O(N) when input is already
    index-ordered.
  - NULL event types are excluded because they cannot form a stable partition
    key in most interview specifications.
  - NULL values are treated as 0 so latest-minus-previous never raises or
    propagates a NULL-only arithmetic result.
------------------------------------------------------------------------- */
-- name: SqlEventsDelta
WITH ranked_events AS (
    SELECT
        event_type,
        COALESCE(value, 0) AS safe_value,
        ROW_NUMBER() OVER (
            PARTITION BY event_type
            ORDER BY event_time DESC
        ) AS row_num
    FROM events
    WHERE event_type IS NOT NULL
),
pivoted AS (
    SELECT
        event_type,
        MAX(CASE WHEN row_num = 1 THEN safe_value END) AS latest_value,
        MAX(CASE WHEN row_num = 2 THEN safe_value END) AS previous_value
    FROM ranked_events
    WHERE row_num <= 2
    GROUP BY event_type
)
SELECT
    event_type,
    COALESCE(latest_value, 0) AS latest_value,
    COALESCE(previous_value, 0) AS previous_value,
    COALESCE(latest_value, 0) - COALESCE(previous_value, 0) AS delta
FROM pivoted
ORDER BY event_type;
-- end: SqlEventsDelta

/* -------------------------------------------------------------------------
SqlWorldCup (Medium)

Expected input tables:
  teams(team_name TEXT)
  matches(host_team TEXT, guest_team TEXT, host_goals INTEGER, guest_goals INTEGER)

Result:
  every known team, including teams with zero matches:
    team_name, points, matches_played

Optimization notes:
  - The match table is scanned twice with UNION ALL: once from the host
    perspective and once from the guest perspective. That is still O(N).
  - The team ledger is then aggregated once by team: O(N) hash/group aggregate.
  - LEFT JOIN from all_teams guarantees teams with no rows in matches remain in
    the final ledger with 0 points and 0 matches.
  - COALESCE converts NULL goals to 0, preventing NULL comparisons from erasing
    a result. In a stricter production schema, NOT NULL goals would be better.
------------------------------------------------------------------------- */
-- name: SqlWorldCup
WITH all_teams AS (
    SELECT team_name
    FROM teams
    WHERE team_name IS NOT NULL
    UNION
    SELECT host_team AS team_name
    FROM matches
    WHERE host_team IS NOT NULL
    UNION
    SELECT guest_team AS team_name
    FROM matches
    WHERE guest_team IS NOT NULL
),
match_points AS (
    SELECT
        host_team AS team_name,
        CASE
            WHEN COALESCE(host_goals, 0) > COALESCE(guest_goals, 0) THEN 3
            WHEN COALESCE(host_goals, 0) = COALESCE(guest_goals, 0) THEN 1
            ELSE 0
        END AS points
    FROM matches
    WHERE host_team IS NOT NULL

    UNION ALL

    SELECT
        guest_team AS team_name,
        CASE
            WHEN COALESCE(guest_goals, 0) > COALESCE(host_goals, 0) THEN 3
            WHEN COALESCE(guest_goals, 0) = COALESCE(host_goals, 0) THEN 1
            ELSE 0
        END AS points
    FROM matches
    WHERE guest_team IS NOT NULL
),
team_totals AS (
    SELECT
        team_name,
        SUM(points) AS points,
        COUNT(*) AS matches_played
    FROM match_points
    GROUP BY team_name
)
SELECT
    all_teams.team_name,
    COALESCE(team_totals.points, 0) AS points,
    COALESCE(team_totals.matches_played, 0) AS matches_played
FROM all_teams
LEFT JOIN team_totals
    ON team_totals.team_name = all_teams.team_name
ORDER BY
    points DESC,
    all_teams.team_name ASC;
-- end: SqlWorldCup
