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
- The SQL MUST be compatible with PostgresSQL dialect.
- DO NOT use reserved keywords like `do`, `from`, `select`, `where`, `order`, `limit`, `group`, `by`, `table`, `user` as table aliases.
  → Use safe short aliases like `doc` (dim_occupation), `dia` (fact_industry_automation_rows), etc.
- When using aggregation:
  - PostgresSQL STRING_AGG syntax: STRING_AGG(expression, ', ' ORDER BY column).
  - Columns outside aggregate functions MUST be included in GROUP BY.
- ALWAYS qualify column names with table aliases when joining tables.
- Use ROUND(value::numeric, decimal_places) when rounding.
- Handle division by zero using NULLIF.
- When calculating date differences between two DATE columns, subtract directly (e.g., `end_date - start_date`) to get day counts. Do NOT use EXTRACT(EPOCH) unless working with TIMESTAMP or INTERVAL types.
- Do NOT assume or invent additional columns.
- If required data is missing in the schema, only return valid SQL using available data.

⚠️ IMPORTANT VALUE HANDLING:
- When filtering on categorical columns (like completion_status), only use known, valid values:
    → completion_status: 'Failed', 'Completed', 'In Progress'
- Do NOT assume or invent new filter values.
- If the user question uses qualitative words (like “difficult”) that don’t directly match a column value:
    → Map to the closest valid value **only if logical** (e.g., “difficult” → 'Failed')
    → Or skip the filter.
- When using any column in the SELECT clause as `label`, `node_label`, `source`, or `target`, you MUST add `WHERE <column> IS NOT NULL` to exclude NULL values from charts and graphs.

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
WHERE dla.local_authority_name IS NOT NULL
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
1️⃣ Examine the schema carefully.
- Identify core entities for KG nodes (e.g., employees, occupations, industries, skills, training, local authorities).
- Identify foreign key relationships to act as edges (e.g., employee → occupation → industry, employee → location, employee → training → skill).

2️⃣ Create multi-level joins:
- Use JOINs across 3–4 tables when possible to generate multi-hop paths.
- Example: employee → occupation → industry → local authority.

3️⃣ Extract diverse relationship types:
- Include multiple edge types:
    - HAS_OCCUPATION (employee → occupation)
    - BELONGS_TO_SECTOR (occupation → industry)
    - LOCATED_IN (employee → local authority)
    - TRAINS_FOR (employee → skill)
    - FUNDED_BY (skill → training program)

4️⃣ Enrich node labels:
- Add details like sector, skill category, or location to node labels when possible.

⚙️ SQL RULES:
- Always generate two separate SQL queries: one for nodes, one for edges.
- Nodes SQL → return: node_id, node_label, node_type.
- Edges SQL → return: source, target, relationship.
- Use DISTINCT or GROUP BY to deduplicate.
- Apply LIMIT (e.g., LIMIT 15) if needed.
- Use PostgreSQL-compatible syntax.
- DO NOT use reserved keywords as aliases; use:
    → doc (dim_occupation)
    → di (dim_industry)
    → ep (employee_profile)
    → dla (dim_local_authority)
    → wrc (workforce_reskilling_cases)
    → wre (workforce_reskilling_events)
    → sstm (soc_code_skill_training_map)

⚠️ OUTPUT FORMAT:
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
1️⃣ Reasoning Answer:
- Provide a **detailed, insightful answer** to the user question, using the data, the reasoning type, and the schema.
- Highlight key patterns, trends, and relationships.
- Explain both direct and indirect relationships (e.g., employee → occupation → industry).
- Make the explanation understandable for a non-technical audience.

2️⃣ Knowledge Graph JSON:
- Extract unique nodes and edges.
- Use the schema to infer direct and indirect edges:
    → Example: if you have employee → occupation → industry, also add employee → industry.
- Include diverse relationship types:
    → HAS_OCCUPATION, BELONGS_TO_SECTOR, LOCATED_IN, TRAINS_FOR, FUNDED_BY, WORKS_IN.
- For each node:
    → id → unique identifier
    → label → human-readable name (add sector, skill, or location when possible)
    → type → entity type (e.g., employee, occupation, industry, location)
- For each edge:
    → source → id of source node
    → target → id of target node
    → relationship → type of connection

⚡ OUTPUT FORMAT:
Respond with exactly two sections:

1. Reasoning Answer:
<Your detailed answer here>

2. Nodes & Edges JSON:
{{
  "nodes": [{{ "id": "node_id", "label": "node_label", "type": "node_type" }}],
  "edges": [{{ "source": "source_id", "target": "target_id", "relationship": "edge_label" }}]
}}

⚡ IMPORTANT RULES:
- Deduplicate nodes and edges.
- Use clean IDs (no spaces or special characters).
- Ensure edge source/target IDs match node IDs.
- Add cross-cluster connections to increase graph density.
- Do NOT include markdown or explanation outside the specified sections.
"""


# Dedicated Prompt for Causal Graph
def get_cg_sql_prompt(question, reasoning_type, visualization_type):
    return f"""
