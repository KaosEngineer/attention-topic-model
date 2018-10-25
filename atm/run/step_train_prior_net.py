#! /usr/bin/env python

import argparse
import os
import sys

import tensorflow as tf

import context
from core.utilities.utilities import text_to_array, get_train_size_from_meta
from atm.atm import ATMPriorNetwork

parser = argparse.ArgumentParser(description='Compute features from labels.')
parser.add_argument('--valid_size', type=int, default=14188,
                               help='Specify the validation set size')
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
parser.add_argument('--n_samples', type=int, default=1,
                               help='Specify the number of negative samples to take')
parser.add_argument('--seed', type=int, default=100,
                               help='Specify the global random seed')
parser.add_argument('--name', type=str, default='model',
                               help='Specify the name of the model')
parser.add_argument('--debug', type=int, choices=[0, 1, 2], default=0,
                               help='Specify the debug output level')
parser.add_argument('--load_path', type=str, default='./',
                               help='Specify path to model which should be loaded')
parser.add_argument('--init', type=str, default=None,
                               help='Specify path to from which to initialize model')
parser.add_argument('--distortion', type=float, default=1.0,
                               help='Specify whether to use uniform negative sampliong')
parser.add_argument('--epoch', type=str, default=None,
                               help='which should be loaded')
parser.add_argument('train_data_in_domain', type=str,
                    help='which should be loaded')
parser.add_argument('train_data_out_domain', type=str,
                    help='which should be loaded')
parser.add_argument('meta_data_path_in_domain', type=str,
                    help='Path to the meta data file (which contains the dataset size and number of topics).')
parser.add_argument('meta_data_path_out_domain', type=str,
                    help='Path to the meta data file (which contains the dataset size and number of topics).')
parser.add_argument('valid_data', type=str,
                               help='which should be loaded')
parser.add_argument('topic_path', type=str,
                               help='which should be loaded')
parser.add_argument('topic_count_path', type=str,
                               help='which should be loaded')
parser.add_argument('topic_path_in_domain', type=str,
                    help='which should be loaded')
parser.add_argument('topic_count_path_out_domain', type=str,
                    help='which should be loaded')
parser.add_argument('wlist_path', type=str,
                               help='which should be loaded')
parser.add_argument('--strip_start_end', action='store_true', help='whether to strip the <s> </s> marks at the beginning and end of prompts in sorted_topics.txt file (used for legacy sorted_topics.txt formatting')


def main(args):
    if not os.path.isdir('CMDs'):
        os.mkdir('CMDs')
    with open('CMDs/step_train_attention_grader.cmd', 'a') as f:
        f.write(' '.join(sys.argv) + '\n')
        f.write('--------------------------------\n')

    train_size = get_train_size_from_meta(args.meta_data_path_in_domain)

    topics_in_domain, topic_lens_in_domain = text_to_array(args.topic_path_out_domain, args.wlist_path,
                                                           strip_start_end=args.strip_start_end)
    topics_out_domain, topic_lens_out_domain = text_to_array(args.topic_path_out_domain, args.wlist_path,
                                                             strip_start_end=args.strip_start_end)
    if args.strip_start_end: print("Stripping the first and last word (should correspond to <s> and </s> marks) "
                                   "from the input prompts. Should only be used with legacy dataset formatting")

    atm = ATMPriorNetwork(network_architecture=None,
                          seed=args.seed,
                          name=args.name,
                          save_path='./',
                          load_path=args.load_path,
                          debug_mode=args.debug,
                          epoch=args.epoch)

    atm.fit_prior_net(train_data_in_domain=args.train_data_in_domain,
                      train_data_out_domain=args.train_data_out_domain,
                      valid_data=args.valid_data,
                      load_path=args.init,
                      topics_in_domain=topics_in_domain,
                      topics_out_domain=topics_out_domain,
                      topic_lens_in_domain=topic_lens_in_domain,
                      topic_lens_out_domain=topic_lens_out_domain,
                      unigram_path_in_domain=args.topic_count_path_in_domain,
                      unigram_path_out_domain=args.topic_count_path_out_domain,
                      train_size=train_size,
                      learning_rate=args.learning_rate,
                      lr_decay=args.lr_decay,
                      dropout=args.dropout,
                      distortion=args.distortion,
                      batch_size=args.batch_size,
                      optimizer=tf.train.AdamOptimizer,
                      optimizer_params={},
                      n_epochs=args.n_epochs,
                      epoch=0,
                      which_trn_cost='contrastive')


    atm.save()

if __name__ == '__main__':
    args = parser.parse_args()
    main(args)