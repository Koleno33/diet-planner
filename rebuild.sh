sudo docker container stop diet_app 
sudo docker container rm diet_app 
sudo docker image rm diet_planner
sudo docker build -t diet_planner .
sudo docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --name diet_app \
  diet_planner

