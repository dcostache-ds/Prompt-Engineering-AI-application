import io
import os
import re
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
load_dotenv()

from generator.gemini_client import get_model
from utils.langfuse_client import get_langfuse_client

def generate_chart_if_needed(question, df):
    langfuse = get_langfuse_client()
    wants_chart = any(kw in question.lower() for kw in ["plot", "chart", "graph", "bar", "visualiz"])

    if not wants_chart or df.empty:
        return None

    columns_info = df.dtypes.to_dict()
    sample = df.head(5).to_dict(orient='records')

    prompt = f"""Generate Seaborn code for this data.
Request: {question}
Columns: {columns_info}
Sample: {sample}
Requirements:
- Use seaborn as sns, matplotlib.pyplot as plt
- DataFrame is named df
- Use fig, ax = plt.subplots(figsize=(10, 5))
- Add title and labels
- Use plt.tight_layout()
- No plt.show()
Return ONLY Python code.
"""

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="chart-gen",
        model="gemini-2.0-flash",
        input={"question": question},
    ) as obs:
        model = get_model()
        response = model.generate_content(prompt, generation_config={"temperature": 0.2, "max_output_tokens": 1024})
        obs.update(output=response.text[:500])

    code = re.sub(r'^```python\s*|\s*```$', '', response.text.strip())
    local_vars = {"df": df, "sns": sns, "plt": plt, "pd": pd}
    exec(code, local_vars)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close("all")
    buf.seek(0)
    return buf.read()