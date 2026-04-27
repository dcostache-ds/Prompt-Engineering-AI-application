import re

OFF_TOPIC_PATTERNS = [
    r"write (me )?(a |an )?(poem|story|song)",
    r"what is (your name|the meaning of life)",
    r"recipe|weather|sports|news|stock",
    r"how to (cook|fix|repair)",
]

def check_off_topic(question):
    text_lower = question.lower()
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, text_lower):
            return True, f"Pattern: {pattern}"
    return False, ""

ALLOWED_SQL = ["SELECT", "WITH"]

def is_safe_sql(sql):
    sql_upper = sql.strip().upper()
    for keyword in ALLOWED_SQL:
        if sql_upper.startswith(keyword):
            return True, ""
    return False, f"SQL must start with {ALLOWED_SQL}"
