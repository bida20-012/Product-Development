import csv
from flask import Flask, jsonify

app = Flask(__name__)

# Function to read data from CSV
def read_csv_data(filename):
    data = []
    with open(filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data

# Load data on application startup
data = read_csv_data(r"C:\\Users\\bida20-012\\Downloads\\Streamlit\\olympic_web_server_logs.csv")  # Replace with the path to your CSV dataset

# API endpoint to get all data
@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
