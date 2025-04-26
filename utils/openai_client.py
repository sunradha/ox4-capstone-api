import os
import openai
import re

openai.api_key = os.getenv("OPENAI_API_KEY")


# Step 1: Classify Reasoning Type (NO schemas needed here)
def classify_reasoning_and_intent(question):
    prompt = f"""
You are an expert reasoning and visualization assistant.

Given this question:
\"{question}\"

Classify:
1. Reasoning Type (choose one from):
[Deductive, Inductive, Abductive, Causal, Counterfactual, Multi-Hop, Temporal, Probabilistic, Analogical, Ethical, Spatial, Scientific, Commonsense, Planning, Legal, Multi-Agent, Metacognitive]

2. Intent (choose one from):
[knowledge_graph, causal_graph, process_flow, trend_analysis, comparative, ranking, probabilistic, compliance_check, text_summary]

--- IMPORTANT GUIDELINES ---
- Reasoning Type = Choose based on the logical structure of the question.
- Intent = Choose based on the most meaningful way to represent or visualize the answer.

--- INTENT DECISION RULES ---
1. If the question involves **multiple entity types connected through relationships** (such as JOINs between tables like occupations, automation risk, participation, industries), prefer `knowledge_graph` — EVEN IF the question mentions 'highest', 'lowest', or 'compare'.
   Example: "Which occupations at high risk of automation show the lowest participation in reskilling programs?" → knowledge_graph ✅
2. If the question is purely about **ranking one entity by a metric** (no multi-entity relationships), use `comparative` or `ranking`.
   Example: "Compare success rates of different training programs." → comparative ✅
3. If the question asks about **cause and effect**, use `causal_graph`.
4. If the question asks about **time-based sequences or progressions**, use `process_flow` or `trend_analysis`.
5. If the question involves **compliance, fairness, legal, or policy**, use `compliance_check`, even if phrased causally.
6. Use `probabilistic` if the focus is on **likelihood, uncertainty, or risk estimation**.
7. Use `text_summary` if the question clearly requests **explanations, summaries, or textual analysis** without visualization.

--- OUTPUT FORMAT ---
Reply ONLY in the following exact format:

Reasoning Type: <your selected reasoning type>
Intent: <your selected intent>
Reasoning Justification: <one sentence explanation for the reasoning type>
Intent Justification: <one sentence explanation for the intent selection>
"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response['choices'][0]['message']['content'].strip()


# Step 2: Generate SQL + Plot Code (Schemas needed here)
def generate_sql_and_plot_code(schemas, question, reasoning_type):
    prompt = f"""
You are an assistant generating SQL queries and Python plotting code based on the reasoning type.

Reasoning Type: {reasoning_type}
Schemas (use ONLY the tables and columns listed below — do NOT invent new table names):
{schemas}

User Question: "{question}"

⚠️ Important Rules:
- ONLY use the table names and columns provided in the schemas above.
- The SQL MUST be compatible with PostgreSQL dialect.
- When using aggregation functions:
  - Always specify the delimiter in STRING_AGG.
  - PostgreSQL syntax for STRING_AGG is: STRING_AGG(expression, ', ' ORDER BY column).
  - Do NOT use MySQL-specific or SQL Server-specific syntax.
- When calculating the time difference between two dates:
  - Subtract the dates to get the number of days: `end_date::date - start_date::date`.
  - To convert the difference into seconds (epoch time), multiply the result by `INTERVAL '1 day'`.
  - Example: `EXTRACT(EPOCH FROM (end_date::date - start_date::date) * INTERVAL '1 day')`.
  - Do NOT use `EXTRACT(EPOCH FROM integer)` directly.
- When using the ROUND() function:
  - PostgreSQL allows two arguments in ROUND(value, decimal_places) only if `value` is of type `numeric`.
  - If the value is a `double precision` (e.g., result of AVG(), or COUNT()/COUNT()), cast it to `numeric` before rounding.
  - Example: `ROUND(AVG(column_name)::numeric, 2)`.
  - When dividing aggregate counts (like `COUNT() / COUNT()`), always cast either the numerator or the denominator to `numeric`.
  - Example: `ROUND((COUNT(*) FILTER (WHERE condition))::numeric / NULLIF(COUNT(*), 0), 2)`.
  - Always handle potential division by zero safely using `NULLIF(denominator, 0)`.
  - Do NOT use ROUND(double precision, integer) directly — always cast to numeric first.
