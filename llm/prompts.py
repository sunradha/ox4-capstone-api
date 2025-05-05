import textwrap
from db.schemas import TABLE_SCHEMAS


def get_reasoning_prompt(question):
    return f"""
    You are an expert reasoning and visualization assistant.

    Given this question:
    "{question}"

    And the following table schema:
    "{TABLE_SCHEMAS}"

    Perform the following:

    Reasoning Type
    Classify the reasoning type of the question. Choose one from:
    [Deductive, Inductive, Abductive, Causal, Counterfactual, Multi-Hop, Temporal, Probabilistic, Analogical, Ethical, 
    Spatial, Scientific, Commonsense, Planning, Legal, Multi-Agent, Metacognitive]

    Reasoning Justification
    Explain in one or two sentences why you classified the question as that reasoning type.

    Reasoning Path
    Describe the conceptual reasoning chain as a symbolic path of entities, relationships, or operations needed to answer the question.
    Use this exact format:
    Reasoning Path: ["<entity/step 1> → <entity/step 2> → ... → <final target>"]

    Visualization Recommendation
    Based on the reasoning type, data relationships, and question goal, recommend the most suitable visualization type.
    Choose from:
    [Knowledge Graph, Causal Graph, Process Flow, Time Series Chart, Comparative Bar Chart, Ranking Chart, Pie Chart, Histogram]

    For the Visualization Type, briefly include key axis, nodes, or segment details in parentheses. Example:
    Visualization Type: Comparative Bar Chart (X axis - job roles grouped by industry; Y axis - automation risk level)

    OUTPUT FORMAT (strict)

    Reasoning Type: <selected reasoning type>

    Reasoning Justification: <one or two sentence explanation for why this reasoning type fits the question>

    Reasoning Path: [<entity/step 1> → <entity/step 2> → ... → <final target>]

    Visualization Type: <recommended visualization type with short axis or segment details in parentheses>
    """


def get_process_flow_prompt(question, reasoning_type):
    return f"""
    You are an assistant generating SQL queries and Process Flow construction logic.

    Reasoning Type: {reasoning_type}
    Schemas: {TABLE_SCHEMAS}

    User Question: "{question}"

    1. Provide the SQL query to fetch the required process steps.
    2. Define the process flow:
    - Nodes: list of unique steps or states.
    - Edges: source → target with description.

    Output format:

    1. Reasoning Answer:
    <explanation>

    2. SQL Query:
    ```sql
    <SQL>
    ```

    3. Process Flow Schema:
    Nodes:
    - <node_column>
    Edges:
    - source: <source_column>, target: <target_column>, description: <relationship>
    """


def get_custom_prompt(question, reasoning_type, visualization_type):
    pass


