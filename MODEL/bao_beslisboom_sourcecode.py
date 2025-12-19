# Databricks notebook source
# MAGIC %md
# MAGIC # Script that generates profiles for the BAO
# MAGIC
# MAGIC This notebook shows the step-by-step process of building the BAO rule-based decision tree and subsequent generation of the BAO profiles:
# MAGIC
# MAGIC 1. **Package installation & import** - first, all relevant packages and libraries are installed and imported
# MAGIC
# MAGIC 2. **Tree construction** - the tree is built using the `build_tree` function
# MAGIC
# MAGIC 3. **Tree pruning** - the tree is pruned using the `prune_tree` function
# MAGIC
# MAGIC 4. **Leaf filtering** - tree leaves consisting of fewer than 3 attributes are filtered out using the `filter_leaves_under_minimum_depth` function
# MAGIC
# MAGIC 5. **Exporting to dictionary** - the tree is converted to a dictionary format using `export_profiles_to_dict_from_tree`
# MAGIC
# MAGIC 6. **Configuration and calling** - Finally, the configuration is set up and the above functions are called one-by-one

# COMMAND ----------

# MAGIC %md
# MAGIC ### Additional Notes
# MAGIC
# MAGIC - Some functions contain a verbose setting (`verbose=False`), which can optionally be set to 'True' to display additional information via print statements
# MAGIC
# MAGIC - Some values have been removed and are displayed as `{redacted}`. This information has been withheld as it could create security risks by providing insights that might be exploited to manipulate the application process
# MAGIC
# MAGIC - All validations and checks normally built into the script have been removed; this notebook focuses only on demonstrating the decision tree development process
# MAGIC
# MAGIC - For more information see the ReadMe on Github, the factsheet at Nederlandwereldwijd.nl: 
# MAGIC
# MAGIC https://www.nederlandwereldwijd.nl/binaries/content/assets/pdfs-nederlands/factsheet-informatie-ondersteunend-beslissen-032025.pdf 
# MAGIC
# MAGIC and our publication in the algoritmeregister:
# MAGIC
# MAGIC https://algoritmes.overheid.nl/nl/algoritme/mnre1013/94596537/informatie-ondersteund-beslissen-kort-verblijf-schengen-visum-kvv#werking

# COMMAND ----------

# MAGIC %md
# MAGIC ## Initialization
# MAGIC Installing and importing necessary packages

# COMMAND ----------

# MAGIC %pip install networkx

# COMMAND ----------

import json
import pyspark.sql.functions as F
import pyspark.sql.types as T
import pyspark.sql.window as W
import networkx as nx
import hashlib
from datetime import datetime, timedelta

# COMMAND ----------

# MAGIC %md
# MAGIC # Define functions for tree-creation

# COMMAND ----------

