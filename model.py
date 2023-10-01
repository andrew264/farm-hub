import tensorflow as tf


class EffNet(tf.keras.Model):
    def __init__(self, num_classes: int):
        super(EffNet, self).__init__()
        self.num_classes = num_classes
        self.model_head = tf.keras.applications.efficientnet_v2.EfficientNetV2M(
            include_top=False, weights='imagenet'
        )
        self.avg_pool = tf.keras.layers.GlobalAveragePooling2D()
        self.final_layer = tf.keras.layers.Dense(self.num_classes, activation='softmax')
        intermediate_size = (num_classes + 511) // 512 * 512
        self.intermediate_layer_2 = tf.keras.layers.Dense(intermediate_size, activation='relu')
        self.intermediate_layer_1 = tf.keras.layers.Dense(intermediate_size * 2, activation='relu')

        # freeze model head
        self.model_head.trainable = False

    def call(self, inputs, training=None, mask=None):
        x = self.model_head(inputs)
        x = self.avg_pool(x)
        x = self.intermediate_layer_1(x)
        x = self.intermediate_layer_2(x)
        x = self.final_layer(x)
        return x

    def get_config(self):
        config = super(EffNet, self).get_config()
        config.update({'num_classes': self.num_classes})
        return config
