import os


def enable_memory_growth():
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    import tensorflow as tf
    physical_devices = tf.config.list_physical_devices('GPU')
    for device in physical_devices:
        tf.config.experimental.set_memory_growth(device, True)
    # enable cuda_malloc_async allocator
    os.environ['TF_GPU_ALLOCATOR'] = 'cuda_malloc_async'
    print(f"Enabled TF_GPU_ALLOCATOR: {os.environ['TF_GPU_ALLOCATOR']}")
