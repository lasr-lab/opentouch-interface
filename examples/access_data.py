from opentouch_interface.decoder import Decoder

# 1. Load the data set
dataset = Decoder('<full-path-to-touch-file>')

# 2. Inspect the data set
print(f'The following sensors have been captured: {dataset.sensor_names}')
print('The sensors have the following streams:')
for sensor in dataset.sensor_names:
    print(f'\t- {sensor}: {dataset.stream_names_of(sensor)}')

# 3. Isolate the camera data
sensor_name = dataset.sensor_names[0]
data_stream = 'camera'
camera_data = dataset.stream_data_of(sensor_name, data_stream)

camera_data = dataset.stream_data_of('Finger', 'audio')
for event in camera_data:
    delta = event['delta']
    data = event['data']
    print(delta, type(data))