- If filtering or aggregating on boolean columns like `certification_earned`, always confirm whether the column is BOOLEAN or TEXT:
  - If BOOLEAN, use `WHERE certification_earned = TRUE`.
  - If TEXT (e.g., values like 'Yes'/'No' or 'TRUE'/'FALSE'), use `WHERE certification_earned::text ILIKE 'true' OR certification_earned::text ILIKE 'yes'`.
  - Always handle both BOOLEAN and TEXT scenarios safely.
- If the required data is not available in the given schemas, clearly mention that in the reasoning explanation.
- Do not assume any additional columns unless explicitly present in the schema.

⚡ Python Plotting Code Rules:
- Always set an appropriate figure size using `plt.figure(figsize=(10, 12))` for vertical bar plots with many labels.
- For horizontal bar charts (`barh`), reduce Y-axis label font size using `plt.yticks(fontsize=8)`.
- Always use `plt.tight_layout()` to avoid overlapping labels.
- Rotate labels or limit the number of labels if the number of categories is large.
- If the number of categories (rows) is large (e.g., more than 50), always limit the plot to the **top 20 or top 30** entries based on the main metric (e.g., success rate, count, average duration, etc.) to ensure readability.
- Example code:
```python
import matplotlib.pyplot as plt

top_n = 30  # Limit the number of rows to avoid clutter
data_sorted = data.sort_values('success_rate').tail(top_n)

plt.figure(figsize=(10, 12))
plt.barh(data_sorted['training_program'], data_sorted['success_rate'], color='skyblue')
plt.xlabel('Success Rate')
plt.title('Success Rate of Training Programs by Job Role')
plt.yticks(fontsize=8)
plt.tight_layout()
plt.show()
```

Provide your response in the following exact format:

1. Reasoning Explanation:
<Your explanation here>

2. SQL Query:
```sql
<Write the SQL query here>
```

3. Python Plotting Code:
```python
<Write Python plotting code here, assume SQL result is in a pandas DataFrame named 'data'>
```

ONLY follow this exact format. Do not add extra comments outside the required structure.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response['choices'][0]['message']['content']


# Step 3: Regenerate plot code if columns mismatch
def regenerate_plot_code_from_columns(columns, question):
    prompt = f"""
The user asked: "{question}"

The SQL query returned the following DataFrame columns: {columns}.

Write Python plotting code (matplotlib) that best visualizes this data. Assume the DataFrame is called `data`. 
Return only the Python code inside a Python code block.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    code_match = re.search(r"```python\n(.*?)```", response['choices'][0]['message']['content'], re.DOTALL)
    return code_match.group(1).strip() if code_match else None


# Step 4: Parse Reasoning Explanation, SQL, and Python Code
# Step 4: Parse Reasoning Explanation, SQL, and Python Code
def parse_llm_response(response_text, reasoning_type):
    reasoning_match = re.search(r"1\. Reasoning(?: Explanation)?:\s*(.*?)\n2\.", response_text, re.DOTALL)
    sql_match = re.search(r"2\. SQL(?: Query)?:\s*```sql\n(.*?)```", response_text, re.DOTALL)
    python_match = re.search(r"3\. Python(?: Plotting Code)?:\s*```python\n(.*?)```", response_text, re.DOTALL)

    reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
    sql_query = sql_match.group(1).strip() if sql_match else None
    python_code = python_match.group(1).strip() if python_match else None

    # Prepare JSON response based on availability of SQL and Plot Code
    if not sql_query or not python_code:
        return {
            "reasoning_type": reasoning_type,
            "reasoning_explanation": reasoning
        }
    else:
        return {
            "reasoning_type": reasoning_type,
            "reasoning_explanation": reasoning,
            "generated_sql": sql_query,
            "generated_plot_code": python_code
        }
