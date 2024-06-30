import psycopg
import seaborn as sns
import matplotlib.pyplot as plt

print("This is my code change.")
allRecords = []
with psycopg.connect("dbname=bank_failures_test user=jjpowell") as conn:
	with conn.cursor() as cur:
		cur.execute("""
with series as (SELECT
generate_series('2000-01-01', '2023-12-01','1 year'::interval) as timescale)
SELECT
  EXTRACT('YEAR' FROM timescale) as closing_year, 
  COUNT(bank_failures.closing_date) as total_failures  
FROM series LEFT JOIN bank_failures 
on EXTRACT('YEAR' from timescale) = EXTRACT('YEAR' from closing_date)
GROUP BY closing_year
ORDER BY closing_year;
""")
		allRecords = cur.fetchall()
		conn.commit()

# Your data (list of tuples)


# Extract x and y values from the tuples
x_values = [item[0] for item in allRecords]
y_values = [item[1] for item in allRecords]

# Plot the data by year
sns.barplot(x=x_values, y=y_values)

# Add labels to the axes and title to the plot
plt.xlabel('Year')
plt.ylabel('Bank Failures')
plt.title('Bank Failures By Year')

# Show the plot
plt.show()


# TODO: Let's get granular! Plot by month, year
