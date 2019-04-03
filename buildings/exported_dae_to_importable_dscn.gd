extends SceneTree

# Adapted from https://github.com/TwistedTwigleg/DSCN_Plugin
# Runs in the command line: godot -s exported_to_importable.gd
# Expects a folder named 'out' with .dae files.
# Creates a folder named 'importable' with results.

# TODO: rewrite this!
# DSCN FILE FORMAT (0.1.0):
	#	Number of nodes stored in Node list: 1 (or however many nodes are stored)
	#	Number of resources stored in Resource list: 1 (or however many resources are stored)
	#	JSON NodeTree: JSON Dictionary built using the node names as the key, and the children
	#					nodes as values. Leaf nodes only have a single value, called DSCN_Resources
	#					which holds all of the resources the leaf node needs.
	#	Metadata : (Nothing for now, but saving this in case!)
	#	Export Version : 0.1.0
	#	Node list : all nodes are dumped using "file.store_var(nodes));"
	#	Resource list : each node is dumped using "file.store_var(resource);"


# All of the results that can be returned when trying to export/import
# a DSCN file.
enum DSCN_IO_STATUS {
	IMPORT_SUCCESS,
	EXPORT_SUCCESS,
	NO_NODE_SELECTED,
	SELECTED_NODE_NOT_FOUND,
	FILE_NOT_FOUND,
}

# A variable to hold the DSCN_resource_manager script.
var DSCN_resource_manager = null;


func _init() -> void:
	create_importable_dir_if_not_exists()
	
	for file in list_files_in_directory("res://out"):
		if file.ends_with(".dae"):
			var node = load("res://out/" + file).instance()
			export_node_dscn("res://importable/" + file + ".dscn", node)
	
	
func list_files_in_directory(path):
	var files = []
	var dir = Directory.new()
	dir.open(path)
	dir.list_dir_begin()

	while true:
		var file = dir.get_next()
		if file == "":
			break
		elif not file.begins_with("."):
			files.append(file)

	dir.list_dir_end()

	return files
	
	
func create_importable_dir_if_not_exists():
	if not does_dir_exist("importable"):
		create_dir("importable")
	
	
func does_dir_exist(name):
	var dir = Directory.new()
	return dir.dir_exists(name)
	
	
func create_dir(name):
	var dir = Directory.new()
	dir.open("res://")
	dir.make_dir(name)


# ======== EXPORTER FUNCTIONS ==============


# Will export a DSCN file.
#
# Needs the following arguments:
#	filepath: The file path pointing to where you want to save the DSCN file.
#				(This can be anywhere on the file system!)
#	selected_node: The node you want to save
#				(This will save the children of the selected node as well!)
#	scene_root: The root of the scene selected_node is in.
#
# This function needs the scene root to ensure selected_node is in the
# currently open scene.
# (And for argument completeness with the import_dscn function)
#
# Will return one of the values in DSCN_IO_STATUS.
func export_dscn(filepath, selected_node, scene_root):
	
	# Make sure a node is selected. Return a error if it does not.
	if (selected_node == null):
		return DSCN_IO_STATUS.NO_NODE_SELECTED;
	
	# Make sure the node exists in the passed in scene_root.
	var path_in_open_scene = scene_root.get_path_to(selected_node);
	if (path_in_open_scene != null):
		
		# Double check to make sure the node exists.
		# Return a error if it does not.
		if (scene_root.has_node(path_in_open_scene) == false):
			return DSCN_IO_STATUS.SELECTED_NODE_NOT_FOUND;
		
		# Make a new file so we can write the data to it.
		# open the file in WRITE mode at the passed in filepath.
		var export_file = File.new();
		export_file.open(filepath, export_file.WRITE);
		
		# Save all of the DSCN data into the file.
		_save_dscn(scene_root.get_node(path_in_open_scene), export_file);
		
		# Close the file.
		export_file.close();
		
		# If we got this far, then the DSCN file has successfully been exported!
		return DSCN_IO_STATUS.EXPORT_SUCCESS;
	
	# If the node does not exist in the scene, then we need to return a error.
	else:
		return DSCN_IO_STATUS.SELECTED_NODE_NOT_FOUND;
		
func export_node_dscn(filepath, node):
	var export_file = File.new();
	export_file.open(filepath, export_file.WRITE);
	
	# Save all of the DSCN data into the file.
	_save_dscn(node, export_file);
	
	# Close the file.
	export_file.close();


