from braphy.graph_measures.measure import Measure
from braphy.graph_measures.measure_degree import MeasureDegree
from braphy.graph_measures.measure_strength import MeasureStrength
from braphy.graph import *
import numpy as np
import copy

class MeasureAssortativity(Measure):

    def get_description():

        description = {}
        txt = 'The assortativity coefficient is a correlation coefficient ' + \
              'between the degrees/strengths of all nodes on two opposite ' + \
              'ends of a link.' + \
              'A positive assortativity coefficient indicates ' + \
              'that nodes tend to link to other nodes with the same or ' + \
              'similar degree/strength.'
        description['assortativity_in_in'] = txt
        description['assortativity_in_out'] = txt
        description['assortativity_out_in'] = txt
        description['assortativity_out_out'] = txt
        description['assortativity'] = txt

        return description

    def compute_measure(graph):
        A = graph.A.copy()
        np.fill_diagonal(A, 0)
        if graph.is_binary():
            summed_edges = graph.get_measure(MeasureDegree)
            summed_edges_str = 'degree'
        else:
            summed_edges = graph.get_measure(MeasureStrength)
            summed_edges_str = 'strength'

        if graph.is_undirected():
            summed_edges = summed_edges[summed_edges_str]
            [i, j] = np.where(np.triu(A, 1))
            K = len(i)
            graph.measure_dict[MeasureAssortativity]['assortativity'] = \
                MeasureAssortativity.compute_assortativity(summed_edges[i],
                                                           summed_edges[j], K)

        else:
            summed_edges_in = summed_edges['in_' + summed_edges_str]
            summed_edges_out = summed_edges['out_' + summed_edges_str]
            [i, j] = np.where(A>0)
            K = len(i)

            graph.measure_dict[MeasureAssortativity]['assortativity_out_in'] = \
                MeasureAssortativity.compute_assortativity(summed_edges_out[i], summed_edges_in[j], K)
            graph.measure_dict[MeasureAssortativity]['assortativity_in_out'] = \
                MeasureAssortativity.compute_assortativity(summed_edges_in[i], summed_edges_out[j], K)
            graph.measure_dict[MeasureAssortativity]['assortativity_out_out'] = \
                MeasureAssortativity.compute_assortativity(summed_edges_out[i], summed_edges_out[j], K)
            graph.measure_dict[MeasureAssortativity]['assortativity_in_in'] = \
                MeasureAssortativity.compute_assortativity(summed_edges_in[i], summed_edges_in[j], K)

    def compute_assortativity(_in, _out, K):
        numerator = np.sum(_in * _out)/K - (np.sum(0.5 * (_in + _out))/K)**2
        denominator = np.sum(0.5*(_in**2 + _out**2))/K - (np.sum(0.5*(_in + _out))/K)**2
        assortativity = numerator / denominator
        return assortativity


    def get_valid_graph_types():
        graph_type_measures = {}
        graph_type_measures[GraphBD] = []
        graph_type_measures[GraphBU] = []
        graph_type_measures[GraphWD] = []
        graph_type_measures[GraphWU] = []

        for graph_type in graph_type_measures.keys():
            if graph_type.directed:
                graph_type_measures[graph_type].extend(['assortativity_out_in',
                                                        'assortativity_in_out',
                                                        'assortativity_out_out',
                                                        'assortativity_in_in'])
            else:
                graph_type_measures[graph_type].extend(['assortativity'])

        return graph_type_measures
