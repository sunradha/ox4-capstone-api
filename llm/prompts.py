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
    [Deductive, Inductive, Abductive, Causal, Counterfactual, Multi-Hop, Temporal, Probabilistic, Analogical, Ethical, Spatial, Scientific, Commonsense, Planning, Legal, Multi-Agent, Metacognitive]

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
You are an assistant generating only SQL queries (no Python code) based on the reasoning type and visualization type.

Reasoning Type: {reasoning_type}
Visualization Type: {visualization_type}
Schemas (use ONLY the tables and columns listed below — do NOT invent new table names):
{TABLE_SCHEMAS}

User Question: \"{question}\"

⚡ --- IMPORTANT SQL GENERATION RULES (MUST FOLLOW) --- ⚡
- ONLY use the table names and columns provided in the schemas above.
- The SQL MUST be compatible with PostgreSQL dialect.
- DO NOT use reserved keywords like `do`, `from`, `select`, `where`, `order`, `limit`, `group`, `by`, `table`, `user` as table aliases. 
  → Instead, use safe, non-reserved short aliases like `doc` for dim_occupation, `dia` for fact_industry_automation_rows, etc.
- When using aggregation functions:
  - Always specify the delimiter in STRING_AGG.
  - PostgreSQL syntax for STRING_AGG is: STRING_AGG(expression, ', ' ORDER BY column).
  - DO NOT use aggregate functions inside the GROUP BY clause — they belong in the SELECT list.
  - Columns listed in the SELECT clause that are NOT part of aggregate functions MUST be included in GROUP BY.
- Identify ALL columns used in the SELECT clause and classify them as aggregated or non-aggregated.
- ONLY include the non-aggregated columns in the GROUP BY clause.
- If STRING_AGG or similar aggregation is applied, use a subquery or CTE.
- ALWAYS qualify column names with table aliases when joining tables.
- When calculating time difference between two dates, subtract the dates to get days, and multiply by INTERVAL '1 day' to get seconds.
- Use ROUND(value::numeric, decimal_places) when rounding double precision values.
- Always handle division by zero safely using NULLIF.
- If filtering on boolean columns, use proper checks for BOOLEAN or TEXT types.
- If required data is not available in the given schemas, mention it in the reasoning.
- Do NOT assume or invent additional columns.
- **NEW RULES FOR CLEAN CHARTS:**
  - When querying local_authority_code, always JOIN dim_local_authority ON local_authority_code and SELECT dim_local_authority.local_authority_name AS label instead of just showing the code.
  - When showing metrics per location or category, apply aggregation (like AVG) and GROUP BY the dimension (e.g., GROUP BY local_authority_code, local_authority_name).
  - For Ranking Chart, Comparative Bar Chart, Histogram, Pie Chart → use DISTINCT ON or a window function to remove duplicates.
  - For Time Series Chart → include a date range filter or ORDER BY date DESC LIMIT 100.
  - For all visualizations → add LIMIT 10 or LIMIT 15 to avoid clutter.
  - ALWAYS alias SELECT columns as:
    - x, y, label (for Ranking Chart)
    - label, value (for Pie Chart)
    - x, y (for Time Series Chart)
    - x, series1, series2, etc. (for Comparative Bar Chart)
    - value (for Histogram)
- **NEW RULES FOR DEDUPLICATION AND READABLE OUTPUT:**
  - When selecting location or entity names (such as local authorities), always JOIN to the corresponding dimension table to include human-readable names.
  - For ranking and comparative charts, aggregate the data (for example, use AVG, SUM, or MAX) and apply GROUP BY on the non-aggregated columns.
  - Always deduplicate results using DISTINCT ON, GROUP BY, or window functions to ensure clean chart outputs.
  - When joining fact tables with dimension tables, always ensure that the result has one row per dimension entity (such as per local authority name) by applying:
    (a) aggregation with GROUP BY, or
    (b) DISTINCT ON (dimension column), or
    (c) a window function (like ROW_NUMBER() OVER PARTITION BY dimension ORDER BY metric DESC).
    Example: 
    SELECT DISTINCT ON (dla.local_authority_name) dla.local_authority_name AS label, fgar.probability_of_automation AS y
    FROM fact_geographic_automation_rows fgar
    JOIN dim_local_authority dla ON fgar.local_authority_code = dla.local_authority_code
    ORDER BY dla.local_authority_name, fgar.probability_of_automation DESC
    LIMIT 10;
    or
    SELECT dla.local_authority_name AS label, MAX(fgar.probability_of_automation) AS y
    FROM fact_geographic_automation_rows fgar
    JOIN dim_local_authority dla ON fgar.local_authority_code = dla.local_authority_code
    GROUP BY dla.local_authority_name
    ORDER BY y DESC
    LIMIT 10;

⚠️ **CRITICAL REMINDER ON ALIASING:**  
NEVER use reserved words like `do`, `from`, `select`, `where`, `order`, `limit`, `group`, `by`, `table`, `user` as table aliases.  
→ Always pick safe, clear aliases like `doc` (dim_occupation), `dia` (fact_industry_automation_rows), `ind` (dim_industry), etc.

