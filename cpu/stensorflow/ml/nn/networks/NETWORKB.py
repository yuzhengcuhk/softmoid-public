#!/usr/bin/env python
# coding=utf-8
"""
   Ant Group
   Copyright (c) 2004-2020 All Rights Reserved.
   ------------------------------------------------------
   File Name : CNN
   Description :
   This is a 4-layer convolutional neural network that has the following structure.
   First is a 2-dimensional convolutional layer with 1 input channel, 16 output channels and a 5×5 filter.
   The activation functions following this layer are ReLU, followed by a 2×2 Average pool.
   The second layer is a 2-dimensional convolutional layer with 16 input channels, 16 output channels and another 5×5 filter.
   The activation functions following this layer are once again ReLU and a 2 × 2 Average pool.
   The third layer is an 256×100 fully-connected layer. The next activation function is ReLU.
   The final layer is a 100 × 10 linear layer and this is normalized using ASM(·) to get a probability distribution.
   Here, ASM(u_i)= ReLu(u_i)/sum(ReLu(u_0),ReLu(u_1),...ReLu(u_i),....)
   The loss function is cross entropy and stochastic gradient descent is used to minimize loss.
"""

from stensorflow.ml.nn.networks.NN import NN
from stensorflow.ml.nn.layers.layer import Layer
from stensorflow.ml.nn.layers.input import Input
from stensorflow.ml.nn.layers.relu import ReLU
from stensorflow.ml.nn.layers.conv2d import Conv2d
from stensorflow.ml.nn.layers.pooling import AveragePooling2D, MaxPooling2D
from stensorflow.basic.basic_class.pair import SharedVariablePair
from stensorflow.ml.nn.layers.loss import CrossEntropyLossWithSoftmax
from stensorflow.ml.nn.layers.flatten import Flatten
from stensorflow.ml.nn.layers.dense import Dense
import numpy as np
from stensorflow.random import random


