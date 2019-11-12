# PRINCE: Provider-side Interpretability with Counterfactual Explanations in Recommender Systems
#### Author: [Azin Ghazimatin](http://people.mpi-inf.mpg.de/~aghazima/) (aghazima@mpi-inf.mpg.de)
## Overview
In this repository, we provide the code for generating counterfactual explanations in random walk-based recommender systems in polynomial time. The explanations are in form of a subset of the user's actions, whose removal displaces the top-most recommendation. To clarify, user's actions are modeled as the outgoing edges of the user's node in her interaction graph. 

## Usage
The relevance of items for a user is measured based on the their PageRank scores personalized for the user. In local_push.py, the PPR (personalized PageRank) scores are computed using reverse local push algorithm (with approximation guarantee of epsilon). For a given user and her interction graph, the function "cfe_item_centric_algo_poly" in cfe_generator.py returns the counterfactual explanation and the replacement item (the rew top-most recommendation). 

## Example
In toy_example.py, the algorithm is tested on random graphs. For example, in the graph below, the user node is shown in red (node 12). The only item nodes in the graph are nodes 13 an 14. Node 14 has the higher PageRank score, hence the top recommendation. Deleting the red edges swaps the rank of the nodes 13 and 14, and makes node 13 the new top recommendation.

![toy_example](https://github.com/azinmatin/prince/blob/master/images/toy_example.png)
