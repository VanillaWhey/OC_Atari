import os
import warnings

import numpy as np
import gymnasium as gym
from collections import deque

from ocatari.ram.extract_ram_info import (detect_objects_ram, init_objects,  # noqa: F401
                                          get_max_objects, get_object_state,
                                          get_object_state_size, get_reference_list,
                                          get_masked_dqn_state, get_masked_dqn_state2, get_masked_dqn_state3,
                                          get_module as get_ram_module, get_object_types)
from ocatari.vision.extract_vision_info import (detect_objects_vision,
                                                get_module as get_vision_module)
from ocatari.vision.utils import mark_bb, to_rgba
from ocatari.ram.game_objects import GameObject, ValueObject
from ocatari.utils import draw_label, draw_arrow

try:
    import ale_py
except ModuleNotFoundError:
    warnings.warn('ALE is required when using the ALE env wrapper. '
                  'Try `pip install "gymnasium[atari,accept-rom-license]"`.',
                  ImportWarning)

try:
    import cv2
except ModuleNotFoundError:
    warnings.warn('OpenCV is required when using the ALE env wrapper. '
                  'Try `pip install opencv-python`.', ImportWarning)

try:
    import pygame
except ModuleNotFoundError:
    warnings.warn('pygame is required for human rendering. '
                  'Try `pip install pygame`.', ImportWarning)

try:
    import torch

    torch_imported = True
    _tensor = torch.tensor
    _uint8 = torch.uint8
    _zeros = torch.zeros
    _zeros_like = torch.zeros_like
    _stack = torch.stack
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    _tensor_kwargs = {"device": "cpu"}
except ModuleNotFoundError:
    torch_imported = False
    _tensor = np.array
    _uint8 = np.uint8
    _zeros = np.zeros
    _zeros_like = np.zeros_like
    _stack = np.stack
    DEVICE = "cpu"
    _tensor_kwargs = {}
    warnings.warn("pytorch installation not found, using numpy instead of torch")


def get_available_games():
    gym_games = list(set([k[4:-3] if k.startswith("ALE/") else k[:-3] for k in gym.envs.registry.keys()]))
    lower_games = [k.lower() for k in gym_games]
    dir_path = os.path.dirname(os.path.realpath(__file__))
    files = os.listdir(dir_path + "/ram")
    games = []
    for game in files:
        if game.endswith(".py"):
            name = game[:-3]
            if name in lower_games or f"ale/{game}" in lower_games:
                i = lower_games.index(name)
                games.append(gym_games[i])
    return games


AVAILABLE_GAMES = get_available_games()
UPSCALE_FACTOR = 4