def get_sql_prompt(question, reasoning_type, visualization_type):
    return f"""
You are an assistant generating only SQL queries (no Python code, no explanations, no reasoning text) based on the reasoning type and visualization type.

Reasoning Type: {reasoning_type}
Visualization Type: {visualization_type}
Schemas (use ONLY the tables and columns listed below — do NOT invent new table names):
{TABLE_SCHEMAS}

User Question: \"{question}\"

⚡ --- IMPORTANT SQL GENERATION RULES (MUST FOLLOW) --- ⚡
- Only use columns that are explicitly listed in the provided schema.
- If the schema lacks required columns to create edges (e.g., no employee_id available), only return node-level results without edges.
- The SQL MUST be compatible with PostgreSQL dialect.
- DO NOT use reserved keywords like `do`, `from`, `select`, `where`, `order`, `limit`, `group`, `by`, `table`, `user` as table aliases.
  → Use safe short aliases like `doc` (dim_occupation), `dia` (fact_industry_automation_rows), etc.
- When using aggregation:
  - PostgreSQL STRING_AGG syntax: STRING_AGG(expression, ', ' ORDER BY column).
  - Columns outside aggregate functions MUST be included in GROUP BY.
- ALWAYS qualify column names with table aliases when joining tables.
- Use ROUND(value::numeric, decimal_places) when rounding.
- Handle division by zero using NULLIF.
- Do NOT assume or invent additional columns.
- If required data is missing in the schema, only return valid SQL using available data.

⚠️ IMPORTANT VALUE HANDLING:
- When filtering on categorical columns (like completion_status), only use known, valid values:
    → completion_status: 'Failed', 'Completed', 'In Progress'
- Do NOT assume or invent new filter values.
- If the user question uses qualitative words (like “difficult”) that don’t directly match a column value:
    → Map to the closest valid value **only if logical** (e.g., “difficult” → 'Failed')
    → Or skip the filter.

**RULES FOR VISUALIZATION:**
- When querying local_authority_code, JOIN dim_local_authority and SELECT dim_local_authority.local_authority_name AS label.
- When showing metrics per location/category, apply aggregation (e.g., AVG) and GROUP BY the dimension.
- Deduplicate using DISTINCT ON, GROUP BY, or ROW_NUMBER() window functions.
- Apply row limits to avoid clutter:
    → Bar Chart → LIMIT 10
    → Pie Chart → LIMIT 5
    → Knowledge Graph / Causal Graph → LIMIT 20–25
    → Time Series → ORDER BY date DESC LIMIT 100
- Always alias SELECT columns as:
    - Ranking Chart → x, y, label
    - Pie Chart → label, value
    - Time Series → x, y
    - Comparative Bar Chart → x, series1, series2, etc.
    - Histogram → value
    - Knowledge Graph → node_id, node_label, node_type, source, target, relationship
    - Causal Graph → cause, effect, relationship

**EXAMPLES FOR DEDUPLICATION AND GRAPHS:**
-- Example for Ranking Chart
SELECT DISTINCT ON (dla.local_authority_name) dla.local_authority_name AS label, fgar.probability_of_automation AS y
FROM fact_geographic_automation_rows fgar
JOIN dim_local_authority dla ON fgar.local_authority_code = dla.local_authority_code
ORDER BY dla.local_authority_name, fgar.probability_of_automation DESC
LIMIT 10;

⚠️ **ALIASING REMINDER:**
NEVER use reserved words as table aliases.
→ Use aliases like `doc` (dim_occupation), `dia` (fact_industry_automation_rows), `ind` (dim_industry), etc.

Based on the provided Schemas, Reasoning Type, Visualization Type, and User Question, generate the correct SQL query following these rules.

Provide ONLY the following exact response format (no explanation, no reasoning, no commentary):

SQL Query:
```sql
<SQL>
    ```
"""


def get_kg_sql_prompt(question, reasoning_type, visualization_type):
    return f"""
You are an expert assistant generating SQL queries for Knowledge Graph (KG) construction.

⚡ IMPORTANT: Only return the final SQL queries. Do NOT include explanations, reasoning, or comments.

Reasoning Type: {reasoning_type}
Visualization Type: {visualization_type}
Schemas (use ONLY the tables and columns listed below — do NOT invent new table names or columns):
{TABLE_SCHEMAS}

User Question: \"{question}\"

⚡ HOW TO THINK BEFORE WRITING SQL:
1️⃣ Carefully examine the schema.
- Identify which tables contain core entities that should become KG nodes (e.g., employees, programs, skills, events).
- Identify which columns or foreign key relationships can act as edges between those entities (e.g., program → status, employee → department).

2️⃣ Classify:
- Nodes → select columns for node_id, node_label, node_type.
- Edges → select pairs for source, target, relationship.

3️⃣ Select logically:
- Only include real columns from the schema.
- Avoid hardcoding arbitrary edge labels unless they logically fit the schema.
- If no meaningful edge columns exist, return only the node SQL.

4️⃣ Ensure nodes and edges are aligned:
- FIRST, write the SQL to select the node set.
- THEN, write a second SQL to select the edge set, using only node IDs that appear in the first node query.
- This guarantees all edges connect to valid nodes and no dangling edges appear.

⚙️ IMPORTANT SQL RULES:
- Always generate two separate SQL queries: one for nodes, one for edges.
- Nodes SQL → always return: node_id, node_label, node_type.
- Edges SQL → always return: source, target, relationship.
- Explicitly CAST node_id, source, and target to TEXT to avoid type conflicts.
- Use DISTINCT or GROUP BY to deduplicate if needed.
- Apply LIMIT inside each SQL query if necessary (e.g., LIMIT 20).
- Use safe table aliases (avoid reserved words).
- Use only valid categorical values (e.g., completion_status: 'Failed', 'Completed').
- Use PostgreSQL-compatible syntax.

⚠️ IMPORTANT OUTPUT FORMAT:
- Always first output the Nodes SQL, then the Edges SQL.
- Separate them under clear headers.
- Example format:

1. Nodes SQL:
```sql
<Write the Nodes SQL here>
2. Edges SQL:
<Write the Edges SQL here>
```
"""