Based on the provided `Schemas`, `Reasoning Type`, `Visualization Type`, and `User Question`, perform the following actions:
Analyze the User Question carefully and provide a clear reasoning explanation for the approach.
Generate the correct SQL query following all the SQL generation rules and relationship constraints listed above.

Provide your response in the following exact format:

1. Reasoning Answer:
<Your explanation here>

2. SQL Query:
```sql
<Write the SQL query here>
```
"""


def get_kg_sql_prompt(question, reasoning_type, visualization_type):
    return f"""
You are an assistant generating SQL queries and Knowledge Graph construction logic.

Reasoning Type: {reasoning_type}
Visualization Type: {visualization_type}
Schemas (use ONLY the tables and columns listed below — do NOT invent new table names):
{TABLE_SCHEMAS}

User Question: "{question}"

⚡ IMPORTANT RULES:
- Provide both the conceptual KG schema (based on schema relationships) AND the SQL query.
- ONLY use the table names and columns provided in the schemas above.
- Do NOT invent or assume extra columns or labels.
- Check the schema carefully for data types (e.g., numeric, text, boolean) and apply correct conditions:
  → For numeric fields like 'score', use numeric comparisons (e.g., WHERE score >= 70), NOT text comparisons (e.g., WHERE score = 'high').
- The SQL MUST be compatible with PostgreSQL dialect.
- DO NOT use reserved keywords like `do`, `from`, `select`, `where`, `order`, `limit`, `group`, `by`, `table`, `user` as table aliases.
  → Instead, use safe, non-reserved short aliases like `doc` for dim_occupation, `dia` for fact_industry_automation_rows, etc.
- When using aggregation functions:
  - Always specify the delimiter in STRING_AGG.
  - PostgreSQL syntax: STRING_AGG(expression, ', ' ORDER BY column).
  - Do NOT use aggregates in GROUP BY — only in SELECT.
  - All non-aggregated SELECT columns MUST be in GROUP BY.
  - When using GROUP BY, any non-grouped columns in SELECT or ORDER BY must be wrapped in aggregate functions (e.g., MAX, MIN).
- If STRING_AGG or similar is used, apply it in a subquery or CTE.
- ALWAYS qualify column names with table aliases when joining.
- Use ROUND(value::numeric, decimal_places) when rounding doubles.
- Handle division by zero safely using NULLIF.
- If filtering on boolean/text, apply correct type checks.
- If required data is missing in the schema, mention this in the reasoning.
- For deduplication:
  - Use DISTINCT ON, GROUP BY, or window functions.
  - When using DISTINCT ON, make sure the ORDER BY clause starts with the same columns used in DISTINCT ON.
  - When using GROUP BY with ORDER BY, ensure ORDER BY references only grouped or aggregated columns.
- Alias SQL columns as:
  node_id, node_label, node_type, source, target, relationship.
- ALWAYS include both node and edge columns in the final SELECT: node_id, node_label, node_type, source, target, relationship.
- When using CTEs or subqueries, apply ORDER BY and LIMIT at the outermost SELECT, not inside the CTE, unless explicitly needed.
- Prefer using DISTINCT ON when you want one representative row per group, and control which row is kept using ORDER BY.
- Conceptual schema:
  - Define all unique node types and edge relationships.
  - Include meaningful edges between entities (e.g., employee → program, skill → program, industry → program) instead of trivial edges (e.g., id → program).
  - Use the schema’s foreign key relationships or join paths to construct edges:
    → Example 1: employee_id → training_program with relationship 'enrolled_in'
    → Example 2: training_program → skill_category with relationship 'requires_skill'
    → Example 3: industry_code → training_program with relationship 'offers'
- NEVER leave source, target, or relationship as NULL.
  → If meaningful edges cannot be determined, explain why in the reasoning section and focus on nodes only.
- IMPORTANT: To avoid overwhelming the frontend, ALWAYS limit the SQL query to **20–50 rows** using `LIMIT`. Apply a meaningful `ORDER BY` before the `LIMIT` — for example, `ORDER BY score DESC`, `timestamp DESC`, or `random()` if no natural ordering exists.
- IMPORTANT: If a table lacks natural foreign key relationships, consider deriving edges from data relationships (e.g., high score → training program) and explain this logic clearly in the reasoning section.

⚠️ NOTE: You cannot access real data values — generate the SQL to extract nodes and edges when executed.

OUTPUT SECTIONS:
1. Reasoning Answer:
<Explain the graph logic and SQL approach>

2. SQL Query:
```sql
<SQL query here>
```
3. Conceptual Knowledge Graph Schema:
Nodes:
- <column>: <entity_type>
Edges:
- source: <column>, target: <column>, relationship: <relationship_label>
"""


def get_kg_data_prompt(question, db_data):
    return f"""
    You are an assistant creating a data-driven Knowledge Graph.

    User Question: "{question}"

    Here is the real query result data:
    {db_data}

    ⚡ IMPORTANT:
    - Extract unique nodes and edges.
    - Identify node_id, node_label, node_type.
    - Identify source, target, and relationship for edges.
    - Return the KG in JSON format:
    {{
      "nodes": [{{ "id": "node_id", "label": "node_label", "type": "node_type" }}],
      "edges": [{{ "source": "source_id", "target": "target_id", "relationship": "edge_label" }}]
    }}

    Provide only the final JSON, no explanation.
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