def build_tree(
    df,
    features_ordered,
    chance_max_hit_percentage_threshold=redacted_value_1,
    chance_max_refusal_percentage_threshold={redacted},
    risk_min_hit_percentage_threshold={redacted},
    minimal_groupsize={redacted},
    verbose=False
):
    """
    Builds a tree where the trail to each node is a profile. Each node gets lot of attribtues with statistics about that exact profile.
    """

    # define color map for coloring the nodes in the tree
    mapping_profile_type_to_color = {
        "chance": "springgreen",
        "inbetween": "yellow",
        "risk": "red"
    }

    # define current depth
    current_depth = 0

    # set counter for current node to 0
    current_node_number = 0

    # create registry of all nodes 
    node_registry = dict()

    # create tree
    tree = nx.DiGraph()

    # add rootnode to the tree
    tree.add_node(
        current_node_number,
        label="Alle aanvragen",
        total_count=df.count(),
        fillcolor="lightblue",
        key="Alle aanvragen",
        profile_type="inbetween",
        depth=current_depth,
    )

    # add hash of the number of the root-node to the registry
    root_node_hash = hashlib.md5(json.dumps({}).encode("utf-8")).hexdigest()
    node_registry[root_node_hash] = current_node_number

    # build a tree layer by layer by iterating over the features
    for index, current_feature in enumerate(features_ordered):

        # update depth for new layer
        current_depth = index + 1

        # get features to use for grouping the dataframe, this gives the information for new layer of nodes
        features_to_current_depth = features_ordered[0:current_depth]

        if verbose:
            print(f'Adding layer {current_depth} for feature "{current_feature}"...')
            print(f'\tUsing following features to group: {features_to_current_depth}')


        # create dataframe
        df_feature_combinations = (
            df

            # grouping by the features gives all groups for a new layer of nodes for the tree
            .groupBy(features_to_current_depth)

            # calculate for each of the combinations some statistics
            .agg(
                F.avg(F.col("aanvrager_hit").cast("integer")).alias("applicant_hit_percentage"),
                F.sum(F.col("aanvrager_hit").cast("integer")).alias("applicant_hit_count"),
                F.avg(F.col("visumaanvraag_beslissing_negatief").cast("integer")).alias("refusal_percentage"),
                F.count("*").alias("group_size"),

                # add counts for different hit-sources to use later in description of profiles
                F.sum(F.col("{redacted}").cast("integer")).alias("{redacted}"),
                F.sum(F.col("{redacted}").cast("integer")).alias("{redacted}"),
                F.sum(F.col("{redacted}").cast("integer")).alias("{redacted}"),

                F.sum(F.col("{redacted}").cast("integer")).alias("{redacted}"),
                F.sum(F.col("{redacted}").cast("integer")).alias("{redacted}"),
                F.sum(F.col("{redacted}").cast("integer")).alias("{redacted}"),
                F.sum(F.col("{redacted}").cast("integer")).alias("{redacted}"),
                F.sum(F.col("{redacted}").cast("integer")).alias("{redacted}"),
            )

            # filter all groups that do not have enough applications
            .filter(F.col("group_size") >= minimal_groupsize)

            # define type of the remaining nodes based on pre-defined business rules
            .withColumn(
                "profile_type",
                F.when((
                          (F.col("applicant_hit_percentage") <= (chance_max_hit_percentage_threshold / 100))
                        & (F.col("refusal_percentage") <= (chance_max_refusal_percentage_threshold / 100))
                    ),
                    "chance"
                )
                .when((
                          (F.col("applicant_hit_percentage") >= (risk_min_hit_percentage_threshold / 100))
                    ),
                    "risk"
                )
                .otherwise("inbetween")
            )
            .withColumn("node_id", F.row_number().over(W.Window().orderBy(features_to_current_depth)))

            # sort by current feature to 
            .sort(features_to_current_depth, ascending=True)

            # calculate dataframe and collect records
            .collect()
        )
        if verbose:
            display(df_feature_combinations)

        # count number of groups calculated
        feature_combinations_count = len(df_feature_combinations)

        if verbose:
            print(f'\tGenerated {feature_combinations_count} combinations in dataframe.\n')
            print('\tStart reading all combinations:')
        
        # loop over rows of dataframe and spawn new functions for each value to add node to tree
        for current_feature_combination in df_feature_combinations:
            # increase node number before adding new node
            current_node_number += 1

            # get value for this group of the current feature
            current_feature_value = current_feature_combination[current_feature]

            # convert value to string if it is currently an integer
            if isinstance(current_feature_value, (int)):
                current_feature_value = str(current_feature_value)

            # print info
            if verbose:
                print(f'\t\tReading group number: {current_node_number} with value: {current_feature_value}')

            # to place the current group in the right place in the tree, we need to retrieve which is the parent node of the current group

            ## create dictionary with all features as keys and their respective values for this combination
            current_feature_combination_values = { feature: current_feature_combination[feature] for feature in features_to_current_depth }

            ## create dictionary for parent by removing the key-value combination of the current feature
            parent_feature_combination_values = { k: v for k, v in current_feature_combination_values.items() if k != current_feature }

            ## define hash for both current and parent node based, this hash is used to identify the node in the tree
            current_node_hash = hashlib.md5(json.dumps(current_feature_combination_values).encode("utf-8")).hexdigest()
            parent_node_hash = hashlib.md5(json.dumps(parent_feature_combination_values).encode("utf-8")).hexdigest()

            ## retrieve node-number of the parent by looking up the hash in the registry
            parent_node_number = node_registry[parent_node_hash]

            ## save the current node number under the hash of the current node
            node_registry[current_node_hash] = current_node_number
            
            # print info
            if verbose:
                print(f'\t\t\tParent of group: {list(parent_feature_combination_values.values())}')
                print(f'\t\t\tType of group: {current_feature_combination["profile_type"]}')
                print(f'\t\t\tApplicant hit-percentage of group:', "{0:.3f}%".format(float(current_feature_combination["applicant_hit_percentage"]) * 100))
                print(f'\t\t\tRefusal-percentage of group:', "{0:.3f}%".format(float(current_feature_combination["refusal_percentage"]) * 100))
                print(f'\t\t\tSize of group: {current_feature_combination["group_size"]}')
                print()

            # define the label of the node
            node_label = (
                str(current_node_number)
                + "\n"
                + str(current_feature_value.encode("utf-8"))
                + "\n\nhit-percentage= "
                + "{0:.3f}%".format(float(current_feature_combination["applicant_hit_percentage"]) * 100)
                + "\nweigerings-percentage= "
                + "{0:.3f}%".format(float(current_feature_combination["refusal_percentage"]) * 100)
                + "\naantal aanvragen= "
                + str(current_feature_combination["group_size"])
            )

            # set color of the node by mapping the profile_type
            node_color = mapping_profile_type_to_color[current_feature_combination["profile_type"]]

            # define statistics and information to add to node to access later
            profile_type = current_feature_combination["profile_type"]
            total_count = current_feature_combination["group_size"]
            hit_percentage = float(current_feature_combination["applicant_hit_percentage"]) * 100
            refusal_percentage = float(current_feature_combination["refusal_percentage"]) * 100

            hit_counts = {
                '{redacted}': current_feature_combination["{redacted}"],
                '{redacted}': current_feature_combination["{redacted}"],
                '{redacted}': current_feature_combination["{redacted}"],
                
                '{redacted}': current_feature_combination["{redacted}"],
                '{redacted}': current_feature_combination["{redacted}"],
                '{redacted}': current_feature_combination["{redacted}"],
                '{redacted}': current_feature_combination["{redacted}"],
                '{redacted}': current_feature_combination["{redacted}"],
            }

            # create node for group
            tree.add_node(
                current_node_number,
                label=repr(node_label)[1:-1],
                fillcolor=node_color,
                depth=current_depth,
                key=current_feature_value,
                profile_type=profile_type,
                total_count=total_count,
                hit_percentage=hit_percentage,
                refusal_percentage=refusal_percentage,
                hit_counts=hit_counts
            )

            # create edge from parent to current child
            tree.add_edge(parent_node_number, current_node_number, color=node_color)
        
        # print info
        if verbose:
            print(f'\tFinished layer {current_depth}.\n\n')

    if verbose:
        print("Ended up with tree with", len(tree), "nodes.")

    # define the set of parameters, by saving this parameter-set, profiles created with the same parameters can be grouped
    parameter_set = {
        "features_ordered": features_ordered,
        "chance_max_hit_percentage_threshold": chance_max_hit_percentage_threshold,
        "chance_max_refusal_percentage_threshold": chance_max_refusal_percentage_threshold,
        "risk_min_hit_percentage_threshold": risk_min_hit_percentage_threshold,
        "minimal_groupsize": minimal_groupsize,
    }

    # return tree and parameter_hash
    return tree, parameter_set

