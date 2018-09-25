#! /usr/bin/env python
"""
The directory structure within the teacher_data_dir should have the following structure:
/teacher_data_dir
    /epoch1
        /tfrecords
            relevance.train.tfrecords
            relevance.valid.tfrecords
            input.wlist.index
            sorted_topics.txt
            unigrams.txt
            dataset_meta.txt
    /epoch1
        ...
"""

from __future__ import print_function
import argparse
import os
import sys

import tensorflow as tf

import context
from core.utilities.utilities import text_to_array, get_train_size_from_meta
from atm.atm import AttentionTopicModelStudent

parser = argparse.ArgumentParser(description='Compute features from labels.')
# parser.add_argument('--valid_size', type=int, default=14188,  # 1034,##28375,
#                                help='Specify the validation set size')
# parser.add_argument('train_size', type=int,
#                     help='which should be loaded')
parser.add_argument('--load_path', type=str, default='./',
                    help='Specify path to model which should be loaded')

parser.add_argument('teacher_data_dir', type=str,
                    help='Directory with teacher data.')
parser.add_argument('--valid_file', type=str, default='relevance.valid.tfrecords',
                    help='file name of the validation tfrecords file')
parser.add_argument('--train_file', type=str, default='relevance.train.tfrecords',
                    help='file name of the training tfrecords file')
parser.add_argument('--topic_file', type=str, default='sorted_topics.txt',
                    help='which should be loaded')
parser.add_argument('--topic_count_file', type=str, default='unigrams.txt',
                    help='which should be loaded')
parser.add_argument('--wlist_file', type=str, default='input.wlist.index',
                    help='which should be loaded')
parser.add_argument('--meta_file', type=str, default='dataset_meta.txt')

parser.add_argument('--num_teachers', type=int, default=10,
                    help='Specify how many teacher predictions there are in the training set.')
parser.add_argument('--batch_size', type=int, default=100,
                    help='Specify the training batch size')
parser.add_argument('--learning_rate', type=float, default=1e-3,
                    help='Specify the intial learning rate')
parser.add_argument('--lr_decay', type=float, default=0.85,
                    help='Specify the learning rate decay rate')
parser.add_argument('--dropout', type=float, default=1.0,
                    help='Specify the dropout keep probability')
parser.add_argument('--n_epochs', type=int, default=1,
                    help='Specify the number of epoch to run training for')
parser.add_argument('--seed', type=int, default=100,
                    help='Specify the global random seed')
parser.add_argument('--name', type=str, default='model',
                    help='Specify the name of the model')
parser.add_argument('--debug', type=int, choices=[0, 1, 2], default=0,
                    help='Specify the debug output level')
parser.add_argument('--init', type=str, default=None,
                    help='Specify path to from which to initialize model')
parser.add_argument('--distortion', type=float, default=1.0,
                    help='Specify whether to use uniform negative sampliong')
parser.add_argument('--load_epoch', type=str, default=None,
                    help='Epoch which should be loaded. Initialise new model if None.')
parser.add_argument('--strip_start_end', action='store_true',
                    help='whether to strip the <s> </s> marks at the beginning and end of prompts in sorted_topics.txt '
                         'file (used for legacy sorted_topics.txt formatting')



def main(args):
    if not os.path.isdir('CMDs'):
        os.mkdir('CMDs')
    with open('CMDs/step_train_attention_grader.cmd', 'a') as f:
        f.write(' '.join(sys.argv) + '\n')
        f.write('--------------------------------\n')

    if args.strip_start_end: print("Stripping the first and last word (should correspond to <s> and </s> marks) from the input prompts. Should only be used with legacy dataset formatting")

    for epoch in range(0, args.n_epochs):

        atm_student = AttentionTopicModelStudent(network_architecture=None,
                                                 seed=args.seed,
                                                 name=args.name,
                                                 save_path='./',
                                                 load_path=args.load_path,
                                                 debug_mode=args.debug,
                                                 epoch=args.load_epoch,
                                                 num_teachers=args.num_teachers)

        # Get the paths to all the relevant files for this epoch
        epoch_tfrecords_dir = os.path.join(args.teacher_data_dir, 'epoch' + str(epoch + 1), 'tfrecords')
        topic_path = os.path.join(epoch_tfrecords_dir, args.topic_file)
        wlist_path = os.path.join(epoch_tfrecords_dir, args.wlist_file)

        topic_count_path = os.path.join(epoch_tfrecords_dir, args.topic_count_path)

        train_data = os.path.join(epoch_tfrecords_dir, args.train_file)
        valid_data = os.path.join(epoch_tfrecords_dir, args.valid_file)

        dataset_meta_path = os.path.join(epoch_tfrecords_dir, args.meta_file)

        topics, topic_lens = text_to_array(topic_path, wlist_path, strip_start_end=args.strip_start_end)

        train_size = get_train_size_from_meta(dataset_meta_path)

        if epoch == 0:
            init = args.init
        else:
            init = None
        atm_student.fit_student(train_data=train_data,
                                valid_data=valid_data,
                                load_path=init,
                                topics=topics,
                                topic_lens=topic_lens,
                                unigram_path=topic_count_path,
                                train_size=train_size,
                                learning_rate=args.learning_rate,
                                lr_decay=args.lr_decay,
                                dropout=args.dropout,
                                distortion=args.distortion,
                                batch_size=args.batch_size,
                                optimizer=tf.train.AdamOptimizer,
                                optimizer_params={},
                                n_epochs=1,
                                epoch=epoch)

        atm_student.save()

        # Reset the graph so that the model can be reloaded for the next epoch (not the nicest way to do it, I know)
        tf.reset_default_graph()



if __name__ == '__main__':
    args = parser.parse_args()
    main(args)