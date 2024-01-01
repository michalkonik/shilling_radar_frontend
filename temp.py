import streamlit as st
import json
import pandas as pd

data_path = "data/stats/tickers_stats.json"

# Load JSON data
with open(data_path, "r") as file:
    crypto_data = json.load(file)

# Convert data to DataFrame for better manipulation
crypto_df = pd.DataFrame(crypto_data).transpose()

# Define the desired order of columns
desired_columns_order = ["1d", "3d", "1w", "2w", "1m", "2m", "3m"]

# Rearrange the columns in the DataFrame
crypto_df = crypto_df[desired_columns_order]

# Streamlit App
def app():
    st.title("Cryptocurrency Statistics")

    # Add option for sorting the table
    selected_sort_option = st.selectbox("Sort table by:", desired_columns_order)

    # Allow user to sort table by selected option
    sorted_crypto_df = crypto_df.sort_values(by=selected_sort_option, ascending=False)

    # Display the sorted table
    st.table(sorted_crypto_df)

# Run the app
if __name__ == "__main__":
    st.set_page_config(page_title="Crypto Statistics", page_icon=":money_with_wings:")
    app()
    