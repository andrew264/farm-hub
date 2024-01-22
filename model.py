from torch import nn
from torchvision.models import convnext_small, ConvNeXt_Small_Weights


class CNeXt(nn.Module):
    def __init__(self, num_classes: int):
        super(CNeXt, self).__init__()
        self.num_classes = num_classes
        self.model_head = convnext_small(weights=ConvNeXt_Small_Weights.DEFAULT)
        for param in self.model_head.parameters():
            param.requires_grad = False
        self.model_head.classifier[2] = nn.Linear(768, num_classes)

    def forward(self, inputs):
        return self.model_head(inputs)

    def get_config(self):
        config = super(CNeXt, self).get_config()
        config.update({'num_classes': self.num_classes})
        return config
