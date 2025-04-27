import logging
import os
import openai
import re
import textwrap

openai.api_key = os.getenv("OPENAI_API_KEY")


def classify_reasoning_and_intent(question):
    prompt = textwrap.dedent(f"""
    You are an expert reasoning and visualization assistant.

    Given this question:
    \"{question}\"

    Classify:
    1. Reasoning Type (choose one from):
    [Deductive, Inductive, Abductive, Causal, Counterfactual, Multi-Hop, Temporal, Probabilistic, Analogical, Ethical, 
        Spatial, Scientific, Commonsense, Planning, Legal, Multi-Agent, Metacognitive]
    
    2. Intent (choose one from):
    [Knowledge Graph, Causal Graph, Process Mining, Time Series Analysis, Comparative, Ranking, 
        Probabilistic, Compliance Check, Text Summary, Scenario Modeling, Decision Matrix]
    
    --- IMPORTANT GUIDELINES ---
    - Reasoning Type = Choose based on the logical structure of the question.
    - Intent = Choose based on the most meaningful way to represent or visualize the answer.
    
    --- INTENT DECISION RULES ---
    1. Use **Knowledge Graph** ONLY if the question involves **explicit multi-entity relationships or joins** between different entity types (such as occupations, automation risk, participation, industries) **AND** you are more than 90% certain this is the best visual format.
    2. Use **Causal Graph** ONLY if the question directly asks about **cause-effect relationships** and you are more than 90% certain that causal modeling applies. If there is uncertainty, fall back to other intent types like `comparative`, `ranking`, `scenario modeling`, or `process mining`.
    3. Use **Scenario Modeling** when the question involves **what-if scenarios, counterfactual reasoning, or exploring alternate possibilities**.
    4. Use **Decision Matrix / Action Plan** if the question requires **ethical reasoning, trade-off evaluation, or planning decisions with multiple criteria**.
    5. If the question is about **ranking or comparison** across single or multiple dimensions but lacks clear relational structure, prefer `comparative` or `ranking`.
    6. If the question asks about **time-based sequences or progressions**, use `process mining / process flow` or `trend / time series analysis`. Choose **process mining / process flow** for **workflow analysis** and **trend / time series analysis** for **metric changes over time**.
    7. For questions related to **compliance, fairness, legal, or policy evaluation**, select `compliance check` even if they mention causality.
    8. Choose `probabilistic` when the question focuses on **likelihood, uncertainty, risk estimation, or prediction**.
    9. Use `text summary` if the question explicitly requests **explanations, summaries, or narrative answers** without requiring structured visualization.
    
    --- CHECK CONFIDENCE ---
    - If unsure whether the intent is `Knowledge Graph` or `Causal Graph`, assess confidence.
    - ONLY select these if confidence is **greater than 90-95%**.
    - Otherwise, choose the next best intent that matches the data structure and query goal.
    
    --- OUTPUT FORMAT ---
    Reply ONLY in the following exact format:
    
    Reasoning Type: <your selected reasoning type>
    Intent: <your selected intent>
    Reasoning Justification: <one sentence explanation for the reasoning type>
    Intent Justification: <one sentence explanation for the intent selection>
    """)

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response['choices'][0]['message']['content'].strip()


def generate_sql_and_plot_code(schemas, question, reasoning_type, intent):
    if intent == "Knowledge Graph":
        prompt = knowledge_graph_sql_prompt(schemas, question, reasoning_type)
    elif intent == "Causal Graph":
        prompt = causal_graph_sql_prompt(schemas, question, reasoning_type)
    else:
        prompt = general_sql_prompt(schemas, question, reasoning_type, intent)

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response['choices'][0]['message']['content'].strip()


