## shilling_radar_frontend

# how to restart the app on EC2:
git pull
pkill -f "streamlit run"
nohup sudo streamlit run frontend_app.py --server.port 80 &
