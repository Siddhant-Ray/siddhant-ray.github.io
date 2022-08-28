---
layout: page
title: FRR - P4 Integrated Super - Node
description: Linux control planes with programmble P4 dataplanes. 
img: assets/img/supernode.webp
importance: 3
category: Research
---

<p align="justify"> We present a new integration system for layer-3 routers in programmable networks, which allows for the creation of a new forwarding node i.e the Super-Node. These nodes retain the traditional routing control plane from layer-3 routers. However, we replace the static data plane of the original routers by a new, programmable data plane. We create networks using these new forwarding nodes,
replacing erstwhile layer-3 routers. These new nodes allow for the creation of smarter data planes and customized control planes to implement traditional routing algorithms. </p>

<p align="justify">  We then use our new forwarding nodes, combining route calculations from the control plane and decision aware forwarding using our programmable data plane, in order to create better network wide routing and traffic management. All in all, we now benefit from the best of each world, as we co-design the control and data planes. </p>

Implementation of entire project can be found here: <a href="https://github.com/Siddhant-Ray/FRR-P4-Super-Node-Prototype"> Code </a>

