Question 1 : Find the total number of trips for each day.
SQL Answer:
SELECT 
    EXTRACT(DATE FROM start_time) AS extract_date,
    COUNT(trip_id) AS trip_count
FROM 
    `bigqueryproject-440214.zeals_assignment.bikeshare_trip`
GROUP BY 
    extract_date
ORDER BY 
    extract_date
;



Question 2 : Calculate the average trip duration for each day.
SQL Answer:
SELECT 
    DATE(start_time) AS extract_date,
    AVG(duration_minutes) AS average_trip_duration_minutes
FROM 
    `bigqueryproject-440214.zeals_assignment.bikeshare_trip`
GROUP BY 
    extract_date
ORDER BY 
    extract_date
;


Question 3 : Identify the top 5 stations with the highest number of trip starts.
SQL Answer:
SELECT 
    start_station_name,
    COUNT(trip_id) AS number_of_trip
FROM 
    `bigqueryproject-440214.zeals_assignment.bikeshare_trip`
GROUP BY 
    start_station_name
ORDER BY 
    number_of_trip DESC
LIMIT 5
;


Question 4 : Find the average number of trips per hour of the day.
SQL Answer:
SELECT
  extract_hour,
  (SUM(count_trip_number) / COUNT(extract_date)) AS avg_trip_number_count_per_hour
FROM 
(
    SELECT
        EXTRACT(DATE FROM start_time) AS extract_date,
        EXTRACT(HOUR FROM start_time) AS extract_hour,
        COUNT(trip_id) AS count_trip_number
    FROM
        `bigqueryproject-440214.zeals_assignment.bikeshare_trip`
    GROUP BY
        extract_date, extract_hour
)
GROUP BY
    extract_hour
ORDER BY
    extract_hour
;


Question 5 : Determine the most common trip route (start station to end station).
SQL Answer:
SELECT 
    route
FROM
(
    SELECT 
        'Route from ' || start_station_name || ' to ' || end_station_name AS route,
        COUNT(trip_id) AS trip_count
    FROM 
        `bigqueryproject-440214.zeals_assignment.bikeshare_trip`
    GROUP BY 
        route
    ORDER BY
        trip_count DESC
)
LIMIT 1
;


Question 6 : Calculate the number of trips each month.
SQL Answer:
SELECT
    EXTRACT(YEAR FROM start_time) AS extract_year,
    EXTRACT(MONTH FROM start_time) AS extract_month,
    COUNT(trip_id) AS number_of_trips
FROM
    `bigqueryproject-440214.zeals_assignment.bikeshare_trip`
GROUP BY 
    extract_year, extract_month
ORDER BY 
    extract_year ASC, extract_month ASC
;


Question 7 : Find the station with the longest average trip duration.
SQL Answer:
SELECT
  start_station_name
FROM
(
    SELECT
        start_station_name,
        AVG(duration_minutes) AS avg_duration_minutes
    FROM
        `bigqueryproject-440214.zeals_assignment.bikeshare_trip`
    GROUP BY
        start_station_name
    ORDER BY
        avg_duration_minutes DESC
)
LIMIT 1
;


Question 8 : Find the busiest hour of the day (most trips started).
SQL Answer:
WITH group_by_date_and_hour_max_count_trip_table AS 
(
    SELECT
        extract_date,
        extract_hour,
        count_trip_number,
        MAX(count_trip_number) OVER (PARTITION BY extract_date) AS max_count_trip_number
    FROM 
    (
        SELECT
            EXTRACT(DATE FROM start_time) AS extract_date,
            EXTRACT(HOUR FROM start_time) AS extract_hour,
            COUNT(trip_id) AS count_trip_number
        FROM
            `bigqueryproject-440214.zeals_assignment.bikeshare_trip`
        GROUP BY
            extract_date, extract_hour
    )
)
SELECT 
    extract_date AS day,
    extract_hour AS busiest_hour_of_the_day
FROM 
    group_by_date_and_hour_max_count_trip_table
WHERE
    count_trip_number = max_count_trip_number
ORDER BY
    extract_date ASC
;


Question 9 : Identify the day with the highest number of trips.
SQL Answer:
SELECT 
    extract_date
FROM 
(
    SELECT
        EXTRACT(DATE FROM start_time) AS extract_date,
        COUNT(trip_id) AS count_trip_number
    FROM
        `bigqueryproject-440214.zeals_assignment.bikeshare_trip`
    GROUP BY
        extract_date
    ORDER BY
        count_trip_number DESC
)
LIMIT 1
;


