# Intro

This year one of my goals was to improve my data analysis skills. As a software engineer, most of time is spent in application level code. Though I work with relational databases, I really don't work with complex queries beyond a few joins. But, data analysis is a common part of our job. If you've ever been on-call, you'v'e probably had to query your database to understand the state of your sysem, who is impacted, when did an issue start? 

To improve my data analysis skills I got a subscription to DataCamp, a popular online course platform focused on data analytics, data engineering, and AI. I've completed a number of courses, and now I'm testing out my skills by doing what's called an Exploratory Data Analysis (EDA).

## Exploratory Data Analysis

### Overview

I grabbed this [Superstore Sales Dataset](https://www.kaggle.com/datasets/bravehart101/sample-supermarket-dataset) from Kaggle as a CSV file.

It has 13 columns that include sales data for a generic superstore:
- Ship Mode: Mode of shipping used for shipment delivery
- Segment: (Categorical) Customer segment product was shipped to
- Country: Country in which the shipment was delivered
- City: City in which shipment was delivered
- State: State in which the shipment was delivered
- Postal Code: Postal code the shipment was delivered to
- Region: Country region
- Category: The category product belongs to
- Sub-Category: Sub-category of the product
- Sales: Sale made in USD
- Quantity: Product quantity
- Discount: Discount given on the product
- Profit: Profit/loss made on the sale

Given this sales data, I asked a few questions to learn more.
I used SQL to parse the CSV and load it into a table I created and I asked a few questions about the data.

## Conclusions
Given the information, what should your supermarket do?



## Exploratory Queries
How many sales were made in the dataset?

```sql
SELECT COUNT(*) FROM sales; -- 9994
```
How many total items were sold?


```sql
SELECT SUM(quantity) FROM sales; -- 37873
```

What was the total profit overall? And, what were the top 10 highest profit states?
```sql
WITH aggregate_profits AS (
SELECT 
	CASE 
		WHEN country IS NOT NULL THEN country
		ELSE 'Overall'
	END as country,
	state,
	SUM(profit) as total_profit 
FROM sales 
GROUP BY GROUPING SETS((country, state), ()) 
ORDER BY country, state)

SELECT country, state, total_profit 
FROM aggregate_profits
ORDER BY total_profit DESC LIMIT 10;
```
```
    country    |   state    | total_profit 
---------------+------------+--------------
 Overall       |            |  286397.0217
 United States | California |   76381.3871
 United States | New York   |   74038.5486
 United States | Washington |   33402.6517
 United States | Michigan   |   24463.1876
 United States | Virginia   |   18597.9504
 United States | Indiana    |   18382.9363
 United States | Georgia    |   16250.0433
 United States | Kentucky   |   11199.6966
 United States | Minnesota  |   10823.1874
``````
Which city had the most profit in each state?
```sql
WITH ranked_profits_by_state_city AS (
	select state, city, sum(profit) as profit, 
	RANK() OVER (PARTITION BY state ORDER BY sum(profit) DESC) as rank  
	FROM sales GROUP BY state, city ORDER BY state, rank)

SELECT state, city, profit FROM 
ranked_profits_by_state_city
WHERE rank = 1;
```
```
        state         |      city       |   profit   
----------------------+-----------------+------------
 Alabama              | Mobile          |  2175.8292
 Arizona              | Glendale        |   182.8598
 Arkansas             | Fayetteville    |  1691.9419
 California           | Los Angeles     | 30440.7579
 Colorado             | Thornton        |   140.8398
 Connecticut          | Fairfield       |  1221.6226
 Delaware             | Newark          |  8086.1715
 District of Columbia | Washington      |  1059.5893
```

What were total sales and profit by catagory, and subcategory?
```sql
SELECT category, 
sub_category, 
COUNT(*) as total_sales,
SUM(profit) as profit
FROM sales 
GROUP BY ROLLUP(category, sub_category)
ORDER BY category ASC NULLS FIRST, sub_category ASC NULLS FIRST;

```

```
    category     | sub_category | total_sales |   profit    
-----------------+--------------+-------------+-------------
                 |              |        9994 | 286397.0217
 Furniture       |              |        2121 |  18451.2728
 Furniture       | Bookcases    |         228 |  -3472.5560
 Furniture       | Chairs       |         617 |  26590.1663
 Furniture       | Furnishings  |         957 |  13059.1436
 Furniture       | Tables       |         319 | -17725.4811
 Office Supplies |              |        6026 | 122490.8008
 Office Supplies | Appliances   |         466 |  18138.0054
 Office Supplies | Art          |         796 |   6527.7870
 Office Supplies | Binders      |        1523 |  30221.7633
 Office Supplies | Envelopes    |         254 |   6964.1767
 Office Supplies | Fasteners    |         217 |    949.5182
 Office Supplies | Labels       |         364 |   5546.2540
 Office Supplies | Paper        |        1370 |  34053.5693
 Office Supplies | Storage      |         846 |  21278.8264
 Office Supplies | Supplies     |         190 |  -1189.0995
 Technology      |              |        1847 | 145454.9481
 Technology      | Accessories  |         775 |  41936.6357
 Technology      | Copiers      |          68 |  55617.8249
 Technology      | Machines     |         115 |   3384.7569
 Technology      | Phones       |         889 |  44515.7306

```

What were sales and profit by region and category?
```sql
SELECT 
region,
category, 
COUNT(*) as total_sales,
SUM(profit) as total_profit,
FROM sales GROUP BY ROLLUP(region, category)
ORDER BY region NULLS FIRST, category NULLS FIRST;
```
```
 region  |    category     | total_sales | total_profit 
---------+-----------------+-------------+--------------
         |                 |        9994 |  286397.0217
 Central |                 |        2323 |   39706.3625
 Central | Furniture       |         481 |   -2871.0494
 Central | Office Supplies |        1422 |    8879.9799
 Central | Technology      |         420 |   33697.4320
 East    |                 |        2848 |   91522.7800
 East    | Furniture       |         601 |    3046.1658
 East    | Office Supplies |        1712 |   41014.5791
 East    | Technology      |         535 |   47462.0351
 South   |                 |        1620 |   46749.4303
 South   | Furniture       |         332 |    6771.2061
 South   | Office Supplies |         995 |   19986.3928
 South   | Technology      |         293 |   19991.8314
 West    |                 |        3203 |  108418.4489
 West    | Furniture       |         707 |   11504.9503
 West    | Office Supplies |        1897 |   52609.8490
 West    | Technology      |         599 |   44303.6496
```
What are the most popular product segments by state?
```sql
select 
	state, 
	segment, 
	RANK() OVER (PARTITION BY state ORDER BY COUNT(quantity)) as popularity 
FROM sales GROUP BY state, segment;
```
```
        state         |   segment   | popularity 
----------------------+-------------+------------
 Alabama              | Home Office |          1
 Alabama              | Consumer    |          2
 Alabama              | Corporate   |          3
 Arizona              | Home Office |          1
 Arizona              | Corporate   |          2
 Arizona              | Consumer    |          3
```
## Process 
-- Make a separate document about process