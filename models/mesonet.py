"""
MesoNet (Meso4 variant) — deepfake-specific lightweight CNN.

Reference:
    Afchar, D., Nozick, V., Yamagishi, J., & Echizen, I. (2018).
    "MesoNet: a Compact Facial Video Forgery Detection Network."
    https://arxiv.org/abs/1809.00888
"""

import torch
import torch.nn as nn


class Meso4(nn.Module):
    """
    Meso4 architecture for deepfake face detection.

    Architecture:
        4 convolutional blocks with BatchNorm + MaxPool,
        followed by a fully-connected classifier.
    Input:  (B, 3, 224, 224)
    Output: (B, num_classes)
    """

    def __init__(self, num_classes: int = 2):
        super().__init__()

        self.features = nn.Sequential(
            # Block 1: 224 → 112
            nn.Conv2d(3, 8, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(8),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 2: 112 → 56
            nn.Conv2d(8, 8, kernel_size=5, padding=2, bias=False),
            nn.BatchNorm2d(8),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 3: 56 → 28
            nn.Conv2d(8, 16, kernel_size=5, padding=2, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 4: 28 → 7
            nn.Conv2d(16, 16, kernel_size=5, padding=2, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=4, stride=4),
        )

        self.classifier = nn.Sequential(
            nn.Dropout(p=0.5),
            nn.Flatten(),
            nn.Linear(16 * 7 * 7, 16),
            nn.LeakyReLU(negative_slope=0.1, inplace=True),
            nn.Dropout(p=0.5),
            nn.Linear(16, num_classes),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.classifier(x)
        return x
