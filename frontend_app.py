import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import plotly.graph_objects as go
import os

class CryptoInfluencerApp:
    def __init__(self):
        self.final_output_file_name = 'data/stats/final_output.json'
        with open(self.final_output_file_name) as f:
            self.influencer_data_list = json.load(f)

        st.set_page_config(layout="wide")

        self.influencers_list = set()
        for key, value in self.influencer_data_list.items():
            for entry in value:
                influencer_name = list(entry.keys())[0]
                self.influencers_list.add(influencer_name)

        self.selected_influencers = st.sidebar.multiselect('Select Influencers', options=self.influencers_list,
                                                           default=self.influencers_list)
        self.cryptos = self.get_file_names()

    def return_list_of_tickers_from_price_files(self):
        with open(self.final_output_file_name, "r") as existing_file:
            data_structure = json.load(existing_file)

        tickers_list = list(data_structure.keys())
        return tickers_list
    
    def get_file_names(self, directory_path="data/crypto_prices"):
        tickers_list = []
        for filename in os.listdir(directory_path):
            if os.path.isfile(os.path.join(directory_path, filename)):
                tickers_list.append(filename.split("_")[0])
        tickers_list.sort()
        return tickers_list

    def generate_chart(self, currency, price_data, influencer_data):
        fig = px.line(price_data, x='timestamp', y='close', title=f'{currency} Price Chart')
        filtered_influencers = self.selected_influencers

        y_values = [1 - i * 0.05 for i in range(len(filtered_influencers))]

        for i, influencer_data in enumerate(influencer_data):
            influencer = list(influencer_data.keys())[0]
            if influencer in filtered_influencers:
                timestamp = datetime.strptime(influencer_data[influencer], "%Y-%m-%dT%H:%M:%S.000Z")

                fig.add_trace(
                    go.Scatter(
                        x=[timestamp],
                        y=[price_data['close'].max() * y_values[i % len(y_values)]],
                        mode='markers',
                        marker=dict(color='rgba(0,0,0,0)'),
                        hovertext=[f'{influencer}: {timestamp}'], 
                        hoverinfo='text'
                    )
                )

                fig.add_annotation(
                    x=timestamp,
                    y=price_data['close'].max() * y_values[i % len(y_values)], 
                    text=f'{influencer}',
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor='red',
                    ax=0,
                    ay=-40
                )

        width_factor = max(len(price_data['timestamp']) / 300, 1)  
        fig.update_layout(width=width_factor * 1000) 

        fig.update_layout(yaxis=dict(range=[price_data['close'].min(), price_data['close'].max()]))

        return fig

    def run(self):
        charts_per_page = 10
        total_cryptos = len(self.cryptos)

        num_pages = -(-total_cryptos // charts_per_page)

        selected_page = st.sidebar.selectbox('Select Page', range(1, num_pages + 1), index=0)

        if selected_page == 1:
            start_index = 0
            end_index = 10
        else:
            start_index = ((selected_page - 1) * charts_per_page) + 1
            end_index = min(start_index + charts_per_page, total_cryptos)


        end_index = min(end_index, total_cryptos)

        print(start_index)
        print(end_index)

        for i, crypto in enumerate(self.cryptos[start_index:end_index]):
            try:
                price_data = pd.read_csv(f'data/crypto_prices/{crypto}_price_data_recent.csv')
            except FileNotFoundError:
                print(f"File with prices not found for {crypto} :( skipping...")
                continue
            with st.container():
                st.plotly_chart(self.generate_chart(crypto, price_data, self.influencer_data_list[crypto]))

app = CryptoInfluencerApp()
app.run()
