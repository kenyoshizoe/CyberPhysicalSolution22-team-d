#! /usr/bin/python3
from train import train
from evaluation import evaluation
import yaml

if (__name__ == '__main__'):
    # load params
    params = None
    with open('config/default.yaml') as f:
        params = yaml.safe_load(f)

    print("--- train ---")
    train_params = params['train']
    train_params['network'] = params['network']
    train_params['name'] = params['name']

    trained_model = train(train_params)

    # evaluation
    print("--- evaluation ---")
    base_params = params['evaluation']
    base_params['network'] = params['network']
    base_params['name'] = params['name']

    PRINT_RESULT = False

    for setting in params['evaluation_settings']:
        eval_params = base_params.copy()
        eval_params.update(params[setting])
        # evaluation
        print("--- evaluation {} ---".format(setting))
        evaluation(trained_model, eval_params)