class OCAtari(gym.Env):
    """
    The OCAtari environment. Initialize it to get an Atari environments with objects tracked.

    :param env_name: The name of the Atari gymnasium environment e.g. "Pong" or "PongNoFrameskip-v5"
    :type env_name: str
    :param mode: The detection method type: one of `ram`, or `vision`, or `both` (i.e. `ram` + `vision`)
    :type mode: str
    :param hud: Whether to include objects from the HUD (e.g. scores, lives)
    :type hud: bool
    :param obs_mode: Define the observation mode. Set to `dqn` (84x84, grayscale), `ori` (210x160x3, RGB image), `obj` (#ObjectsxFEATURE_SIZE). `dqn` and `ori` are also organized in a stack of the last 4 frames.
    :type obs_mode: str
    :param gym_args: The arguments passed to `gym.make(...)`
    :type gym_args: dict
    :param logger: The logger used for logging
    :type logger: logger
    :param feature_attr: The property of `GameObject` to use as feature vector
    :type feature_attr: str
    :param buffer_window_size: The window size for including past features in the observation
    :type buffer_window_size: int

    the remaining \*args and \**kwargs will be passed to the \
        `gymnasium.make <https://gymnasium.farama.org/api/registry/#gymnasium.make>`_ function.
    """

    def __init__(self, env_name, mode="ram", hud=False, obs_mode="ori",
                 render_mode=None, render_oc_overlay=False, gym_args=None,
                 logger=gym.logger, feature_attr="xywh", buffer_window_size=4, *args, **kwargs):
        if gym_args is None:
            gym_args = {}
        if "ALE/" in env_name:  # case if v5 specified
            to_check = env_name[4:8]
            game_name = env_name.split("/")[1].split("-")[0].split("No")[0].split("Deterministic")[0]
        else:
            to_check = env_name[:4]
            game_name = env_name.split("-")[0].split("No")[0].split("Deterministic")[0]
        if to_check[:4] not in [gn[:4] for gn in AVAILABLE_GAMES]:
            logger.warn(f"Game '{env_name}' not covered yet by OCAtari\n"
                        f"Available games: {AVAILABLE_GAMES}")
            self._covered_game = False
        else:
            self._covered_game = True
            self.vision_module_name = get_vision_module(game_name)
            self.ram_module_name = get_ram_module(game_name)

        gym_render_mode = "rgb_array" if render_oc_overlay else render_mode
        self._env = gym.make(env_name, render_mode=gym_render_mode, *args, **gym_args)
        self.game_name = game_name
        self.mode = mode
        self.obs_mode = obs_mode
        self.hud = hud
        self.max_objects = []
        self.buffer_window_size = buffer_window_size
        self.step = self._step_impl
        if not self._covered_game:
            logger.warn("\n\n\tUncovered game !!!!!\n\n")
            global init_objects  # noqa
            init_objects = lambda *args, **kwargs: []  # noqa: F402
            self.detect_objects = lambda *args, **kwargs: None  # noqa: F402
            self.objects_v = []
        elif mode == "vision":
            self.detect_objects = self._detect_objects_vision
        elif mode == "ram":
            self.max_objects = get_max_objects(self.ram_module_name, self.hud)
            self.detect_objects = self._detect_objects_ram

            self.feature_attr = feature_attr
        elif mode == "both":
            self.detect_objects = self._detect_objects_both
            self.objects_v = init_objects(self.ram_module_name, self.hud)  # noqa
        else:
            logger.error("Undefined mode for information extraction")
            exit(1)
        self._objects: list[GameObject] = init_objects(self.ram_module_name, self.hud)
        self._object_types = get_object_types(self.ram_module_name, self.hud)
        if obs_mode == "dqn":
            if torch_imported:
                self._get_state = self._get_state_dqn
                self.observation_space = gym.spaces.Box(0, 255.0, (self.buffer_window_size, 84, 84))
            else:
                logger.warn("To use the buffer of OCAtari, you need to install torch.")
        elif obs_mode == "ori":
            self._get_state = self._get_state_ori
        elif obs_mode == "obj":
            logger.info("Using OBJ State Representation")
            try:
                self.feature_size = len(getattr(GameObject(), feature_attr))
            except Exception as e:
                raise AttributeError("GameObject does not support this "
                                     "feature representation.") from e
            if mode == "ram":
                shape = (self.buffer_window_size, get_object_state_size(self.ram_module_name, self.hud), self.feature_size)
                self.observation_space = gym.spaces.Box(0, 255.0, shape)
                self._get_state = self._get_state_obj
                self.reference_list = get_reference_list(self.ram_module_name, hud)
            else:
                logger.error("This obs mode is only available in ram mode")
                exit(1)
        elif obs_mode == "masked_dqn":
            try:
                self._get_state = getattr(self, f"_get_state_masked_{feature_attr}")
            except Exception as e:
                raise AttributeError("Feature representation is not "
                                     "supported.") from e

            self.observation_space = gym.spaces.Box(0, 255.0, (self.buffer_window_size, 84, 84))
        elif obs_mode is not None:
            logger.error("Undefined mode for observation (obs_mode), has to be one of ['dqn', 'ori', 'obj', None]")
            exit(1)

        self.render_mode = render_mode
        self.render_oc_overlay = render_oc_overlay
        self.rendering_initialized = False

        self._state_buffer = deque([], maxlen=self.buffer_window_size)
        self.action_space = self._env.action_space
        self._ale = self._env.unwrapped.ale  # noqa: F821
        # inherit every attribute and method of env
        for meth in dir(self._env):
            if meth not in dir(self):
                try:
                    setattr(self, meth, getattr(self._env, meth))
                except AttributeError:
                    pass

    def step(self, action, *args, **kwargs):
        """
        Run one timestep of the environment's dynamics using the agent actions. \
        Extracts the objects, using RAM or vision based on the `mode` variable set at initialization. \
        Fills the buffer if `obs_mode` was not None at initialization. The observations follow the `obs_mode`. \
        The method runs the Atari environment `env.step() <https://gymnasium.farama.org/api/env/#gymnasium.Env.step>`_ method

        :param action: The action to perform at this step.
        :type action: int
        """
        return self._step_impl(action, *args, **kwargs)

    def _post_step(self, obs):
        self._fill_buffer()
        if self.obs_mode != "ori":
            obs = self._get_buffer_as_stack()
        return obs

    def _step_impl(self, *args, **kwargs):
        obs, reward, terminated, truncated, info = self._env.step(*args, **kwargs)
        self.detect_objects()
        obs = self._post_step(obs)
        return obs, reward, truncated, terminated, info

    def _detect_objects_ram(self):
        detect_objects_ram(self._objects, self._ale.getRAM(), self.ram_module_name, self.hud)

    def _detect_objects_vision(self):
        detect_objects_vision(self._objects, self.getScreenRGB(), self.vision_module_name, self.hud)

    def _detect_objects_both(self):
        detect_objects_ram(self._objects, self._ale.getRAM(), self.ram_module_name, self.hud)
        detect_objects_vision(self.objects_v, self.getScreenRGB(), self.vision_module_name, self.hud)

    def _reset_buffer(self):
        for _ in range(self.buffer_window_size):
            self._fill_buffer()

    def reset(self, *args, **kwargs):
        """
        Resets the buffer and environment to an initial internal state, returning an initial observation and info.
        See `env.reset() <https://gymnasium.farama.org/api/env/#gymnasium.Env.reset>`_ for gymnasium details.
        """
        obs, info = self._env.reset(*args, **kwargs)
        self._objects = init_objects(self.ram_module_name, self.hud)
        self.detect_objects()
        self._reset_buffer()
        obs = self._post_step(obs)
        return obs, info

    def _get_state_obj(self):
        return _tensor(
            get_object_state(self.reference_list, self._objects,
                             self.feature_attr, self.feature_size),
            **_tensor_kwargs
        )

    def _get_state_ori(self):
        return _tensor(self.getScreenRGB(), dtype=_uint8, **_tensor_kwargs)

    def _get_state_dqn(self):
        return _tensor(
            cv2.resize(self._ale.getScreenGrayscale(),
                       (84, 84), interpolation=cv2.INTER_AREA),
            dtype=_uint8,
            **_tensor_kwargs
        )

    def _get_state_masked_bin(self):
        state = get_masked_dqn_state(self._objects)
        return _tensor(
            cv2.resize(state,
                       (84, 84), interpolation=cv2.INTER_AREA),
            dtype=_uint8,
            **_tensor_kwargs
        )

    def _get_state_masked_gray(self):
        state = get_masked_dqn_state2(self._objects, self._object_types)
        return _tensor(
            cv2.resize(state,
                       (84, 84), interpolation=cv2.INTER_AREA),
            dtype=_uint8,
            **_tensor_kwargs
        )

    def _get_state_masked_ori(self):
        state = get_masked_dqn_state3(self._objects, self._ale.getScreenGrayscale())
        return _tensor(
            cv2.resize(state,
                       (84, 84), interpolation=cv2.INTER_AREA),
            dtype=_uint8,
            **_tensor_kwargs
        )

    def _fill_buffer(self):
        self._state_buffer.append(self._get_state())

    def _get_buffer_as_stack(self):
        return _stack(list(self._state_buffer), 0)

    window: pygame.Surface = None
    clock: pygame.time.Clock = None

    def _initialize_rendering(self, sample_image):
        assert sample_image is not None
        pygame.init()
        if self.render_mode == "human":
            pygame.display.set_caption(self.game_name)
        self.image_size = (sample_image.shape[1], sample_image.shape[0])
        self.window_size = (sample_image.shape[1] * UPSCALE_FACTOR,
                            sample_image.shape[0] * UPSCALE_FACTOR)  # render with higher res
        self.label_font = pygame.font.SysFont('Pixel12x10', 16)
        if self.render_mode == "human":
            self.window = pygame.display.set_mode(self.window_size)
            self.clock = pygame.time.Clock()
        else:
            self.window = pygame.Surface(self.window_size)
        self.rendering_initialized = True

    def render(self):
        """
        Compute the render frames (as specified by render_mode during the
        initialization of the environment). If activated, adds an overlay visualizing
        object properties like position, velocity vector, orientation, name, etc.
        See `env.render() <https://gymnasium.farama.org/api/env/#gymnasium.Env.render>`_
        for gymnasium details.
        """

        image = self._env.render()

        if not self.render_oc_overlay:
            if self.rendering_initialized:
                return image.swapaxes(0, 1).repeat(UPSCALE_FACTOR, axis=0).repeat(UPSCALE_FACTOR, axis=1)
            return image

        else:
            # Prepare screen if not initialized
            if not self.rendering_initialized:
                self._initialize_rendering(image)

            # Render env RGB image
            image = np.transpose(image, (1, 0, 2))
            image_surface = pygame.Surface(self.image_size)
            pygame.pixelcopy.array_to_surface(image_surface, image)
            upscaled_image = pygame.transform.scale(image_surface, self.window_size)
            self.window.blit(upscaled_image, (0, 0))

            # Init overlay surface
            overlay_surface = pygame.Surface(self.window_size)
            overlay_surface.set_colorkey((0, 0, 0))

            # For each object, render its position and velocity vector
            for game_object in self.objects:
                # if game_object is None:
                #     continue

                x, y = game_object.xy
                w, h = game_object.wh

                if x == np.nan:
                    continue

                # Object velocity
                dx = game_object.dx
                dy = game_object.dy

                # Transform to upscaled screen resolution
                x *= UPSCALE_FACTOR
                y *= UPSCALE_FACTOR
                w *= UPSCALE_FACTOR
                h *= UPSCALE_FACTOR
                dx *= UPSCALE_FACTOR
                dy *= UPSCALE_FACTOR

                # Compute center coordinates
                x_c = x + w // 2
                y_c = y + h // 2

                # Draw an 'X' at object center
                pygame.draw.line(overlay_surface, color=(255, 255, 255), width=2,
                                 start_pos=(x_c - 4, y_c - 4), end_pos=(x_c + 4, y_c + 4))
                pygame.draw.line(overlay_surface, color=(255, 255, 255), width=2,
                                 start_pos=(x_c - 4, y_c + 4), end_pos=(x_c + 4, y_c - 4))

                # Draw bounding box
                pygame.draw.rect(overlay_surface, color=(255, 255, 255),
                                 rect=(x, y, w, h), width=2)

                # Draw object category label (optional with value)
                label = game_object.category
                if isinstance(game_object, ValueObject):
                    label += f" ({game_object.value})"
                draw_label(self.window, label, position=(x, y + h + 4), font=self.label_font)

                # Draw object orientation
                # if game_object.orientation is not None:
                #     draw_orientation_indicator(overlay_surface, game_object.orientation.value, x_c, y_c, w, h)

                # Draw velocity vector
                if dx != 0 or dy != 0:
                    draw_arrow(overlay_surface,
                               start_pos=(float(x_c), float(y_c)),
                               end_pos=(x_c + 2 * dx, y_c + 2 * dy),
                               color=(100, 200, 255),
                               width=2)

            self.window.blit(overlay_surface, (0, 0))

            if self.render_mode == "human":
                # noinspection PyProtectedMember
                frameskip = self._env.unwrapped._frameskip  # noqa: F821
                if isinstance(frameskip, tuple):
                    frameskip = frameskip[0]
                self.clock.tick(60 // frameskip)  # limit FPS to avoid super fast movement
                pygame.display.flip()
                pygame.event.pump()

            elif self.render_mode == "rgb_array":
                return pygame.surfarray.array3d(self.window).swapaxes(0, 1)

    def close(self):
        """
        After the user has finished using the environment, close contains the code necessary to "clean up" the environment.
        See `env.close() <https://gymnasium.farama.org/api/env/#gymnasium.Env.close>`_ for gymnasium details.
        """
        return self._env.close()

    @property
    def nb_actions(self):
        """
        The number of actions available in this environment.

        :type: int
        """
        return self.action_space.n  # noqa: F821

    @property
    def dqn_obs(self):
        """
        The 4 (grey+down)scaled last frames (84x84) of the environment, used notably by dqn agents as states.

        :type: torch.tensor
        """
        return self._get_buffer_as_stack().unsqueeze(0).byte()

    @property
    def get_rgb_state(self):
        """
        :type: np.array
        """
        return self.getScreenRGB()

    def set_ram(self, target_ram_position, new_value):
        """
        Directly set a given value at a targeted RAM position.

        :param target_ram_position: The ram position to be altered
        :type target_ram_position: int
        :param new_value: The value to put at this RAM position
        :type new_value: int
        """
        return self._ale.setRAM(target_ram_position, new_value)

    def get_ram(self):
        """
        Returns the RAM state

        :return: The 128 list of RAM bytes
        :rtype: list of 128 uint8 values
        """
        return self._ale.getRAM()

    def get_action_meanings(self):
        return self._env.unwrapped.get_action_meanings()  # noqa: F821

    def _get_obs(self):
        # noinspection PyProtectedMember
        return self._env.unwrapped._get_obs()  # noqa: F821

    def getScreenRGB(self):
        return self._ale.getScreenRGB()

    def detect_objects_both(self):
        import ipdb
        ipdb.set_trace()
        detect_objects_ram(self.objects, self._ale.getRAM, self.ram_module_name, self.hud)
        detect_objects_vision(self.objects_v, self.getScreenRGB, self.vision_module_name, self.hud)

    def _clone_state(self):
        """
        Returns the current system_state of the environment.

        :return: State snapshot
        :rtype: env_snapshot
        """
        return self._ale.cloneSystemState()

    def _restore_state(self):
        """
        Restore the current system_state of the environment.
        """
        return self._ale.cloneSystemState()

    @property
    def objects(self):
        """
        A list of the object present in the environment. The objects are either \
        ocatari.vision.GameObject or ocatari.ram.GameObject, depending on the extraction method.

        :type: list of GameObjects
        """
        return [obj for obj in self._objects if obj]  # filtering out None objects

    @property
    def ocstate(self):
        """
        A list of the object present in the environment. The objects are either \
        ocatari.vision.GameObject or ocatari.ram.GameObject, depending on the extraction method.

        :type: list of GameObjects
        """
        import ipdb
        ipdb.set_trace()
        return [obj for obj in self._objects if obj]  # filtering out None objects

    def render_explanations(self):
        coefs = [0.05, 0.1, 0.25, 0.6]
        rendered = _zeros_like(self._state_buffer[0]).float()
        for coef, state_i in zip(coefs, self._state_buffer):
            rendered += coef * state_i
        rendered = rendered.cpu().detach().to(int).numpy()
        for obj in self.objects:
            mark_bb(rendered, obj.xywh, color=obj.rgb)
        import matplotlib.pyplot as plt
        plt.imshow(rendered)
        rows, cells, colors = [], [], []
        columns = ["X, Y", "W, H", "R, G, B"]
        for obj in self.objects:
            rows.append(obj.category)
            cells.append([obj.xy, obj.wh, obj.rgb])
            colors.append(to_rgba(obj.rgb))
        # import ipdb; ipdb.set_trace()
        t_height = 0.03 * len(rows)
        table = plt.table(cellText=cells,
                          rowLabels=rows,
                          rowColours=colors,
                          colLabels=columns,
                          colWidths=[.2, .2, .3],
                          bbox=[0.1, 1.02, 0.8, t_height],
                          loc='top')
        table.set_fontsize(14)
        plt.subplots_adjust(top=0.8)
        plt.show()

    def aggregated_render(self, coefs=(0.05, 0.1, 0.25, 0.6)):
        rendered = _zeros_like(self._state_buffer[0]).float()
        for coef, state_i in zip(coefs, self._state_buffer):
            rendered += coef * state_i
        rendered = rendered.cpu().detach().to(int).numpy()
        return rendered

    @property
    def unwrapped(self):
        return self._env.unwrapped
