CREATE TABLE active (
    group_id INTEGER,
    group_title TEXT,
    group_link TEXT,
    user_id INTEGER,
    user_name TEXT,
    msg_id INTEGER,
    msg_length INTEGER,
    msg_text TEXT,
	date_time DATETIME DEFAULT CURRENT_TIMESTAMP
)