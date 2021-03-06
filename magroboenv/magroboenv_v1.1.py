import numpy as np
import gym
from gym import error, spaces, utils
from gym.utils import seeding
import math
from time import sleep
import logging
from datetime import datetime

import magroboenv.MProbe as MProbe

def square(x):
    return x*x

def distance(nparray1, nparray2):
    sum = square(nparray1[0] - nparray2[0]) + square(nparray1[1] - nparray2[1]) + square(nparray1[2] - nparray2[2])
    return math.sqrt(sum)

class EnvSpec(object):
    def __init__(self, timestep_limit, id):
        self.timestep_limit = timestep_limit
        self.id = id
        
class MagRoboEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    
    def __init__(self):

        date_str=datetime.now().strftime('%Y%m%d-%H%M%S')
        logfile="./log/magroboenv_" + date_str + ".log"

        logging.basicConfig(filename=logfile, level=logging.DEBUG)

        timestep_limit = 2500
        self.spec = EnvSpec(timestep_limit = timestep_limit, id=1)

        # observation is the x, y, z coordinate of the grid
        self.observation_space = spaces.Box(low=MProbe.MProbe.ob_low, high=MProbe.MProbe.ob_high)

	#Action Space => Current values	
        self.action_space = spaces.Box(low=MProbe.Current.ac_low, high=MProbe.Current.ac_high)

        #initial condition
        self.state = None
        self.steps_beyond_done = None

        # simulation related variables
        self.seed()

        #        self.set_goal() inside reset()
        self.reset()
        #print(self.robot)

        
    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        """
        Parameters
        ----------
        action :

        Returns
        -------
        ob, reward, episode_over, info : tuple
            ob (object) :
                an environment-specific object representing your observation of
                the environment.
            reward (float) :
                amount of reward achieved by the previous action. The scale
                varies between environments, but the goal is always to increase
                your total reward.
            episode_over (bool) :
                whether it's time to reset the environment again. Most (but not
                all) tasks are divided up into well-defined episodes, and done
                being True indicates the episode has terminated. (For example,
                perhaps the pole tipped too far, or you lost your last life.)
            info (dict) :
                 diagnostic information useful for debugging. It can sometimes
                 be useful for learning (for example, it might contain the raw
                 probabilities behind the environment's last state change).
                 However, official evaluations of your agent are not allowed to
                 use this for learning.
        """
        #print("ac={}".format(action))
        logging.debug("action={}".format(action))
        
        self._take_action(action)
        ob = self.state
        
        reward = self._get_reward()

        if reward == 4:
            done = True
        else:
            done = False

        info = {}
        
        return ob, reward, done, info

    def _take_action(self, action):

        for i in range(9):
            if math.isnan(action[i]):
                self.seed(0)
                return

        #change the current
        MProbe.desired_current.set_all_sys_current(action)

        #sleep sometime before reading
        sleep(0.25) #sleep in seconds
        
        #read the changed orientation
        self.state = MProbe.slave.read_sys_orientation()

    def reset(self):
        #set goal
        self.set_goal()

        #generate random seed
        self.seed()
        
        #read current orientation
        self.state = MProbe.slave.read_sys_orientation()
        ob = self.state

        #Find Distance b/w start & goal
        self.init_dist = MProbe.slave.find_distance(MProbe.goal)
        self.curr_dist = self.init_dist
        
        return np.array(ob)

    def set_goal(self):
        #MProbe.goal.set_random_xyz()
        MProbe.goal.set_random_dev_xyz(MProbe.slave)

            
    def _get_reward(self):

        self.last_dist = self.curr_dist

        self.curr_dist = MProbe.slave.find_distance(MProbe.goal)
        print("distance:{}".format(self.curr_dist))
        logging.debug("distance:{}".format(self.curr_dist))
        
        
        """ Reward is given for XYZ. """
        if self.curr_dist == 0.0:
            return 4
        elif self.curr_dist < 1.0:
            return 3
        elif self.curr_dist < 5.0:
            return 2
        elif self.last_dist > self.curr_dist:
            return 1
        elif self.last_dist < self.curr_dist:
            return -1
        else:
            return 0

    def render(self, mode='human', close=False):
        pass
    
    def close(self):
        pass
    

    
