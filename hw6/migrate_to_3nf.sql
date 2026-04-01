DELETE FROM error_logs_3nf;
DELETE FROM requests_3nf;
DELETE FROM ip_country_map;
DELETE FROM countries;

INSERT INTO countries (country_name, is_banned)
SELECT country, MAX(is_banned) AS is_banned
FROM request_logs
WHERE country IS NOT NULL
GROUP BY country;

INSERT INTO ip_country_map (client_ip, country_id)
SELECT ranked.client_ip, c.country_id
FROM (
    SELECT client_ip, country
    FROM (
        SELECT
            client_ip,
            country,
            ROW_NUMBER() OVER (
                PARTITION BY client_ip
                ORDER BY COUNT(*) DESC, country
            ) AS rn
        FROM request_logs
        WHERE client_ip IS NOT NULL
          AND country IS NOT NULL
        GROUP BY client_ip, country
    ) t
    WHERE rn = 1
) ranked
JOIN countries c
  ON ranked.country = c.country_name;

INSERT INTO requests_3nf (
    request_time,
    client_ip,
    gender,
    age,
    income,
    time_of_day,
    requested_file
)
SELECT
    rl.request_time,
    rl.client_ip,
    rl.gender,
    rl.age,
    rl.income,
    rl.time_of_day,
    rl.requested_file
FROM request_logs rl
JOIN ip_country_map m
  ON rl.client_ip = m.client_ip;

INSERT INTO error_logs_3nf (
    request_time,
    requested_file,
    error_code
)
SELECT
    request_time,
    requested_file,
    error_code
FROM error_logs;
