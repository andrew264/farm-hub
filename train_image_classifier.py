import os
import time

import torch
from torch import optim, nn
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from torchvision.transforms import transforms

from model import CNeXt

train_data = './datasets/images/train'
val_data = './datasets/images/valid'
batch_size = 256
device = torch.device("cuda")


def train_model(classifier: nn.Module, train_loader: DataLoader, val_loader: DataLoader, num_epochs=1):
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = optim.Adam(classifier.parameters(), lr=1e-4, fused=True)
    for epoch in range(num_epochs):
        losses = []
        time_start = time.time()
        for i, (images, labels) in enumerate(train_loader):
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = classifier(images)
            loss = criterion(outputs, labels)
            losses.append(loss.item())
            loss.backward()
            optimizer.step()

            if i > 1 and i % 100 == 0:
                loss_val = sum(losses) / len(losses)
                print('Epoch [{}/{}], Step [{}/{}], Loss: {:.4f}'.format(epoch + 1, num_epochs, i + 1,
                                                                         len(train_loader), loss_val))
        loss_val = sum(losses) / len(losses)
        print('Epoch [{}/{}], Step [{}/{}], Loss: {:.4f}'.format(epoch + 1, num_epochs, i + 1,
                                                                 len(train_loader), loss_val))
        print(f"Epoch {epoch + 1} took {time.time() - time_start} seconds")

        # Evaluate on validation set
        validate_model(classifier, val_loader)

        # Save the fine-tuned model
        torch.save(classifier.state_dict(), 'models/convnext_small.pth')


def validate_model(classifier, val_loader):
    classifier.eval()
    with torch.no_grad():
        class_correct = list(0. for i in range(num_classes))  # Initialize correct counts for each class
        class_total = list(0. for i in range(num_classes))  # Initialize total counts for each class
        for images, labels in val_loader:
            images = images.to(device)
            labels = labels.to(device)
            outputs = classifier(images)
            _, predicted = torch.max(outputs.data, 1)
            c = (predicted == labels).squeeze()  # Get correct predictions for each class
            for i in range(num_classes):
                label = labels[i]
                class_correct[label] += c[i].item()
                class_total[label] += 1

        # Calculate and print accuracy for each class
        for i in range(num_classes):
            class_accuracy = 100 * class_correct[i] / class_total[i]
            print('Accuracy of class {}: {:.2f} %'.format(i, class_accuracy))

        # Calculate and print overall accuracy
        overall_accuracy = 100 * sum(class_correct) / sum(class_total)
        print('Accuracy of the model on the validation set: {:.2f} %'.format(overall_accuracy))
        print(f"Total correct: {sum(class_correct)}")
        print(f"Total: {sum(class_total)}")
    classifier.train()


if __name__ == '__main__':
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    }
    train = ImageFolder(train_data, transform=data_transforms['train'])
    valid = ImageFolder(val_data, transform=data_transforms['val'])
    train_dataset = DataLoader(train, batch_size=batch_size, shuffle=True, num_workers=4)
    val_dataset = DataLoader(valid, batch_size=batch_size, shuffle=False, num_workers=4)

    class_names = train.classes
    num_classes = len(class_names)
    print(f"Total classes: {num_classes}")
    with open('models/num_classes.txt', 'w') as f:
        f.write(str(num_classes))

    model = CNeXt(num_classes=num_classes)
    model.to(dtype=torch.float32, device=device)
    if os.path.exists('models/convnext_small.pth'):
        model.load_state_dict(torch.load('models/convnext_small.pth'))
        print("Loaded model from disk")
    train_model(model, train_loader=train_dataset, val_loader=val_dataset, num_epochs=1)
    # validate_model(model, val_dataset)