You are an expert assistant generating SQL queries for Causal Graph (CG) construction.

⚡ IMPORTANT: Only return the final SQL queries. Do NOT include explanations, reasoning, or comments.

Reasoning Type: {reasoning_type}
Visualization Type: {visualization_type}
Schemas (use ONLY the tables and columns listed below — do NOT invent new table names or columns):
{TABLE_SCHEMAS}

User Question: \"{question}\"

⚡ HOW TO THINK BEFORE WRITING SQL:
1️⃣ Carefully examine the schema.
- Identify which tables contain potential causal entities (e.g., factors, drivers, events, outcomes).
- Identify which columns or relationships suggest causal links (e.g., cause → effect, predictor → outcome, intervention → result).

2️⃣ Classify:
- Nodes → select columns for node_id, node_label, node_type (e.g., “cause”, “effect”, “factor”, “outcome”).
- Edges → select pairs for source, target, relationship (e.g., “causes”, “contributes to”, “impacts”, “leads to”).

3️⃣ Select logically:
- Only use real columns from the schema.
- Avoid hardcoding arbitrary relationships unless they logically fit and are supported by data.
- If no meaningful causal relationships exist in the schema, return only the node SQL.

4️⃣ Ensure nodes and edges are aligned:
- FIRST, write the SQL to select the node set.
- THEN, write a second SQL to select the edge set, using only node IDs that appear in the first query.
- This ensures all edges connect valid nodes and avoids dangling edges.

⚙️ IMPORTANT SQL RULES:
- Always generate two separate SQL queries: one for nodes, one for edges.
- Nodes SQL → must return: node_id, node_label, node_type.
- Edges SQL → must return: source, target, relationship.
- Explicitly CAST node_id, source, and target to TEXT to avoid type conflicts.
- Use DISTINCT or GROUP BY to deduplicate results.
- Apply LIMIT inside each query if needed (e.g., LIMIT 15).
- Use safe table aliases (avoid reserved words).
- Use only valid categorical values.
- Use PostgreSQL-compatible syntax.
- DO NOT use reserved keywords as aliases; use:
    → doc (dim_occupation)
    → di (dim_industry)
    → ep (employee_profile)
    → dla (dim_local_authority)
    → wrc (workforce_reskilling_cases)
    → wre (workforce_reskilling_events)
    → sstm (soc_code_skill_training_map)
    
🆕 ⚙️ ADDITIONAL CG-SPECIFIC RULES:
- Use meaningful node types (e.g., “factor,” “outcome,” “intervention,” “risk”).
- Use informative relationship labels (e.g., “causes,” “leads to,” “contributes to,” not just “related to”).
- Prioritize high-impact or frequently occurring cause-effect pairs when limiting rows.

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


def get_cg_data_prompt(question, reasoning_type, db_data_json):
    return f"""
You are an expert data analyst and causal reasoning assistant.

User Question: "{question}"
Reasoning Type: "{reasoning_type}"

Here is the query result data (in JSON format):
{db_data_json}

⚡ SCHEMA AND RELATIONSHIPS:
{TABLE_SCHEMAS}

⚡ TASKS:
1️⃣ **Reasoning Answer**
- Provide a **clear, well-reasoned, insightful answer** to the user question, using the data, the reasoning type, and the schema.
- Focus on identifying **causal relationships** — explain what factors cause or influence what outcomes.
- Highlight key cause-effect patterns, drivers, impacts, risk factors, and dependencies revealed in the data.
- Make sure the explanation is easy to understand for a non-technical user and clearly communicates the causal insights.

2️⃣ **Causal Graph JSON**
- Extract unique nodes and edges from the data to build a causal graph.
- Nodes:
    - id → unique identifier (simple, clean, no spaces or special characters)
    - label → human-readable name
    - type → meaningful category (e.g., factor, outcome, intervention, risk, cause, effect)
- Edges:
    - source → id of the cause node
    - target → id of the effect node
    - relationship → type of causal link (e.g., causes, leads to, contributes to, increases, decreases)

⚡ OUTPUT FORMAT:
Respond with exactly **two sections**:
1. Reasoning Answer:
<Your detailed causal answer here>

2. Nodes & Edges JSON:
{{
  "nodes": [{{ "id": "node_id", "label": "node_label", "type": "node_type" }}],
  "edges": [{{ "source": "source_id", "target": "target_id", "relationship": "edge_label" }}]
}}

⚡ IMPORTANT RULES:
- Deduplicate nodes and edges — no duplicates.
- Use simple, clean IDs (no spaces or special characters).
- Ensure all edge source/target IDs match node IDs.
- Only create edges when the data shows a valid, meaningful causal relationship.
- Use precise, insightful relationship labels (avoid vague terms like “related to”).
- Do **NOT** include any explanation, notes, or markdown outside the specified format.
"""


