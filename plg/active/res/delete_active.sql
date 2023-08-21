DELETE FROM active
WHERE date_time <= date('now', '-? day')