# COMMAND ----------

# MAGIC %md
# MAGIC #prune_tree()

# COMMAND ----------

def prune_tree(tree, min_depth_required=3, verbose=False):
    """
    Prunes iteratively leaves where all leaves have the same type as parent.
    Function keeps pruning until there is no leave pruned in the last run.

    Cases that are pruned:
        - all leaves that have the type 'inbetween' 
        - when parent and childs all have the same type
    
    NB: Note that all childs of a parent need to be leaves to be able to safely prune the childs.

    Parameters:
    G (nx.DiGraph): a tree to be pruned. Pruning will be done on the same object.
    """

    if verbose:
        print("Start pruning with tree with", len(tree), "nodes.")

    # initialize variable to keep track if a run had no pruning
    last_run_clear = False

    # keep pruning until last run was clear and no pruning happened in the last run
    while not last_run_clear:
        
        # switch variable that last run was clear, when a node is pruned the variable will be flipped to false 
        last_run_clear = True

        # get all leaves of the tree 
        leaves = [x for x in tree.nodes() if tree.out_degree(x) == 0]

        # remove all leaves of type 'inbetweeen'
        leaves_of_type_inbetween = [leaf_node for leaf_node in leaves if tree.nodes[leaf_node]['profile_type'] == 'inbetween']

        for c in leaves_of_type_inbetween:
            tree.remove_node(c)
            last_run_clear = False
        
        # get all leaves of the new tree after removing the leaves with type inbetween
        leaves = [x for x in tree.nodes() if tree.out_degree(x) == 0]
        
        # get all parents of leaves including type
        parents_of_leaves = set([[node for node in tree.predecessors(leaf)][0] for leaf in leaves])

        # loop over the parents of each leaf to check if any of the leaves can be pruned
        for parent_id in parents_of_leaves:

            # check if depth of the parent is not below the minimum required depth
            parent_depth = tree.nodes[parent_id]['depth']
            if parent_depth < min_depth_required:
                continue
            # get all children of parent
            children = [x for x in tree.successors(parent_id)]

            # check if all childs are leafs, otherwise no pruning can be done,
            # childs are all leafs if every child has an outdegree of 0.
            children_outdegrees = [tree.out_degree(x) for x in children]
            
            if set(children_outdegrees) != set([0]):
                continue

            # retrieve type of parent
            parent_type = tree.nodes[parent_id]['profile_type']

            # retrieve types of childs of the parent
            leaf_types = [tree.nodes[child]["profile_type"] for child in children]
            unique_leaf_types = set(leaf_types)
            num_unique_leaf_types = len(unique_leaf_types)
           
            # remove all childs when they all have the same type as the parent
            if (num_unique_leaf_types == 1 and (list(unique_leaf_types)[0] == parent_type)):
                for c in children:
                    tree.remove_node(c)
                last_run_clear = False
    
    if verbose:
        print("Finished pruning and ended up with tree with", len(tree), "nodes.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Filter profiles from tree not meeting the minimum depth requirement
# MAGIC This function removes all leaves which do not meet a requirement for certain depth.

# COMMAND ----------

def filter_leaves_under_minimum_depth(tree: nx.DiGraph, min_depth_required=3, root_node_id=0, verbose=True):
    num_removed_nodes = 0

    # each profile is defined by the shortest path to each leave. here we find shortest paths to leaves to find all profiles
    paths_to_leaves = [
        nx.shortest_path(tree, root_node_id, x) for x in tree.nodes() if tree.out_degree(x) == 0 and tree.in_degree(x) == 1
    ]

    # loop over the set of shortest paths aka set of profiles and store each profile
    # a path consist of a list of indexes of nodes, i.e. [0,6,14,246]
    for path in paths_to_leaves:
        
        # check if path (profile) has at least as many nodes as the minimum depth requires
        # we use the > because the root node is also in the path.
        if len(path) > min_depth_required:
            continue

        # minimum required depth is not met, so we remove the nodes from bottom to top if the have no children.
        # otherwise, we remove a parent of another child which does meet the minimum required depth.
        for node in path[::-1]:
            number_of_childs = tree.out_degree(node)

            if number_of_childs == 0:
                tree.remove_node(node)
                num_removed_nodes += 1

    if verbose:
        print(f'Removed {num_removed_nodes} under minimum depth of {min_depth_required}.')

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read profiles from tree
# MAGIC Read all the profiles from tree and return in a dictionary.

# COMMAND ----------

def export_profiles_to_dict_from_tree(G, dimensions, root_node_id=0):
    """ Create a list with all profiles from given tree. Each profile is stored as a dictionary with metadata. """

    # setup dict to store all profiles
    profiles = {}

    # each profile is defined by the shortest path to each leave. here we find shortest paths to leaves to find all profiles
    paths_to_leaves = [
        nx.shortest_path(G, 0,x) for x in G.nodes() if G.out_degree(x)==0 and G.in_degree(x)==1
    ]

    # loop over the set of shortest paths aka set of profiles and store each profile
    # a path consist of a list of indexes of nodes, i.e. [0,6,14,246]
    for index, path in enumerate(paths_to_leaves):

        # setup profile-object to store all information
        profile_temp = {}
        
        # get statistics for profile from leaf node of the path
        leaf_node_id = path[-1]
        leaf_node = G.nodes[leaf_node_id]
        
        profile_temp['type'] = leaf_node['profile_type']
        profile_temp['hit_percentage'] = leaf_node['hit_percentage'] / 100
        profile_temp['refusal_percentage'] = leaf_node['refusal_percentage'] / 100
        profile_temp['size'] = leaf_node['total_count']

        # add information about hits for later on generating the correct description for each profile
        profile_temp["hit_counts"] = leaf_node['hit_counts']

        # loop over path and get all attributes and values for profile
        profile_temp['features'] = dict()
        
        for fragment_index, fragment in enumerate(path[1:]):
                # get name of the attribute
                feature = dimensions[fragment_index]
                value = G.nodes[fragment]['key']
                profile_temp['features'][feature] = value

        
        # save the profile to the total set
        profiles[index] = profile_temp

    return profiles   

# COMMAND ----------

# MAGIC %md
# MAGIC #Settings

# COMMAND ----------

# settings
BAO_PROFIELEN_DATASET = {redacted}

# dimensions
BAO_PROFILES_DIMENSIONS_ORDERED = {redacted}

# minimum depth for tree, aka minimum clauses in profile
BAO_PROFILES_MIN_DEPTH_REQUIRED = 3

# chance profile settings
BAO_PROFILES_CHANCE_MAX_HIT_PERCENTAGE = redacted_value_1
BAO_PROFILES_CHANCE_MAX_REFUSED_PERCENTAGE = y

# risk profile settings
BAO_PROFILES_RISK_MIN_HIT_PERCENTAGE = z

# group size settings
BAO_PROFILES_MINIMAL_GROUPSIZE = n

# COMMAND ----------

# MAGIC %md
# MAGIC # Generate profiles and export

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load dataset and set version

# COMMAND ----------

# load data
df = spark.table(BAO_PROFIELEN_DATASET).cache()

# retrieve and save version of the retrieved dataset
BAO_PROFIELEN_DATASET_VERSION = spark.sql('DESCRIBE HISTORY ' + BAO_PROFIELEN_DATASET).select('version').first()[0]

print('Using dataset:', BAO_PROFIELEN_DATASET, 'on version:', BAO_PROFIELEN_DATASET_VERSION)
print('Number of visa-applications in dataset:', df.count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Build tree

# COMMAND ----------

tree_profiles, parameter_set = build_tree(
    df,
    features_ordered=BAO_PROFILES_DIMENSIONS_ORDERED, 
    chance_max_hit_percentage_threshold = BAO_PROFILES_CHANCE_MAX_HIT_PERCENTAGE, 
    chance_max_refusal_percentage_threshold = BAO_PROFILES_CHANCE_MAX_REFUSED_PERCENTAGE, 
    risk_min_hit_percentage_threshold = BAO_PROFILES_RISK_MIN_HIT_PERCENTAGE, 
    minimal_groupsize = BAO_PROFILES_MINIMAL_GROUPSIZE,
    verbose=False
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prune tree
# MAGIC

# COMMAND ----------

prune_tree(tree_profiles, min_depth_required=BAO_PROFILES_MIN_DEPTH_REQUIRED, verbose=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Make sure all profiles have at least a minimal number of features

# COMMAND ----------

filter_leaves_under_minimum_depth(tree_profiles, min_depth_required=BAO_PROFILES_MIN_DEPTH_REQUIRED)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create dataframe from profile store to save to data-catalog

# COMMAND ----------

# create dataframe
df_profiles = spark.createDataFrame(profile_store.values())

# add extra metadata-columns to dataframe
df_profiles = (
    df_profiles
    .withColumn('dcv_creation_datetime', F.lit(datetime.now()))
    .withColumn('dcv_parameter_set', F.lit(json.dumps(parameter_set)))
    .withColumn('dcv_dataset', F.lit(BAO_PROFIELEN_DATASET))
    .withColumn('dcv_dataset_version', F.lit(BAO_PROFIELEN_DATASET_VERSION))
)

# COMMAND ----------

display(df_profiles)
