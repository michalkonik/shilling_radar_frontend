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

        self.influencers_list = list({author for token in self.influencer_data_list.values() for tweet in token for author in [tweet["author"]]})

        st.set_page_config(layout="wide")

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
            price_data = pd.read_csv(f'data/crypto_prices/{crypto}_price_data_recent.csv', parse_dates=['timestamp'])
            return price_data
        except FileNotFoundError:
            st.warning(f"File with prices not found for {crypto}. Skipping...")
            return None
        
    def get_midnight_timestamps(self, data_csv):
        data_csv['date'] = data_csv['timestamp'].dt.date

        earliest_date = data_csv['date'].min()
        latest_date = data_csv['date'].max()

        midnight_timestamps = pd.date_range(start=earliest_date, end=latest_date, freq='D')
        midnight_timestamps_list = midnight_timestamps.to_list()
        return midnight_timestamps_list

    def generate_chart(self, currency, price_data, influencer_data_list):
        fig = px.line(price_data, x='timestamp', y='close', title=f'{currency} Price Chart')

        y_values = [1 - i * 0.05 for i in range(len(self.selected_influencers))]

        annotations = []
        shapes = []  # List to store vertical lines for day borders

        for i, influencer_data in enumerate(influencer_data_list):  # Change the loop variable name
            #author_list = [item["author"] for item in influencer_data]
            #influencer_entry = list(influencer_data.keys())[0]
            influencer_username = influencer_data["author"]
            if influencer_username in self.selected_influencers:
                timestamp = datetime.strptime(influencer_data["created_at"], "%Y-%m-%dT%H:%M:%S.000Z")

                # Calculate the y_value as a percentage of the y-axis range
                y_range = price_data['close'].max() - price_data['close'].min()
                y_value = price_data['close'].min() + y_range * y_values[i % len(y_values)]
                
                annotation_text = f'{influencer_username}'

                annotations.append(
                    go.layout.Annotation(
                        x=timestamp,
                        y=y_value,
                        text=annotation_text,
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor='red',
                        ax=0,
                        ay=-40,
                        hovertext=timestamp.strftime("%Y-%m-%d %H:%M:%S"),  # Use a single value for hovertext
                    )
                )

        midnight_timestamps = self.get_midnight_timestamps(price_data)

        for timestamp_at_midnight in midnight_timestamps:
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

        # Update layout to set x-axis tick frequency to every second day
        fig.update_layout(xaxis=dict(tickmode='linear', tick0=midnight_timestamps[0], dtick=2 * (midnight_timestamps[1] - midnight_timestamps[0])))

        fig.update_layout(annotations=annotations)
        fig.update_layout(shapes=shapes)
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

        print(start_index)
        print(end_index)

        end_index = min(end_index, total_cryptos)

        # Move the page selector above the influencer selector
        self.selected_influencers = st.sidebar.multiselect('Select Influencers', options=self.influencers_list, default=self.influencers_list)

        with ThreadPoolExecutor() as executor:
            crypto_data = executor.map(self.process_crypto, self.cryptos[start_index:end_index])

        for crypto, price_data, influencer_data in crypto_data:
            with st.container():
                st.plotly_chart(self.generate_chart(crypto, price_data, influencer_data))

app = CryptoInfluencerApp()
app.run()
