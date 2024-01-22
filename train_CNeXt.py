import torch

from torch import optim, nn
from torchvision.transforms import transforms
from torch.utils.data import DataLoader, Dataset
from torchvision.datasets import ImageFolder

from model import CNeXt

train_data = './datasets/images/train'
val_data = './datasets/images/valid'
batch_size = 256
device = torch.device("cuda")


def train_model(classifier: nn.Module, train_loader, val_loader, num_epochs):
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = optim.Adam(classifier.parameters(), lr=0.001, fused=True)
    for epoch in range(num_epochs):
        for i, (images, labels) in enumerate(train_loader):
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = classifier(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            if i % 100 == 0:
                print('Epoch [{}/{}], Step [{}/{}], Loss: {:.4f}'.format(epoch + 1, num_epochs, i + 1,
                                                                         len(train_loader), loss.item()))

        # Evaluate on validation set
        with torch.no_grad():
            correct = 0
            total = 0
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)
                outputs = classifier(images)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

            accuracy = 100 * correct / total
            print('Epoch [{}/{}], Validation Accuracy: {:.2f}%'.format(epoch + 1, num_epochs, accuracy))

        # Save the fine-tuned model
        torch.save(classifier.state_dict(), 'models/convnext_small.pth')


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
    train_model(model, train_loader=train_dataset, val_loader=val_dataset, num_epochs=1)

