---
layout: page
title: Maximizing Flows in Cross Traffic Networks
description: Programmable networks to minimize packet drops.
img:
importance: 3
category: Misc.
---

<p align="justify"> This was a course project for the course Advanced Topics in Communication Networks at ETH Zurich, in Autumn 2020. The primary objective was to deliver as much traffic (i.e. maximize the number of successfully delivered packets) as possible for different traffic patterns and failures. FLows could belong to different classes of traffic, which had varying levels of priority.  Flows were sent in a non-deterministic fashion, however the total numnber of flows for each traffic class was fixed. During the network operation, a given number of links would fail pseudo-randomly. </p>

<p align="justify"> One of the main challenges was to detect and handle the mentioned link failures, using traffic engineering methods such as backup Loop Free Alternative (LFA) paths etc. It was also necessary to ensure that less important flows do not kill high priority traffic. Many times, the link capacity was much lower than the required transmission bandwidth, which required smart re-routing of traffic leveraging the programmable P4 data planes. </p>

Implementation of entire project can be found here: <a href="https://github.com/Siddhant-Ray/Cross-Traffic-Flow-Maximization-in-L2L3-Networks"> Code </a>


