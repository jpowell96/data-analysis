# FDIC Bank Failures - Time Series Analysis

My latest endeavor with SQL is working with timeseries data.
For this mini-analysis, I decided to chart out US bank failures overtime.

I found the [csv file of the data](https://catalog.data.gov/dataset/fdic-failed-bank-list) on data.gov, which has public
datasets from the US governemnt. It lists all the banks that have failed since 2000.

## Importing the Data

To import the data into my Postgres Database I did the following steps
1. Create a table to represent the rows in the CSV file
```sql
CREATE TABLE bank_failures (
id bigserial,
bank_name TEXT,
city TEXT,
state TEXT,
cert TEXT,
acquiring_institution TEXT,
closing_date DATE,
fund BIGINT
);
```

2. Copy the data into the table from the csv file, using the [COPY command](https://www.postgresql.org/docs/current/sql-copy.html)
```sql
COPY bank_failures (
bank_name,
city,
state,
cert,
acquiring_institution,
closing_date,
fund
) FROM '/path/to/banklist.csv' WITH (FORMAT csv, DELIMITER ',', QUOTE '"', ESCAPE '"', ENCODING 'UTF-8');
```

I originally set the ENCODING to ASCII, but after running into some issues realized I needed to set the encoding to 'UTF-8'. 
Now, with the correct character encoding, 
I imported my data for real but got this error message: 

`ERROR:  invalid byte sequence for encoding "UTF8": 0x96`

After some digging online, I realized this meant there was a non UTF-8 character in the csv file. There was a hyphen character '-' for one of the banks was a special character. I replaced it with a "regular" hyphen - character and that allowed me to import all the data.

## Querying the data

My goal was to run a few simple queries to get the number of bank failures by year,
and then another query to get all the bank failures by month.

I started with a query to find all the months/years that banks had failures

```sql
-- Return bank failures by month, year based on the dataset
 SELECT
  EXTRACT('YEAR' FROM closing_date) as closing_year, 
  EXTRACT('MONTH' FROM closing_date) as closing_month, 
  COUNT(*) as total_failures  
FROM bank_failures 
GROUP BY closing_year, closing_month
ORDER BY closing_year, closing_month;
```

To my surprise, there were some months missing from this query. There wasn't a row for months from January - October, 2000. 

This should be though, if there weren't any failures for a given month in a year, there wouldn't be rows. If I want there to be rows for every month from 2000 - 2023, I need to have date for those months too.

To accomplish this I made a table called timescale, that contains all the months, years from January, 2000 - December 2023. My initial attempt was overcomplicated, but I realized PostgreSQL provides a helpful function, [generate_series()](https://www.postgresql.org/docs/current/functions-srf.html) That lets me generate a series of rows between to dates:

```sql
-- Generate a row for every month between Jan, 2000 and Dec, 2023
SELECT generate_series('2000-01-01', '2023-12-01','1 month'::interval) as timescale;
```

```sql
-- Generate a row for every year between Jan, 2000 and Dec, 2023
SELECT generate_series('2000-01-01', '2023-12-01','1 year'::interval) as timescale;
```

This code will return a result set containing a row for every month from January 2000 until December 2023. 

With this table in mind, we can redo our original "Failures per Month" query and JOIN the timescale onto our bank_failures table:

```sql
-- Return bank failures by month, year based on the dataset
with series as (SELECT
generate_series('2000-01-01', '2023-12-01','1 month'::interval) as timescale)
SELECT
  EXTRACT('YEAR' FROM timescale) as closing_year, 
  EXTRACT('MONTH' FROM timescale) as closing_month, 
  COUNT(bank_failures.closing_date) as total_failures  
FROM series LEFT JOIN bank_failures 
on EXTRACT('YEAR' from timescale) = EXTRACT('YEAR' from closing_date)
and EXTRACT('MONTH' from timescale) = EXTRACT('MONTH' from closing_date)
GROUP BY closing_year, closing_month
ORDER BY closing_year, closing_month;
```

Important Notes:
1. The bank_failures table is left joined onto the timescale. This is done because the timescale
includes every month, year while the bank_failures table only includes records for month/years where a bank failed.
2. We do a `COUNT(bank_failures.closing_date)` rather than a  `COUNT(*)`
    -   A left join will return a record for each row on the timescale table. COUNT(*) would 
    return 1 failure, because it counts rows including NULLs. `COUNT(bank_failures.closing_date)` ensures that we only count cases where there were bank failure in a given month.

Likewise, if we wanted to upsample the data to yearly buckets, the query would look like this:

```sql
with series as (SELECT
generate_series('2000-01-01', '2023-12-01','1 year'::interval) as timescale)
SELECT
  EXTRACT('YEAR' FROM timescale) as closing_year, 
  COUNT(bank_failures.closing_date) as total_failures  
FROM series LEFT JOIN bank_failures 
on EXTRACT('YEAR' from timescale) = EXTRACT('YEAR' from closing_date)
GROUP BY closing_year
ORDER BY closing_year;
```

We've updated the generate_series() function to use an interval of 1 year rather than 1 month, and
updated our JOIN condition to be based on matching years.


## Analyzing the Data

I saved the queries as materialized views and ran a few queries on the data. I used a materialized view because I know that the data is for a fixed time period and will not need to be refreshed. A temp table, or even writing to an actual table would work as well.

```sql
create materialized view bank_failures_by_month as (
with series as (SELECT
generate_series('2000-01-01', '2023-12-01','1 month'::interval) as timescale)
SELECT
  EXTRACT('YEAR' FROM timescale) as closing_year, 
  EXTRACT('MONTH' FROM timescale) as closing_month, 
  COUNT(bank_failures.closing_date) as total_failures  
FROM series LEFT JOIN bank_failures 
on EXTRACT('YEAR' from timescale) = EXTRACT('YEAR' from closing_date)
and EXTRACT('MONTH' from timescale) = EXTRACT('MONTH' from closing_date)
GROUP BY closing_year, closing_month
ORDER BY closing_year, closing_month);
```


Questions:

Which years had the most bank failures?
```sql
select 
	RANK() over (order by sum(total_failures) desc),
	closing_year::int, 
	SUM(total_failures) as total_failures
from bank_failures_by_month 
group by closing_year
order by SUM(total_failures) desc
limit 5;
```

|rank|closing_year|total_failures|
|----|------------|--------------|
|1|2010|157|
|2|2009|140|
|3|2011|92|
|4|2012|51|
|5|2008|25|


Which month/year had the most bank failures?

```sql
select 
	RANK() over (order by total_failures desc),
	closing_year :: INT, 
	closing_month,
	total_failures
from bank_failures_by_month 
order by total_failures desc
limit 5;
```

|rank|closing_year|closing_month|total_failures|
|----|------------|-------------|--------------|
|1|2009|7|24|
|2|2010|4|23|
|3|2010|7|22|
|4|2009|10|20|
|5|2010|3|19|

## Wrapping it up

For time series data that has gaps, the generate_series() function can enable 
analyzing the data with a complete timeline. And, if needed, can support different
levels of granularity (day, week, month, etc.) to match the granularity of your date.


### Helpful Links
[generate_series() postgres docs](https://www.postgresql.org/docs/current/functions-srf.html)
[timescale db - generate series explanation](https://www.timescale.com/blog/how-to-create-lots-of-sample-time-series-data-with-postgresql-generate_series/)