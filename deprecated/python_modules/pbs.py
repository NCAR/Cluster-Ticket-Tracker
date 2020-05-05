#!/usr/bin/python
from ClusterShell.Task import task_self, NodeSet
from nlog import vlog
import json
from pipes import quote

def run_task(cmd):
    """ run task on pbs server node """

    task = task_self()

    for node in NodeSet('@pbsadmin'): 
	""" run on pbs nodes until it works """
	#print (cmd, node)
	task.run(cmd, nodes=node, timeout=60)

	#print 'node: %s error: %s' % (node, task.node_error(node))
	vlog(4, '%s timeouts:%s Error=%s' % (node, task.num_timeout(), task.node_error(node)))

	for output, nodelist in task.iter_buffers():
	    #print 'nodelist:%s' % NodeSet.fromlist(nodelist)
	    if str(NodeSet.fromlist(nodelist)) == node:
		return str(output)
	    #print '%s: %s' % (NodeSet.fromlist(nodelist), output)

    return None

def node_states():
    """ Query Node states from PBS """
    statesjson = run_task("/opt/pbs/default/bin/pbsnodes -av -Fjson")

    if statesjson is None:
	return None
    state = json.loads(statesjson)
    del statesjson

    return state['nodes']
    
#   for name, node in state['nodes'].iteritems():
#       print name
#	for cluster, cregex in clusters.iteritems():
#	    #match = cregex.match(name);
#	    #if match:
#		vmsg("%s match %s" % (name, cluster));
#
#		#known PBS states
#		#'free', 'job-busy', 'job-exclusive', 'resv-exclusive', offline, down, provisioning, wait-provisioning, stale, state-unknown
#
#		if node['state'] in ['job-exclusive', 'resv-exclusive']:
#		    stats[cluster]['nodes']['up'] += 1;
#		    stats[cluster]['nodes']['busy'] += 1;
#		    #PBS doesn't round up to the max avail
#		    stats[cluster]['cores'] += int(cluster_cores[cluster]);
#		    stats[cluster]['threads'] += int(cluster_threads[cluster]);
#
#		elif node['state'] in ['job-busy', 'free', 'provisioning', 'wait-provisioning']:
#		    stats[cluster]['nodes']['up'] += 1;
#
#		    if 'ncpus' in node['resources_assigned'] and node['resources_assigned']['ncpus'] > 0:
#			stats[cluster]['nodes']['busy'] += 1;
#
#			cores=node['resources_assigned']['ncpus']
#			#since Linux uses threads, fudge cores if there are too many jobs
#			#basically assume the user isnt packing the threads
#			if cores > int(cluster_cores[cluster]):
#			    cores = int(cluster_cores[cluster]);
#
#			stats[cluster]['cores'] += cores;
#			stats[cluster]['threads'] += node['resources_assigned']['ncpus'];
#
#		else: #default to down
#		    stats[cluster]['nodes']['down'] += 1;
	   
def set_offline_nodes(nodes, comment = None):
    """ Set nodes offline in PBS 
    nodeset: nodes to offline
    string: comment
    """

    if comment:
	return run_task("/opt/pbs/default/bin/pbsnodes -o -C %s %s" % (quote(comment), ' '.join(nodes)) )
    else:
	return run_task("/opt/pbs/default/bin/pbsnodes -o %s" % (' '.join(nodes)) )

def set_online_nodes(nodes, comment = None):
    """ Set nodes online in PBS 
    nodeset: nodes to online
    string: comment
    """
    if comment:
	return run_task("/opt/pbs/default/bin/pbsnodes -r -C %s %s" % (quote(comment), ' '.join(nodes)) )
    else:
	return run_task("/opt/pbs/default/bin/pbsnodes -r %s" % (' '.join(nodes)) )
           
def is_pbs_down(states):
    """ Do the PBS Node states mean node is down """
    for state in states:
	if state in [ "offline" , "offline_by_mom" , "down" , "Stale" , "state-unknown" , "maintenance" , "initializing" , "unresolvable" ]:
	    return True

    return False

def is_pbs_job_excl(states):
    """ Do the PBS Node states mean node has exclusive job """
    for state in states:
	if state in [ "job-exclusive" , "resv-exclusive" , "default_excl" , "default_exclhost" , "force_excl" , "force_exclhost" ]:
	    return True

    return False

def is_pbs_node_busy(node):
    """ Check if node can be considered to have a job """
    return 'ncpus' in node['resources_assigned'] and node['resources_assigned']['ncpus'] > 0



