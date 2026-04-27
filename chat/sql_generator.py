import os
import re
from dotenv import load_dotenv
load_dotenv()

from generator.gemini_client import get_model
from chat.guardrails import check_off_topic, is_safe_sql
from utils.langfuse_client import get_langfuse_client

def generate_sql(question, ddl_content):
    langfuse = get_langfuse_client()
    is_offtopic, reason = check_off_topic(question)
    if is_offtopic:
        return {"sql": None, "error": "off-topic", "message": f"Question is off-topic ({reason})"}

    prompt = f"""You are a PostgreSQL expert.

Schema:
```sql
{ddl_content}
```

Generate ONLY SELECT query for: {question}

IMPORTANT RULES:
- ONLY SELECT queries
- All table names and column names must be LOWERCASE
- Use table aliases
- Include GROUP BY for aggregations
"""

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="sql-generation",
        input={"question": question},
    ) as obs:
        model = get_model()
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 2048},
        )
        response_text = response.text
        obs.update(output=response_text, model="gemini-2.0-flash")

    sql_match = re.search(r'```sql\s*(.*?)\s*```', response_text, re.DOTALL)
    sql_query = sql_match.group(1).strip() if sql_match else response_text.strip()

    is_safe, msg = is_safe_sql(sql_query)
    if not is_safe:
        return {"sql": sql_query, "error": "unsafe-sql", "message": f"Security error: {msg}"}

    return {"sql": sql_query, "error": None, "message": "OK"}