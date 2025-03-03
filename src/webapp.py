from flask import Flask, render_template_string, request, g
import sqlite3
import pandas as pd
import os
from utils.db import Database  # Use the Database class from utils/db.py

app = Flask(__name__)

# Create a global Database instance
db_instance = Database()

# HTML template for leaderboard
template = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Leaderboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
            color: #333;
        }
        .container {
            width: 80%;
            margin: 20px auto;
            background: white;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        h1, h2 {
            color: #444;
        }
        .section {
            margin-bottom: 20px;
        }
        .highlight {
            font-weight: bold;
            color: #007BFF;
        }
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .stats-table th, .stats-table td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        .stats-table th {
            background-color: #007BFF;
            color: white;
        }
        .input-form {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>Leaderboard</h1>
        
        <div class=\"section\">
            <h2 class=\"highlight\">Top Performers</h2>
            <form class=\"input-form\" method=\"get\" action=\"/\">
                <label for=\"limit\">Number of users to show:</label>
                <input type=\"number\" id=\"limit\" name=\"limit\" min=\"1\" value=\"{{ limit }}\">
                <button type=\"submit\">Update</button>
            </form>
            <table class=\"stats-table\">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>User</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    {% for index, row in data.iterrows() %}
                    <tr>
                        <td>{{ index + 1 }}</td>
                        <td>{{ row['username'] }}</td>
                        <td>{{ row['score'] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

# Frontend route to display leaderboard
@app.route('/')
def index():
    limit = request.args.get('limit', default=10, type=int)
    conn = db_instance.get_db_connection()
    try:
        cur = conn.execute(f"""
            SELECT u.username, MAX(m.final_score) as score
            FROM messages m
            JOIN users u ON m.user_id = u.id
            GROUP BY u.username
            ORDER BY score DESC
            LIMIT {limit}
        """)
        entries = cur.fetchall()
    except Exception as e:
        return f"Database error: {e}", 500
    finally:
        conn.close()
    
    # Convert sqlite3.Row objects to a list of dicts and then to a DataFrame
    data_list = [dict(row) for row in entries]
    df = pd.DataFrame(data_list)
    if df.empty:
        # Create empty columns if no data returned
        df = pd.DataFrame(columns=['username', 'score'])
    return render_template_string(template, data=df, limit=limit)

@app.route('/leaderboard')
def leaderboard():
    limit = request.args.get('limit', default=10, type=int)
    conn = db_instance.get_db_connection()
    try:
        cur = conn.execute(f"""
            SELECT u.username, MAX(m.final_score) as score
            FROM messages m
            JOIN users u ON m.user_id = u.id
            GROUP BY u.username
            ORDER BY score DESC
            LIMIT {limit}
        """)
        entries = cur.fetchall()
    except Exception as e:
        return f"Database error: {e}", 500
    finally:
        conn.close()
    
    # Convert sqlite3.Row objects to a list of dicts and then to a DataFrame
    data_list = [dict(row) for row in entries]
    df = pd.DataFrame(data_list)
    if df.empty:
        # Create empty columns if no data returned
        df = pd.DataFrame(columns=['username', 'score'])
    return df.to_string(index=False)

if __name__ == '__main__':
    # Run the Flask app on port 8000
    app.run(port=8000, debug=True, use_reloader=False)
