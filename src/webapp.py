from flask import Flask, g
import sqlite3

# Configuration
DATABASE = 'src/data/messages.db'

app = Flask(__name__)

# Helper function to get a database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

# Clean up db connection after each request
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Frontend route: index
@app.route('/')
def index():
    return "<h1>Welcome to the ActivityBot Dashboard</h1><p>Visit /leaderboard to view leaderboard.</p>"

# Frontend route: leaderboard
@app.route('/leaderboard')
def leaderboard():
    db = get_db()
    try:
        # Updated SQL query to aggregate scores from messages table
        cur = db.execute("""
            SELECT user_id as username, MAX(final_score) as score 
            FROM messages 
            GROUP BY user_id 
            ORDER BY score DESC 
            LIMIT 10
        """)
        entries = cur.fetchall()
    except Exception as e:
        return f"Database error: {e}", 500
    
    html = "<h1>Leaderboard</h1><table border='1' style='border-collapse: collapse;'>\n<tr><th>Username</th><th>Score</th></tr>\n"
    for row in entries:
        html += f"<tr><td>{row['username']}</td><td>{row['score']}</td></tr>\n"
    html += "</table>"
    return html

# New API endpoint for plain text leaderboard
@app.route('/api/leaderboard')
def api_leaderboard():
    db = get_db()
    try:
        cur = db.execute("""
            SELECT user_id as username, MAX(final_score) as score 
            FROM messages 
            GROUP BY user_id 
            ORDER BY score DESC 
            LIMIT 10
        """)
        entries = cur.fetchall()
    except Exception as e:
        return f"Database error: {e}", 500
    
    # Create a plain text representation
    response = "Leaderboard:\n"
    for row in entries:
        response += f"User {row['username']}: {row['score']}\n"
    return response

if __name__ == '__main__':
    # Run the Flask app on port 8000
    app.run(port=8000, debug=False, use_reloader=False)