def get_kg_data_prompt(question, reasoning_type, db_data_json):
    return f"""
You are an expert data analyst and knowledge graph assistant.

User Question: "{question}"
Reasoning Type: "{reasoning_type}"

Here is the query result data (in JSON format):
{db_data_json}

⚡ SCHEMA AND RELATIONSHIPS:
{TABLE_SCHEMAS}

⚡ TASKS:
1️⃣ **Reasoning Answer**  
- Provide a **detailed, insightful answer** to the user question based on the data, the reasoning type, and the schema.
- Explain key patterns, trends, relationships, and important insights you can extract from the data.
- Highlight meaningful relationships between entities (for example, which industries are most impacted, which regions stand out, key connections between occupations and risk, etc.).
- Make the explanation easy to understand for a non-technical user.

2️⃣ **Knowledge Graph JSON**  
- Extract unique nodes and edges from the data.
- Use the schema and relationships to infer meaningful edges — only create edges when data shows a clear relationship or when the schema defines a known connection.
- For each node, include:
    - id → unique identifier
    - label → human-readable name
    - type → category of node (e.g., industry, region, job, person, etc.)
- For each edge, include:
    - source → id of source node
    - target → id of target node
    - relationship → type of connection between source and target

⚡ OUTPUT FORMAT:
Respond with exactly **two sections**:
1. Reasoning Answer:
<Your detailed answer here>

2. Nodes & Edges JSON:
{{
  "nodes": [{{ "id": "node_id", "label": "node_label", "type": "node_type" }}],
  "edges": [{{ "source": "source_id", "target": "target_id", "relationship": "edge_label" }}]
}}

⚡ IMPORTANT RULES:
- Deduplicate nodes and edges — no duplicates.
- Use simple, clean IDs (no spaces or special characters).
- Ensure all edge source/target IDs match node IDs.
- Do **NOT** include any explanation, notes, or markdown outside the specified format.
"""


# Dedicated Prompt for Causal Graph
def get_cg_sql_prompt(question, reasoning_type, visualization_type):
    return f"""
You are an assistant generating SQL queries and Causal Graph construction logic.

Reasoning Type: {reasoning_type}
Visualization Type: {visualization_type}
Schemas:
{TABLE_SCHEMAS}

User Question: "{question}"

⚡ IMPORTANT:

Return all cause and effect columns explicitly.

Alias final columns as: cause, effect, relationship.

Explain joins and relationships in the reasoning.

Provide your response in this format:

Reasoning Answer:

<Explain the query and causal logic>
SQL Query:
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


def get_reasoning_answer_prompt(question, reasoning_type, visualization_type, db_data_json):
    return f"""
You are an expert data analyst and reasoning assistant.

User Question: "{question}"
Reasoning Type: "{reasoning_type}"
Visualization Type: "{visualization_type}"

Here is the query result data (in JSON format):
{db_data_json}

⚡ SCHEMA:
{TABLE_SCHEMAS}

⚡ TASK:
- Provide a clear, accurate, and well-reasoned **answer to the user's question** based entirely on the provided data.
- Use the reasoning type and visualization type as context to guide your thinking.
- Highlight key patterns, trends, comparisons, correlations, or anomalies from the data.
- Walk through your reasoning so the user understands **why** this is the correct answer.
- Make the explanation simple, precise, and understandable to a non-technical audience.

⚡ OUTPUT FORMAT:
Respond with exactly **one section**:

Final Answer:
<Your complete and reasoned answer here>

⚡ IMPORTANT RULES:
- Use only the actual data provided — do not invent or assume values not present in the JSON.
- Stay concise but thorough; avoid unnecessary technical jargon.
- Do **NOT** include markdown, bullet points, or formatting outside the specified section.
- Do **NOT** include any code, SQL, or comments.
"""


