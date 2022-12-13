#! /usr/bin/python3
import train
import evaluation
import yaml

if (__name__ == '__main__'):
    # load params
    params = None
    with open('config/default.yaml') as f:
        params = yaml.safe_load(f)

    # extract params
    train_params = params['train']
    eval_params = params['evaluation']
    for p in [train_params, eval_params]:
        p['network'] = params['network']
        p['name'] = params['name']

    # print(train_params)
    # print(eval_params)

    print("--- train ---")
    trained_model = train.train(train_params)

    # evaluation
    print("--- evaluation ---")
    evaluation.evaluation(trained_model, eval_params)
