# docker login wildme.azurecr.io
docker tag wildme/houston:latest wildme.azurecr.io/houston:latest
docker push wildme.azurecr.io/houston:latest

docker tag wildme.azurecr.io/houston wildme/houston:latest
docker push wildme/houston:latest