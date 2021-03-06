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
from PIL import Image
#from matplotlib import pyplot as plt
from torch.utils.data import DataLoader


def get_accuracy(y_pred, y):
    y_argmax = torch.round(y_pred)

    return torch.mean((y_argmax==y).type(torch.float))

def save_images(y_pred, y):
    y = y * 255

    y_argmax = torch.round(y_pred)
    y_pred = y_pred * 255

    prints = y.cpu().detach().numpy().astype(np.uint8)
    #train = TrainDataset()
    #palette = Image.open(train.train_annotations[0][0][0])
    for i in range(len(prints[0][0])):
        c = Image.fromarray(prints[0][0][i], mode='P')#.resize(size=palette.size)
        #c.putpalette(palette.getpalette())
        c.save('./SavedImages/%d_%d.png' % (i, config.epoch), "PNG", mode='P')

    prints2 = y_argmax.cpu().detach().numpy().astype(np.uint8)
    for i in range(len(prints2[0][0])):
        c = Image.fromarray(prints2[0][0][i], mode='P')#.resize(size=palette.size)
        #c.putpalette(palette.getpalette())
        c.save('./SavedImages/%d_%d pred.png' % (i, config.epoch), "PNG", mode='P')

def train(model, dloader, criterion, optimizer):
    model.train()
    losses, accs = [], []

    for i, sample in enumerate(dloader):
        video_inputs_batch, video_annotations_batch, video_annotations_indeces_batch, video_annotations_mask_batch = sample
        video_annotations_indeces_batch = video_annotations_indeces_batch.cpu().detach().numpy()

        optimizer.zero_grad()
        video_inputs_batch, video_annotations_batch = video_inputs_batch.type(torch.float), video_annotations_batch.type(torch.float)
        video_annotations_mask_batch = video_annotations_mask_batch.type(torch.float)
   
        if config.use_cuda:
            video_inputs_batch = video_inputs_batch.cuda()
            video_annotations_batch = video_annotations_batch.cuda()
            video_annotations_mask_batch = video_annotations_mask_batch.cuda()

        y_pred, _ = model(video_inputs_batch, video_inputs_batch[:, :, 0], video_annotations_batch[:, :, 0])
        #print('Finished prediction %d...' % i)
        loss = criterion(y_pred, video_annotations_batch) * video_annotations_mask_batch
        loss = loss.mean()
        acc = get_accuracy(y_pred[:, :, video_annotations_indeces_batch[0][0], :, :], video_annotations_batch[:, :, video_annotations_indeces_batch[0][0], :, :])
        if i == 0:
            save_images(y_pred[:, :, video_annotations_indeces_batch[0][0], :, :], video_annotations_batch[:, :, video_annotations_indeces_batch[0][0], :, :])
        loss.backward()
        optimizer.step()
		
        losses.append(loss.item())
        accs.append(acc.item())

    print('Finished predictions...')
    return float(np.mean(losses)), float(np.mean(accs))

def run_experiment():
    print("runnning...")
    train_dataset = TrainDataset()
    print("dataset loaded...")
    criterion = nn.BCELoss(reduction='none')
    model = VOSModel()

    #load_model = torch.load(config.model_path)
    #model.load_state_dict(load_model['state_dict'])

    if config.use_cuda:
        model.cuda()
    optimizer = torch.optim.Adam(model.parameters(), weight_decay=config.weight_decay)
    print("model loaded...")
    best_loss = 1000000

    losses = []
    accuracies = []
    for epoch in range(1, config.n_epochs + 1):
        print('Epoch:', epoch)
        config.epoch = epoch
        dloader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True, num_workers=8)
        #video_inputs_batch, video_annotations_batch, video_annotations_indeces_batch = train_dataset.Datalaoder()

        loss, acc = train(model, dloader, criterion, optimizer)
        print('Finished training. Loss: ',  loss, ' Accuracy: ', acc)
        losses.append(loss)
        accuracies.append(acc)
        if epoch % 5 == 0:
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