import config
import torch
import os
import random
from torch.autograd.variable import Variable
import numpy as np
from dataloader import TrainDataset, ValidationDataset
import torch.nn as nn
import torch.optim as optim
from model import VOSModel
#from matplotlib import pyplot as plt

def get_accuracy(y_pred, y):
    y_argmax = torch.round(y_pred)
    return torch.mean((y_argmax==y).type(torch.float))

def train(model, video_inputs_batch, video_annotations_batch, video_annotations_indeces_batch, criterion, optimizer):
    model.train()

    optimizer.zero_grad()
    video_inputs_batch = torch.from_numpy(video_inputs_batch)
    video_annotations_batch = torch.from_numpy(video_annotations_batch)
    video_inputs_batch, video_annotations_batch = video_inputs_batch.type(torch.float), video_annotations_batch.type(torch.float)
    if config.use_cuda:
        video_inputs_batch = video_inputs_batch.cuda()
        video_annotations_batch = video_annotations_batch.cuda()
    #print(video_inputs_batch[:, :, 0])
    #print(video_annotations_batch[:, :, 0])

    y_pred, _ = model(video_inputs_batch, video_inputs_batch[:, :, 0], video_annotations_batch[:, :, 0])
    print('Finished predictions...')

    loss = criterion(y_pred[:, :, video_annotations_indeces_batch[0][0], :, :], video_annotations_batch[:, :, video_annotations_indeces_batch[0][0], :, :])
    acc = get_accuracy(y_pred[:, :, video_annotations_indeces_batch[0][0], :, :], video_annotations_batch[:, :, video_annotations_indeces_batch[0][0], :, :])
    loss.backward()
    optimizer.step()

    return loss.item(), acc.item()

def run_experiment():
    print("runnning...")
    train_dataset = TrainDataset()
    print("dataset loaded...")
    criterion = nn.BCELoss(reduction='mean')
    model = VOSModel()
    if config.use_cuda:
        model.cuda()
    optimizer = torch.optim.Adam(model.parameters(), weight_decay=config.weight_decay)
    print("model loaded...")
    best_loss = 1000000

    losses = []
    accuracies = []
    for epoch in range(1, config.n_epochs + 1):
        print('Epoch:', epoch)
        video_inputs_batch, video_annotations_batch, video_annotations_indeces_batch = train_dataset.Datalaoder()

        loss, acc = train(model, video_inputs_batch, video_annotations_batch, video_annotations_indeces_batch, criterion, optimizer)
        print('Finished training. Loss: ',  loss, ' Accuracy: ', acc)
        losses.append(loss)
        accuracies.append(acc)
        if loss < best_loss:
            print('Model Improved -- Saving.')
            best_loss = loss

            save_file_path = os.path.join(config.save_dir, 'model_{}_{:.4f}.pth'.format(epoch, loss))
            states = {
                'epoch': epoch + 1,
                'state_dict': model.state_dict(),
                'optimizer': optimizer.state_dict(),
            }

            try:
                os.mkdir(config.save_dir)
            except:
                pass

            torch.save(states, save_file_path)
            print('Model saved ', str(save_file_path))
    else:
        save_file_path = os.path.join(config.save_dir, 'modeel_{}_{:.4f}.pth'.format(epoch, loss))
        states = {
            'epoch': epoch + 1,
            'state_dict': model.state_dict(),
            'optimizer': optimizer.state_dict(),
        }

        try:
            os.mkdir(config.save_dir)
        except:
            pass

        torch.save(states, save_file_path)

    print('Training Finished')
    # multiple line plot
    # multiple line plot
    #plt.plot(losses, label='loss')
    #plt.plot(accuracies, label='accuracy')
    #plt.legend()
    #plt.axis([0, 99, 0, 1])
    #plt.show()


if __name__ == '__main__':
    run_experiment()