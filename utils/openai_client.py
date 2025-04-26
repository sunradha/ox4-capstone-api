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
[Deductive, Inductive, Abductive, Causal, Counterfactual, Multi-Hop, Temporal, Probabilistic, Analogical, Ethical, 
    Spatial, Scientific, Commonsense, Planning, Legal, Multi-Agent, Metacognitive]

2. Intent (choose one from):
[knowledge_graph, causal_graph, process_flow, trend_analysis, comparative, ranking, probabilistic, compliance_check, 
    text_summary]

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


def generate_sql_and_plot_code(schemas, question, reasoning_type, intent):
    if intent == "knowledge_graph":
        prompt = knowledge_graph_sql_prompt(schemas, question, reasoning_type)
    elif intent == "causal_graph":
        prompt = causal_graph_sql_prompt(schemas, question, reasoning_type)
    else:
        prompt = general_sql_prompt(schemas, question, reasoning_type)

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response['choices'][0]['message']['content'].strip()


# Step 2: Generate SQL + Plot Code (Schemas needed here)
def generate_sql_and_plot_code1(schemas, question, reasoning_type):
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


# General Prompt for most intents (bar charts, trend, comparative, etc.)
def general_sql_prompt(schemas, question, reasoning_type):
    return f"""
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


# Dedicated Prompt for Knowledge Graph
def knowledge_graph_sql_prompt(schemas, question, reasoning_type):
    return f"""
You are an assistant generating SQL queries and Knowledge Graph construction logic based on the reasoning type.

Reasoning Type: {reasoning_type}
Schemas (use ONLY the tables and columns listed below — do NOT invent new table names):
{schemas}

User Question: "{question}"

⚠️ --- CRITICAL INSTRUCTIONS FOR KNOWLEDGE GRAPH GENERATION --- ⚠️
1. Define a Knowledge Graph with:
    - Nodes (entity types)
    - Edges (relationships between entity types)
2. Clearly specify which columns are used as:
    - NODES (e.g., job_title, automation_probability, etc.)
    - EDGES (source and target column pairs with their relationship label)

⚡ IMPORTANT SQL GENERATION RULES:
- ✅ Include **ALL columns used in the Nodes and Edges schema** directly in the SELECT clause of the SQL query.
- ✅ Do not omit any columns that are required for constructing the Knowledge Graph.
- ✅ Use DISTINCT if necessary to avoid duplicate relationships.
- ✅ The SQL MUST use PostgreSQL syntax.
- ❌ Do NOT invent table names or column names that are not present in the provided schemas.
- ⚠️ Do NOT use LIMIT clauses unless the user specifically asks for a fixed number of results.
- ✅ Include WHERE conditions (such as `automation_probability > 0.65`) only if relevant to the question, but do NOT artificially limit the number of rows.
- ⚠️ If a required column is not present in the schema, clearly mention this in the Reasoning Explanation.

🎯 Example of correct behavior:
If your Nodes are defined as:
    - job_title: Occupation
    - automation_probability: Risk
Then your SQL should SELECT both `job_title` and `automation_probability` explicitly.

If your Edges are:
    - source: job_title
    - target: automation_probability
    - relationship: has automation risk
Then both `job_title` and `automation_probability` MUST appear in the SQL result.

⚠️ Do not proceed with graph schema definitions if these columns are not included in the SQL.

Provide your response in the following exact format:

1. Reasoning Explanation:
<Explain the reasoning and how entities and relationships are derived from the SQL result>

2. SQL Query:
```sql
<SQL query to fetch data — must include all node and edge columns>
```

3. Knowledge Graph Schema:
Nodes:
- <column_name>: <entity_type>
Edges:
- source: <source_column>, target: <target_column>, relationship: <relationship_label>

ONLY follow this exact format. Do not add extra comments outside the required structure.
"""


# Dedicated Prompt for Causal Graph
def causal_graph_sql_prompt(schemas, question, reasoning_type):
    return f"""
You are an assistant generating SQL queries and Causal Graph construction logic based on the reasoning type.

Reasoning Type: {reasoning_type}
Schemas (use ONLY the tables and columns listed below — do NOT invent new table names):
{schemas}

User Question: "{question}"

⚠️ Instructions for Causal Graph:
- Generate the SQL query to collect the necessary columns for cause-effect relationships.
- Identify the CAUSE columns and the EFFECT columns.
- Specify the causal relationship label (e.g., "causes", "influences", "leads to").
- Provide the Causal Graph schema clearly.

Provide your response in the following exact format:

1. Reasoning Explanation:
<Explain the reasoning and how cause-effect relationships are derived from the SQL result>

2. SQL Query:
```sql
<SQL query to fetch data>
```

3. Causal Graph Schema:
Cause Nodes:
- <column_name>: <cause_type>
Effect Nodes:
- <column_name>: <effect_type>
Causal Edges:
- source: <cause_column>
  target: <effect_column>
  relationship: "causes" or other appropriate label

ONLY follow this exact format. Do not add extra comments outside the required structure.
"""


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
def parse_llm_response(response_text, reasoning_type, intent):
    reasoning_match = re.search(r"1\. Reasoning(?: Explanation)?:\s*(.*?)\n2\.", response_text, re.DOTALL)
    sql_match = re.search(r"2\.\s*SQL.*?```sql\n(.*?)```", response_text, re.DOTALL)

    reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
    sql_query = sql_match.group(1).strip() if sql_match else None

    if intent == "knowledge_graph":
        nodes_section = re.search(r"Nodes:\s*(.*?)\nEdges:", response_text, re.DOTALL)
        edges_section = re.search(r"Edges:\s*(.*)", response_text, re.DOTALL)
        return {
            "reasoning_type": reasoning_type,
            "reasoning_explanation": reasoning,
            "generated_sql": sql_query,
            "graph_schema": {
                "nodes": nodes_section.group(1).strip() if nodes_section else None,
                "edges": edges_section.group(1).strip() if edges_section else None
            }
        }

    elif intent == "causal_graph":
        cause_nodes = re.search(r"Cause Nodes:\s*(.*?)\nEffect Nodes:", response_text, re.DOTALL)
        effect_nodes = re.search(r"Effect Nodes:\s*(.*?)\nCausal Edges:", response_text, re.DOTALL)
        causal_edges = re.search(r"Causal Edges:\s*(.*)", response_text, re.DOTALL)
        return {
            "reasoning_type": reasoning_type,
            "reasoning_explanation": reasoning,
            "generated_sql": sql_query,
            "graph_schema": {
                "cause_nodes": cause_nodes.group(1).strip() if cause_nodes else None,
                "effect_nodes": effect_nodes.group(1).strip() if effect_nodes else None,
                "causal_edges": causal_edges.group(1).strip() if causal_edges else None
            }
        }

    else:
        python_match = re.search(r"3\. Python(?: Plotting Code)?:\s*```python\n(.*?)```", response_text, re.DOTALL)
        python_code = python_match.group(1).strip() if python_match else None

        return {
            "reasoning_type": reasoning_type,
            "reasoning_explanation": reasoning,
            "generated_sql": sql_query,
            "generated_plot_code": python_code
        }
