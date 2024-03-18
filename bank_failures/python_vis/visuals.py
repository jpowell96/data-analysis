import psycopg
import seaborn as sns
import matplotlib.pyplot as plt

allRecords = []
with psycopg.connect("dbname=bank_failures_test user=jjpowell") as conn:
	with conn.cursor() as cur:
		cur.execute("""
with years AS(
SELECT DATE_TRUNC('year', timescale) as year FROM 
generate_series('2000-01-01', '2023-12-01','1 year'::interval) as
timescale)
select extract( 'year' from years.year), COUNT(bf.closing_date) as bank_failures
from years left join bank_failures bf 
on years.year = DATE_TRUNC('year', bf.closing_date)
group by year
order by year asc;
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
