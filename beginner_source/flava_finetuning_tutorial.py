# -*- coding: utf-8 -*-
"""
TorchMultimodal Tutorial: Finetuning FLAVA
============================================
"""

######################################################################
# Multimodal AI has recently become very popular owing to its ubiquitous
# nature, from use cases like image captioning and visual search to more
# recent applications like image generation from text. **TorchMultimodal
# is a library powered by Pytorch consisting of building blocks and end to
# end examples, aiming to enable and accelerate research in
# multimodality**.
# 
# In this tutorial, we will demonstrate how to use a **pretrained SoTA
# model called** `FLAVA <https://arxiv.org/pdf/2112.04482.pdf>`__ **from
# TorchMultimodal library to finetune on a multimodal task i.e. visual
# question answering** (VQA).
# 


######################################################################
# Installations
#
#
# We will use TextVQA dataset from HuggingFace for this
# tutorial. So we install datasets in addition to TorchMultimodal.

import os
import sys
sys.path.append(os.path.join(os.getcwd(),"multimodal"))
sys.path.append(os.getcwd())

######################################################################
# For this tutorial, we treat VQA as a classification task. So we need to
# download the vocab file with answer classes and create the answer to
# label mapping.
#
# We also load the `textvqa
# dataset <https://arxiv.org/pdf/1904.08920.pdf>`__ from HuggingFace
#

with open("data/vocabs/answers_textvqa_more_than_1.txt") as f:
  vocab = f.readlines()

answer_to_idx = {}
for idx, entry in enumerate(vocab):
  answer_to_idx[entry.strip("\n")] = idx


######################################################################
# We see there are 3997 answer classes including a class representing
# unknown answers
#

print(len(vocab))
print(vocab[:5])

from datasets import load_dataset
dataset = load_dataset("textvqa")

from IPython.display import display, Image
idx = 5
print("Question: ", dataset["train"][idx]["question"])
print("Answers: " ,dataset["train"][idx]["answers"])
display(dataset["train"][idx]["image"].resize((500,500)))


######################################################################
# Next we write the transform function to convert the image and text into
# Tensors consumable by our model - For images, we use the transforms from
# torchvision to convert to Tensor and resize to uniform sizes - For text,
# we tokenize (and pad) them using the BertTokenizer from HuggingFace -
# For answers (i.e. labels), we take the most frequently occuring answer
# as the label to train with
#

import torch
from torchvision import transforms
from collections import defaultdict
from transformers import BertTokenizer
from functools import partial

def transform(tokenizer, input):
  batch = {}
  image_transform = transforms.Compose([transforms.ToTensor(), transforms.Resize([224,224])])
  image = image_transform(input["image"][0].convert("RGB"))
  batch["image"] = [image]

  tokenized=tokenizer(input["question"],return_tensors='pt',padding="max_length",max_length=512)
  batch.update(tokenized)


  ans_to_count = defaultdict(int)
  for ans in input["answers"][0]:
    ans_to_count[ans] += 1
  max_value = max(ans_to_count, key=ans_to_count.get)
  ans_idx = answer_to_idx.get(max_value,0)
  batch["answers"] = torch.as_tensor([ans_idx])

  return batch

tokenizer=BertTokenizer.from_pretrained("bert-base-uncased",padding="max_length",max_length=512)
transform=partial(transform,tokenizer)
dataset.set_transform(transform)


######################################################################
# Finally, we import the flava_model_for_classification from
# torchmultimodal. It loads the pretrained flava checkpoint by default and
# includes a classification head.
#
# The model forward function passes the image through the visual encoder
# and the question through the text encoder. The image and question
# embeddings are then passed through the multimodal encoder. The final
# embedding corresponding to the CLS token is passed through a MLP head
# which finally gives the probability distribution over each possible
# answers.
#

from torchmultimodal.models.flava.model import flava_model_for_classification
model = flava_model_for_classification(num_classes=len(vocab))


######################################################################
# We put together the dataset and model in a toy training loop to
# demonstrate how to train the model for 3 iterations.
#

from torch import nn
BATCH_SIZE = 2
MAX_STEPS = 3
from torch.utils.data import DataLoader

train_dataloader = DataLoader(dataset["train"], batch_size= BATCH_SIZE)
optimizer = torch.optim.AdamW(model.parameters())


epochs = 1
for _ in range(epochs):
  for idx, batch in enumerate(train_dataloader):
    optimizer.zero_grad()
    out = model(text = batch["input_ids"], image = batch["image"], labels = batch["answers"], required_embedding="mm")
    loss = out.loss
    loss.backward()
    optimizer.step()
    print(f"Loss at step {idx} = {loss}")
    if idx > MAX_STEPS-1:
      break


######################################################################
# Conclusion
#
# This tutorial introduced the basics around how to finetune on a
# multimodal task using FLAVA from TorchMultimodal. Please also check out
# other examples from the library like
# `MDETR <https://github.com/facebookresearch/multimodal/tree/main/torchmultimodal/models/mdetr>`__
# which is a multimodal model for object detection and
# `Omnivore <https://github.com/facebookresearch/multimodal/blob/main/torchmultimodal/models/omnivore.py>`__
# which is multitask model spanning image, video and 3d classification.
#