# General Prompt for most intents (bar charts, trend, comparative, etc.)
def general_sql_prompt(schemas, question, reasoning_type, intent):
    return f"""
You are an assistant generating SQL queries and Python plotting code based on the reasoning type and intent.

Reasoning Type: {reasoning_type}
Intent: {intent}
Schemas (use ONLY the tables and columns listed below — do NOT invent new table names):
{schemas}

User Question: "{question}"

⚡ --- IMPORTANT SQL GENERATION RULES (MUST FOLLOW) --- ⚡
- ONLY use the table names and columns provided in the schemas above.
- The SQL MUST be compatible with PostgreSQL dialect.
- When using aggregation functions:
  - Always specify the delimiter in STRING_AGG.
  - PostgreSQL syntax for STRING_AGG is: STRING_AGG(expression, ', ' ORDER BY column).
  - DO NOT use aggregate functions (like STRING_AGG, SUM, AVG, COUNT, etc.) inside the GROUP BY clause — they belong in the SELECT list.
  - Columns listed in the SELECT clause that are NOT part of aggregate functions MUST be included in GROUP BY.
  - **NEW RULE:** NEVER put aggregate functions inside the GROUP BY clause.
  - **Always group by the non-aggregated selected columns only.**
  - ✅ **MANDATORY SQL GENERATION STEPS:**
    1. Identify ALL columns used in the SELECT clause.
    2. For each column, classify it as:
        - Aggregated (e.g., inside STRING_AGG, COUNT, AVG, SUM, etc.)
        - Non-aggregated (direct columns without aggregation).
    3. ONLY include the non-aggregated columns in the GROUP BY clause.
    4. NEVER include any aggregate function (like STRING_AGG, COUNT, etc.) in the GROUP BY clause.
  - **If STRING_AGG or similar sequence-based aggregation is applied, use a subquery or CTE (WITH clause) to generate sequences grouped by IDs (such as case_id), and then apply further aggregation on top of that result. DO NOT directly use STRING_AGG in the outer GROUP BY.**
  - ✅ **ALWAYS QUALIFY COLUMN NAMES WITH TABLE ALIASES (e.g., wrc.case_id, wre.activity) when joining tables, especially if the same column name exists in multiple tables. Do NOT use unqualified column names.**
  - ✅ Example:
    ```sql
    WITH activity_sequences AS (
        SELECT
            wrc.case_id,
            STRING_AGG(wre.activity, ', ' ORDER BY wre.timestamp) AS sequence,
            wrc.certification_earned
        FROM
            workforce_reskilling_events wre
        JOIN
            workforce_reskilling_cases wrc ON wre.case_id = wrc.case_id
        GROUP BY
            wrc.case_id, wrc.certification_earned
    )
    SELECT
        sequence,
        COUNT(*) FILTER (WHERE certification_earned = TRUE) AS certifications_earned,
        COUNT(*) AS total_cases,
        ROUND((COUNT(*) FILTER (WHERE certification_earned = TRUE))::numeric / NULLIF(COUNT(*), 0), 2) AS certification_rate
    FROM
        activity_sequences
    GROUP BY
        sequence;
    ```
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

⚡ Python Plotting Code Rules: (MUST FOLLOW) --- ⚡
- Always select the **most appropriate plot type** based on the `Intent` and nature of the data:
  - `Trend / Time Series Analysis`: line chart, area chart, or bar plot.
  - `Comparative` or `Ranking`: bar plot, horizontal bar (`barh`), or pie chart.
  - `Probabilistic`: bar plot, density plot, violin plot, or histogram.
  - `Compliance Check`: bar plot, stacked bar chart, or heatmap.
  - `Process Mining / Process Flow`: gantt chart, sankey diagram, or process flow diagram.
  - `Scenario Modeling`: stacked bar chart, comparative bar chart, or spider/radar chart.
  - `Decision Matrix / Action Plan`: heatmap, color-coded tables, or spider charts.
  - `Text Summary`: no plotting required — return only text.
- **DO NOT limit the number of rows by default**. Only apply row limiting (e.g., top N) if the data volume will likely clutter the graph or make labels unreadable (e.g., more than 50 categories).
- **If the number of rows (categories) exceeds 50, ALWAYS sort by the main metric (e.g., certification_rate or count) and select the top 30 rows for clarity. Provide reasoning in the explanation for why limiting was applied to improve readability.**
- Adjust plot settings (like font size, figure size, label rotation) to ensure readability.
- Example code for limiting (if needed, based on clutter):
```python
if len(data) > 50:
    data_sorted = data.sort_values('main_metric_column', ascending=False).head(30)
else:
    data_sorted = data.sort_values('main_metric_column', ascending=False)
```

Based on the provided `Schemas`, `Reasoning Type`, `Intent`, and `User Question`, perform the following actions:

1. Analyze the User Question carefully and provide a clear reasoning explanation for the approach.
2. Generate the correct SQL query following all the SQL generation rules and relationship constraints listed above.
3. Generate the corresponding Python plotting code (assuming the SQL result is in a pandas DataFrame named 'data'), and strictly apply the plotting rules for clutter prevention, readability, and limiting logic.

⚠️ DO NOT skip any of these steps. You MUST provide all three outputs as specified below.

Provide your response in the following exact format:

1. Reasoning Answer:
<Your explanation here>

2. SQL Query:
```sql
<Write the SQL query here>
```

3. Python Plotting Code:
```python
<Write Python plotting code here, assume SQL result is in a pandas DataFrame named 'data'>
```
"""


