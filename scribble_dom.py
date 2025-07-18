import sys# %%
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.autograd import Variable
import argparse
import numpy as np
import pandas as pd
import torch.nn.init
from tqdm import tqdm
import pickle
import matplotlib.pyplot as plt
import os
from sklearn.metrics.cluster import adjusted_rand_score
from sklearn.metrics.pairwise import euclidean_distances
import math
from scipy import spatial
from scipy import stats
import json
import random
from code_utils.inception import Inception_block

torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

import json

import argparse


# exit()
###################
from util import * 
###################


parser = argparse.ArgumentParser(description='ScribbleSeg expert annotation pipeline')
parser.add_argument('--params', help="The input parameters json file path", required=True)
parser.add_argument('--curr_iteration', help="Current Iteration of scribble", required=True)
parser.add_argument('--n_max_scribble_files', help="Current Iteration of scribble", required=True)

args = parser.parse_args()

curr_iteration = int(args.curr_iteration)
n_max_scribble_files = int(args.n_max_scribble_files)



n_iterations = min(n_max_scribble_files,curr_iteration)
iterativescribbledom_iterations = range(curr_iteration-n_iterations+1,curr_iteration+1)


def hyp_function(cur_time, total_time):
    total = (total_time+1)*total_time/2
    return cur_time/total

with open(args.params) as f:
   params = json.load(f)
dataset = params['dataset']
n_pcs = params['n_pcs']
max_iter = params['max_iter']
nConv = params['nConv']
seed_options = params['seed_options']
lr_options = params['lr_options']
alpha_options = params['alpha_options']
samples = params['samples']
matrix_format_representation_of_data_path = params['matrix_represenation_of_ST_data_folder']
output_data_path = params['model_output_folder']
scheme = params['schema']
n_clusters = params['n_cluster_for_auto_scribble']
final_output_folder = params['final_output_folder']

use_cuda = torch.cuda.is_available()

if use_cuda:
    display("GPU available")
else:
    display("GPU not available")



intermediate_channels = n_pcs

models = []
for sample in samples:
    for seed in seed_options:
        for lr in lr_options:
            for alpha in alpha_options:
                models.append(
                    {
                        'seed': seed,
                        'lr': lr,
                        'sample': sample,
                        'alpha': alpha
                    }
                )

