# Define SQL queries for each analysis type
sql_queries = {
    # 1. Process Mining Queries
    'process_mining_events': '''
        SELECT
            case_id,
            event_id,
            activity,
            timestamp,
            actor,
            skill_category,
            score,
            completion_status
        FROM workforce_reskilling_events
        ORDER BY case_id, timestamp
    ''',

    # 2. Knowledge Graph Queries
    'knowledge_graph_relationships': '''
        SELECT
            ep.employee_id,
            jr.job_title,
            jr.soc_code,
            jr.automation_probability,
            wrc.case_id,
            wrc.training_program,
            wrc.start_date,
            wrc.completion_date,
            wrc.certification_earned
        FROM employee_profile ep
        JOIN job_risk jr ON ep.soc_code = jr.soc_code
        LEFT JOIN workforce_reskilling_cases wrc ON ep.employee_id = wrc.employee_id
    ''',

    # 3. Causal Graph Queries
    'causal_relationships': '''
        SELECT
            jr.automation_probability,
            wrc.training_program,
            wrc.certification_earned,
            wre.skill_category,
            wre.score,
            wre.completion_status,
            (wrc.completion_date - wrc.start_date) AS training_duration
        FROM workforce_reskilling_cases wrc
        JOIN employee_profile ep ON wrc.employee_id = ep.employee_id
        JOIN job_risk jr ON ep.soc_code = jr.soc_code
        JOIN workforce_reskilling_events wre ON wrc.case_id = wre.case_id
        WHERE wre.activity = 'Completed Training'
    '''
}

# Define reasoning queries for OpenAI O3
reasoning_queries = {
    'process_mining': '''
        Analyze the training event data to identify:
        1. What are the most common training paths?
        2. Where are the biggest bottlenecks in the training process?
        3. Which training sequences lead to the highest certification rates?
        4. What are the average time intervals between training activities?
        5. What process improvements would you recommend based on this analysis?

        Provide detailed analysis with specific insights for optimizing the training process.
    ''',

    'knowledge_graph': '''
        Analyze the relationships between employees, jobs, automation risks, and training programs to identify:
        1. What patterns exist between job automation risk and training program selection?
        2. Which employee characteristics correlate with successful certification?
        3. What are the implicit relationships between job roles and successful training outcomes?
        4. How does the knowledge graph reveal hidden connections in the workforce reskilling ecosystem?
        5. What personalized training recommendations would you make based on this knowledge graph analysis?

        Provide detailed insights focused on relationship patterns and personalized recommendations.
    ''',

    'causal_graph': '''
        Analyze the causal relationships in the workforce reskilling data to identify:
        1. Does high automation risk cause lower training completion rates?
        2. What is the causal effect of training program type on certification outcomes?
        3. What would happen if employees in high-risk jobs were assigned different training programs?
        4. How would a 30% reduction in available training affect overall certification rates?
        5. What interventions would have the highest causal impact on successful reskilling?

        Provide detailed causal analysis with emphasis on interventions and counterfactual scenarios.
    '''
}