---
layout: page
title: Inductive Biases in CNNs and Transformers
description: Correlating performance to inductive biases.
img:
importance: 3
category: Misc.
---

<p align="justify"> This was a course project for the course Deep Learning at ETH Zurich, in Autumn 2021. Deep learning models for vision tasks have been shown to work well due to factors like inductive biases, generalization of models and so on. In this project, we explore the possible inductive biases or lack of them across different architectures used in vision tasks such as Convolutional Neural Networks and Transformer architectures. We present a series of experiments which help understand these inductive bias, and their role in helping these models generalize.</p>

<p align="justify"> We benchmarked the performance of a CNN-based architecture and local sparse attention transformers on a standard image dataset (CIFAR-10). We then studies the heuristics of the performances and attempted to correlate them with the inductive biases which we started upon. Particularly, to tried to determine if the inductive biases work in local attention transformers as well as in CNNs, the extent to which the performances match, where they differ, etc. </p>

<p align="justify"> Our major experiments were based on classification on the full CIFAR-10 dataset, classification on combined CIFAR-10 images and classification on CIFAR-10 images, with additionally large backgrounds, to correlate the inductive biases stemming from the principal of locality in images. We compared there standard implementations, ResNet-50, Vision Transformer and Vision Transformer with Local Attention.</p>


Implementation of entire project can be found here: <a href="https://github.com/Siddhant-Ray/Inductive-Biases-in-CNNs-vs-Transformers"> Code </a>