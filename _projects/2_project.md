---
layout: page
title: Multi-Label News Classification
description: Text transformer for hierarchical label classification.
img: assets/img/model.webp
importance: 2
category: Research
---

<p align="justify"> In this project, we present a model for a downstream news classification task on a multicategory news dataset. We develop the model using a Transformer based neural network architecture, which we use to classify the news items into its category labelled in the dataset. In the process, we discovered that classifcation of news across categories which overlap in context (e.g. entertainment and comedy) is extremely hard, even with the state-of-the-art word embeddings from Transformers.  </p>

<p align="justify"> We propose a new statistical algorithm, which helps learn the degree of overlap between similar news categories in the dataset using intermediate representations from our model. Finally, we fine-tune our dataset based on our algorithm, and re-train our model on it, showing significant improvement in performance over the the training carried out on the original dataset. </p>

Implementation of entire project can be found here: <a href="https://github.com/Siddhant-Ray/Attentive-neural-networks-for-news-classification"> Code </a>