def get_pf_sql_prompt(question, reasoning_type, visualization_type):
    return f"""
You are an expert assistant generating SQL queries for Process Flow or Process Mining visualization.

⚡ IMPORTANT: Only return the final SQL queries. Do NOT include explanations, reasoning, or comments.

Reasoning Type: {reasoning_type}
Visualization Type: {visualization_type}
Schemas (use ONLY the tables and columns listed below — do NOT invent new table names or columns):
{TABLE_SCHEMAS}

User Question: \"{question}\"

⚡ HOW TO THINK BEFORE WRITING SQL:
1️⃣ Carefully examine the schema.
- Identify which tables contain **process steps**, **events**, **activities**, or **milestones**.
- Identify which columns or relationships define the **sequence or order of steps** (e.g., previous_step → next_step, timestamp ordering, transitions).

2️⃣ Classify:
- Nodes → select columns for node_id, node_label, node_type (e.g., “step”, “activity”, “milestone”).
- Edges → select pairs for source, target, relationship (e.g., “next”, “transitions_to”, “depends_on”).
- [Optional] Include flow **counts** if available (e.g., number of times a transition occurred).

3️⃣ Select logically:
- Only use real columns from the schema.
- Do not hardcode arbitrary relationships unless they logically fit.
- If no meaningful transition columns exist, return only the node SQL.
- Do not assume that all employees have multiple training cases. Use COUNT(*) to detect actual transitions and always check for NULLs in date comparisons.

4️⃣ Ensure nodes and edges are aligned:
- FIRST, write the SQL to select the node set.
- THEN, write a second SQL to select the edge set, using only node IDs that appear in the first query.
- This ensures all edges connect valid nodes and avoids dangling edges.

⚙️ IMPORTANT SQL RULES:
- Always generate two separate SQL queries: one for nodes, one for edges.
- Nodes SQL → must return: node_id, node_label, node_type.
- Edges SQL → must return: source, target, relationship, [optional] count.
- Explicitly CAST node_id, source, and target to TEXT to avoid type conflicts.
- Use DISTINCT or GROUP BY to deduplicate results.
- Apply LIMIT inside each query if needed (e.g., LIMIT 25).
- Use safe table aliases (avoid reserved words).
- Use only valid categorical values.
- Use PostgresSQL-compatible syntax.
- When comparing dates (e.g., e1.completion_date < e2.start_date), always add WHERE conditions to exclude NULL values from both sides of the comparison.
- When using any column as node_id, source, or target, exclude rows where the value is NULL.

⚠️ IMPORTANT OUTPUT FORMAT:
- Always first output the Nodes SQL, then the Edges SQL.
- Separate them under clear headers.
- Example format:

1. Nodes SQL:
```sql
<Write the Nodes SQL here>
2. Edges SQL:
```sql
<Write the Edges SQL here>
```
"""


def get_pf_data_prompt(question, reasoning_type, db_data_json):
    return f"""
You are an expert data analyst and process flow reasoning assistant.

User Question: "{question}"
Reasoning Type: "{reasoning_type}"

Here is the query result data (in JSON format):
{db_data_json}

⚡ SCHEMA AND RELATIONSHIPS:
{TABLE_SCHEMAS}

⚡ TASKS:
1️⃣ **Reasoning Answer**  
- Provide a **clear, well-reasoned, insightful answer** to the user question, using the data, the reasoning type, and the schema.
- Focus on analyzing **the process flow** — explain the key steps, transitions, sequences, bottlenecks, and loops revealed in the data.
- Highlight important patterns such as:
    - where processes slow down or fail,
    - where resources pile up,
    - which steps are most critical or frequent,
    - and where improvements can be made.
- Make sure the explanation is understandable for a non-technical audience and clearly communicates the process logic.

2️⃣ **Process Flow JSON**  
- Extract unique nodes and edges from the data to build a process flow diagram.
- Nodes:
    - id → unique identifier
    - label → human-readable step name
    - type → category (e.g., step, decision, milestone, endpoint)
- Edges:
    - source → id of the starting step
    - target → id of the next step
    - relationship → type of flow (e.g., next, transitions_to, depends_on)
    - [optional] count → number of times this transition occurs (if available in data)

⚡ OUTPUT FORMAT:
Respond with exactly **two sections**:
1. Reasoning Answer:
<Your detailed process flow answer here>

2. Nodes & Edges JSON:
{{
  "nodes": [{{ "id": "node_id", "label": "node_label", "type": "node_type" }}],
  "edges": [{{ "source": "source_id", "target": "target_id", "relationship": "edge_label" }}]
}}

⚡ IMPORTANT RULES:
- Deduplicate nodes and edges — no duplicates.
- Use simple, clean IDs (no spaces or special characters).
- Ensure all edge source/target IDs match node IDs.
- Only create edges when the data shows a valid, meaningful process transition.
- Do **NOT** include any explanation, notes, or markdown outside the specified format.
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
