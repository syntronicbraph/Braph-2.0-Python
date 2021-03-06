import numpy as np
import copy
from numpy.linalg import matrix_power, multi_dot
from braphy.graph.accum_array import AccumArray

class RandomGraph():

    def random_graph(graph, bin_swaps = 5, w_freq = 0.1):

        # TODO add checks for input arguments
    
        if graph.is_directed():
            A_null, correlation = RandomGraph.get_random_directed_graph(graph, bin_swaps, w_freq)
        else:
            A_null, correlation = RandomGraph.get_random_undirected_graph(graph, bin_swaps, w_freq)

        return A_null, correlation

    def get_random_directed_graph(graph, bin_swaps, w_freq):
        A = graph.A.copy()
        np.fill_diagonal(A,0)
        node_number = np.shape(A)[0]

        A_pos = A > 0
        if np.count_nonzero(A_pos) < (node_number*(node_number-1)):
            nbr_pos_nodes = np.shape(A_pos)[0]

            nodes_x = np.where(np.tril(A_pos))[0]
            nodes_y = np.where(np.tril(A_pos))[1]

            nodes_length = len(nodes_x)
            bin_swaps = nodes_length*bin_swaps

            max_rewire_attempts = round(nbr_pos_nodes*nodes_length/(nbr_pos_nodes*(nbr_pos_nodes-1)))
            succ_rewirings = 0

            for item in range(0,bin_swaps):
                attempts = 0
                while attempts <= max_rewire_attempts:
                    while 1:
                        node_index1 = np.random.randint(0,nodes_length)
                        node_index2 = np.random.randint(0,nodes_length)
                        while node_index1 == node_index2:
                            node_index2 = np.random.randint(0,nodes_length)

                        node1_x = nodes_x[node_index1]
                        node1_y = nodes_y[node_index1]
                        node2_x = nodes_x[node_index2]
                        node2_y = nodes_y[node_index2]

                        if np.all(node1_x!=[node2_x,node2_y]) and np.all(node1_y!=[node2_x,node2_y]):
                            break

                    if not (A_pos[node1_x, node2_y] or A_pos[node2_x, node1_y]):
                        A_pos[node1_x, node2_y] = A_pos[node1_x, node1_y]
                        A_pos[node1_x, node1_y] = 0
                        A_pos[node2_x, node1_y] = A_pos[node2_x, node2_y]
                        A_pos[node2_x, node2_y] = 0

                        nodes_y[node_index1] = node2_y
                        nodes_y[node_index2] = node1_y
                        succ_rewirings = succ_rewirings +1
                        break
                    attempts = attempts + 1

            A_pos_random = A_pos.copy()
        else:
            A_pos_random = A_pos.copy()
        
        A_neg = (A_pos==0)
        np.fill_diagonal(A_neg, 0)
        A_neg_random = (A_pos_random==0)
        np.fill_diagonal(A_neg_random, 0)

        A_null = np.zeros([node_number,node_number])
        for switch in [1,-1]:
            if switch==1:
                in_strength = (A*A_pos).sum(axis = 0)
                out_strength = (A*A_pos).sum(axis = 1)
                sorted_w = np.sort(A[A_pos])
                w_x = np.where(A_pos_random)[0]
                w_y = np.where(A_pos_random)[1]
                linear_w_ind = node_number*(w_y)+w_x
            else:
                in_strength = (-A*A_neg).sum(axis = 0)
                out_strength = (-A*A_neg).sum(axis = 1)
                sorted_w = np.sort(-A[A_neg])
                w_x = np.where(A_neg_random)[0]
                w_y = np.where(A_neg_random)[1]
                linear_w_ind = node_number*(w_y)+w_x

            expected_w = np.outer(out_strength, in_strength)

            if w_freq==1:
                for w in range(sorted_w.size, 0, -1):
                    sorted_index = np.argsort(expected_w.flatten('F')[linear_w_ind])
                    r = np.random.randint(0,w)
                    rand_w_ind = sorted_index[r]
                    val = switch*sorted_w[r]
                    A_null.itemset(linear_w_ind[rand_w_ind], val)

                    expected_w_prob = 1 - sorted_w[r]/out_strength[w_x[rand_w_ind]] 
                    expected_w[w_x[rand_w_ind],:] = expected_w[w_x[rand_w_ind],:].dot(expected_w_prob)

                    expected_w_prob = 1 - sorted_w[r]/in_strength[w_y[rand_w_ind]]
                    expected_w[:,w_y[rand_w_ind]] = expected_w[:,w_y[rand_w_ind]].dot(expected_w_prob)

                    out_strength[w_x[rand_w_ind]] = out_strength[w_x[rand_w_ind]] - sorted_w[r]
                    in_strength[w_y[rand_w_ind]] = in_strength[w_y[rand_w_ind]] - sorted_w[r]

                    linear_w_ind = np.delete(linear_w_ind, rand_w_ind)
                    w_x = np.delete(w_x, rand_w_ind)
                    w_y = np.delete(w_y, rand_w_ind)
                    sorted_w = np.delete(sorted_w, r)

            else:
                w_period = round(1/w_freq)
                for w in range(sorted_w.size, 0, -w_period):
                    sorted_index = np.argsort(expected_w.flatten('F')[linear_w_ind])
                    r = np.arange(w)
                    np.random.shuffle(r)
                    r = r[0:min(w,w_period)]
                    rand_w_ind = sorted_index[r]
                    val = switch*sorted_w[r]
                    for idx, value in enumerate(linear_w_ind[rand_w_ind]):
                        A_null.itemset(value, val[idx])
                    
                    cumulative_w_x = AccumArray.accum( w_x[rand_w_ind], sorted_w[r], size=np.array([node_number, 1]))
                    cum_nonzero = cumulative_w_x > 0 
                    expected_w_prob = 1 - cumulative_w_x[cum_nonzero]/out_strength[cum_nonzero]
                    expected_w_prob = np.tile(expected_w_prob, (node_number,1)).T 
                    expected_w[cum_nonzero,:] = expected_w[cum_nonzero,:]*expected_w_prob
                    expected_w[:,cum_nonzero] = expected_w[:,cum_nonzero]*np.transpose(expected_w_prob)
                    out_strength[cum_nonzero] = out_strength[cum_nonzero] - cumulative_w_x[cum_nonzero]

                    cumulative_w_y = AccumArray.accum( w_y[rand_w_ind], sorted_w[r], size=np.array([node_number, 1]))
                    cum_nonzero = cumulative_w_y > 0 
                    expected_w_prob = 1 - cumulative_w_y[cum_nonzero]/in_strength[cum_nonzero]
                    expected_w_prob = np.tile(expected_w_prob, (node_number,1)).T 
                    expected_w[cum_nonzero,:] = expected_w[cum_nonzero,:]*expected_w_prob
                    expected_w[:,cum_nonzero] = expected_w[:,cum_nonzero]*np.transpose(expected_w_prob)
                    in_strength[cum_nonzero] = in_strength[cum_nonzero] - cumulative_w_y[cum_nonzero]

                    rand_w_ind = sorted_index[r]
                    linear_w_ind = np.delete(linear_w_ind, rand_w_ind)
                    w_x = np.delete(w_x, rand_w_ind)
                    w_y = np.delete(w_y, rand_w_ind)
                    sorted_w = np.delete(sorted_w, r)

        A_null = A_null.T

        pos_correlation_in = np.corrcoef(sum(A*(A>0), 0), sum(A_null*(A_null>0), 0))
        pos_correlation_out = np.corrcoef(sum(A*(A>0), 1), sum(A_null*(A_null>0), 1))
        neg_correlation_in = np.corrcoef(sum(-A*(A<0), 0), sum(-A_null*(A_null<0), 0))
        neg_correlation_out = np.corrcoef(sum(-A*(A<0), 1), sum(-A_null*(A_null<0), 1))
        correlation = np.array([pos_correlation_in.item(2), pos_correlation_out.item(2), neg_correlation_in.item(2), neg_correlation_out.item(2)])
        return A_null, correlation

    def get_random_undirected_graph(graph, bin_swaps, w_freq):
        A = graph.A.copy()
        np.fill_diagonal(A,0)
        node_number = np.shape(A)[0]

        A_pos = A > 0
        if np.count_nonzero(A_pos) < (node_number*(node_number-1)):
            nbr_pos_nodes = np.shape(A_pos)[0]

            nodes_x = np.where(np.tril(A_pos))[0]
            nodes_y = np.where(np.tril(A_pos))[1]

            nodes_length = len(nodes_x)
            bin_swaps = nodes_length*bin_swaps

            max_rewire_attempts = round(nbr_pos_nodes*nodes_length/(nbr_pos_nodes*(nbr_pos_nodes-1)))
            succ_rewirings = 0

            for item in range(0,bin_swaps):
                attempts = 0
                while attempts <= max_rewire_attempts:
                    while 1:
                        node_index1 = np.random.randint(0,nodes_length)
                        node_index2 = np.random.randint(0,nodes_length)
                        while node_index1 == node_index2:
                            node_index2 = np.random.randint(0,nodes_length)

                        node1_x = nodes_x[node_index1]
                        node1_y = nodes_y[node_index1]
                        node2_x = nodes_x[node_index2]
                        node2_y = nodes_y[node_index2]

                        if np.all(node1_x!=[node2_x,node2_y]) and np.all(node1_y!=[node2_x,node2_y]):
                            break
                    
                    if np.random.uniform()>0.5:
                        nodes_x[node_index2] = node2_y
                        nodes_y[node_index2] = node2_x

                        node2_x = nodes_x[node_index2]
                        node2_y = nodes_y[node_index2]

                    if not (A_pos[node1_x, node2_y] or A_pos[node2_x, node1_y]):
                        A_pos[node1_x, node2_y] = A_pos[node1_x, node1_y]
                        A_pos[node1_x, node1_y] = 0
                        A_pos[node2_y, node1_x] = A_pos[node1_y, node1_x]
                        A_pos[node1_y, node1_x] = 0
                        A_pos[node2_x, node1_y] = A_pos[node2_x, node2_y]
                        A_pos[node2_x, node2_y] = 0
                        A_pos[node1_y, node2_x] = A_pos[node2_y, node2_x]
                        A_pos[node2_y, node2_x] = 0

                        nodes_y[node_index1] = node2_y
                        nodes_y[node_index2] = node1_y
                        succ_rewirings = succ_rewirings +1
                        break
                    attempts = attempts +1

            A_pos_random = A_pos.copy()
        else:
            A_pos_random = A_pos.copy()
        
        A_neg = (A_pos==0)
        np.fill_diagonal(A_neg, 0)
        A_neg_random = (A_pos_random==0)
        np.fill_diagonal(A_neg_random, 0)

        A_null = np.zeros([node_number,node_number])
        for switch in [1,-1]:
            if switch==1:
                strength = (A*A_pos).sum(axis=1)
                sorted_w = np.sort(A[np.triu(A_pos)])
                w_x = np.where(np.triu(A_pos_random))[0]
                w_y = np.where(np.triu(A_pos_random))[1]
                linear_w_ind = node_number*(w_y)+w_x
            else:
                strength = (-A*A_neg).sum(axis=1)
                sorted_w = np.sort(-A[np.triu(A_neg)])
                w_x = np.where(np.triu(A_neg_random))[0]
                w_y = np.where(np.triu(A_neg_random))[1]
                linear_w_ind = node_number*(w_y)+w_x

            expected_w = np.outer(strength,strength)

            if w_freq==1:
                for w in range(sorted_w.size, 0, -1):
                    sorted_index = np.argsort(expected_w.flatten('F')[linear_w_ind])
                    r = np.random.randint(0,w)
                    rand_w_ind = sorted_index[r]
                    val = switch*sorted_w[r]
                    A_null.itemset(linear_w_ind[rand_w_ind], val)

                    expected_w_prob = 1 - sorted_w[r]/strength[w_x[rand_w_ind]] 

                    expected_w[w_x[rand_w_ind],:] = expected_w[w_x[rand_w_ind],:].dot(expected_w_prob)
                    expected_w[:,w_x[rand_w_ind]] = expected_w[:,w_x[rand_w_ind]].dot(expected_w_prob)

                    expected_w_prob = 1 - sorted_w[r]/strength[w_y[rand_w_ind]]

                    expected_w[w_y[rand_w_ind],:] = expected_w[w_y[rand_w_ind],:].dot(expected_w_prob)
                    expected_w[:,w_y[rand_w_ind]] = expected_w[:,w_y[rand_w_ind]].dot(expected_w_prob)

                    strength[[w_x[rand_w_ind],w_y[rand_w_ind]]] = \
                        strength[[w_x[rand_w_ind],w_y[rand_w_ind]]] - sorted_w[r]

                    linear_w_ind = np.delete(linear_w_ind, rand_w_ind)
                    w_x = np.delete(w_x, rand_w_ind)
                    w_y = np.delete(w_y, rand_w_ind)
                    sorted_w = np.delete(sorted_w, r)

            else:
                w_period = round(1/w_freq)
                for w in range(sorted_w.size, 0, -w_period):
                    sorted_index = np.argsort(expected_w.flatten('F')[linear_w_ind])
                    r = np.arange(w)
                    np.random.shuffle(r)
                    r = r[0:min(w,w_period)]
                    rand_w_ind = sorted_index[r]
                    val = switch*sorted_w[r]
                    for idx, value in enumerate(linear_w_ind[rand_w_ind]):
                        A_null.itemset(value, val[idx])
                    
                    cumulative_w = AccumArray.accum( np.append(w_x[rand_w_ind], w_y[rand_w_ind]), sorted_w[np.append(r,r)], size=np.array([node_number, 1]))
                    cum_nonzero = cumulative_w > 0 
                    expected_w_prob = 1 - cumulative_w[cum_nonzero]/strength[cum_nonzero]
                    expected_w_prob = np.tile(expected_w_prob, (node_number,1)).T 
                    expected_w[cum_nonzero,:] = expected_w[cum_nonzero,:]*expected_w_prob
                    expected_w[:,cum_nonzero] = expected_w[:,cum_nonzero]*np.transpose(expected_w_prob)
                    strength[cum_nonzero] = strength[cum_nonzero] - cumulative_w[cum_nonzero]

                    rand_w_ind = sorted_index[r]
                    linear_w_ind = np.delete(linear_w_ind, rand_w_ind)
                    w_x = np.delete(w_x, rand_w_ind)
                    w_y = np.delete(w_y, rand_w_ind)
                    sorted_w = np.delete(sorted_w, r)

        A_null = A_null + A_null.T

        pos_correlation = np.corrcoef(sum(A*(A>0)), sum(A_null*(A_null>0)))
        neg_correlation = np.corrcoef(sum(-A*(A<0)), sum(-A_null*(A_null<0)))
        correlation = np.array([pos_correlation.item(2), neg_correlation.item(2)])
        return A_null, correlation
