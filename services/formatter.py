from typing import List, Dict, Any
import pandas as pd


def format_data_for_openai(data: List[Dict[str, Any]], query_type: str) -> Dict[str, Any]:
    if query_type == "process_mining":
        events_df = pd.DataFrame(data)
        if 'timestamp' in events_df.columns:
            events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
            events_df = events_df.sort_values('timestamp')
        process_instances = {
            str(case_id): group.to_dict(orient='records')
            for case_id, group in events_df.groupby('case_id')
        }
        return {
            "process_instances": process_instances,
            "event_count": len(events_df),
            "case_count": len(process_instances)
        }

    elif query_type == "knowledge_graph":
        entities = {}
        relationships = []
        for record in data:
            if 'employee_id' in record:
                entity_id = f"employee_{record['employee_id']}"
                if entity_id not in entities:
                    entities[entity_id] = {"type": "employee", **record}
            if 'case_id' in record:
                case_id = f"case_{record['case_id']}"
                if case_id not in entities:
                    entities[case_id] = {"type": "case", **record}
                if 'employee_id' in record:
                    relationships.append({
                        "source": f"employee_{record['employee_id']}",
                        "target": case_id,
                        "type": "participates_in"
                    })
        return {
            "knowledge_graph": {
                "entities": list(entities.values()),
                "relationships": relationships
            }
        }

    elif query_type == "causal_graph":
        df = pd.DataFrame(data)
        causal_factors = {}
        if 'certification_earned' in df.columns and 'training_program' in df.columns:
            program_success = df.groupby('training_program')['certification_earned'].mean().to_dict()
            causal_factors['program_success_rate'] = program_success
        if 'automation_probability' in df.columns and 'certification_earned' in df.columns:
            risk_success = {}
            for risk in ['low', 'medium', 'high']:
                if risk == 'low':
                    subset = df[df['automation_probability'] <= 0.33]
                elif risk == 'medium':
                    subset = df[(df['automation_probability'] > 0.33) & (df['automation_probability'] <= 0.66)]
                else:
                    subset = df[df['automation_probability'] > 0.66]
                if not subset.empty:
                    risk_success[risk] = subset['certification_earned'].mean()
            causal_factors['risk_success_correlation'] = risk_success
        return {
            "causal_data": {
                "factors": causal_factors,
                "record_count": len(df)
            }
        }

    return {"data": data}
