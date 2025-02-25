<?php
// Updated Leaderboard endpoint for PHP
// Connect to SQLite database (adjust path and credentials as needed)
try {
    $db = new PDO('sqlite:' . __DIR__ . '/../data/messages.db');
    // Adjust query and table/column names according to your database schema
    $stmt = $db->query('SELECT username, SUM(final_score) as total_score FROM scores GROUP BY username ORDER BY total_score DESC LIMIT 10');
    $leaderboard = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode($leaderboard);
} catch (PDOException $e) {
    http_response_code(500);
    echo 'Database error: ' . $e->getMessage();
    exit;
}
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Leaderboard</title>
    <style>
        body { font-family: Arial, sans-serif; }
        table { border-collapse: collapse; width: 50%; margin: auto; }
        th, td { padding: 8px 12px; border: 1px solid #ccc; text-align: center; }
        th { background-color: #f4f4f4; }
    </style>
</head>
<body>
    <h1 style="text-align: center;">Leaderboard</h1>
    <table>
        <thead>
            <tr>
                <th>User ID</th>
                <th>Total Score</th>
            </tr>
        </thead>
        <tbody id="leaderboard">
            <!-- Scores will be inserted here -->
        </tbody>
    </table>

    <script>
        fetch('leaderboard.php')
            .then(response => response.json())
            .then(data => {
                const leaderboard = document.getElementById('leaderboard');
                data.forEach(score => {
                    const row = document.createElement('tr');
                    row.innerHTML = `<td>${score.username}</td><td>${score.total_score}</td>`;
                    leaderboard.appendChild(row);
                });
            })
            .catch(error => console.error('Error fetching leaderboard:', error));
    </script>
</body>
</html>