# %%
complete_runs = 0
for model in tqdm(models):
    ############################################
    if check_flag(ABORT):
        print('\n\n\nEXITING DUE TO ABORT!!!\n\n\n')
        # update_flag(SERVER_LOCKED,False)
        exit()
    ############################################

    seed = model['seed']
    lr = model['lr']
    sample = model['sample']
    alpha = model['alpha']

    display("\n\n************************************************\n")
    display('Model description:')
    display(f'sample: {sample}')
    display(f'seed: {seed}')
    display(f'lr: {lr}')
    display(f'alpha: {alpha}')

    sys.stdout.flush()

    # %%
    def make_directory_if_not_exist(path):
        if not os.path.exists(path):
            os.makedirs(path)

    
    local_data_folder_path = matrix_format_representation_of_data_path

    npy_path = f'{local_data_folder_path}/{dataset}/{sample}/Npys'
    pickle_path = f'{local_data_folder_path}/{dataset}/{sample}/Pickles'

    scribble_img = f'{local_data_folder_path}/{dataset}/{sample}/Scribble/manual_scribble.npy'
    iterative_scribble_img = f'{local_data_folder_path}/{dataset}/{sample}/Scribble/manual_scribble/'
    iterative_scribble_img = iterative_scribble_img + "manual_scribble_{i}.npy"
    input_pcs = f'{npy_path}/mapped_{n_pcs}.npy'
    background = npy_path+'/backgrounds.npy'
    foreground = npy_path+'/foregrounds.npy'
    pixel_barcode_file_path = f'{local_data_folder_path}/{dataset}/{sample}/Npys/pixel_barcode.npy'

    output_folder_path = f'./{output_data_path}/{dataset}/{sample}'
    leaf_output_folder_path = f'{output_folder_path}/{scheme}/Hyper_{alpha}'
    leaf_output_folder_path_model = f"{leaf_output_folder_path}/Model"

    # %%
    pixel_barcode = np.load(pixel_barcode_file_path)
    pixel_rows_cols = np.argwhere(pixel_barcode != '')
    backgrounds = np.load(background)
    foregrounds = np.load(foreground)

    # %%
    make_directory_if_not_exist(leaf_output_folder_path)
    make_directory_if_not_exist(leaf_output_folder_path_model)

    torch.manual_seed(seed)
    np.random.seed(seed)

    no_of_scribble_layers = 0

    # CNN model
    class MyNet(nn.Module):
        def __init__(self,input_dim):
            super(MyNet, self).__init__()
            self.conv1 = nn.Conv2d(input_dim, intermediate_channels, kernel_size=1, stride=1, padding=0 )
            self.bn1 = nn.BatchNorm2d(intermediate_channels)

            # inception_block(in_channels, out_1x1, red_3x3, out_3x3, red_5x5, out_5x5, out_1x1pool)
            self.inception3a = Inception_block(intermediate_channels, 160, 96, 64, 16, 16, 16)
            self.bn_i_1 = nn.BatchNorm2d(256)

            self.inception3b = nn.ModuleList()
            self.bn_i_2 = nn.ModuleList()

            if nConv >= 1:
                self.inception3b.append(Inception_block(256, 96, 32, 16, 16, 8, 8))
                self.bn_i_2.append(nn.BatchNorm2d(128))

                for i in range(nConv-1):
                    self.inception3b.append(Inception_block(128, 96, 32, 16, 16, 8, 8))
                    self.bn_i_2.append(nn.BatchNorm2d(128))

            r = last_layer_channel_count

            display('last layer size:', r)
            if nConv>=1:
                self.conv3 = nn.Conv2d(128, r, kernel_size=1, stride=1, padding=0 )
            else:
                self.conv3 = nn.Conv2d(256, r, kernel_size=1, stride=1, padding=0 )
            self.bn3 = nn.BatchNorm2d(r)

        def forward(self, x):
            x = self.conv1(x)
            x = F.relu( x )
            x = self.bn1(x)
            
            x = self.inception3a(x)
            x = F.relu( x )
            x = self.bn_i_1(x)

            for i in range(nConv):
                x = self.inception3b[i](x)
                x = F.relu( x )
                x = self.bn_i_2[i](x)

            x = self.conv3(x)
            x = self.bn3(x)
            return x

    # %%
    im = np.load(input_pcs)
    im.shape

    # %%
    data = torch.from_numpy( np.array([im.transpose( (2, 0, 1) ).astype('float32')]) ) # z, y, x
    data.shape

    # %%
    if use_cuda:
        data = data.cuda()
    data = Variable(data)
    data.shape

    # %%
    def relabel_mask(mask, background_val):
        row, col = mask.shape
        mask = mask.reshape(-1)
        values = np.unique(mask[mask != background_val])
        # lookup = {k: v for v, k in enumerate(dict.fromkeys(values))}
        if dataset == "Human_DLPFC":
            lookup = {k: k for v, k in enumerate(dict.fromkeys(values))}
        else:
            lookup = {k: k-1 for v, k in enumerate(dict.fromkeys(values))}
        lookup[background_val] = background_val
        mask = np.array([lookup[i] for i in mask])
        return mask.reshape(row, col)

    n_scibble_file = len(iterativescribbledom_iterations)
    inds_scr_array = [None for _ in range(n_scibble_file)]
    target_scr = [None for _ in range(n_scibble_file)]
    inds_sim = [None for _ in range(n_scibble_file)]
    mask_inds = [None for _ in range(n_scibble_file)]
    cnt = 0

    for scribble_idx in iterativescribbledom_iterations:
        mask = np.load(iterative_scribble_img.format(i=scribble_idx))
        foreground_val = 1000
        background_val = 255
        mask = relabel_mask(mask.copy(), background_val)
        if len(mask[mask != background_val]) == 0:
            display('Expecting some scribbles, but no scribbles are found!')
            last_layer_channel_count = 100 + added_layers
            nChannel = last_layer_channel_count
        else:
            mask_foreground = mask.copy()
            mask_foreground[foregrounds[:, 0], foregrounds[:, 1]] = foreground_val
            
            mx_label_num = mask[mask != background_val].max()
            mask = mask.reshape(-1)
            scr_idx = np.where(mask != 255)[0]
            mask_foreground = mask_foreground.reshape(-1)

            mask_inds[cnt] = np.unique(mask)
            mask_inds[cnt] = np.delete( mask_inds[cnt], np.argwhere(mask_inds[cnt]==background_val) )

            # for i in range(1, len(mask_inds)):
            #     if mask_inds[i] - mask_inds[i-1] != 1:
            #         display("Problem in scribble labels. Not increasing by 1.")

            # # Take the non-scribbled foreground into similarity component
            mask_foreground[scr_idx] = background_val
            inds_sim[cnt] = torch.from_numpy( np.where( mask_foreground == foreground_val )[ 0 ] )

            inds_scr_array[cnt] = [None for _ in range(mask_inds[cnt].shape[0])]

            for i in range(mask_inds[cnt].shape[0]):
                inds_scr_array[cnt][i] = torch.from_numpy( np.where( mask == mask_inds[cnt][i] )[ 0 ] )

            target_scr[cnt] = torch.from_numpy( mask.astype(np.int64) )

            if use_cuda:
                inds_sim[cnt] = inds_sim[cnt].cuda()
                target_scr[cnt] = target_scr[cnt].cuda()
                inds_scr_array[cnt] = [inds_scr_array[cnt][i].cuda() for i in range(mask_inds[cnt].shape[0])]


            target_scr[cnt] = Variable( target_scr[cnt] )
            cnt += 1

        minLabels = n_clusters
        nChannel = minLabels
        no_of_scribble_layers = minLabels
        last_layer_channel_count = no_of_scribble_layers


    model = MyNet( data.size(1) )

    final_output_model = f"{final_output_folder}/{dataset}/{sample}/{scheme}/final_model.pt"
    if os.path.exists(final_output_model):
        display("Loaded...")
        model.load_state_dict(torch.load(final_output_model))
    if use_cuda:
        model.cuda()
    model.train()

    loss_fn_sim = torch.nn.CrossEntropyLoss()
    loss_fn_scr = torch.nn.CrossEntropyLoss()

    optimizer = optim.SGD(model.parameters(), lr=lr, momentum=0.9)

    loss_comparison = 0
    label_colours = np.random.randint(255,size=(255,3))

    import warnings
    warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

    loss_per_itr = []
    for batch_idx in (range(max_iter)):
        optimizer.zero_grad()

        output = model( data )[ 0 ]
        output[:, backgrounds[:, 0], backgrounds[:, 1]] = 0
        output = output.permute( 1, 2, 0 )
        output = output.contiguous().view( -1, nChannel )

        ignore, target = torch.max( output, 1 )

        im_target = target.data.cpu().numpy()

        loss_sim = 0
        loss_lr = 0
        for scribble_idx in range(n_scibble_file):
            loss_sim += loss_fn_sim(output[ inds_sim[scribble_idx] ], target[ inds_sim[scribble_idx] ]) / n_scibble_file
            for i in range(mask_inds[scribble_idx].shape[0]):
                loss_lr += loss_fn_scr(output[ inds_scr_array[scribble_idx][i] ], target_scr[scribble_idx][ inds_scr_array[scribble_idx][i] ])*hyp_function(scribble_idx+1,n_scibble_file)


        loss = alpha * loss_sim + (1 - alpha) * loss_lr
        loss_per_itr.append(loss.data.cpu().numpy())

        loss.backward()
        optimizer.step()

    model_path = os.path.join(leaf_output_folder_path_model,'model.pt')
    torch.save(model.state_dict(), model_path)
    output = model( data )[ 0 ]
    output = output.permute( 1, 2, 0 ).contiguous().view( -1, nChannel )
    ignore, target = torch.max( output, 1 )
    im_target = target.data.cpu().numpy()
    im_cluster_num = im_target.reshape(im.shape[0], im.shape[1])

    labels = im_cluster_num[pixel_rows_cols[:, 0], pixel_rows_cols[:, 1]]
    ##############################
    # making 1-indexed
    # labels = [x+1 for x in labels]
    ##############################
    df_labels = pd.DataFrame({'label': labels}, index=pixel_barcode[pixel_barcode != ''])
    # display("current iteration: ", curr_iteration)
    df_labels.to_csv(f'{leaf_output_folder_path}/final_barcode_labels.csv')

    df_meta = pd.DataFrame(
        [{
            "dataset": dataset,
            "sample": sample,
            "npcs": n_pcs,
            "nconv": nConv,
            "seed": seed,
            "learing_rate": lr,
            "alpha": alpha
        }]
    )
    df_meta.to_csv(f'{leaf_output_folder_path}/meta_data.csv')

    sys.stdout.flush()

    complete_runs += 1
    pct = round((complete_runs/len(models))*100,2)
    display(f'\nModel Run Progress: {pct} %')
    display(f'{complete_runs} of {len(models)} models ran successfully\n')
