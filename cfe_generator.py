from local_push import update_reverse_push_multi
from local_push import reverse_local_push
from local_push import edge_deletion_multiple
from local_push import edge_addition_multiple
import numpy as np


class CFE:
    # Assumption is that edges can only be deleted.

    def __init__(self, graph, p, r, alpha, epsilon):
        self.graph = graph
        self.p = p
        self.r = r
        self.p_no_u = {}
        self.r_no_u = {}
        self.alpha = alpha
        self.epsilon = epsilon

    def compute_pagerank_wo_u(self, user, items):
        """
        This function computes PPR(n_i, item | A) for all the items and all the neighbors of the user  
        """
        self.r_no_u = {}
        self.p_no_u = {}
        p_no_u = dict(self.p)
        r_no_u = dict(self.r)
        deleted_neighbors = []
        for node in self.graph.successors(user):
            if node != user:
                deleted_neighbors.append(node)
        if self.graph.has_edge(user, user):
            # compute the delta r
            for item in items:
                update_reverse_push_multi(self.graph, user, deleted_neighbors, p_no_u[item], r_no_u[item],
                                          self.alpha)

            # update graph
            weights = edge_deletion_multiple(self.graph, user, deleted_neighbors)

            # recompute scores
            for item in items:
                reverse_local_push(self.graph, item, p_no_u[item], r_no_u[item], alpha=self.alpha, e=self.epsilon,
                                   update=True)
                self.r_no_u[item] = dict(r_no_u[item])
                self.p_no_u[item] = dict(p_no_u[item])
                # self.p_no_u[item], self.r_no_u[item] = reverse_local_push(self.graph, item, {}, {}, alpha=self.alpha,
                #                                                   e=self.epsilon)
        else:
            # update graph
            weights = edge_deletion_multiple(self.graph, user, deleted_neighbors)

            # recompute scores
            for item in items:
                p_no_u[item], r_no_u[item] = reverse_local_push(self.graph, item, {}, {},
                                                              alpha=self.alpha, e=self.epsilon)
                self.r_no_u[item] = dict(r_no_u[item])
                self.p_no_u[item] = dict(p_no_u[item])
                # self.p_no_u[item], self.r_no_u[item] = reverse_local_push(self.graph, item, {}, {}, alpha=self.alpha,
                #                                                   e=self.epsilon)

        # restore graph
        edge_addition_multiple(self.graph, user, deleted_neighbors, weights)

        return p_no_u, r_no_u

    def cfe_single_item_poly(self, user, top_item, item, min_number, p):
        # returns the possibility of replacing top item with item
        # with deleting at most min_number actions
        neighbors = [node for node in self.graph.successors(user)]
        deleted_neighbors = []
        replaced = False
        diff_values = []
        for neighbor in neighbors:
            if neighbor == user:
                continue
            diff_val = p[item].get(neighbor, 0) - p[top_item].get(neighbor, 0)
            weight = self.graph[user][neighbor]['weight']
            diff_val *= weight
            diff_values.append((neighbor, diff_val, weight))
        sorted_diff_values = sorted(diff_values, key=lambda x: x[1])
        sum_diff = sum([elem[1] for elem in sorted_diff_values])
        sum_weight = sum([elem[2] for elem in sorted_diff_values])

        # the approximate ppr scores (computed by reverse push) are within epsilon
        # distance from the true value, so the difference of two approximate ppr
        # scores is within 2 * epsilon distance from the true value
        if sum_diff > 2 * self.epsilon:
            message = 'top item cannot be top item %d\t%d\t%e\t%e\t%e\t%e\n' % \
                      (top_item, item, sum_diff, self.p[top_item].get(user, 0.0), self.p[item].get(user, 0.0),
                       self.epsilon)
            print message

        for i in range(len(sorted_diff_values)-1):
            if i+1 > min_number:
                break
            sum_diff -= sorted_diff_values[i][1]
            sum_weight -= sorted_diff_values[i][2]
            deleted_neighbors.append(sorted_diff_values[i][0])
            # print 'deleted neighbors', deleted_neighbors, sum_diff, sum_weight
            if sum_diff > 2 * self.epsilon * sum_weight:
                replaced = True
                break
        return replaced, deleted_neighbors, sum_diff

    def cfe_item_centric_algo_poly(self, user, top_item, items):
        items_info = {}
        replacing_item = None
        max_number = np.iinfo(np.int32).max
        min_number = max_number
        cfe = []
        index = -1
        for item in items:
            if item == top_item:
                continue
            index += 1
            replaced, output, diff = self.cfe_single_item_poly(user, top_item, item, min_number, self.p_no_u)
            items_info[item] = {'size': len(output), 'diff': diff, 'cfe': output}
            if not replaced:
                continue
            if len(output) < min_number:
                min_number = len(output)

        # the replacement item is the one which has the maximum score difference with rec
        if min_number == max_number:
            return [], None, 0
        else:
            max_diff = -10
            for item in items:
                if item == top_item:
                    continue
                if items_info[item]['size'] == min_number:
                    if items_info[item]['diff'] > max_diff:
                        max_diff = items_info[item]['diff']
                        cfe = items_info[item]['cfe']
                        replacing_item = item
        return cfe, replacing_item, min_number
