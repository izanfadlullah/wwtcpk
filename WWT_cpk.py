import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="WWT 6 Sigma Dashboard", layout="wide")

st.title("🏭 WWT Process Capability & Compliance Dashboard")
st.markdown("""
This tool calculates **Cpk (Process Capability)** and generates **Control Charts** to compare your effluent data against **DOE Standard B**.
""")

# --- SIDEBAR: SETTINGS & LIMITS ---
st.sidebar.header("1. DOE Standard B Limits (mg/L)")
st.sidebar.info("Adjust these limits based on Regulations 2009")

# Default values set to Standard B
limit_pb = st.sidebar.number_input("Lead (Pb) Limit", value=0.5, step=0.1)
limit_mn = st.sidebar.number_input("Manganese (Mn) Limit", value=1.0, step=0.1)
limit_b = st.sidebar.number_input("Boron (B) Limit", value=4.0, step=0.1)
limit_cod = st.sidebar.number_input("COD Limit", value=200.0, step=10.0)

# Map limits to parameter names for easy lookup
limits_dict = {
    "Lead (Pb)": limit_pb,
    "Manganese (Mn)": limit_mn,
    "Boron (B)": limit_b,
    "COD": limit_cod
}

# --- FUNCTIONS ---
def calculate_cpk(data, usl):
    mu = np.mean(data)
    sigma = np.std(data, ddof=1)
    
    if sigma == 0:
        return 0.0 # Avoid division by zero
        
    cpu = (usl - mu) / (3 * sigma)
    return cpu, mu, sigma, (mu + 3*sigma)

# --- MAIN APP ---
st.header("2. Upload Data")
uploaded_file = st.file_uploader("Upload your WWT Excel/CSV file", type=['xlsx', 'csv'])

# Template download (helper for user)
if not uploaded_file:
    st.info("👆 Upload a file to begin. The file should have columns like: 'Lead (Pb)', 'Manganese (Mn)', etc.")
    
    # Create dummy data for demo purposes
    demo_data = pd.DataFrame({
        'Date': pd.date_range(start='2025-01-01', periods=10),
        'Lead (Pb)': [0.12, 0.15, 0.11, 0.20, 0.13, 0.45, 0.18, 0.12, 0.10, 0.15],
        'Manganese (Mn)': [0.65, 0.70, 0.55, 0.85, 0.60, 0.75, 0.68, 0.72, 0.58, 0.62],
        'Boron (B)': [2.1, 2.3, 1.9, 2.5, 2.0, 2.2, 2.4, 2.1, 1.8, 2.2]
    })
    st.write("Don't have a file? Here is what your data should look like:")
    st.dataframe(demo_data)

else:
    # LOAD DATA
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success("Data loaded successfully!")
        
        # Select columns to analyze
        # We filter for numeric columns only to avoid selecting "Date" or "Remarks"
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        selected_params = st.multiselect("Select Parameters to Analyze:", numeric_cols, default=numeric_cols[:3])
        
        if selected_params:
            # Create tabs for Report and Charts
            tab1, tab2 = st.tabs(["📊 Summary Report", "📈 Control Charts"])
            
            summary_data = []
            
            # --- LOOP THROUGH SELECTED PARAMETERS ---
            for param in selected_params:
                # Get the limit (default to 1.0 if not defined in sidebar)
                # Matches sidebar names loosely or defaults
                usl = limits_dict.get(param, 1.0) 
                
                # Get values and clean (drop empty)
                values = df[param].dropna()
                
                # Calculate
                cpk, mu, sigma, ucl = calculate_cpk(values, usl)
                
                # Determine Status
                if cpk < 1.0:
                    status = "🔴 NOT CAPABLE"
                elif cpk < 1.33:
                    status = "🟠 MARGINAL"
                else:
                    status = "🟢 EXCELLENT"
                    
                summary_data.append([param, usl, round(mu, 3), round(sigma, 3), round(cpk, 2), status])

                # PLOT CHART (for Tab 2)
                with tab2:
                    st.subheader(f"{param} Analysis")
                    
                    fig, ax = plt.subplots(figsize=(10, 4))
                    
                    # Plot Data
                    ax.plot(values.index, values, marker='o', linestyle='-', color='#1f77b4', label='Result')
                    
                    # Plot Limits
                    ax.axhline(y=usl, color='purple', linewidth=2, linestyle='-', label=f'DOE Limit ({usl})')
                    ax.axhline(y=ucl, color='red', linestyle='--', label=f'UCL ({ucl:.2f})')
                    ax.axhline(y=mu, color='green', linestyle='-', alpha=0.5, label=f'Avg ({mu:.2f})')
                    
                    # Formatting
                    ax.set_ylabel("Concentration (mg/L)")
                    ax.set_title(f"Control Chart: {param}")
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    
                    st.pyplot(fig)
                    st.markdown("---")

            # DISPLAY SUMMARY TABLE (for Tab 1)
            with tab1:
                summary_df = pd.DataFrame(summary_data, columns=["Parameter", "Std B Limit", "Mean", "StdDev", "Cpk", "Status"])
                st.dataframe(summary_df, use_container_width=True)
                
                # Highlighting Cpk logic
                st.caption("Status Guide: 🔴 Cpk < 1.0 (High Risk), 🟠 1.0 < Cpk < 1.33 (Warning), 🟢 Cpk > 1.33 (Safe)")

    except Exception as e:
        st.error(f"Error reading file: {e}")