# Dedicated Prompt for Knowledge Graph
def knowledge_graph_sql_prompt(schemas, question, reasoning_type):
    return f"""
You are an assistant generating SQL queries and Knowledge Graph construction logic based on the reasoning type.

Reasoning Type: {reasoning_type}
Schemas Definitions and Relationships (use ONLY the tables and columns listed below — do NOT invent new table names):
{schemas}

User Question: "{question}"

⚠️ --- CRITICAL INSTRUCTIONS FOR KNOWLEDGE GRAPH GENERATION --- ⚠️

1. Define a Knowledge Graph with:
   - Nodes (entity types)
   - Edges (relationships between entity types)
2. Clearly specify which columns are used as:
   - NODES (e.g., job_title, automation_probability, etc.)
   - EDGES (source and target column pairs with their relationship label)

⚡ --- IMPORTANT SQL GENERATION RULES (MUST FOLLOW) --- ⚡
✅ SELECT only from the provided schemas. Do **NOT** create or assume extra tables or columns.
✅ Always SELECT **ALL columns** that are part of the Nodes and Edges definition — no exceptions.
✅ Use proper JOINs (INNER JOIN / LEFT JOIN) explicitly based on foreign key relationships where needed — never use Cartesian joins.
✅ Always qualify column names with their table aliases to avoid ambiguity.
✅ Use DISTINCT if needed to avoid duplicate rows in the final output, especially for edges in the graph.
✅ If aggregation (e.g., COUNT, SUM, AVG) is necessary, use GROUP BY properly and ensure the grouping aligns with the graph entities.
✅ WHERE clauses should only reflect relevant business rules or constraints from the question — do not artificially filter or limit unless explicitly requested.
✅ The SQL MUST be valid PostgreSQL syntax.
❌ Do NOT use LIMIT clauses unless the question specifically asks for a fixed number of results.
✅ If subqueries are required to filter or join data meaningfully, use them appropriately and explain their purpose in the Reasoning Answer.
⚠️ If any required column is missing from the schema, clearly mention this in the Reasoning Answer and suggest alternative columns if possible.

🎨 --- KNOWLEDGE GRAPH ALIGNMENT RULES --- 🎨

- Ensure that **every column used for Nodes and Edges** is included in the SQL SELECT clause.
- Do NOT proceed with the Knowledge Graph schema definition unless the SQL query fully supports the graph structure.
- The graph relationships (Edges) must directly map to the result of the SQL query.

🔎 --- OUTPUT FORMAT (STRICTLY FOLLOW THIS FORMAT) --- 🔎

1. Reasoning Answer:
   <Explain the reasoning behind the query, how entities (nodes) and relationships (edges) are derived from the SQL result, and how this supports the Knowledge Graph structure. Mention any join logic or key assumptions.>

2. SQL Query:
```sql
<SQL query to fetch the required data — include all node and edge columns explicitly>
```

3. Knowledge Graph Schema:
Nodes:
- <column_name>: <entity_type>
Edges:
- source: <source_column>, target: <target_column>, relationship: <relationship_label>
"""


