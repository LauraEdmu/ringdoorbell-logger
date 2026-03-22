-- hour
SELECT
    TO_CHAR(occurred_at, 'HH24') AS hour,
    COUNT(*) AS motion_count
FROM ring_events
WHERE event_type = 'motion'
  AND occurred_at IS NOT NULL
GROUP BY hour
ORDER BY motion_count DESC;

-- minute
SELECT
    DATE_TRUNC('minute', occurred_at) AS minute,
    COUNT(*) AS motion_count
FROM ring_events
WHERE event_type = 'motion'
GROUP BY minute
ORDER BY motion_count DESC
LIMIT 10;

-- day of the week
SELECT
    TO_CHAR(occurred_at, 'Day') AS day,
    COUNT(*) AS motion_count
FROM ring_events
WHERE event_type = 'motion'
GROUP BY day
ORDER BY motion_count DESC;

-- mix
SELECT
    EXTRACT(DOW FROM occurred_at) AS dow,   -- 0 = Sunday
    EXTRACT(HOUR FROM occurred_at) AS hour,
    COUNT(*) AS motion_count
FROM ring_events
WHERE event_type = 'motion'
GROUP BY dow, hour
ORDER BY dow, hour;
