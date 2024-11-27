# Models

## The different type of models
There are two different models `dqn.gz` und `c51.gz`. Both models are taken from https://github.com/floringogianu/atari-agents. 
The DQN model refers to the modern DQN (or M-DQN) model from the repo, while the c51 model is a implementation of the architecture introduced by http://proceedings.mlr.press/v70/bellemare17a.html, also imported from Gogianu.

We extended the list of models, using https://github.com/vwxyzjn/cleanrl, to also include PPO models and to cover more than 45 games. Our combined list can be found under https://drive.google.com/drive/folders/1oCLc2cyftDFUepVZewt6msA3ZtLFDViG?usp=drive_link

## Usage
The easiest way is to load an agent based on its path, see example below. After loading an agent, one can calculate a policy bases on the current observation state and use this max(policy) as potential next action. 

```python
    opts.path = f"../models/{opts.game}/dqn.gz"
    dqn_agent = load_agent(opts, env.action_space.n)
    
    action = dqn_agent.draw_action(env.dqn_obs)
    obs, reward, terminated, truncated, info = env.step(action)
```