# Dedicated Prompt for Causal Graph
def causal_graph_sql_prompt(schemas, question, reasoning_type):
    return f"""
You are an assistant generating SQL queries and Causal Graph construction logic based on the reasoning type.

Reasoning Type: {reasoning_type}
Schemas Definitions and Relationships (use ONLY the tables and columns listed below — do NOT invent new table names):
{schemas}

User Question: "{question}"

⚠️ --- CRITICAL INSTRUCTIONS FOR CAUSAL GRAPH GENERATION --- ⚠️

1. Generate the SQL query to collect the necessary columns for cause-effect relationships.
2. Identify the CAUSE columns and the EFFECT columns.
3. Specify the causal relationship label (e.g., "causes", "influences", "leads to").
4. Provide the Causal Graph schema clearly.

⚡ --- IMPORTANT SQL GENERATION RULES (MUST FOLLOW) --- ⚡
✅ SELECT only from the provided schemas. Do **NOT** create or assume extra tables or columns.
✅ Always SELECT **ALL columns** that are part of the Cause and Effect schema — no exceptions.
✅ Use proper JOINs (INNER JOIN / LEFT JOIN) explicitly based on foreign key relationships where needed — never use Cartesian joins.
✅ Always qualify column names with their table aliases to avoid ambiguity.
✅ Use DISTINCT if needed to avoid duplicate rows in the final output, especially for causal relationships.
✅ If aggregation (e.g., COUNT, SUM, AVG) is necessary, use GROUP BY properly and ensure the grouping aligns with the causal entities.
✅ WHERE clauses should only reflect relevant business rules or constraints from the question — do not artificially filter or limit unless explicitly requested.
✅ The SQL MUST be valid PostgreSQL syntax.
❌ Do NOT use LIMIT clauses unless the question specifically asks for a fixed number of results.
✅ If subqueries are required to filter or join data meaningfully, use them appropriately and explain their purpose in the Reasoning Answer.
⚠️ If any required column is missing from the schema, clearly mention this in the Reasoning Answer and suggest alternative columns if possible.

🎯 --- CAUSAL GRAPH ALIGNMENT RULES --- 🎯

- Ensure that **every column used for Cause and Effect nodes** is included in the SQL SELECT clause.
- Do NOT proceed with the Causal Graph schema definition unless the SQL query fully supports the graph structure.
- The causal relationships (edges) must directly map to the result of the SQL query.

🔎 --- OUTPUT FORMAT (STRICTLY FOLLOW THIS FORMAT) --- 🔎

1. Reasoning Answer:
   <Explain the reasoning behind the query, how cause-effect relationships are derived from the SQL result, and how this supports the Causal Graph structure. Mention any join logic, key assumptions, or constraints.>

2. SQL Query:
```sql
<SQL query to fetch the required data — include all cause and effect columns explicitly>
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


def parse_llm_response(response_text, reasoning_type, intent):
    # Parse Reasoning Answer
    reasoning_match = re.search(
        r"1[\.\):\-]?\s*Reasoning(?: Answer)?:\s*(.*?)(?:\n\s*2[\.\):\-])",
        response_text,
        re.DOTALL | re.IGNORECASE
    )

    reasoning_answer = reasoning_match.group(1).strip() if reasoning_match else ""

    # Parse SQL Query
    sql_match = re.search(r"2\.\s*SQL.*?```sql\n(.*?)```", response_text, re.DOTALL)
    sql_query = sql_match.group(1).strip() if sql_match else None

    # Knowledge Graph Parsing
    if intent.lower() == "knowledge graph":
        logging.info("Generating Knowledge Graph Queries")
        nodes_section = re.search(r"Nodes:\s*(.*?)(?:\nEdges:|\Z)", response_text, re.DOTALL)
        edges_section = re.search(r"Edges:\s*(.*?)(?:\n[A-Z]|\\Z)", response_text, re.DOTALL)

        return {
            "reasoning_answer": reasoning_answer,
            "generated_sql": sql_query,
            "graph_schema": {
                "nodes": nodes_section.group(1).strip() if nodes_section else None,
                "edges": edges_section.group(1).strip() if edges_section else None
            }
        }

    # Causal Graph Parsing
    elif intent.lower() == "causal graph":
        logging.info("Generating Causal Graph Queries")
        cause_nodes = re.search(r"Cause Nodes:\s*(.*?)(?:\nEffect Nodes:|\Z)", response_text, re.DOTALL)
        effect_nodes = re.search(r"Effect Nodes:\s*(.*?)(?:\nCausal Edges:|\Z)", response_text, re.DOTALL)
        causal_edges = re.search(r"Causal Edges:\s*(.*?)(?:\n[A-Z]|\\Z)", response_text, re.DOTALL)

        return {
            "reasoning_answer": reasoning_answer,
            "generated_sql": sql_query,
            "graph_schema": {
                "cause_nodes": cause_nodes.group(1).strip() if cause_nodes else None,
                "effect_nodes": effect_nodes.group(1).strip() if effect_nodes else None,
                "causal_edges": causal_edges.group(1).strip() if causal_edges else None
            }
        }

    # General SQL + Python Plot Code Parsing
    else:
        logging.info("Generating General Python Graph Queries")
        python_match = re.search(r"3\. Python(?: Plotting Code)?:\s*```python\n(.*?)```", response_text, re.DOTALL)
        python_code = python_match.group(1).strip() if python_match else None

        return {
            "reasoning_answer": reasoning_answer,
            "generated_sql": sql_query,
            "generated_plot_code": python_code
        }
