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

## Analyzing the data

My goal was to run a few simple queries to get the number of bank failures by year,
and then another query to get all the bank failures by month.

I started with a query to find all the months/years that banks had failures

```sql
 SELECT
  EXTRACT('YEAR' FROM closing_date) as closing_year, 
  EXTRACT('MONTH' FROM closing_date) as closing_month, 
  COUNT(*) as total_failures  
FROM bank_failures 
GROUP BY closing_year, closing_month
ORDER BY closing_year, closing_month;
```

To my surprise, there were some months missing from this query. There wasn't a row for 
January,