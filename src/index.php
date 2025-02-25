<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Leaderboard</title>
    <style>
        table {
            width: 50%;
            margin: 50px auto;
            border-collapse: collapse;
            text-align: left;
        }
        th, td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
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
                    row.innerHTML = `<td>${score.user_id}</td><td>${score.total_score}</td>`;
                    leaderboard.appendChild(row);
                });
            })
            .catch(error => console.error('Error fetching leaderboard:', error));
    </script>
</body>
</html>