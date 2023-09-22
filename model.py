import tensorflow as tf


class EffNet(tf.keras.Model):
    def __init__(self, num_classes: int):
        super(EffNet, self).__init__()
        self.num_classes = num_classes
        self.model_head = tf.keras.applications.efficientnet_v2.EfficientNetV2S(
            include_top=False, weights='imagenet'
        )
        self.avg_pool = tf.keras.layers.GlobalAveragePooling2D()
        self.dense1 = tf.keras.layers.Dense(512, activation='relu')
        self.dense2 = tf.keras.layers.Dense(128, activation='relu')
        self.dense3 = tf.keras.layers.Dense(self.num_classes, activation='softmax')

        # freeze model head
        self.model_head.trainable = False

    def call(self, inputs, training=None, mask=None):
        x = self.model_head(inputs)
        x = self.avg_pool(x)
        x = self.dense1(x)
        x = self.dense2(x)
        x = self.dense3(x)
        return x

    def get_config(self):
        config = super(EffNet, self).get_config()
        config.update({'num_classes': self.num_classes})
        return config
