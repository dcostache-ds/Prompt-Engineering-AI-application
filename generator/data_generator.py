import re
import json
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

from generator.gemini_client import get_model
from utils.langfuse_client import get_langfuse_client

INJECTION_PATTERNS = [
    r"ignore (previous|all) instructions",
    r"you are now",
    r"forget (everything|your role)",
    r"act as",
    r"jailbreak",
]

def detect_injection(text):
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True, f"Pattern: {pattern}"
    return False, ""

def generate_synthetic_data(ddl_content, user_instructions="", temperature=0.7, max_tokens=8192):
    langfuse = get_langfuse_client()
    is_injection, reason = detect_injection(user_instructions)
    if is_injection:
        raise ValueError(f"Injection detected: {reason}")

    from generator.ddl_parser import parse_ddl
    info = parse_ddl(ddl_content)
    table_names = info["table_names"]

    row_count = 50
    if user_instructions:
        m = re.search(r'(\d+)\s*rows?', user_instructions, re.IGNORECASE)
        if m:
            row_count = int(m.group(1))

    BATCH_SIZE = 25
    dataframes = {}

    with langfuse.start_as_current_observation(
        as_type="span",
        name="data-generation",
        input={"tables": table_names, "row_count": row_count},
    ) as root_obs:
        for table in table_names:
            all_rows = []
            batches = (row_count + BATCH_SIZE - 1) // BATCH_SIZE

            for batch_num in range(batches):
                current_batch = min(BATCH_SIZE, row_count - len(all_rows))
                offset = batch_num * BATCH_SIZE

                prompt = f"""Generate realistic synthetic data for this SQL table.

Rules:
- Generate exactly {current_batch} rows
- Row IDs should start from {offset + 1}
- Respect data types and constraints
- Use realistic data
- 15% null values for nullable columns
- Dates in YYYY-MM-DD format
- Return ONLY valid JSON array: [{{"col": "val"}}, ...]

Full schema for context:
```sql
{ddl_content}
```

Generate data ONLY for table: {table}
"""
                with langfuse.start_as_current_observation(
                    as_type="generation",
                    name=f"generate-{table}-batch-{batch_num+1}",
                    model="gemini-2.0-flash",
                    input={"table": table, "batch": batch_num+1},
                ) as obs:
                    model = get_model()
                    response = model.generate_content(
                        prompt,
                        generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
                    )
                    response_text = response.text
                    obs.update(output=response_text[:500])

                clean_json = re.sub(r'^```json\s*|\s*```$', '', response_text.strip())
                try:
                    rows = json.loads(clean_json)
                    all_rows.extend(rows)
                except json.JSONDecodeError as e:
                    raise ValueError(f"JSON error for table {table} batch {batch_num+1}: {e}")

            dataframes[table] = pd.DataFrame(all_rows)

        root_obs.update(output={"tables_generated": list(dataframes.keys())})

    return dataframes

def apply_textual_edit(df, table_name, instruction):
    langfuse = get_langfuse_client()
    is_injection, reason = detect_injection(instruction)
    if is_injection:
        raise ValueError(f"Injection detected: {reason}")

    current_json = df.to_json(orient='records', indent=2)
    prompt = f"""Modify this data.
Table: {table_name}
Data: {current_json}
Instruction: {instruction}
Return ONLY JSON array, no explanation.
"""

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="data-edit",
        model="gemini-2.0-flash",
        input={"table": table_name, "instruction": instruction},
    ) as obs:
        model = get_model()
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.3, "max_output_tokens": 4096},
        )
        obs.update(output=response.text[:500])

    clean_json = re.sub(r'^```json\s*|\s*```$', '', response.text.strip())
    rows = json.loads(clean_json)
    return pd.DataFrame(rows)