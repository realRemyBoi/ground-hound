import gym
import numpy as np
from utils import *
from gym import spaces
import matplotlib.pyplot as plt

class Hound(gym.Env):
	"""
	Hound is a custom environment class that defines how the agent interacts with its
	environment, utilizing the OpenAI gym class.
	:param env: Environment class to use for scene graph and occupancy grid
	:param scene_parent: The root node of the scene graph to start from (such as a room or building)
	:param target_obj: Object to locate and be rewarded for finding.
	"""
	def __init__(self, env, scene_parent, target_obj) -> None:
		super(Hound, self).__init__()
		# TODO:	Alternative approach to terminal state definition: specifying number of target objects
		#				and then defining the terminal state to be when all objects are found.
		#				The current method simply has the agent try to maximize its reward from object search, rather than maximize
		#				objects found.
		# TODO: Another approach to observations: try using scene graph adjacency matrix instead of 
		# 			container locations as observation.
		self.__env_type = env
		init_env = env()
		self.__scene_graph, self.__grid = init_env.build_env()
		self.__scene_parent = scene_parent
		self.__containers_list = [edge[1] for edge in self.__scene_graph.edges(self.__scene_parent)] # need to change this when adding high-level building node
		self.__cont_locations = [self.__scene_graph.nodes[container]["location"] for container in self.__containers_list]
		self.__num_containers = len(self.__containers_list)
		self.__target_obj = target_obj
		self.__grid_shape = np.shape(self.__grid)
		self.__start_pos = (4, 7)
		self.__curr_pos = self.__start_pos
		self.__num_cont_visited = 0
		self.__grid[self.__start_pos[0]][self.__start_pos[1]] = -1 # Initialize agent on grid.

		self.action_space = spaces.Discrete(self.__num_containers)
		# observation = [grid space, agent-pos, container-0-location,...,reward-n-location]
		self.observation_space = spaces.Box(low=np.array([-2] * self.__grid_shape[0] * self.__grid_shape[1] + [0] * (2 + 2 * self.__num_containers)), 
																				high=np.array([20] * self.__grid_shape[0] * self.__grid_shape[1] + [self.__grid_shape[0]] * (1 + self.__num_containers) + [self.__grid_shape[1]] * (1 + self.__num_containers)), 
																				shape=(2 + 2 * self.__num_containers + (self.__grid_shape[0] * self.__grid_shape[1]),), dtype=np.int32)


	def reset(self):
		self.__curr_pos = self.__start_pos
		init_env = self.__env_type()
		self.__scene_graph, self.__grid = init_env.build_env()
		self.__containers_list = [edge[1] for edge in self.__scene_graph.edges(self.__scene_parent)]
		self.__num_containers = len(self.__containers_list)
		self.__cont_locations = [self.__scene_graph.nodes[container]["location"] for container in self.__containers_list]
		self.__grid_shape = np.shape(self.__grid)
		self.__start_pos = (4, 7)
		self.__curr_pos = self.__start_pos
		self.__num_cont_visited = 0
		self.__grid[self.__curr_pos[0]][self.__curr_pos[1]] = -1 # Initialize agent on grid.

		self.action_space = spaces.Discrete(self.__num_containers)
		# observation = [grid space, agent-pos, container-0-location,...,reward-n-location]
		self.observation_space = spaces.Box(low=np.array([-2] * self.__grid_shape[0] * self.__grid_shape[1] + [0] * (2 + 2 * self.__num_containers)), 
																				high=np.array([20] * self.__grid_shape[0] * self.__grid_shape[1] + [self.__grid_shape[0]] * (1 + self.__num_containers) + [self.__grid_shape[1]] * (1 + self.__num_containers)), 
																				shape=(2 + 2 * self.__num_containers + (self.__grid_shape[0] * self.__grid_shape[1]),), dtype=np.int32)

		flattened_grid = (np.ndarray.flatten(np.array(self.__grid))).tolist()

		obsv = flattened_grid + [self.__start_pos[0], self.__start_pos[1]] + (np.ndarray.flatten(np.array(self.__cont_locations))).tolist()
		return np.array(obsv).astype(np.int32)


	def step(self, action):
		self.__grid[self.__curr_pos[0]][self.__curr_pos[1]] = 0
		reward = 0

		done = False

		location = self.__cont_locations[action]
		# Check that there is no confusion about which container is being picked.
		assert location == self.__scene_graph.nodes[self.__containers_list[action]]["location"]

		cost = self.__scene_graph.nodes[self.__containers_list[action]]["cost"]

		path = a_star(self.__grid, self.__curr_pos, location)
		self.__curr_pos = path[-1]
		self.__grid[self.__curr_pos[0]][self.__curr_pos[1]] = -1
		
		self.__num_cont_visited += 1
		
		# TODO: Investigate tweaking penalties for removing occlusion and path planning
		# reward -= len(path)
		# reward -= cost

		remove_obj = []
		obj_contained = False
		container_status = [self.__containers_list[action], False]

		for edge in self.__scene_graph.edges(self.__containers_list[action]):
			if self.__target_obj in edge[1]:
				# TODO: maybe play a little animation when a reward is found?
				container_status[1] = True
				obj_contained = True
				reward += 10
				remove_obj.append(edge[1])

		if obj_contained:
			self.__scene_graph.remove_nodes_from(remove_obj)

		# TODO: Investigate using number of target objects as terminal state.
		if self.__num_cont_visited == self.__num_containers:
			done = True

		flattened_grid = (np.ndarray.flatten(np.array(self.__grid))).tolist()
		obsv = flattened_grid + [self.__start_pos[0], self.__start_pos[1]] + (np.ndarray.flatten(np.array(self.__cont_locations))).tolist()

		# Auxillary information dictionary
		info = {0:self.__grid, 1:path, 2:container_status}

		return np.array(obsv).astype(np.int32), reward, done, info


	def render(self):
		"""
		Required function for custom gym subclass, but implementation optional.
		"""
		pass


	def close(self):
		"""
		Required function for custom gym subclass, but implementation optional.
		"""
		pass