class NetworkB(NN):
    def __init__(self, feature, label, pooling='max'):
        super(NetworkB, self).__init__()
        # input layer, init data；
        layer = Input(dim=28, x=feature)
        self.addLayer(layer)
        # convolutional layer with 1 input channel, 16 output channels and a 5×5 filter
        layer = Conv2d(output_dim=None, fathers=[layer], filters=16,
                       kernel_size=5, input_shape=[28, 28, 1])
        self.addLayer(layer)
        # Relu Layer
        layer = ReLU(output_dim=layer.output_dim, fathers=[layer])
        self.addLayer(layer)
        # Average pool
        if pooling == 'max':
            layer = MaxPooling2D(output_dim=None, fathers=[layer], pool_size=(2, 2))
        else:
            layer = AveragePooling2D(output_dim=None, fathers=[layer], pool_size=(2, 2))

        self.addLayer(layer)
        # 16 input channels, 16 output channels and another 5×5 filter
        layer = Conv2d(output_dim=None, fathers=[layer], filters=16,
                       kernel_size=5, input_shape=layer.output_dim
                       )
        self.addLayer(layer)
        # Relu Layer
        layer = ReLU(output_dim=layer.output_dim, fathers=[layer])
        self.addLayer(layer)
        # Average pool
        if pooling == 'max':
            layer = MaxPooling2D(output_dim=None, fathers=[layer], pool_size=(2, 2))
        else:
            layer = AveragePooling2D(output_dim=None, fathers=[layer], pool_size=(2, 2))

        self.addLayer(layer)
        # flatten data, only consider data_format = "NWHC"
        layer = Flatten(output_dim=None, fathers=[layer])
        self.addLayer(layer)
        # 全连接层
        # 256×100 fully-connected layer
        layer = Dense(output_dim=100, fathers=[layer])
        self.addLayer(layer)
        # Relu Layer
        layer = ReLU(output_dim=layer.output_dim, fathers=[layer])
        self.addLayer(layer)
        # a 100 × 10 linear layer
        layer = Dense(output_dim=10, fathers=[layer])
        self.addLayer(layer)
        # 输出层
        layer_label = Input(dim=10, x=label)
        self.addLayer(ly=layer_label)
        # 损失层
        layer_loss = CrossEntropyLossWithSoftmax(layer_score=layer, layer_label=layer_label)
        self.addLayer(ly=layer_loss)

    def predict(self, x, out_prob=True):
        """
        Generates output predictions for the input samples.
        :param x: Input samples.
        :param out_prob: True or False
        :return: The predicted result or probability
        """
        self.cut_off()
        # Input Layer
        l_input = self.layers[0]
        assert isinstance(l_input, Input)
        l_input.replace(x)
        self.layers[0] = l_input
        # Output Layer
        ly = self.layers[-1]
        if not isinstance(ly, Layer):
            raise Exception("l must be a Layer")
        else:
            ly.forward()

        if out_prob:
            return ly.y
        else:
            return ly.score

    def predict_to_file(self, sess, x, predict_file_name,
                        pred_batch_num, model_file_machine,
                        out_prob=True):
        """
        Save prediction results to file
        Computation is done in batches.
        :param sess: session
        :param x: PrivateTensor. Input samples.
        :param predict_file_name: String.
        :param pred_batch_num: Number of samples per batch.
        :param model_file_machine: String.
        :param with_sigmoid:
        :return:
        """
        y_pred = self.predict(x=x,  out_prob=out_prob)
        id_y_pred = y_pred.to_tf_str(owner=model_file_machine)
        random.random_init(sess)
        # 分批写入文件
        with open(predict_file_name, "w") as f:
            for batch in range(pred_batch_num):
                records = sess.run(id_y_pred)
                records = "\n".join(records.astype('str'))
                # records.to_file()
                f.write(records + "\n")

    def print(self, model_file_machine, sess):
        """
        print model weights
        """
        for ly in self.layers:
            if isinstance(ly, Dense) or isinstance(ly, Conv2d):
                print(ly)
                for weight in ly.w:
                    print(weight)
                    weight = weight.to_tf_tensor(owner=model_file_machine)
                    print("***")
                    print(sess.run(weight))

    def replace_weight(self, keras_weight):
        """
        将传入的权重赋值给当前网络
        """
        i = 0
        for ly in self.layers:
            if isinstance(ly, Conv2d):
                # 用传入的权重直接进行预测
                # kernel = SharedPair(ownerL="L", ownerR="R", shape=keras_weight[i].shape)
                # kernel.load_from_numpy(keras_weight[i])
                # ly.w[0] = kernel
                # 用传入的权重进行训练
                kernel = ly.w[0]
                assert isinstance(kernel, SharedVariablePair)
                kernel.load_from_tf_tensor(keras_weight[i])
                i += 1

            if isinstance(ly, Dense):
                # 用传入的权重直接进行预测
                # kernel1 = SharedPair(ownerL="L", ownerR="R", shape=keras_weight[i].shape)
                # kernel1.load_from_numpy(keras_weight[i])
                # ly.w[0] = kernel1
                # kernel2 = SharedPair(ownerL="L", ownerR="R", shape=keras_weight[i+1].shape)
                # kernel2.load_from_numpy(keras_weight[i+1])
                # ly.w[1] = kernel2
                # 用传入的权重进行训练
                kernel1 = ly.w[0]
                assert isinstance(kernel1, SharedVariablePair)
                kernel1.load_from_tf_tensor(keras_weight[i])
                kernel2 = ly.w[1]
                assert isinstance(kernel2, SharedVariablePair)
                kernel2.load_from_tf_tensor(keras_weight[i+1])
                i += 2

    def save_model(self, sess, save_file_path, model_file_machine):
        """
        Save the model weights to npz file.
        :param sess: session
        :param save_file_path: String, path to save the model.
        :param model_file_machine: String, the machine name.
        :return:
        """
        res = []
        for ly in self.layers:
            if isinstance(ly, Dense) or isinstance(ly, Conv2d):
                for weight in ly.w:
                    weight = weight.to_tf_tensor(owner=model_file_machine)
                    weight = sess.run(weight)
                    res.append(weight)
        res = np.array(res)
        np.savez(save_file_path, weight=res)




