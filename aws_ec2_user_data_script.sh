#!/bin/bash  

sudo apt update -y  

sudo apt install -y python3-pip  

sudo pip3 install streamlit pandas plotly  

git clone https://github.com/michalkonik/shilling_radar_frontend.git  

cd shilling_radar_frontend  

sudo streamlit run frontend_app.py --server.port 80 