# This function will save all of the DSCN data into the passed in file.
#
# Needs the following arguments:
#	node: The node you want to save to into the DSCN file.
#	file: The file the DSCN data needs to be saved into.
func _save_dscn(node, file):
	
	# Duplicate the node (and all it's children).
	# Make sure we are also duplicating scripts, groups, and signals!
	var duplicate_node = node.duplicate(7); # Signals, groups, scripts
	
	# Make a JSON NodeTree, make the resource list, and make the node list, all using
	# the add_node_to_json_node_tree function
	
	# Make the JSON node tree. This is where we will be storing any/all information
	# about the nodes that we will need to convert/parse the DSCN file back into
	# a scene.
	var JSON_node_tree = {};
	# Make the Resource list. This is a list where we will store all of the resources
	# needed in the scene. We will access resources in this list based on the index
	# they are assigned with when added to the list.
	var resource_list = [];
	# Make the Node list. This is a list where all of the nodes (and children nodes)
	# needed in the scene will be stored. Like with Resource List, we will access
	# nodes in the list using the index they are assigned with when added to the list.
	var node_list = [];
	
	# A temporary dictionary for checking for resources.
	# We need this because some resources return new references when we get the data we
	# need out of them, and if we do not check the actual object (not the data), we
	# would in up storing duplicates of each resource used (which increases file size).
	#
	# This is primarily used for images, because get_data returns a new reference every
	# time it is used.
	var resource_check_dict = {};
	
	# Start adding the node data into JSON_node_tree, node_list, resource_list,
	# and resource_check_dict.
	#
	# This is a recursive function that will add the node data for all of the
	# children of the passed in node until there are no children left.
	_add_node_data_to_dscn(duplicate_node, JSON_node_tree, node_list, resource_list, resource_check_dict)
	
	# Add all of the signals for all of the nodes
	for node in node_list:
		_add_node_signals(node, node_list, JSON_node_tree);
	
	# Store the number of nodes in node_list.
	file.store_line(str(node_list.size()));
	# Store the number of resources in resource_list.
	file.store_line(str(resource_list.size()));
	
	# Store the JSON tree.
	file.store_line(to_json(JSON_node_tree));
	
	# Store Metadata and Export version
	file.store_line("NULL");
	file.store_line("0.1.0");
	
	# Store nodes
	for node_to_store in node_list:
		file.store_var(node_to_store);
	
	# Store resources
	for resource_to_store in resource_list:
		file.store_var(resource_to_store);
	
	# Print success!
	print ("**** DSCN_IO ****");
	print ("Saved the following node tree: ")
	print (duplicate_node.print_tree_pretty());
	print ("*****************");


# This function will add all of the data into json_tree, node_list, resource_list
# and resource_check_dict that we need to load the nodes out of DSCN files.
# 
# Needs the following arguments:
#	node: The node whose data is currently being saved.
#	json_tree: The JSON node tree dictionary where we can store data needed
#				load the nodes we are saving.
#	node_list: A list holding all of the nodes in the scene we want to save.
#				This function will populate this list with node and it's children!
#	resource_list: A list holding all of the resources in the scene we need to save.
#				This function will populate this list with the resources node needs!
#	resource_check_dict: A dictionary holding resources we may need to check against
#				To avoid storing duplicate data. This function may populate this dictionary.
func _add_node_data_to_dscn(node, json_tree, node_list, resource_list, resource_check_dict):
	
	# Add the node to the node_list and get it's position in node_list.
	node_list.append(node);
	var node_position_in_list = node_list.size()-1
	
	# Get all of the resources this node is dependent on and store them into
	# node_dependency_dict.
	var node_dependency_dict = {}
	#DSCN_resource_manager.add_node_resources_to_list_and_dict(node, node_dependency_dict, resource_list, resource_check_dict);
	
	# Tell all of the children nodes to save their data.
	var child_nodes_for_node = node.get_children();
	for child_node in child_nodes_for_node:
		_add_node_data_to_dscn(child_node, json_tree, node_list, resource_list, resource_check_dict);
	
	# Get the positions of the children nodes in node_list so we can later
	# reconstruct the node tree when loading DSCN files.
	var child_ids = [];
	for child in child_nodes_for_node:
		child_ids.append(node_list.find(child));
	
	# Save the data needed to import this node into json_tree.
	json_tree[node_position_in_list] = {
		"DSCN_Dependencies":node_dependency_dict,
		"DSCN_Children":child_ids,
		"DSCN_Node_Name":node.name,
	};
	

# This function will add all of the signals from the passed in node into json_tree.
#
# Needs the following arguments:
#	node: The node whose data is currently being saved.
#	node_list: A list holding all of the nodes in the scene we want to save.
#	json_tree: The JSON node tree dictionary where we can store data needed
#				load the nodes we are saving.
func _add_node_signals(node, node_list, json_tree):
	
	# Figure out where this node is positioned in node_list.
	var position_of_node_in_list = node_list.find(node);
	
	# Get all of the signals this node COULD have connected.
	# Make sure this node has at least one (possibly) connected signal.
	var signal_list = node.get_signal_list();
	if (signal_list.size() > 0):
		
		# Add the amount of signals this node has to json_tree.
		json_tree[position_of_node_in_list]["DSCN_Signal_Count"] = signal_list.size();
		
		# Go through each signal in signal list...
		for i in range(0, signal_list.size()):
			
			# Get the signal data and store it in signal_item.
			var signal_item = signal_list[i];
			
			# Get all of the connections this signal may have.
			# Make sure this signal has at least one connection.
			var signal_connections = node.get_signal_connection_list(signal_item["name"])
			if (signal_connections.size() > 0):
				
				# Add the amount of connections this one signal has to json_tree.
				json_tree[position_of_node_in_list]["DSCN_Connection_Count_" + str(i)] = signal_connections.size();
				
				# Go through each connection in signal_connections...
				for j in range(0, signal_connections.size()):
					
					# Get the connection data.
					var signal_connection = signal_connections[j];
					# Find the source node and target node in node_list.
					var source_position = node_list.find(signal_connection["source"])
					var target_position = node_list.find(signal_connection["target"]);
					
					# Make sure node_list contains both the source and the target.
					if (source_position != -1 and target_position != -1):
						# Change the source and target variables in the signal_connection
						# dictionary to store the position of the source and target nodes
						# in node_list.
						signal_connection["source"] = source_position;
						signal_connection["target"] = target_position;
						
						# Save the signal connection in json_tree.
						json_tree[position_of_node_in_list]["DSCN_Signal_" + str(j)] = signal_connection;
				
