import matplotlib.pyplot as plt  # For creating plots
from matplotlib.gridspec import GridSpec  # For custom subplot layouts
import pandas as pd  # For handling dataframes

def create_robust_dashboard(event_data, kg_data, causal_data):
    """
    Create a dashboard visualization that's robust to data quality issues
    """
    try:
        plt.figure(figsize=(14, 10))

        # Use GridSpec for a custom layout
        from matplotlib.gridspec import GridSpec
        gs = GridSpec(2, 2, figure=plt.figure(figsize=(15, 10)))

        # 1. Process Mining Summary - Safety check all required columns
        if 'activity' in event_data.columns and 'completion_status' in event_data.columns:
            ax1 = plt.subplot(gs[0, 0])
            try:
                # Safely compute completion rate
                completed_rate = event_data.groupby('activity')['completion_status'].apply(
                    lambda x: (x == 'Completed').mean()
                )
                if not completed_rate.empty:
                    completed_rate.sort_values().plot(kind='barh', ax=ax1, color='skyblue')
                    ax1.set_title('Completion Rate by Activity', fontsize=12)
                    ax1.set_xlim(0, 1)
                else:
                    ax1.text(0.5, 0.5, "No completion data available",
                            ha='center', va='center', fontsize=12)
            except Exception as e:
                ax1.text(0.5, 0.5, f"Error creating completion chart: {str(e)}",
                        ha='center', va='center', fontsize=10)
        else:
            ax1 = plt.subplot(gs[0, 0])
            ax1.text(0.5, 0.5, "Missing required columns for process analysis",
                    ha='center', va='center', fontsize=12)

        # 2. Knowledge Graph Summary - High Risk Jobs
        if 'job_title' in kg_data.columns and 'automation_probability' in kg_data.columns:
            ax2 = plt.subplot(gs[0, 1])
            try:
                # Safely get high-risk jobs
                high_risk_jobs = kg_data[kg_data['automation_probability'] >= 0.7]['job_title'].value_counts()
                if not high_risk_jobs.empty and len(high_risk_jobs) > 0:
                    colors = plt.cm.Spectral(np.linspace(0, 1, len(high_risk_jobs)))
                    high_risk_jobs.plot(kind='pie', ax=ax2, autopct='%1.1f%%', colors=colors)
                    ax2.set_title('High Automation Risk Jobs', fontsize=12)
                    ax2.set_ylabel('')
                else:
                    ax2.text(0.5, 0.5, "No high-risk jobs identified",
                            ha='center', va='center', fontsize=12)
            except Exception as e:
                ax2.text(0.5, 0.5, f"Error creating high-risk jobs chart: {str(e)}",
                        ha='center', va='center', fontsize=10)
        else:
            ax2 = plt.subplot(gs[0, 1])
            ax2.text(0.5, 0.5, "Missing required columns for risk analysis",
                    ha='center', va='center', fontsize=12)

        # 3. Combined chart - Training success by automation risk
        if ('training_program' in causal_data.columns and
            'automation_probability' in causal_data.columns and
            'certification_earned' in causal_data.columns):

            ax3 = plt.subplot(gs[1, :])
            try:
                # Create risk bins safely
                risk_bins = [0, 0.3, 0.5, 0.7, 1.0]
                risk_labels = ['Very Low', 'Low', 'Medium', 'High']

                # Handle potential errors in categorical creation
                try:
                    causal_data['risk_bin'] = pd.cut(causal_data['automation_probability'],
                                              bins=risk_bins, labels=risk_labels)

                    # Group and plot only if we have valid data
                    if not causal_data['risk_bin'].isna().all() and len(causal_data) > 0:
                        risk_success = causal_data.groupby(['risk_bin', 'training_program'])['certification_earned'].mean().unstack()

                        if not risk_success.empty and not risk_success.isna().all().all():
                            risk_success.plot(kind='bar', ax=ax3)
                            ax3.set_title('Certification Success by Risk Level and Training Program', fontsize=12)
                            ax3.set_ylim(0, 1)
                            ax3.set_xlabel('Automation Risk Level')
                            ax3.set_ylabel('Certification Rate')
                            ax3.legend(title='Training Program', loc='upper right')
                        else:
                            ax3.text(0.5, 0.5, "Insufficient certification data for analysis",
                                    ha='center', va='center', fontsize=12)
                    else:
                        ax3.text(0.5, 0.5, "No valid risk categorization available",
                                ha='center', va='center', fontsize=12)
                except Exception as e:
                    ax3.text(0.5, 0.5, f"Error in risk categorization: {str(e)}",
                            ha='center', va='center', fontsize=10)
            except Exception as e:
                ax3.text(0.5, 0.5, f"Error creating certification chart: {str(e)}",
                        ha='center', va='center', fontsize=10)
        else:
            ax3 = plt.subplot(gs[1, :])
            ax3.text(0.5, 0.5, "Missing required columns for certification analysis",
                    ha='center', va='center', fontsize=12)

        plt.suptitle('Workforce Reskilling Analytics Dashboard', fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig('integrated_analytics_dashboard.png', dpi=300, bbox_inches='tight')
        plt.show()

    except Exception as e:
        print(f"Error creating dashboard: {e}")
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f"Unable to create dashboard due to data issues:\n{str(e)}",
                ha='center', va='center', fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig('dashboard_error.png', dpi=300)
        plt.show()
