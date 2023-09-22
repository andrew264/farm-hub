import tensorflow as tf
from keras.optimizers import Lion

from model import EffNet
from utils import enable_memory_growth

enable_memory_growth()
# tf.keras.mixed_precision.set_global_policy('mixed_bfloat16')
print(f"Global dtype policy: {tf.keras.mixed_precision.global_policy()}")
# tf.config.run_functions_eagerly(True)

train_data = './datasets/images/train'
val_data = './datasets/images/valid'
image_size = (512, 512)
batch_size = 128

if __name__ == '__main__':
    train_dataset = tf.keras.preprocessing.image_dataset_from_directory(
        train_data,
        image_size=image_size,
        batch_size=batch_size,
    )
    val_dataset = tf.keras.preprocessing.image_dataset_from_directory(
        val_data,
        image_size=image_size,
    )

    class_names = train_dataset.class_names
    num_classes = len(class_names)

    model = EffNet(num_classes=num_classes)
    model.build(input_shape=(batch_size, *image_size, 3))

    model.compile(optimizer=Lion(lr=0.001), loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'], jit_compile=True)
    model.summary()

    model.fit(train_dataset, epochs=2, validation_data=val_dataset)
    model.save_weights('./models/effnetv2s.h5')
