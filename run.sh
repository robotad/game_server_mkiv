docker network create --driver=bridge unity

docker rm -f game-server-mkiv

# DEV_ASYNC_DEBUG_LOG - Show asyncio debug logs - will override LOG_LEVEL
# DEV_LOG - Show dev logs (opens if gates to log certain statements)
# DEV_PROFILE - Show profiling lib outputs
# DEV_IS_LOCAL_DOCKER - Set to True if using local docker networking
# LOG_LEVEL - Can be "debug", "info", or "warn"
# UDP_EXTERNAL_HOST Set the bind host for the server's UDP listener
# UDP_RECV_PORT - Set the bind port for the server's UDP listener
DEV_PROFILE="True"
docker run --network unity \
  -e DEV_ASYNC_DEBUG_LOG="False" \
  -e DEV_LOG="True" \
  -e DEV_PROFILE=${DEV_PROFILE} \
  -e DEV_IS_LOCAL_DOCKER="True" \
  -e LOG_LEVEL="info" \
  -e UDP_EXTERNAL_HOST="0.0.0.0" \
  -e UDP_RECV_PORT="5002" \
  -p 5002:5002/udp \
  --name game-server-mkiv game-server-mkiv &

#  2>&1 | tee .out

#if [ "${DEV_PROFILE}" == "True" ]; then
#  sleep 70s
#  docker cp $(docker ps -aqf "name=game-server-async"):/server.cprof .
#  pyprof2calltree -k -i server.cprof
#fi