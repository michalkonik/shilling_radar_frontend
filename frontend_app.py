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

        self.cryptos = self.return_list_of_tickers_from_price_files()

    def return_list_of_tickers_from_price_files(self, directory_path="data/crypto_prices"):
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
        shapes = [] 

        for i, influencer_data in enumerate(influencer_data_list):
            influencer_username = influencer_data["author"]
            if influencer_username in self.selected_influencers:
                timestamp = datetime.strptime(influencer_data["created_at"], "%Y-%m-%dT%H:%M:%S.000Z")

                y_range = price_data['close'].max() - price_data['close'].min()
                y_value = price_data['close'].min() + y_range * y_values[i % len(y_values)]

                annotation_text =  f'<a href="{influencer_data["tweet_url"]}" target="_blank">{influencer_username}</a>'

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
                        hovertext=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
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
        
    def set_tickers_from_multiselect_window(self):
        print("main page executed")
        selected_tickers = st.sidebar.multiselect('# Select Cryptocurrencies (Max 8)', options=self.cryptos, default=[])
        go_button = st.sidebar.button('See selected Cryptocurrencies')

        if go_button:
            print("go button present")
            if len(selected_tickers) > 0 and len(selected_tickers) <= 8:
                # Redirect to the page with charts
                st.experimental_set_query_params(page=1, ticker=",".join(selected_tickers))
            else:
                # Reset ticker param to None if no ticker is selected
                #st.experimental_set_query_params(page=1, ticker=None)
                st.experimental_set_query_params(page=1, ticker=",".join(self.cryptos))
                st.warning("Please select between 1 and 8 cryptocurrencies. Going to 1st page...")

    def run(self):
        self.set_tickers_from_multiselect_window()

        charts_per_page = 6
        total_cryptos = len(self.cryptos)

        num_pages = -(-total_cryptos // charts_per_page)

        # Read the page parameter from the URL
        url_params = st.experimental_get_query_params()
        print("url_params:")
        print(url_params)
        selected_page = int(url_params.get('page', [1])[0])
        print("selected_page:")
        print(selected_page)
        selected_tickers = url_params.get('ticker', [""])[0]
        print("selected_tickers:")
        print(selected_tickers)

        if selected_tickers != "":
            print("weszło")
            self.cryptos = selected_tickers.split(',')

        if len(self.cryptos) <= charts_per_page and selected_page != 1:
            st.warning("Not many tickers selected. All fit on one page. Page number reset to 1.")
            selected_page = 1
        else:
            selected_page = st.sidebar.selectbox('Select page to see all Cryptocurrencies', range(1, num_pages + 1), index=selected_page - 1)
        print("selected_page from selectbox:")
        print(selected_page)

        st.experimental_set_query_params(page=selected_page, ticker=selected_tickers)

        if selected_page == 1:
            start_index = 0
            end_index = charts_per_page
        else:
            start_index = ((selected_page - 1) * charts_per_page)
            end_index = min(start_index + charts_per_page, total_cryptos)

        end_index = min(end_index, total_cryptos)

        print("start_index:")
        print(start_index)
        print("end_index:")
        print(end_index)

        # Move the page selector above the influencer selector
        self.selected_influencers = st.sidebar.multiselect('Select Influencers', options=self.influencers_list, default=self.influencers_list)
        print("self.selected_influencers:")
        print(self.selected_influencers)

        print("self.cryptos right before multithreading:")
        print(self.cryptos)
        with ThreadPoolExecutor() as executor:
            crypto_data = executor.map(self.process_crypto, self.cryptos[start_index:end_index])

        print("crypto_data:")
        print(crypto_data)

        for crypto, price_data, influencer_data in crypto_data:
            with st.container():
                try:
                    st.plotly_chart(self.generate_chart(crypto, price_data, influencer_data))
                except AttributeError as ae:
                    print(f"error poped up: {ae}")


app = CryptoInfluencerApp()
app.run()
