sudo docker run -d \
  --name=consul \
  -p 8500:8500 \
  -p 8600:8600/udp \
  --network "beer_review_network"\
  consul:1.15 agent -dev -client=0.0.0.0