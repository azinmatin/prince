import networkx as nx
import random
import time
import operator
import math
import numpy as np

"""
The following functions implement the Reverse Local Push on 
Dynamic graphs. 
Resource: "Approximate Personalized PageRank on Dynamic Graphs"
https://www.kdd.org/kdd2016/papers/files/rfp1146-zhangA.pdf
"""


def update_reverse_push(graph, u, v, p, r, alpha, action='d'):
    """
    Updates the r[u] caused by deletion or addition of (u, v)
    before the actual deletion/addition 
    """
    tmp = ((1 - alpha) * p.get(v, 0) - p.get(u, 0) - alpha * r.get(u, 0)) * graph[u][v]['weight']
    if u == v:
        tmp += 1

    if action == 'd':
        new_denom = 1 - graph[u][v]['weight']
        r[u] -= float(tmp) / (alpha * new_denom)
    else:
        new_denom = 1 + graph[u][v]['weight']
        r[u] += float(tmp) / (alpha * new_denom)
    return r


def compute_delta_r(graph, u, neighbors, p, r, alpha):
    """
    Computes the delta r when multiple edges are deleted. 
    The implementation is based on the update rule in Algorithm 3  
    in the paper.
    """

    neighbors_weights = [graph[u][v]['weight'] for v in neighbors]
    sum_weights = sum(neighbors_weights)
    avg_deleted = sum([p.get(neighbors[i], 0) * neighbors_weights[i] for i in range(len(neighbors))])
    avg_deleted /= sum_weights

    old_avg = (p.get(u, 0) + alpha * r.get(u, 0)) / (1 - alpha)
    tmp = (avg_deleted - old_avg) * sum_weights / (1.0 - sum_weights)

    return (float(tmp) * (1 - alpha)) / alpha


def update_reverse_push_multi(graph, u, neighbors, p, r, alpha, action='d'):
    delta_r = compute_delta_r(graph, u, neighbors, p, r, alpha)
    if action == 'd':
        r[u] = r.get(u, 0) - delta_r
    else:
        r[u] = r.get(u, 0) + delta_r
    return r


def reverse_local_push(graph, t, p, r, alpha=0.15, e=0.00008, update=False):
    """
    This function implements Algorithm 2 in the paper
    """

    out_r = []
    if not update:
        p = {}
        r = {t: 1.0}
    for k, v in r.items():
        if abs(float(v)) > e:
            out_r.append(k)
    iter = 0
    while out_r:
        iter += 1
        push_node = out_r.pop()
        if abs(float(r[push_node])) <= e:
            continue
        p[push_node] = p.get(push_node, 0) + alpha * r[push_node]
        self_weight = 0
        if graph.has_edge(push_node, push_node):
            self_weight = graph[push_node][push_node]['weight']
        for node in graph.predecessors(push_node):
            if node == push_node:
                continue
            edge_weight = graph[node][push_node]['weight']
            r[node] = r.get(node, 0) + (1 - alpha) * r[push_node] * edge_weight
            if abs(float(r.get(node, 0))) > e:
                out_r.append(node)

        r[push_node] = (1-alpha) * self_weight * r[push_node]
        if abs(float(r[push_node])) > e:
            out_r.append(push_node)
    return p, r


def edge_deletion(graph, u, v):
    delta_weight = graph[u][v]['weight']
    for node in graph.successors(u):
        graph[u][node]['weight'] /= (1 - delta_weight)
    graph.remove_edge(u, v)


def edge_deletion_multiple(graph, u, neighbors):
    weights = [graph[u][v]['weight'] for v in neighbors]
    sum_weights = sum(weights)
    for n in neighbors:
        graph.remove_edge(u, n)
    for n in graph.successors(u):
        graph[u][n]['weight'] /= (1.0 - sum_weights)
    return weights


def edge_addition(graph, u, v, weight):
    for node in graph.successors(u):
        graph[u][node]['weight'] *= (1 - weight)
    graph.add_edge(u, v)
    graph[u][v]['weight'] = weight


def edge_addition_multiple(graph, u, neighbors, weights):
    sum_weights = sum(weights)
    for n in graph.successors(u):
        graph[u][n]['weight'] *= (1.0 - sum_weights)
    index = 0
    for n in neighbors:
        graph.add_edge(u, n)
        graph[u][n]['weight'] = weights[index]
        index += 1
