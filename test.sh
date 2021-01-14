export LOG_LEVEL='info'
export DEV_ASYNC_DEBUG_LOG='False'
export DEV_IS_LOCAL_DOCKER='False'
export DEV_LOG='False'
export DEV_SEND_PULSE_SLEEP="0.0"
export UDP_EXTERNAL_HOST="0.0.0.0"
export UDP_RECV_PORT="5002"

python -m app.test.test_client