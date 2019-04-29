import tensorflow as tf


class Model:

    def __init__(self, images, labels, imageSize, numClasses, batchSize, trainable):
        def loss_and_summary(logits, labels):
            cross_entropy = tf.reduce_mean(-tf.reduce_sum(labels * tf.log(logits + 1e-10), 1))
            tf.summary.scalar("cross_entropy", cross_entropy)
            return cross_entropy

        def accuracy_and_summary(logits, labels):
            correct_prediction = tf.equal(tf.argmax(logits, 1), tf.argmax(labels, 1))
            accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
            tf.summary.scalar("accuracy", accuracy)
            return accuracy

        self.images = images
        self.labels = labels
        self.imageSize = imageSize
        self.numClasses = numClasses
        self.batchSize = batchSize
        self.keepProb = tf.placeholder("float")
        self.isTraining = tf.placeholder("bool")
        self.normalizer_params = {'is_training': trainable, 'trainable': trainable}

        self.logits = self.build(self.images)
        self.loss = loss_and_summary(self.logits, self.labels)
        self.accuracy = accuracy_and_summary(self.logits, self.labels)

    def build(self, x):
        x_image = tf.reshape(x, [-1,  self.imageSize, self.imageSize, 3])
        print(x_image)

        # Convolution Layer 1
        conv1 = tf.contrib.layers.conv2d(
            x_image,
            num_outputs=32,
            kernel_size=2,
            stride=1,
            normalizer_fn=tf.contrib.layers.batch_norm,
            normalizer_params=self.normalizer_params,
        )

        print('Convolution Layer 1: ', conv1)

        # Pooling layer 1
        pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2, 2], strides=2)

        # pool1 = tf.layers.dropout(inputs=pool1, rate=1 - self.keepProb, training=self.isTraining)

        print('Pooling Layer 1: ', pool1)

        # Convolution Layer 2
        conv2 = tf.contrib.layers.conv2d(
            pool1,
            num_outputs=64,
            kernel_size=2,
            stride=1,
            normalizer_fn=tf.contrib.layers.batch_norm,
            normalizer_params=self.normalizer_params
        )

        print('Convolution Layer 2: ', conv2)

        # Pooling layer 2
        pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2, 2], strides=2)

        # pool2 = tf.layers.dropout(inputs=pool2, rate=1 - self.keepProb, training=self.isTraining)

        print('Pooling Layer 2: ', pool2)

        # Convolution Layer 3
        conv3 = tf.contrib.layers.conv2d(
            pool2,
            num_outputs=128,
            kernel_size=2,
            stride=1,
            normalizer_fn=tf.contrib.layers.batch_norm,
            normalizer_params=self.normalizer_params
        )

        print('Convolution Layer 3: ', conv3)

        # Pooling layer 3
        pool3 = tf.layers.max_pooling2d(inputs=conv3, pool_size=[2, 2], strides=2)

        # pool3 = tf.layers.dropout(inputs=pool3, rate=1 - self.keepProb, training=self.isTraining)

        print('Pooling Layer 3: ', pool3)

        # Convolution Layer 4
        conv4 = tf.contrib.layers.conv2d(
            pool3,
            num_outputs=256,
            kernel_size=2,
            stride=1,
            normalizer_fn=tf.contrib.layers.batch_norm,
            normalizer_params=self.normalizer_params
        )

        print('Convolution Layer 4: ', conv4)

        # Pooling layer 4
        pool4 = tf.layers.max_pooling2d(inputs=conv4, pool_size=[2, 2], strides=2)

        # pool4 = tf.layers.dropout(inputs=pool4, rate=1 - self.keepProb, training=self.isTraining)

        print('Pooling Layer 4: ', pool4)

        # Convolution Layer 5
        conv5 = tf.contrib.layers.conv2d(
            pool4,
            num_outputs=512,
            kernel_size=2,
            stride=1,
            normalizer_fn=tf.contrib.layers.batch_norm,
            normalizer_params=self.normalizer_params
        )

        print('Convolution Layer 5: ', conv5)

        # Pooling layer 5
        pool5 = tf.layers.max_pooling2d(inputs=conv5, pool_size=[2, 2], strides=2)

        # pool5 = tf.layers.dropout(inputs=pool5, rate=1 - self.keepProb, training=self.isTraining)

        print('Pooling Layer 5: ', pool5)

        dimension = 1
        for d in pool5.get_shape()[1:].as_list():
            dimension *= d
        pool5_flat = tf.reshape(pool5, [-1, dimension])

        pool5_flat = tf.layers.dropout(inputs=pool5_flat, rate=1 - self.keepProb, training=self.isTraining)

        print(pool5_flat)

        # 全結合層 1
        dense1 = tf.layers.dense(inputs=pool5_flat, units=1024, activation=tf.nn.relu)

        dense1 = tf.layers.dropout(inputs=dense1, rate=1 - self.keepProb, training=self.isTraining)

        print(dense1)

        # 全結合層2
        dense2 = tf.layers.dense(inputs=dense1, units=256, activation=tf.nn.relu)

        print(dense2)

        # ドロップアウト
        # dense2 = tf.layers.dropout(inputs=dense2, rate=1 - self.keepProb, training=self.isTraining)

        y_conv = tf.layers.dense(
            dense2,
            units=self.numClasses, activation=tf.nn.softmax,
            kernel_initializer=tf.truncated_normal_initializer(stddev=0.1))

        print(y_conv)

        return y_conv
