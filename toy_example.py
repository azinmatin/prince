import networkx as nx
import matplotlib.pyplot as plt
import random
import itertools
from local_push import update_reverse_push_multi
from local_push import reverse_local_push
from cfe_generator import CFE


def draw_interaction_graph(g, source, targets, top_target, selected_edges=[]):
    node_colors_map = {node: 'white' for node in g.nodes()}
    node_colors_map[source] = 'red'
    for target in targets:
       node_colors_map[target] = 'green'
    node_colors_map[top_target] = 'yellow'
    node_colors = [node_colors_map[node] for node in g.nodes()]

    # red edges to neighbors of a source
    # red_edges = [(source, n) for n in g.successors(source)]
    red_edges = selected_edges
    black_edges = [edge for edge in g.edges() if edge not in red_edges]

    # edge labels
    edge_labels = dict([((u, v,), d['weight'])
                        for u, v, d in g.edges(data=True)])

    # Need to create a layout when doing
    # separate calls to draw nodes and edges
    pos = nx.spring_layout(g)
    nx.draw_networkx_nodes(g, pos, cmap=plt.get_cmap('jet'),
                           node_color=node_colors, node_size=500)
    nx.draw_networkx_labels(g, pos)
    # nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels)
    nx.draw_networkx_edges(g, pos, edgelist=red_edges, edge_color='r', arrows=True)
    nx.draw_networkx_edges(g, pos, edgelist=black_edges, arrows=False)
    plt.show()


def interaction_graph_generator(num_nodes, num_edges, num_neighbors, num_targets, num_neighbors_target):
    g = nx.DiGraph()
    self_loop = True
    target_neighbors = num_neighbors_target

    # adding nodes
    for i in range(num_nodes):
        g.add_node(i)
        if self_loop:
            g.add_edge(i, i)
        if i > 0:
            neighbor = random.randint(0, i-1)
            g.add_edge(i, neighbor)
            g.add_edge(neighbor, i)
    s = len(g.edges())
    while s <= num_edges:
        node1 = random.randint(0, num_nodes-1)
        f = False
        while not f:
            node2 = random.randint(0, num_nodes-1)
            if node2 != node1 and not g.has_edge(node1, node2):
                g.add_edge(node1, node2)
                g.add_edge(node2, node1)
                f = True
                s += 2

    # add source node
    node_s = num_nodes
    g.add_node(node_s)
    if self_loop:
        g.add_edge(node_s, node_s)
    potential_neighbors = [i for i in range(num_nodes)]
    random.shuffle(potential_neighbors)
    for neighbor in potential_neighbors[:num_neighbors]:
        g.add_edge(node_s, neighbor)
        if random.randint(0, 1) == 1:
            g.add_edge(neighbor, node_s)

    # add target nodes
    target_nodes = []
    potential_neighbors = [i for i in range(num_nodes)]
    for i in range(num_targets):
        node_t = num_nodes + i + 1
        g.add_node(node_t)
        target_nodes.append(node_t)
        if self_loop:
            g.add_edge(node_t, node_t)
        random.shuffle(potential_neighbors)
        for neighbor in potential_neighbors[:target_neighbors]:
            g.add_edge(node_t, neighbor)
            g.add_edge(neighbor, node_t)

    return g, node_s, target_nodes


def add_weights(g, mode='random'):
    if mode == 'random':
        for node in g.nodes():
            num_succ = len(g.successors(node))
            random_weights = [random.randint(1, 10) for i in range(num_succ)]
            total_weights = sum(random_weights)
            index = 0
            for neighbor in g.successors(node):
                g[node][neighbor]['weight'] = random_weights[index] / float(total_weights)
                index += 1

    if mode == 'uniform':
        for node in g.nodes():
            num_succ = len(g.successors(node))
            for neighbor in g.successors(node):
                g[node][neighbor]['weight'] = 1.0 / num_succ


