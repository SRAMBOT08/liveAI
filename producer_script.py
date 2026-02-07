from streaming.producer_manager import producer_manager
import time
import signal
import sys

def signal_handler(sig, frame):
    print('\nStopping producer...')
    producer_manager.shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print('Initializing producer...')
if producer_manager.initialize():
    print('Starting streaming (Historical mode)...')
    producer_manager.start_streaming()
    print('Producer is running. Press Ctrl+C to stop.')
    while True:
        status = producer_manager.get_status()
        print(f'Events published: {status[\"events_published\"]} | Errors: {status[\"errors\"]}')
        time.sleep(10)
else:
    print('Failed to initialize producer')
