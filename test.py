import matplotlib.pyplot as plt

# Assuming 'data' is a pandas DataFrame obtained from the SQL query execution
plt.figure(figsize=(10, 6))
plt.bar(data['training_program'], data['frequency'], color='skyblue')
plt.xlabel('Training Program')
plt.ylabel('Frequency')
plt.title('Most Common Training Paths')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()