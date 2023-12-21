import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor

class CryptoInfluencerApp:
    def __init__(self):
        self.final_output_file_name = 'data/stats/final_output.json'
        with open(self.final_output_file_name) as f:
            self.influencer_data_list = json.load(f)

        st.set_page_config(layout="wide")

        self.influencers_list = {influencer for data in self.influencer_data_list.values() for entry in data for influencer in entry}
        self.selected_influencers = st.sidebar.multiselect('Select Influencers', options=self.influencers_list, default=self.influencers_list)
        self.cryptos = self.get_file_names()

    def return_list_of_tickers_from_price_files(self):
        return list(self.influencer_data_list.keys())

    def get_file_names(self, directory_path="data/crypto_prices"):
        tickers_list = []
        for filename in os.listdir(directory_path):
            if os.path.isfile(os.path.join(directory_path, filename)):
                tickers_list.append(filename.split("_")[0])
                tickers_list.sort()
        return tickers_list

    @st.cache_data(ttl=600)
    def load_price_data(_self, crypto):
        try:
            return pd.read_csv(f'data/crypto_prices/{crypto}_price_data_recent.csv')
        except FileNotFoundError:
            st.warning(f"File with prices not found for {crypto}. Skipping...")
            return None

    def generate_chart(self, currency, price_data, influencer_data):
        fig = px.line(price_data, x='timestamp', y='close', title=f'{currency} Price Chart')

        y_values = [1 - i * 0.05 for i in range(len(self.selected_influencers))]

        annotations = []
        shapes = []  # List to store vertical lines for day borders

        # Calculate the percentage of the y-axis range for annotation placement
        y_range_percentage = 0.1  # Adjust this value based on your preference

        for i, influencer_data in enumerate(influencer_data):
            influencer = list(influencer_data.keys())[0]
            if influencer in self.selected_influencers:
                timestamp = datetime.strptime(influencer_data[influencer], "%Y-%m-%dT%H:%M:%S.000Z")

                # Calculate the y_value as a percentage of the y-axis range
                y_range = price_data['close'].max() - price_data['close'].min()
                y_value = price_data['close'].min() + y_range * y_values[i % len(y_values)]

                annotations.append(
                    go.layout.Annotation(
                        x=timestamp,
                        y=y_value,
                        text=f'{influencer}',
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor='red',
                        ax=0,
                        ay=-40
                    )
                )

                timestamp_at_midnight = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

                # Add vertical line for day border
                shapes.append(
                    go.layout.Shape(
                        type='line',
                        x0=timestamp_at_midnight,
                        x1=timestamp_at_midnight,
                        y0=price_data['close'].min(),
                        y1=price_data['close'].max(),
                        line=dict(color='black', width=2)
                    )
                )

        fig.update_layout(annotations=annotations)
        fig.update_layout(shapes=shapes)  # Add day borders to the layout

        width_factor = max(len(price_data['timestamp']) / 350, 1)
        fig.update_layout(width=width_factor * 1000)
        fig.update_layout(yaxis=dict(range=[price_data['close'].min(), price_data['close'].max()]))

        return fig

    def process_crypto(self, crypto):
        price_data = self.load_price_data(crypto)
        if price_data is not None:
            return crypto, price_data, self.influencer_data_list[crypto]

    def run(self):
        charts_per_page = 6
        total_cryptos = len(self.cryptos)

        num_pages = -(-total_cryptos // charts_per_page)

        selected_page = st.sidebar.selectbox('Select Page', range(1, num_pages + 1), index=0)

        if selected_page == 1:
            start_index = 0
            end_index = charts_per_page
        else:
            start_index = ((selected_page - 1) * charts_per_page)
            end_index = min(start_index + charts_per_page, total_cryptos)

        end_index = min(end_index, total_cryptos)

        with ThreadPoolExecutor() as executor:
            crypto_data = executor.map(self.process_crypto, self.cryptos[start_index:end_index])

        for crypto, price_data, influencer_data in crypto_data:
            with st.container():
                st.plotly_chart(self.generate_chart(crypto, price_data, influencer_data))

app = CryptoInfluencerApp()
app.run()