if __name__ == "__main__":
    num_nodes = 12
    num_edges = 45
    num_neighbors = 5
    num_targets = 2
    num_neighbors_target = 2
    tol = 1.0e-9
    max_iter = 700

    # generating a random graph
    g, source_node, target_nodes = interaction_graph_generator(num_nodes, num_edges, num_neighbors, num_targets,
                                                                   num_neighbors_target=num_neighbors_target)

    # printing statistics
    print '============ Graph statistics ============'
    print 'Source node:', source_node
    s_neighbors = []
    for n in g.successors(source_node):
        if n != source_node:
            s_neighbors.append(n)
    print 'source node has', len(s_neighbors), 'neighbors:', s_neighbors


    # tuning graph into a weighted one
    add_weights(g, mode='uniform')
    # add_weights(g, mode='random')

    # compute the page rank scores
    alpha = 0.15
    epsilon = 1.0 / (num_nodes * 10000)
    p_top_org = {}
    r_top_org = {}
    p_other_org = {}
    r_other_org = {}
    top_node = target_nodes[0]
    other_node = target_nodes[1]
    p_1, r_1 = reverse_local_push(g, target_nodes[0], {}, {}, alpha=alpha, e=epsilon)
    p_2, r_2 = reverse_local_push(g, target_nodes[1], {}, {}, alpha=alpha, e=epsilon)
    if p_1.get(source_node, 0.0) > p_2.get(source_node, 0.0):
        p_top_org = p_1
        r_top_org = r_1
        p_other_org = p_2
        r_other_org = r_2
    else:
        top_node = target_nodes[1]
        other_node = target_nodes[0]
        p_top_org = p_2
        r_top_org = r_2
        p_other_org = p_1
        r_other_org = r_1
    # print p_1
    # print p_2
    print 'Top item:', top_node
    print 'Replacement item:', other_node

    # instantiating counterfactual explanation
    p_both_org = {top_node: dict(p_top_org), other_node: dict(p_other_org)}
    r_both_org = {top_node: dict(r_top_org), other_node: dict(r_other_org)}
    cfe_instance = CFE(g, p_both_org, r_both_org, alpha, epsilon)

    min_actions_toy = 1000000

    # searching over all the subsets of actions exhaustively
    print '============ All Counterfactual Explanations ============'
    contributions = {}
    x = [itertools.combinations(s_neighbors, r) for r in range(1, len(s_neighbors))]
    exp_count = 1
    for elem in x:
        for e in elem:
            # compute update residual (r) values
            neighbors = list(e)
            r_top = update_reverse_push_multi(g, source_node, neighbors, dict(p_top_org), dict(r_top_org), alpha)
            r_other = update_reverse_push_multi(g, source_node, neighbors, dict(p_other_org), dict(r_other_org), alpha)

            # update the graph
            deleted_weights = [g[source_node][neighbor]['weight'] for neighbor in neighbors]
            for neighbor in neighbors:
                g.remove_edge(source_node, neighbor)
            for neighbor in g.successors(source_node):
                g[source_node][neighbor]['weight'] /= (1.0 - sum(deleted_weights))

            # compute the updated values page rank (p) and residual values (r)
            p_top, r_top = reverse_local_push(g, top_node, dict(p_top_org), dict(r_top), alpha=alpha, e=epsilon,
                                       update=True)
            p_other, r_other = reverse_local_push(g, other_node, dict(p_other_org), dict(r_other), alpha=alpha,
                                                  e=epsilon,
                                              update=True)

            # # test with static version of reverse push
            # p_top, r_top = reverse_local_push(g, top_node, {}, {}, alpha=alpha, e=epsilon)
            # p_other, r_other = reverse_local_push(g, other_node, {}, {}, alpha=alpha, e=epsilon)

            # restore the graph
            for neighbor in g.successors(source_node):
                g[source_node][neighbor]['weight'] *= (1.0 - sum(deleted_weights))
            for i in range(len(neighbors)):
                g.add_edge(source_node, neighbors[i])
                g[source_node][neighbors[i]]['weight'] = deleted_weights[i]

            if p_top.get(source_node, 0.0) + 2*epsilon < p_other.get(source_node, 0.0) and min_actions_toy > len(neighbors):
                min_actions_toy = len(neighbors)
            if p_top.get(source_node, 0.0) + 2*epsilon < p_other.get(source_node, 0.0) and min_actions_toy == len(neighbors):
                print 'Explanation', exp_count
                print [(source_node, elem) for elem in neighbors]
                # print 'Replacement item updated score:', p_other.get(source_node, 0.0)
                # print 'top item updated score', p_top.get(source_node, 0.0)
                exp_count += 1

    # finding the explanation using PRINCE
    cfe_instance.compute_pagerank_wo_u(source_node, [top_node, other_node])
    cfe, replacing_item, min_number = cfe_instance.cfe_item_centric_algo_poly(source_node, top_node, [top_node,
                                                                                                  other_node])
    print '============ PRINCE Explanation ============'
    prince_exp = [(source_node, elem) for elem in cfe]
    print prince_exp

    draw_interaction_graph(g, source=source_node, targets=target_nodes, top_target=top_node, selected_edges=prince_exp)





