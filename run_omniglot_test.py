import os
import numpy as np
import tensorflow as tf
import argparse
from models.classifiers import MNISTClassifier
from components.learners import Learner
import data.omniglot as omniglot

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--load_params', help='', action='store_true', default=False)
parser.add_argument('--num_inner_iters', help='', default=10, type=int)
args = parser.parse_args()


if os.path.exists("/Users/Aaron-MAC/mldata/omniglot"):
    DATA_DIR = "/Users/Aaron-MAC/mldata/omniglot"
else:
    DATA_DIR = "/data/ziz/not-backed-up/jxu/omniglot"
meta_train_set, meta_test_set = omniglot.load(data_dir=DATA_DIR, inner_batch_size=5, num_train=1200, augment_train_set=False, one_hot=True)


model = MNISTClassifier(num_classes=5, inputs=None, targets=None)
update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
with tf.control_dependencies(update_ops):
    optimizer = tf.train.AdamOptimizer(1e-4).minimize(model.loss)

global_init_op = tf.global_variables_initializer()

saver = tf.train.Saver()
save_dir = "/data/ziz/jxu/hmaml-saved-models"

config = tf.ConfigProto()
config.gpu_options.allow_growth = True
with tf.Session(config=config) as sess:
    sess.run(global_init_op)

    if args.load_params:
        ckpt_file = save_dir + '/params_' + "mnist" + '.ckpt'
        print('restoring parameters from', ckpt_file)
        saver.restore(sess, ckpt_file)
    acc_arr = []
    for dk in range(20):
        print(dk, "resample dataset...")
        train_set, val_set = meta_train_set.sample_mini_dataset(num_classes=5, num_shots=15, test_shots=5)

        learner = Learner(session=sess, model=model)
        accs = []
        for epoch in range(args.num_inner_iters):
            # print(epoch, "......")
            learner.train(train_set, optimizer)
            evals = learner.evaluate(val_set)
            accs.append(evals["accuracy"])
        acc_arr.append(accs)
    m = np.array(acc_arr)
    print(m.mean(0))
